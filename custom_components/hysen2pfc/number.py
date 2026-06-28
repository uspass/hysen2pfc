"""
Number platform for the Hysen 2 Pipe Fan Coil integration.

Provides three NumberEntity instances:

- HysenCalibrationNumber — temperature sensor offset (-5.0 to +5.0 degC, 0.1 steps).
  Adjusts the displayed room temperature without changing setpoints.

- HysenMaxTempNumber — upper bound for the setpoint in the active HVAC mode.
  Available only when the device is on in COOL or HEAT mode. Its minimum
  slider bound is dynamically set to max(mode_min, target_temp, mode_min_temp)
  to prevent setting a max below the current target or mode minimum.

- HysenMinTempNumber — lower bound for the setpoint in the active HVAC mode.
  Available only when the device is on in COOL or HEAT mode. Its maximum
  slider bound is dynamically set to min(mode_max, target_temp, mode_max_temp).
"""

import logging
import voluptuous as vol
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_platform
from homeassistant.components.number import NumberEntity
from homeassistant.components.climate import HVACMode
from .const import (
    DOMAIN,
    UnitOfTemperature,
    STATE_OFF,
    PRECISION_WHOLE,
    PRECISION_TENTHS,
    DATA_KEY_CALIBRATION,
    DATA_KEY_MAX_TEMP,
    DATA_KEY_MIN_TEMP,
    DATA_KEY_COOLING_MAX_TEMP,
    DATA_KEY_COOLING_MIN_TEMP,
    DATA_KEY_HEATING_MAX_TEMP,
    DATA_KEY_HEATING_MIN_TEMP,
    DATA_KEY_TARGET_TEMP,
    DATA_KEY_HVAC_MODE,
    DATA_KEY_POWER_STATE,
    ATTR_CALIBRATION,
    ATTR_MAX_TEMP,
    ATTR_MIN_TEMP,
    SERVICE_SET_CALIBRATION,
    SERVICE_SET_MAX_TEMP,
    SERVICE_SET_MIN_TEMP,
    HYSEN2PFC_CALIBRATION_MIN,
    HYSEN2PFC_CALIBRATION_MAX,
    HYSEN2PFC_COOLING_MAX_TEMP,
    HYSEN2PFC_COOLING_MIN_TEMP,
    HYSEN2PFC_HEATING_MAX_TEMP,
    HYSEN2PFC_HEATING_MIN_TEMP,
)
from .entity import HysenEntity

_LOGGER = logging.getLogger(__name__)

_TEMP_RANGE_MIN = min(HYSEN2PFC_COOLING_MIN_TEMP, HYSEN2PFC_HEATING_MIN_TEMP)
_TEMP_RANGE_MAX = max(HYSEN2PFC_COOLING_MAX_TEMP, HYSEN2PFC_HEATING_MAX_TEMP)


async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities):
    """Set up the Hysen number entities from a config entry."""
    device_data = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([
        HysenCalibrationNumber(device_data),
        HysenMaxTempNumber(device_data),
        HysenMinTempNumber(device_data),
    ])

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_SET_CALIBRATION,
        {
            vol.Required(ATTR_CALIBRATION): vol.All(
                vol.Coerce(float),
                vol.Range(min=HYSEN2PFC_CALIBRATION_MIN, max=HYSEN2PFC_CALIBRATION_MAX),
            )
        },
        "async_set_calibration",
    )
    platform.async_register_entity_service(
        SERVICE_SET_MAX_TEMP,
        {
            vol.Required(ATTR_MAX_TEMP): vol.All(
                vol.Coerce(int),
                vol.Range(min=_TEMP_RANGE_MIN, max=_TEMP_RANGE_MAX),
            )
        },
        "async_set_max_temp",
    )
    platform.async_register_entity_service(
        SERVICE_SET_MIN_TEMP,
        {
            vol.Required(ATTR_MIN_TEMP): vol.All(
                vol.Coerce(int),
                vol.Range(min=_TEMP_RANGE_MIN, max=_TEMP_RANGE_MAX),
            )
        },
        "async_set_min_temp",
    )


