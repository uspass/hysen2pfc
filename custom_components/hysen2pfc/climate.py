"""
Climate platform for the Hysen 2 Pipe Fan Coil integration.

Provides HysenClimate, a ClimateEntity that controls the Hysen HY03AC-1-Wifi
fan coil unit. Supported features vary by device state:

  OFF          : TURN_ON | TURN_OFF
  FAN_ONLY     : TURN_ON | TURN_OFF | FAN_MODE
  HEAT / COOL  : TURN_ON | TURN_OFF | FAN_MODE | TARGET_TEMPERATURE | PRESET_MODE

Available HVAC and fan modes shown in the UI are dynamic and computed by the
coordinator to prevent invalid combinations (e.g. FAN_ONLY with auto fan speed).
"""

import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.exceptions import ServiceValidationError
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_platform
from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature
from .const import (
    DOMAIN,
    PRECISION_WHOLE,
    UnitOfTemperature,
    DEFAULT_CURRENT_TEMP,
    DEFAULT_TARGET_TEMP_STEP,
    DATA_KEY_VALVE_STATE,
    DATA_KEY_POWER_STATE,
    DATA_KEY_HVAC_MODE,
    DATA_KEY_HVAC_MODES,
    DATA_KEY_FAN_MODE,
    DATA_KEY_FAN_MODES,
    DATA_KEY_HVAC_ACTION,
    DATA_KEY_CURRENT_TEMP,
    DATA_KEY_TARGET_TEMP,
    DATA_KEY_PRESET_MODE,
    DATA_KEY_MIN_TEMP,
    DATA_KEY_MAX_TEMP,
    DATA_KEY_COOLING_MAX_TEMP,
    DATA_KEY_COOLING_MIN_TEMP,
    DATA_KEY_HEATING_MAX_TEMP,
    DATA_KEY_HEATING_MIN_TEMP,
    STATE_ON,
    STATE_OFF,
    HVACMode,
    ATTR_TEMPERATURE,
    ATTR_HVAC_MODE,
    ATTR_FAN_MODE,
    ATTR_PRESET_MODE,
    ATTR_POWER_STATE,
    ATTR_COOLING_MAX_TEMP,
    ATTR_COOLING_MIN_TEMP,
    ATTR_HEATING_MAX_TEMP,
    ATTR_HEATING_MIN_TEMP,
    ATTR_VALVE_STATE,
    SERVICE_TURN_ON,
    SERVICE_TURN_OFF,
    HVAC_MODES,
    HVAC_MODES_NO_FAN,
    HVAC_MODES_COOL,
    HVAC_MODES_HEAT,
    HVAC_MODES_FAN_ONLY,
    FAN_AUTO,
    FAN_MODES,
    FAN_MODES_MANUAL,
    PRESET_MODES,
    POWER_STATE_HASS_TO_HYSEN,
    MODE_HASS_TO_HYSEN,
    FAN_HASS_TO_HYSEN,
    PRESET_HASS_TO_HYSEN,
)
from .entity import HysenEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities):
    """Set up the Hysen climate entity from a config entry."""
    device_data = hass.data[DOMAIN][config_entry.entry_id]
    climate_entity = HysenClimate(device_data)
    async_add_entities([climate_entity])

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(SERVICE_TURN_ON, {}, "async_turn_on")
    platform.async_register_entity_service(SERVICE_TURN_OFF, {}, "async_turn_off")


