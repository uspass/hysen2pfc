"""
Support for Hysen 2 Pipe Fan Coil Controller number entities.

This module provides number entities for setting calibration and dynamic max/min temperatures based on HVAC mode.
"""

import logging
import asyncio
import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.components.number import NumberEntity
from homeassistant.components.climate import HVACMode
from .const import (
    DOMAIN,
    UnitOfTemperature,
    STATE_OFF,
    DATA_KEY_CALIBRATION,
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

async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities):
    """Set up the Hysen number entities from a config entry.

    Args:
        hass: The Home Assistant instance.
        config_entry: The configuration entry containing device details.
        async_add_entities: Callback to add entities asynchronously.

    Returns:
        None
    """
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
                vol.Range(min=HYSEN2PFC_CALIBRATION_MIN, max=HYSEN2PFC_CALIBRATION_MAX)
            )
        },
        "async_set_calibration",
    )
    platform.async_register_entity_service(
        SERVICE_SET_MAX_TEMP,
        {
            vol.Required(ATTR_MAX_TEMP): vol.All(
                vol.Coerce(int),
                vol.Range(min=HYSEN2PFC_COOLING_MIN_TEMP, max=HYSEN2PFC_COOLING_MAX_TEMP)
            )
        },
        "async_set_max_temp",
    )
    platform.async_register_entity_service(
        SERVICE_SET_MIN_TEMP,
        {
            vol.Required(ATTR_MIN_TEMP): vol.All(
                vol.Coerce(int),
                vol.Range(min=HYSEN2PFC_COOLING_MIN_TEMP, max=HYSEN2PFC_COOLING_MAX_TEMP)
            )
        },
        "async_set_min_temp",
    )

class HysenCalibrationNumber(HysenEntity, NumberEntity):
    """Representation of a Hysen Calibration number entity."""

    def __init__(self, device_data):
        """Initialize the number entity.

        Args:
            device_data: Dictionary containing device-specific data.
        """
        super().__init__(device_data["coordinator"], device_data)
        self._attr_unique_id = f"{device_data['mac']}_calibration"
        self._attr_name = f"{device_data['name']} Sensor Calibration"
        self._attr_native_min_value = HYSEN2PFC_CALIBRATION_MIN
        self._attr_native_max_value = HYSEN2PFC_CALIBRATION_MAX
        self._attr_native_step = 0.1
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_icon = "mdi:thermometer"

    @property
    def native_value(self):
        """Return the current calibration value.

        Returns:
            float: The current calibration.
        """
        return self.coordinator.data.get(DATA_KEY_CALIBRATION)

    async def async_set_native_value(self, value: float):
        """Set the calibration value.

        Args:
            value: The calibration value to set.

        Returns:
            None
        """
        _LOGGER.debug("[%s] Setting calibration to %s", self._host, value)
        success = await self._async_try_command(
            "Error in set_calibration",
            self.coordinator.device.set_calibration,
            value,
        )
        if success:
            # Delay to allow device to stabilize
            await asyncio.sleep(0.2)
            # Force an immediate update to fetch the latest device state
            await self.coordinator.async_refresh()
            self.async_write_ha_state()

    async def async_set_calibration(self, calibration):
        """Set the calibration value (for service calls).

        Args:
            calibration: The calibration value to set.

        Returns:
            None
        """
        await self.async_set_native_value(calibration)