# ---------------------------------------------------------------------------
# Calibration
# ---------------------------------------------------------------------------

class HysenCalibrationNumber(HysenEntity, NumberEntity):
    """Calibration offset for the room temperature sensor."""

    def __init__(self, device_data):
        super().__init__(device_data["coordinator"], device_data)
        self._attr_unique_id = f"{device_data['mac']}_calibration"
        self._attr_name = f"{device_data['name']} Sensor Calibration"
        self._attr_native_min_value = HYSEN2PFC_CALIBRATION_MIN
        self._attr_native_max_value = HYSEN2PFC_CALIBRATION_MAX
        self._attr_native_step = PRECISION_TENTHS
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_icon = "mdi:thermometer"
        self._attr_native_value = self.coordinator.data.get(DATA_KEY_CALIBRATION)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Refresh calibration value from coordinator data."""
        self._attr_native_value = self.coordinator.data.get(DATA_KEY_CALIBRATION)
        self.async_write_ha_state()

    @property
    def native_value(self):
        return self._attr_native_value

    async def async_set_native_value(self, value: float):
        """Set the calibration value."""
        _LOGGER.debug("[%s] Setting calibration to %s", self._host, value)
        await self._async_try_command(
            "Error in set_calibration",
            self.coordinator.device.set_calibration,
            value,
        )

    async def async_set_calibration(self, calibration):
        """Service call handler."""
        await self.async_set_native_value(calibration)


# ---------------------------------------------------------------------------
# Max Temperature
# ---------------------------------------------------------------------------

class HysenMaxTempNumber(HysenEntity, NumberEntity):
    """Maximum allowed setpoint temperature (mode-dependent)."""

    def __init__(self, device_data):
        super().__init__(device_data["coordinator"], device_data)
        self._attr_unique_id = f"{device_data['mac']}_max_temp"
        self._attr_name = f"{device_data['name']} Max Temperature"
        self._attr_native_step = PRECISION_WHOLE
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_icon = "mdi:thermometer-high"
        self._attr_native_value = self._resolve_native_value()

    def _resolve_native_value(self):
        hvac_mode = self.coordinator.data.get(DATA_KEY_HVAC_MODE)
        if hvac_mode == HVACMode.COOL:
            return self.coordinator.data.get(DATA_KEY_COOLING_MAX_TEMP)
        if hvac_mode == HVACMode.HEAT:
            return self.coordinator.data.get(DATA_KEY_HEATING_MAX_TEMP)
        return None

    @callback
    def _handle_coordinator_update(self) -> None:
        self._attr_native_value = self._resolve_native_value()
        self.async_write_ha_state()

    @property
    def available(self):
        """Available only in COOL or HEAT mode."""
        if not self.coordinator.last_update_success:
            return False
        if self.coordinator.data.get(DATA_KEY_POWER_STATE) == STATE_OFF:
            return False
        return self.coordinator.data.get(DATA_KEY_HVAC_MODE) in (HVACMode.COOL, HVACMode.HEAT)

    @property
    def native_value(self):
        return self._attr_native_value

    @property
    def native_min_value(self):
        hvac_mode = self.coordinator.data.get(DATA_KEY_HVAC_MODE)
        target_temp = self.coordinator.data.get(DATA_KEY_TARGET_TEMP)
        if hvac_mode == HVACMode.COOL:
            min_temp = self.coordinator.data.get(DATA_KEY_COOLING_MIN_TEMP)
            base = HYSEN2PFC_COOLING_MIN_TEMP
        elif hvac_mode == HVACMode.HEAT:
            min_temp = self.coordinator.data.get(DATA_KEY_HEATING_MIN_TEMP)
            base = HYSEN2PFC_HEATING_MIN_TEMP
        else:
            return HYSEN2PFC_COOLING_MIN_TEMP
        result = base
        if target_temp is not None:
            result = max(result, target_temp)
        if min_temp is not None:
            result = max(result, min_temp)
        return result

    @property
    def native_max_value(self):
        hvac_mode = self.coordinator.data.get(DATA_KEY_HVAC_MODE)
        if hvac_mode == HVACMode.COOL:
            return HYSEN2PFC_COOLING_MAX_TEMP
        if hvac_mode == HVACMode.HEAT:
            return HYSEN2PFC_HEATING_MAX_TEMP
        return HYSEN2PFC_COOLING_MAX_TEMP

    async def async_set_native_value(self, value: float):
        """Set the max temperature (mode-aware)."""
        hvac_mode = self.coordinator.data.get(DATA_KEY_HVAC_MODE)
        target_temp = self.coordinator.data.get(DATA_KEY_TARGET_TEMP)

        if hvac_mode == HVACMode.COOL:
            min_temp = self.coordinator.data.get(DATA_KEY_COOLING_MIN_TEMP)
            if target_temp is not None and value < target_temp:
                raise ServiceValidationError(
                    f"Cooling max temperature ({value}°C) must not be lower than target temperature ({target_temp}°C)",
                    translation_domain=DOMAIN,
                    translation_key="cooling_max_below_target",
                )
            if min_temp is not None and value < min_temp:
                raise ServiceValidationError(
                    f"Cooling max temperature ({value}°C) must not be lower than cooling min temperature ({min_temp}°C)",
                    translation_domain=DOMAIN,
                    translation_key="cooling_max_below_min",
                )
            _LOGGER.debug("[%s] Setting cooling max temp to %s", self._host, value)
            await self._async_try_command(
                "Error in set_cooling_max_temp",
                self.coordinator.device.set_cooling_max_temp,
                int(value),
            )
        elif hvac_mode == HVACMode.HEAT:
            min_temp = self.coordinator.data.get(DATA_KEY_HEATING_MIN_TEMP)
            if target_temp is not None and value < target_temp:
                raise ServiceValidationError(
                    f"Heating max temperature ({value}°C) must not be lower than target temperature ({target_temp}°C)",
                    translation_domain=DOMAIN,
                    translation_key="heating_max_below_target",
                )
            if min_temp is not None and value < min_temp:
                raise ServiceValidationError(
                    f"Heating max temperature ({value}°C) must not be lower than heating min temperature ({min_temp}°C)",
                    translation_domain=DOMAIN,
                    translation_key="heating_max_below_min",
                )
            _LOGGER.debug("[%s] Setting heating max temp to %s", self._host, value)
            await self._async_try_command(
                "Error in set_heating_max_temp",
                self.coordinator.device.set_heating_max_temp,
                int(value),
            )
        else:
            raise ServiceValidationError(
                f"Cannot set max temperature in {hvac_mode} mode",
                translation_domain=DOMAIN,
                translation_key="invalid_hvac_mode_for_temp",
            )

    async def async_set_max_temp(self, max_temp):
        """Service call handler."""
        await self.async_set_native_value(max_temp)


# ---------------------------------------------------------------------------
# Min Temperature
# ---------------------------------------------------------------------------

class HysenMinTempNumber(HysenEntity, NumberEntity):
    """Minimum allowed setpoint temperature (mode-dependent)."""

    def __init__(self, device_data):
        super().__init__(device_data["coordinator"], device_data)
        self._attr_unique_id = f"{device_data['mac']}_min_temp"
        self._attr_name = f"{device_data['name']} Min Temperature"
        self._attr_native_step = PRECISION_WHOLE
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_icon = "mdi:thermometer-low"
        self._attr_native_value = self._resolve_native_value()

    def _resolve_native_value(self):
        hvac_mode = self.coordinator.data.get(DATA_KEY_HVAC_MODE)
        if hvac_mode == HVACMode.COOL:
            return self.coordinator.data.get(DATA_KEY_COOLING_MIN_TEMP)
        if hvac_mode == HVACMode.HEAT:
            return self.coordinator.data.get(DATA_KEY_HEATING_MIN_TEMP)
        return None

    @callback
    def _handle_coordinator_update(self) -> None:
        self._attr_native_value = self._resolve_native_value()
        self.async_write_ha_state()

    @property
    def available(self):
        """Available only in COOL or HEAT mode."""
        if not self.coordinator.last_update_success:
            return False
        if self.coordinator.data.get(DATA_KEY_POWER_STATE) == STATE_OFF:
            return False
        return self.coordinator.data.get(DATA_KEY_HVAC_MODE) in (HVACMode.COOL, HVACMode.HEAT)

    @property
    def native_value(self):
        return self._attr_native_value

    @property
    def native_min_value(self):
        hvac_mode = self.coordinator.data.get(DATA_KEY_HVAC_MODE)
        if hvac_mode == HVACMode.COOL:
            return HYSEN2PFC_COOLING_MIN_TEMP
        if hvac_mode == HVACMode.HEAT:
            return HYSEN2PFC_HEATING_MIN_TEMP
        return HYSEN2PFC_COOLING_MIN_TEMP

    @property
    def native_max_value(self):
        hvac_mode = self.coordinator.data.get(DATA_KEY_HVAC_MODE)
        target_temp = self.coordinator.data.get(DATA_KEY_TARGET_TEMP)
        if hvac_mode == HVACMode.COOL:
            max_temp = self.coordinator.data.get(DATA_KEY_COOLING_MAX_TEMP)
            base = HYSEN2PFC_COOLING_MAX_TEMP
        elif hvac_mode == HVACMode.HEAT:
            max_temp = self.coordinator.data.get(DATA_KEY_HEATING_MAX_TEMP)
            base = HYSEN2PFC_HEATING_MAX_TEMP
        else:
            return HYSEN2PFC_COOLING_MAX_TEMP
        result = base
        if target_temp is not None:
            result = min(result, target_temp)
        if max_temp is not None:
            result = min(result, max_temp)
        return result

    async def async_set_native_value(self, value: float):
        """Set the min temperature (mode-aware)."""
        hvac_mode = self.coordinator.data.get(DATA_KEY_HVAC_MODE)
        target_temp = self.coordinator.data.get(DATA_KEY_TARGET_TEMP)

        if hvac_mode == HVACMode.COOL:
            max_temp = self.coordinator.data.get(DATA_KEY_COOLING_MAX_TEMP)
            if target_temp is not None and value > target_temp:
                raise ServiceValidationError(
                    f"Cooling min temperature ({value}°C) must not be higher than target temperature ({target_temp}°C)",
                    translation_domain=DOMAIN,
                    translation_key="cooling_min_above_target",
                )
            if max_temp is not None and value > max_temp:
                raise ServiceValidationError(
                    f"Cooling min temperature ({value}°C) must not be higher than cooling max temperature ({max_temp}°C)",
                    translation_domain=DOMAIN,
                    translation_key="cooling_min_above_max",
                )
            _LOGGER.debug("[%s] Setting cooling min temp to %s", self._host, value)
            await self._async_try_command(
                "Error in set_cooling_min_temp",
                self.coordinator.device.set_cooling_min_temp,
                int(value),
            )
        elif hvac_mode == HVACMode.HEAT:
            max_temp = self.coordinator.data.get(DATA_KEY_HEATING_MAX_TEMP)
            if target_temp is not None and value > target_temp:
                raise ServiceValidationError(
                    f"Heating min temperature ({value}°C) must not be higher than target temperature ({target_temp}°C)",
                    translation_domain=DOMAIN,
                    translation_key="heating_min_above_target",
                )
            if max_temp is not None and value > max_temp:
                raise ServiceValidationError(
                    f"Heating min temperature ({value}°C) must not be higher than heating max temperature ({max_temp}°C)",
                    translation_domain=DOMAIN,
                    translation_key="heating_min_above_max",
                )
            _LOGGER.debug("[%s] Setting heating min temp to %s", self._host, value)
            await self._async_try_command(
                "Error in set_heating_min_temp",
                self.coordinator.device.set_heating_min_temp,
                int(value),
            )
        else:
            raise ServiceValidationError(
                f"Cannot set min temperature in {hvac_mode} mode",
                translation_domain=DOMAIN,
                translation_key="invalid_hvac_mode_for_temp",
            )

    async def async_set_min_temp(self, min_temp):
        """Service call handler."""
        await self.async_set_native_value(min_temp)