class HysenClimate(HysenEntity, ClimateEntity):
    """Representation of a Hysen 2 Pipe Fan Coil climate entity."""

    def __init__(self, device_data):
        """Initialize the climate entity."""
        super().__init__(device_data["coordinator"], device_data)
        self._attr_unique_id = f"{device_data['mac']}_climate"
        self._attr_name = device_data["name"]
        self._attr_precision = PRECISION_WHOLE
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_target_temperature_step = DEFAULT_TARGET_TEMP_STEP
        self._attr_preset_modes = PRESET_MODES
        self._host = device_data["host"]
        # Initialise attrs from coordinator data (already available at this point)
        self._update_attrs_from_coordinator()

    # ------------------------------------------------------------------
    # Coordinator integration
    # ------------------------------------------------------------------

    def _update_attrs_from_coordinator(self):
        """Sync all local _attr_* fields from the coordinator data dict."""
        data = self.coordinator.data
        self._attr_power_state          = data.get(DATA_KEY_POWER_STATE)
        self._attr_hvac_mode            = data.get(DATA_KEY_HVAC_MODE)
        self._attr_hvac_modes           = data.get(DATA_KEY_HVAC_MODES)
        self._attr_fan_mode             = data.get(DATA_KEY_FAN_MODE)
        self._attr_fan_modes            = data.get(DATA_KEY_FAN_MODES)
        self._attr_hvac_action          = data.get(DATA_KEY_HVAC_ACTION)
        self._attr_preset_mode          = data.get(DATA_KEY_PRESET_MODE)
        self._attr_target_temperature   = data.get(DATA_KEY_TARGET_TEMP)
        self._attr_current_temperature  = data.get(DATA_KEY_CURRENT_TEMP)
        self._attr_min_temp             = data.get(DATA_KEY_MIN_TEMP)
        self._attr_max_temp             = data.get(DATA_KEY_MAX_TEMP)
        self._attr_valve_state          = data.get(DATA_KEY_VALVE_STATE)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_attrs_from_coordinator()
        self.async_write_ha_state()

    # ------------------------------------------------------------------
    # HA ClimateEntity properties
    # ------------------------------------------------------------------

    @property
    def supported_features(self):
        """Return the list of supported features."""
        if self._attr_power_state == STATE_OFF:
            return ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF
        if self._attr_hvac_mode == HVACMode.FAN_ONLY:
            return (
                ClimateEntityFeature.TURN_ON
                | ClimateEntityFeature.TURN_OFF
                | ClimateEntityFeature.FAN_MODE
            )
        return (
            ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
            | ClimateEntityFeature.FAN_MODE
            | ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.PRESET_MODE
        )

    @property
    def precision(self):
        return self._attr_precision

    @property
    def temperature_unit(self):
        return self._attr_temperature_unit

    @property
    def hvac_mode(self):
        return self._attr_hvac_mode

    @property
    def hvac_modes(self):
        return self._attr_hvac_modes

    @property
    def hvac_action(self):
        return self._attr_hvac_action

    @property
    def current_temperature(self):
        return self._attr_current_temperature

    @property
    def target_temperature(self):
        return self._attr_target_temperature

    @property
    def target_temperature_step(self):
        return self._attr_target_temperature_step

    @property
    def min_temp(self):
        return self._attr_min_temp

    @property
    def max_temp(self):
        return self._attr_max_temp

    @property
    def fan_mode(self):
        return self._attr_fan_mode

    @property
    def fan_modes(self):
        return self._attr_fan_modes

    @property
    def preset_mode(self):
        return self._attr_preset_mode

    @property
    def preset_modes(self):
        return self._attr_preset_modes

    @property
    def power_state(self):
        return self._attr_power_state

    @property
    def valve_state(self):
        return self._attr_valve_state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        data = {
            ATTR_POWER_STATE:      self._attr_power_state,
            ATTR_HVAC_MODE:        self._attr_hvac_mode,
            ATTR_FAN_MODE:         self._attr_fan_mode,
            ATTR_PRESET_MODE:      self._attr_preset_mode,
            ATTR_VALVE_STATE:      self._attr_valve_state,
            ATTR_COOLING_MAX_TEMP: self.coordinator.data.get(DATA_KEY_COOLING_MAX_TEMP),
            ATTR_COOLING_MIN_TEMP: self.coordinator.data.get(DATA_KEY_COOLING_MIN_TEMP),
            ATTR_HEATING_MAX_TEMP: self.coordinator.data.get(DATA_KEY_HEATING_MAX_TEMP),
            ATTR_HEATING_MIN_TEMP: self.coordinator.data.get(DATA_KEY_HEATING_MIN_TEMP),
        }
        return {k: v for k, v in data.items() if v is not None}

    # ------------------------------------------------------------------
    # Commands — each simply calls _async_try_command; the coordinator
    # refresh triggered inside it propagates to all entities via their
    # _handle_coordinator_update callback.
    # ------------------------------------------------------------------

    async def async_turn_on(self):
        """Turn the entity on."""
        _LOGGER.debug("[%s] Turning on", self._host)
        await self._async_try_command(
            "Error in set_power",
            self.coordinator.device.set_power,
            POWER_STATE_HASS_TO_HYSEN[STATE_ON],
        )

    async def async_turn_off(self):
        """Turn the entity off."""
        _LOGGER.debug("[%s] Turning off", self._host)
        await self._async_try_command(
            "Error in set_power",
            self.coordinator.device.set_power,
            POWER_STATE_HASS_TO_HYSEN[STATE_OFF],
        )

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        temperature = int(round(temperature))

        if self._attr_min_temp is None or self._attr_max_temp is None:
            _LOGGER.error("[%s] Device min_temp or max_temp is not set", self._host)
            raise ServiceValidationError(
                "Device temperature range is not set",
                translation_domain=DOMAIN,
                translation_key="missing_temperature_range",
            )
        if temperature < self._attr_min_temp or temperature > self._attr_max_temp:
            _LOGGER.error(
                "[%s] Temperature %s out of range [%s, %s]",
                self._host, temperature, self._attr_min_temp, self._attr_max_temp,
            )
            raise ServiceValidationError(
                f"Temperature {temperature} is out of range. "
                f"Valid range is {self._attr_min_temp} to {self._attr_max_temp}.",
                translation_domain=DOMAIN,
                translation_key="invalid_temperature",
            )

        _LOGGER.debug("[%s] Setting target temperature to %s", self._host, temperature)
        await self._async_try_command(
            "Error in set_target_temp",
            self.coordinator.device.set_target_temp,
            temperature,
        )

    async def async_set_hvac_mode(self, hvac_mode):
        """Set the HVAC mode."""
        _LOGGER.debug("[%s] Requested HVAC mode %s (available: %s)",
                      self._host, hvac_mode, self._attr_hvac_modes)
        valid_modes = self._attr_hvac_modes
        if hvac_mode == HVACMode.FAN_ONLY and self.fan_mode == FAN_AUTO:
            raise ServiceValidationError(
                f"HVAC mode {hvac_mode} is not allowed when fan mode is auto. "
                "Set fan mode to low, medium, or high first.",
                translation_domain=DOMAIN,
                translation_key="fan_only_with_auto_fan",
            )
        if hvac_mode not in valid_modes:
            _LOGGER.error("[%s] HVAC mode %s not valid. Valid: %s",
                          self._host, hvac_mode, ", ".join(valid_modes))
            raise ServiceValidationError(
                f"Invalid HVAC mode: {hvac_mode}. Valid modes are: {valid_modes}.",
                translation_domain=DOMAIN,
                translation_key="invalid_hvac_mode",
            )

        _LOGGER.debug("[%s] Setting HVAC mode to %s", self._host, hvac_mode)
        if hvac_mode == HVACMode.OFF:
            await self._async_try_command(
                "Error in set_power",
                self.coordinator.device.set_power,
                POWER_STATE_HASS_TO_HYSEN[STATE_OFF],
            )
        elif self._attr_power_state == STATE_OFF:
            # Device is off; the only available mode is the current one,
            # so turning power on is sufficient — no mode change needed.
            await self._async_try_command(
                "Error in set_power",
                self.coordinator.device.set_power,
                POWER_STATE_HASS_TO_HYSEN[STATE_ON],
            )
        else:
            await self._async_try_command(
                "Error in set_operation_mode",
                self.coordinator.device.set_operation_mode,
                MODE_HASS_TO_HYSEN[hvac_mode],
            )

    async def async_set_fan_mode(self, fan_mode):
        """Set the fan mode."""
        _LOGGER.debug("[%s] Requested fan mode %s (available: %s)",
                      self._host, fan_mode, self.fan_modes)
        valid_modes = self.fan_modes
        if fan_mode == FAN_AUTO and self.hvac_mode == HVACMode.FAN_ONLY:
            raise ServiceValidationError(
                f"Fan mode {fan_mode} is not allowed when HVAC mode is fan_only. "
                "Set HVAC mode to off, heat, or cool first.",
                translation_domain=DOMAIN,
                translation_key="auto_fan_with_fan_only",
            )
        if fan_mode not in valid_modes:
            _LOGGER.error("[%s] Fan mode %s not valid. Valid: %s",
                          self._host, fan_mode, ", ".join(valid_modes))
            raise ServiceValidationError(
                f"Invalid fan mode: {fan_mode}. Valid fan modes are: {valid_modes}.",
                translation_domain=DOMAIN,
                translation_key="invalid_fan_mode",
            )
        _LOGGER.debug("[%s] Setting fan mode to %s", self._host, fan_mode)
        await self._async_try_command(
            "Error in set_fan_mode",
            self.coordinator.device.set_fan_mode,
            FAN_HASS_TO_HYSEN[fan_mode],
        )

    async def async_set_preset_mode(self, preset_mode):
        """Set the preset mode."""
        _LOGGER.debug("[%s] Setting preset mode to %s", self._host, preset_mode)
        valid_modes = self._attr_preset_modes
        if preset_mode not in valid_modes:
            _LOGGER.error("[%s] Preset mode %s not valid. Valid: %s",
                          self._host, preset_mode, ", ".join(valid_modes))
            raise ServiceValidationError(
                f"Invalid preset mode: {preset_mode}. Valid modes are: {valid_modes}.",
                translation_domain=DOMAIN,
                translation_key="invalid_preset_mode",
            )
        await self._async_try_command(
            "Error in set_weekly_schedule",
            self.coordinator.device.set_weekly_schedule,
            PRESET_HASS_TO_HYSEN[preset_mode],
        )