class HysenMaxTempNumber(HysenEntity, NumberEntity):
    """Representation of a Hysen Max Temperature number entity."""

    def __init__(self, device_data):
        """Initialize the number entity.

        Args:
            device_data: Dictionary containing device-specific data.
        """
        super().__init__(device_data["coordinator"], device_data)
        self._attr_unique_id = f"{device_data['mac']}_max_temp"
        self._attr_native_step = 1
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_icon = "mdi:thermometer"
        self._attr_entity_registry_enabled_default = True  # Enabled by default

    @property
    def available(self):
        """Return True if the entity is available (not in fan_only or off mode).

        Returns:
            bool: Availability status.
        """
        power_state = self.coordinator.data.get(DATA_KEY_POWER_STATE)
        if power_state == STATE_OFF:
            _LOGGER.debug(
                "[%s] Max Temperature entity unavailable, power state: %s",
                self._host,
                power_state,
            )
            return False
        hvac_mode = self.coordinator.data.get(DATA_KEY_HVAC_MODE)
        is_available = hvac_mode in (HVACMode.COOL, HVACMode.HEAT)
        if not is_available:
            _LOGGER.debug(
                "[%s] Max Temperature entity unavailable, HVAC mode: %s, power state: %s, last_update_success: %s",
                self._host,
                hvac_mode,
                power_state,
                self.coordinator.last_update_success,
            )
        return is_available

    @property
    def name(self):
        """Return the name of the entity.

        Returns:
            str: The entity name.
        """
        return f"{self._attr_device_info['name']} Max Temperature"

    @property
    def native_min_value(self):
        """Return the minimum allowed value, based on HVAC mode, target temp, and min temp.

        Returns:
            int: The minimum value.
        """
        hvac_mode = self.coordinator.data.get(DATA_KEY_HVAC_MODE)
        target_temp = self.coordinator.data.get(DATA_KEY_TARGET_TEMP)
        if hvac_mode == HVACMode.COOL:
            min_temp = self.coordinator.data.get(DATA_KEY_COOLING_MIN_TEMP)
            min_value = HYSEN2PFC_COOLING_MIN_TEMP
            if target_temp is not None:
                min_value = max(min_value, target_temp)
            if min_temp is not None:
                min_value = max(min_value, min_temp)
            return min_value
        elif hvac_mode == HVACMode.HEAT:
            min_temp = self.coordinator.data.get(DATA_KEY_HEATING_MIN_TEMP)
            min_value = HYSEN2PFC_HEATING_MIN_TEMP
            if target_temp is not None:
                min_value = max(min_value, target_temp)
            if min_temp is not None:
                min_value = max(min_value, min_temp)
            return min_value
        return HYSEN2PFC_COOLING_MIN_TEMP

    @property
    def native_max_value(self):
        """Return the maximum allowed value, based on HVAC mode.

        Returns:
            int: The maximum value.
        """
        hvac_mode = self.coordinator.data.get(DATA_KEY_HVAC_MODE)
        if hvac_mode == HVACMode.COOL:
            return HYSEN2PFC_COOLING_MAX_TEMP
        elif hvac_mode == HVACMode.HEAT:
            return HYSEN2PFC_HEATING_MAX_TEMP
        return HYSEN2PFC_COOLING_MAX_TEMP

    @property
    def native_value(self):
        """Return the current max temperature value based on HVAC mode.

        Returns:
            int: The current max temperature.
        """
        hvac_mode = self.coordinator.data.get(DATA_KEY_HVAC_MODE)
        if hvac_mode == HVACMode.COOL:
            return self.coordinator.data.get(DATA_KEY_COOLING_MAX_TEMP)
        elif hvac_mode == HVACMode.HEAT:
            return self.coordinator.data.get(DATA_KEY_HEATING_MAX_TEMP)
        return None

    async def async_set_native_value(self, value: float):
        """Set the max temperature value based on HVAC mode.

        Args:
            value: The max temperature to set.

        Returns:
            None

        Raises:
            ValueError: If the value is invalid for the current mode.
        """
        hvac_mode = self.coordinator.data.get(DATA_KEY_HVAC_MODE)
        target_temp = self.coordinator.data.get(DATA_KEY_TARGET_TEMP)
        if hvac_mode == HVACMode.COOL:
            min_temp = self.coordinator.data.get(DATA_KEY_COOLING_MIN_TEMP)
            if target_temp is not None and value < target_temp:
                _LOGGER.error(
                    "[%s] Cooling max temp (%s) cannot be set lower than target temp (%s)",
                    self._host,
                    value,
                    target_temp,
                )
                raise ValueError(
                    f"Cooling max temperature ({value}°C) must not be lower than target temperature ({target_temp}°C)"
                )
            if min_temp is not None and value < min_temp:
                _LOGGER.error(
                    "[%s] Cooling max temp (%s) cannot be set lower than cooling min temp (%s)",
                    self._host,
                    value,
                    min_temp,
                )
                raise ValueError(
                    f"Cooling max temperature ({value}°C) must not be lower than cooling min temperature ({min_temp}°C)"
                )
            _LOGGER.debug("[%s] Setting cooling max temp to %s", self._host, value)
            success = await self._async_try_command(
                "Error in set_cooling_max_temp",
                self.coordinator.device.set_cooling_max_temp,
                int(value),
            )
        elif hvac_mode == HVACMode.HEAT:
            min_temp = self.coordinator.data.get(DATA_KEY_HEATING_MIN_TEMP)
            if target_temp is not None and value < target_temp:
                _LOGGER.error(
                    "[%s] Heating max temp (%s) cannot be set lower than target temp (%s)",
                    self._host,
                    value,
                    target_temp,
                )
                raise ValueError(
                    f"Heating max temperature ({value}°C) must not be lower than target temperature ({target_temp}°C)"
                )
            if min_temp is not None and value < min_temp:
                _LOGGER.error(
                    "[%s] Heating max temp (%s) cannot be set lower than heating min temp (%s)",
                    self._host,
                    value,
                    min_temp,
                )
                raise ValueError(
                    f"Heating max temperature ({value}°C) must not be lower than heating min temperature ({min_temp}°C)"
                )
            _LOGGER.debug("[%s] Setting heating max temp to %s", self._host, value)
            success = await self._async_try_command(
                "Error in set_heating_max_temp",
                self.coordinator.device.set_heating_max_temp,
                int(value),
            )
        else:
            _LOGGER.error("[%s] Cannot set max temp in mode %s", self._host, hvac_mode)
            raise ValueError(f"Cannot set max temperature in {hvac_mode} mode")

        if success:
            # Delay to allow device to stabilize
            await asyncio.sleep(0.2)
            # Force an immediate update to fetch the latest device state
            await self.coordinator.async_refresh()
            self.async_write_ha_state()

    async def async_set_max_temp(self, max_temp):
        """Set the max temperature value (for service calls).

        Args:
            max_temp: The max temperature to set.

        Returns:
            None
        """
        await self.async_set_native_value(max_temp)

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator.

        Returns:
            None
        """
        super()._handle_coordinator_update()
        # Update the state to reflect changes in availability, name, or native_min_value
        self.async_write_ha_state()

class HysenMinTempNumber(HysenEntity, NumberEntity):
    """Representation of a Hysen Min Temperature number entity."""

    def __init__(self, device_data):
        """Initialize the number entity.

        Args:
            device_data: Dictionary containing device-specific data.
        """
        super().__init__(device_data["coordinator"], device_data)
        self._attr_unique_id = f"{device_data['mac']}_min_temp"
        self._attr_native_step = 1
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_icon = "mdi:thermometer"
        self._attr_entity_registry_enabled_default = True  # Enabled by default

    @property
    def available(self):
        """Return True if the entity is available (not in fan_only or off mode).

        Returns:
            bool: Availability status.
        """
        power_state = self.coordinator.data.get(DATA_KEY_POWER_STATE)
        if power_state == STATE_OFF:
            _LOGGER.debug(
                "[%s] Min Temperature entity unavailable, power state: %s",
                self._host,
                power_state,
            )
            return False
        hvac_mode = self.coordinator.data.get(DATA_KEY_HVAC_MODE)
        is_available = hvac_mode in (HVACMode.COOL, HVACMode.HEAT)
        if not is_available:
            _LOGGER.debug(
                "[%s] Min Temperature entity unavailable, HVAC mode: %s, power state: %s, last_update_success: %s",
                self._host,
                hvac_mode,
                power_state,
                self.coordinator.last_update_success,
            )
        return is_available

    @property
    def name(self):
        """Return the name of the entity.

        Returns:
            str: The entity name.
        """
        return f"{self._attr_device_info['name']} Min Temperature"

    @property
    def native_min_value(self):
        """Return the minimum allowed value, based on HVAC mode.

        Returns:
            int: The minimum value.
        """
        hvac_mode = self.coordinator.data.get(DATA_KEY_HVAC_MODE)
        if hvac_mode == HVACMode.COOL:
            return HYSEN2PFC_COOLING_MIN_TEMP
        elif hvac_mode == HVACMode.HEAT:
            return HYSEN2PFC_HEATING_MIN_TEMP
        return HYSEN2PFC_COOLING_MIN_TEMP

    @property
    def native_max_value(self):
        """Return the maximum allowed value, based on HVAC mode, target temp, and max temp.

        Returns:
            int: The maximum value.
        """
        hvac_mode = self.coordinator.data.get(DATA_KEY_HVAC_MODE)
        target_temp = self.coordinator.data.get(DATA_KEY_TARGET_TEMP)
        if hvac_mode == HVACMode.COOL:
            max_temp = self.coordinator.data.get(DATA_KEY_COOLING_MAX_TEMP)
            max_value = HYSEN2PFC_COOLING_MAX_TEMP
            if target_temp is not None:
                max_value = min(max_value, target_temp)
            if max_temp is not None:
                max_value = min(max_value, max_temp)
            return max_value
        elif hvac_mode == HVACMode.HEAT:
            max_temp = self.coordinator.data.get(DATA_KEY_HEATING_MAX_TEMP)
            max_value = HYSEN2PFC_HEATING_MAX_TEMP
            if target_temp is not None:
                max_value = min(max_value, target_temp)
            if max_temp is not None:
                max_value = min(max_value, max_temp)
            return max_value
        return HYSEN2PFC_COOLING_MAX_TEMP

    @property
    def native_value(self):
        """Return the current min temperature value based on HVAC mode.

        Returns:
            int: The current min temperature.
        """
        hvac_mode = self.coordinator.data.get(DATA_KEY_HVAC_MODE)
        if hvac_mode == HVACMode.COOL:
            return self.coordinator.data.get(DATA_KEY_COOLING_MIN_TEMP)
        elif hvac_mode == HVACMode.HEAT:
            return self.coordinator.data.get(DATA_KEY_HEATING_MIN_TEMP)
        return None

    async def async_set_native_value(self, value: float):
        """Set the min temperature value based on HVAC mode.

        Args:
            value: The min temperature to set.

        Returns:
            None

        Raises:
            ValueError: If the value is invalid for the current mode.
        """
        hvac_mode = self.coordinator.data.get(DATA_KEY_HVAC_MODE)
        target_temp = self.coordinator.data.get(DATA_KEY_TARGET_TEMP)

        if hvac_mode == HVACMode.COOL:
            max_temp = self.coordinator.data.get(DATA_KEY_COOLING_MAX_TEMP)
            if target_temp is not None and value > target_temp:
                _LOGGER.error(
                    "[%s] Cooling min temp (%s) cannot be set higher than target temp (%s)",
                    self._host,
                    value,
                    target_temp,
                )
                raise ValueError(
                    f"Cooling min temperature ({value}°C) must not be higher than target temperature ({target_temp}°C)"
                )
            if max_temp is not None and value > max_temp:
                _LOGGER.error(
                    "[%s] Cooling min temp (%s) cannot be set higher than cooling max temp (%s)",
                    self._host,
                    value,
                    max_temp,
                )
                raise ValueError(
                    f"Cooling min temperature ({value}°C) must not be higher than cooling max temperature ({max_temp}°C)"
                )
            _LOGGER.debug("[%s] Setting cooling min temp to %s", self._host, value)
            success = await self._async_try_command(
                "Error in set_cooling_min_temp",
                self.coordinator.device.set_cooling_min_temp,
                int(value),
            )
        elif hvac_mode == HVACMode.HEAT:
            max_temp = self.coordinator.data.get(DATA_KEY_HEATING_MAX_TEMP)
            if target_temp is not None and value > target_temp:
                _LOGGER.error(
                    "[%s] Heating min temp (%s) cannot be set higher than target temp (%s)",
                    self._host,
                    value,
                    target_temp,
                )
                raise ValueError(
                    f"Heating min temperature ({value}°C) must not be higher than target temperature ({target_temp}°C)"
                )
            if max_temp is not None and value > max_temp:
                _LOGGER.error(
                    "[%s] Heating min temp (%s) cannot be set higher than heating max temp (%s)",
                    self._host,
                    value,
                    max_temp,
                )
                raise ValueError(
                    f"Heating min temperature ({value}°C) must not be higher than heating max temperature ({max_temp}°C)"
                )
            _LOGGER.debug("[%s] Setting heating min temp to %s", self._host, value)
            success = await self._async_try_command(
                "Error in set_heating_min_temp",
                self.coordinator.device.set_heating_min_temp,
                int(value),
            )
        else:
            _LOGGER.error("[%s] Cannot set min temp in mode %s", self._host, hvac_mode)
            raise ValueError(f"Cannot set min temperature in {hvac_mode} mode")

        if success:
            # Delay to allow device to stabilize
            await asyncio.sleep(0.2)
            # Force an immediate update to fetch the latest device state
            await self.coordinator.async_refresh()
            self.async_write_ha_state()

    async def async_set_min_temp(self, min_temp):
        """Set the min temperature value (for service calls).

        Args:
            min_temp: The min temperature to set.

        Returns:
            None
        """
        await self.async_set_native_value(min_temp)

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator.

        Returns:
            None
        """
        super()._handle_coordinator_update()
        # Update the state to reflect changes in availability, name, or native_max_value
        self.async_write_ha_state()