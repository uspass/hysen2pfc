"""
Support for Hysen 2 Pipe Fan Coil Controller.

This module provides a climate entity for controlling the Hysen HY03AC-1-Wifi
device and derivatives, supporting HVAC modes, fan modes, temperature settings,
and advanced features like scheduling.
"""

import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.exceptions import ServiceValidationError
from datetime import datetime
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature
from .const import (
    DOMAIN,
    HYSEN2PFC_HEATING_MIN_TEMP,
    HYSEN2PFC_HEATING_MAX_TEMP,
    ATTR_ENTITY_ID,
    ATTR_TEMPERATURE,
    PRECISION_WHOLE,
    UnitOfTemperature,
    DEFAULT_CURRENT_TEMP,
    DEFAULT_TARGET_TEMP,
    DEFAULT_TARGET_TEMP_STEP,
    DEFAULT_MIN_TEMP,
    DEFAULT_MAX_TEMP,
    DEFAULT_CALIBRATION,
    DATA_KEY_FWVERSION,
    DATA_KEY_KEY_LOCK,
    DATA_KEY_VALVE_STATE,
    DATA_KEY_POWER_STATE,
    DATA_KEY_HVAC_MODE,
    DATA_KEY_ROOM_TEMP,
    DATA_KEY_TARGET_TEMP,
    DATA_KEY_FAN_MODE,
    DATA_KEY_PRESET_MODE,
    DATA_KEY_HYSTERESIS,
    DATA_KEY_CALIBRATION,
    DATA_KEY_COOLING_MAX_TEMP,
    DATA_KEY_COOLING_MIN_TEMP,
    DATA_KEY_HEATING_MAX_TEMP,
    DATA_KEY_HEATING_MIN_TEMP,
    DATA_KEY_FAN_CONTROL,
    DATA_KEY_FROST_PROTECTION,
    DATA_KEY_CLOCK_HOUR,
    DATA_KEY_CLOCK_MINUTE,
    DATA_KEY_CLOCK_SECOND,
    DATA_KEY_CLOCK_WEEKDAY,
    DATA_KEY_SLOT1_START_ENABLE,
    DATA_KEY_SLOT1_START_TIME,
    DATA_KEY_SLOT1_STOP_ENABLE,
    DATA_KEY_SLOT1_STOP_TIME,
    DATA_KEY_SLOT2_START_ENABLE,
    DATA_KEY_SLOT2_START_TIME,
    DATA_KEY_SLOT2_STOP_ENABLE,
    DATA_KEY_SLOT2_STOP_TIME,
    DATA_KEY_TIME_VALVE_ON,
    STATE_ON,
    STATE_OFF,
    STATE_CLOSED,
    HVACMode,
    HVACAction,
    ATTR_HVAC_MODE,
    ATTR_FAN_MODE,
    ATTR_FWVERSION,
    ATTR_KEY_LOCK,
    ATTR_POWER_STATE,
    ATTR_HYSTERESIS,
    ATTR_CALIBRATION,
    ATTR_COOLING_MAX_TEMP,
    ATTR_COOLING_MIN_TEMP,
    ATTR_HEATING_MAX_TEMP,
    ATTR_HEATING_MIN_TEMP,
    ATTR_FAN_CONTROL,
    ATTR_FROST_PROTECTION,
    ATTR_DEVICE_TIME,
    ATTR_DEVICE_WEEKDAY,
    ATTR_SLOT1_START_ENABLE,
    ATTR_SLOT1_START_TIME,
    ATTR_SLOT1_STOP_ENABLE,
    ATTR_SLOT1_STOP_TIME,
    ATTR_SLOT2_START_ENABLE,
    ATTR_SLOT2_START_TIME,
    ATTR_SLOT2_STOP_ENABLE,
    ATTR_SLOT2_STOP_TIME,
    ATTR_TIME_VALVE_ON,
    ATTR_VALVE_STATE,
    SERVICE_TURN_ON,
    SERVICE_TURN_OFF,
    HVAC_MODES_NO_FAN,
    HVAC_MODES,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH,
    FAN_AUTO,
    FAN_MODES,
    FAN_MODES_MANUAL,
    PRESET_TODAY,
    PRESET_WORKDAYS,
    PRESET_SIXDAYS,
    PRESET_FULLWEEK,
    PRESET_MODES,
    POWER_STATE_HASS_TO_HYSEN,
    MODE_HASS_TO_HYSEN,
    FAN_HASS_TO_HYSEN,
    PRESET_HASS_TO_HYSEN,
)
from .entity import HysenEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities):
    """Set up the Hysen climate entity from a config entry.

    Args:
        hass (HomeAssistant): The Home Assistant instance.
        config_entry: The configuration entry for the device.
        async_add_entities: Callback to add entities to Home Assistant.
    """
    device_data = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([HysenClimate(device_data)])

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_TURN_ON,
        {},
        "async_turn_on",
    )
    platform.async_register_entity_service(
        SERVICE_TURN_OFF,
        {},
        "async_turn_off",
    )

class HysenClimate(HysenEntity, ClimateEntity):
    """Representation of a Hysen 2 Pipe Fan Coil climate entity.

    This class manages the state and control of a Hysen climate device,
    supporting HVAC modes, fan modes, temperature settings, and scheduling.
    """

    def __init__(self, device_data):
        """Initialize the climate entity.

        Args:
            device_data (dict): Configuration data for the device, including coordinator, mac, name, and host.
        """
        super().__init__(device_data["coordinator"], device_data)
        self._attr_unique_id = f"{device_data['mac']}_climate"
        self._attr_name = device_data["name"]
        self._attr_precision = PRECISION_WHOLE
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_hvac_mode = None
        self._attr_hvac_modes = HVAC_MODES
        self._attr_hvac_action = HVACAction.OFF
        self._attr_current_temperature = DEFAULT_CURRENT_TEMP
        self._attr_target_temperature = DEFAULT_TARGET_TEMP
        self._attr_target_temperature_step = DEFAULT_TARGET_TEMP_STEP
        self._attr_min_temp = DEFAULT_MIN_TEMP
        self._attr_max_temp = DEFAULT_MAX_TEMP
        self._attr_fan_mode = FAN_LOW
        self._attr_fan_modes = FAN_MODES
        self._attr_preset_mode = PRESET_TODAY
        self._attr_preset_modes = PRESET_MODES
        self._attr_power_state = STATE_OFF
        self._attr_valve_state = STATE_CLOSED
        self._attr_supported_features = (
            ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
        )
        self._host = device_data["host"]

    @property
    def supported_features(self):
        """Return the list of supported features.

        Returns:
            int: A bitwise combination of supported ClimateEntityFeature flags.
        """
        if self.power_state == STATE_OFF or self.hvac_mode == HVACMode.OFF:
            self._attr_supported_features = (
                ClimateEntityFeature.TURN_ON
                | ClimateEntityFeature.TURN_OFF
            )
        elif self.hvac_mode == HVACMode.FAN_ONLY:
            self._attr_supported_features = (
                ClimateEntityFeature.TURN_ON
                | ClimateEntityFeature.TURN_OFF
                | ClimateEntityFeature.FAN_MODE
            )
        else:  # hvac_mode is HEAT or COOL
            self._attr_supported_features = (
                ClimateEntityFeature.TURN_ON
                | ClimateEntityFeature.TURN_OFF
                | ClimateEntityFeature.TARGET_TEMPERATURE
                | ClimateEntityFeature.PRESET_MODE
                | ClimateEntityFeature.FAN_MODE
            )
        return self._attr_supported_features

    @property
    def precision(self):
        """Return the precision of the system.

        Returns:
            float: The precision for temperature settings (e.g., whole numbers).
        """
        return self._attr_precision

    @property
    def temperature_unit(self):
        """Return the unit of measurement which this thermostat uses.

        Returns:
            str: The temperature unit, e.g., UnitOfTemperature.CELSIUS.
        """
        return self._attr_temperature_unit

    @property
    def hvac_mode(self):
        """Return the current HVAC mode.

        Returns:
            str: The current HVAC mode.
        """
        if self.power_state == STATE_OFF:
            self._attr_hvac_mode = HVACMode.OFF
        else:
            self._attr_hvac_mode = self.coordinator.data.get(DATA_KEY_HVAC_MODE)
        return self._attr_hvac_mode

    @property
    def hvac_modes(self):
        """Return the list of available HVAC modes.

        Returns:
            list: The list of supported HVAC modes, dynamically adjusted based on state.
        """
        if self.hvac_mode == HVACMode.FAN_ONLY:
            self._attr_fan_modes = FAN_MODES_MANUAL
        elif self.fan_mode == FAN_AUTO:
            self._attr_hvac_modes = HVAC_MODES_NO_FAN
            self._attr_fan_modes = FAN_MODES
        else:
            self._attr_hvac_modes = HVAC_MODES
            self._attr_fan_modes = FAN_MODES
        return self._attr_hvac_modes

    @property
    def hvac_action(self):
        """Return the current HVAC action.

        Returns:
            str: The current HVAC action (e.g., off, heating, cooling, idle, fan).
        """
        if self.power_state == STATE_OFF:
            self._attr_hvac_action = HVACAction.OFF
        elif self.hvac_mode is None:
            _LOGGER.warning("[%s] Unknown operation mode: %s", self._host, self.hvac_mode)
            self._attr_hvac_action = HVACAction.IDLE  # Default to IDLE for safety
        elif self.valve_state is None:
            _LOGGER.warning("[%s] Unknown valve state: %s", self._host, self.valve_state)
            self._attr_hvac_action = HVACAction.IDLE  # Default to IDLE for safety
        elif self.valve_state == STATE_CLOSED:
            self._attr_hvac_action = HVACAction.IDLE
        elif self.hvac_mode == HVACMode.HEAT:
            self._attr_hvac_action = HVACAction.HEATING
        elif self.hvac_mode == HVACMode.COOL:
            self._attr_hvac_action = HVACAction.COOLING
        elif self.hvac_mode == HVACMode.FAN_ONLY:
            self._attr_hvac_action = HVACAction.FAN
        return self._attr_hvac_action

    @property
    def current_temperature(self):
        """Return the current temperature.

        Returns:
            float: The current room temperature from the device.
        """
        self._attr_current_temperature = self.coordinator.data.get(DATA_KEY_ROOM_TEMP)
        return self._attr_current_temperature

    @property
    def target_temperature(self):
        """Return the target temperature.

        Returns:
            float: The current target temperature.
        """
        self._attr_target_temperature = self.coordinator.data.get(DATA_KEY_TARGET_TEMP)
        return self._attr_target_temperature

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature.

        Returns:
            float: The step for adjusting target temperature.
        """
        return self._attr_target_temperature_step

    @property
    def min_temp(self):
        """Return the minimum temperature.

        Returns:
            float: The minimum temperature setting, dynamically adjusted based on mode.
        """
        if self.hvac_mode == HVACMode.COOL:
            self._attr_min_temp = self.coordinator.data.get(DATA_KEY_COOLING_MIN_TEMP)
        else:
            self._attr_min_temp = self.coordinator.data.get(DATA_KEY_HEATING_MIN_TEMP)
        return self._attr_min_temp

    @property
    def max_temp(self):
        """Return the maximum temperature.

        Returns:
            float: The maximum temperature setting, dynamically adjusted based on mode.
        """
        if self.hvac_mode == HVACMode.COOL:
            self._attr_max_temp = self.coordinator.data.get(DATA_KEY_COOLING_MAX_TEMP)
        else:
            self._attr_max_temp = self.coordinator.data.get(DATA_KEY_HEATING_MAX_TEMP)
        return self._attr_max_temp

    @property
    def fan_mode(self):
        """Return the fan mode.

        Returns:
            str: The current fan mode.
        """
        self._attr_fan_mode = self.coordinator.data.get(DATA_KEY_FAN_MODE)
        return self._attr_fan_mode

    @property
    def fan_modes(self):
        """Return the list of available fan modes.

        Returns:
            list: The list of supported fan modes, dynamically adjusted based on hvac_mode.
        """
        return self._attr_fan_modes

    @property
    def preset_mode(self):
        """Return the preset mode.

        Returns:
            str: The current preset mode.
        """
        self._attr_preset_mode = self.coordinator.data.get(DATA_KEY_PRESET_MODE)
        return self._attr_preset_mode

    @property
    def preset_modes(self):
        """Return the list of available preset modes.

        Returns:
            list: The list of supported preset modes.
        """
        return PRESET_MODES

    @property
    def power_state(self):
        """Return the power state.

        Returns:
            str: The current power state (on or off).
        """
        self._attr_power_state = self.coordinator.data.get(DATA_KEY_POWER_STATE)
        return self._attr_power_state

    @property
    def valve_state(self):
        """Return the valve state.

        Returns:
            str: The current valve state (open or closed).
        """
        self._attr_valve_state = self.coordinator.data.get(DATA_KEY_VALVE_STATE)
        return self._attr_valve_state

    def _update_hvac_mode(self):
        """Update the HVAC mode based on device data."""
        if self.power_state == STATE_OFF:
            self._attr_hvac_mode = HVACMode.OFF
        else:
            self._attr_hvac_mode = self.coordinator.data.get(DATA_KEY_HVAC_MODE)

    def _update_fan_mode(self):
        """Update the fan mode based on device data."""
        self._attr_fan_mode = self.coordinator.data.get(DATA_KEY_FAN_MODE)

    def _update_preset_mode(self):
        """Update the preset mode based on device data."""
        self._attr_preset_mode = self.coordinator.data.get(DATA_KEY_PRESET_MODE)

    async def async_added_to_hass(self):
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        self._update_hvac_mode()
        self._update_fan_mode()
        self._update_preset_mode()

    async def async_update(self):
        """Update the entity state from the coordinator data."""
        self._update_hvac_mode()
        self._update_fan_mode()
        self._update_preset_mode()
        self._attr_current_temperature = self.coordinator.data.get(DATA_KEY_ROOM_TEMP)
        self._attr_target_temperature = self.coordinator.data.get(DATA_KEY_TARGET_TEMP)
        self._attr_min_temp = self.coordinator.data.get(DATA_KEY_HEATING_MIN_TEMP) if self.hvac_mode != HVACMode.COOL else self.coordinator.data.get(DATA_KEY_COOLING_MIN_TEMP)
        self._attr_max_temp = self.coordinator.data.get(DATA_KEY_HEATING_MAX_TEMP) if self.hvac_mode != HVACMode.COOL else self.coordinator.data.get(DATA_KEY_COOLING_MAX_TEMP)
        self._attr_power_state = self.coordinator.data.get(DATA_KEY_POWER_STATE)
        self._attr_valve_state = self.coordinator.data.get(DATA_KEY_VALVE_STATE)
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self):
        """Return the state attributes.

        Returns:
            dict: Additional state attributes for the entity.
        """
        data = {
            ATTR_POWER_STATE: self.power_state,
            ATTR_HVAC_MODE: self._attr_hvac_mode,
            ATTR_FAN_MODE: self._attr_fan_mode,
            ATTR_VALVE_STATE: self.valve_state,
            ATTR_KEY_LOCK: self.coordinator.data.get(DATA_KEY_KEY_LOCK),
            ATTR_COOLING_MAX_TEMP: self.coordinator.data.get(DATA_KEY_COOLING_MAX_TEMP),
            ATTR_COOLING_MIN_TEMP: self.coordinator.data.get(DATA_KEY_COOLING_MIN_TEMP),
            ATTR_HEATING_MAX_TEMP: self.coordinator.data.get(DATA_KEY_HEATING_MAX_TEMP),
            ATTR_HEATING_MIN_TEMP: self.coordinator.data.get(DATA_KEY_HEATING_MIN_TEMP),
            ATTR_HYSTERESIS: self.coordinator.data.get(DATA_KEY_HYSTERESIS),
            ATTR_CALIBRATION: self.coordinator.data.get(DATA_KEY_CALIBRATION),
            ATTR_FAN_CONTROL: self.coordinator.data.get(DATA_KEY_FAN_CONTROL),
            ATTR_FROST_PROTECTION: self.coordinator.data.get(DATA_KEY_FROST_PROTECTION),
            ATTR_DEVICE_TIME: f"{self.coordinator.data.get(DATA_KEY_CLOCK_HOUR)}:{self.coordinator.data.get(DATA_KEY_CLOCK_MINUTE):02d}",
            ATTR_DEVICE_WEEKDAY: self.coordinator.data.get(DATA_KEY_CLOCK_WEEKDAY),
            ATTR_SLOT1_START_ENABLE: self.coordinator.data.get(DATA_KEY_SLOT1_START_ENABLE),
            ATTR_SLOT1_START_TIME: self.coordinator.data.get(DATA_KEY_SLOT1_START_TIME),
            ATTR_SLOT1_STOP_ENABLE: self.coordinator.data.get(DATA_KEY_SLOT1_STOP_ENABLE),
            ATTR_SLOT1_STOP_TIME: self.coordinator.data.get(DATA_KEY_SLOT1_STOP_TIME),
            ATTR_SLOT2_START_ENABLE: self.coordinator.data.get(DATA_KEY_SLOT2_START_ENABLE),
            ATTR_SLOT2_START_TIME: self.coordinator.data.get(DATA_KEY_SLOT2_START_TIME),
            ATTR_SLOT2_STOP_ENABLE: self.coordinator.data.get(DATA_KEY_SLOT2_STOP_ENABLE),
            ATTR_SLOT2_STOP_TIME: self.coordinator.data.get(DATA_KEY_SLOT2_STOP_TIME),
            ATTR_TIME_VALVE_ON: self.coordinator.data.get(DATA_KEY_TIME_VALVE_ON),
            ATTR_FWVERSION: self.coordinator.data.get(DATA_KEY_FWVERSION),
        }
        return {k: v for k, v in data.items() if v is not None}

    async def async_turn_on(self):
        """Turn the entity on.

        Sends a command to power on the device and refreshes the state.
        """
        _LOGGER.debug("[%s] Turning on", self._host)
        success = await self._async_try_command(
            "Error in set_power",
            self.coordinator.device.set_power,
            POWER_STATE_HASS_TO_HYSEN[STATE_ON],
        )
        if success:
            await self.coordinator.async_refresh()
            self.async_write_ha_state()

    async def async_turn_off(self):
        """Turn the entity off.

        Sends a command to power off the device and refreshes the state.
        """
        _LOGGER.debug("[%s] Turning off", self._host)
        success = await self._async_try_command(
            "Error in set_power",
            self.coordinator.device.set_power,
            POWER_STATE_HASS_TO_HYSEN[STATE_OFF],
        )
        if success:
            await self.coordinator.async_refresh()
            self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature.

        Args:
            **kwargs: Keyword arguments containing the target temperature (ATTR_TEMPERATURE).
        """
        temperature = int(round(kwargs.get(ATTR_TEMPERATURE)))
        if temperature is None:
            return
        _LOGGER.debug("[%s] Setting target temperature to %s", self._host, temperature)
        success = await self._async_try_command(
            "Error in set_target_temp",
            self.coordinator.device.set_target_temp,
            temperature,
        )
        if success:
            await self.coordinator.async_refresh()
            self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode):
        """Set the HVAC mode.

        Args:
            hvac_mode (str): The desired HVAC mode (e.g., HEAT, COOL, FAN_ONLY, OFF).
        """
        _LOGGER.debug("Hysen: [%s] HVAC modes are %s", self._host, self.hvac_modes)
        _LOGGER.debug("Hysen: [%s] Requested HVAC mode is %s", self._host, hvac_mode)
        valid_modes = self.hvac_modes
        if hvac_mode == HVACMode.FAN_ONLY and self.fan_mode == FAN_AUTO:
            _LOGGER.error("Hysen: [%s] HVAC mode %s is not allowed when fan mode is auto. Valid HVAC modes are: %s", self._host, hvac_mode, ", ".join(valid_modes))
            raise ServiceValidationError(
                f"Hysen: HVAC mode {hvac_mode} is not allowed when fan mode is auto. Set fan mode to low, medium, or high first.",
                translation_domain=DOMAIN,
                translation_key="fan_only_with_auto_fan",
            )
        if hvac_mode not in valid_modes:
            _LOGGER.error("Hysen: [%s] HVAC mode %s is not valid. Valid HVAC modes are: %s", self._host, hvac_mode, ", ".join(valid_modes))
            raise ServiceValidationError(
                f"Hysen: Invalid HVAC mode: {hvac_mode}. Valid modes are: {valid_modes}.",
                translation_domain=DOMAIN,
                translation_key="invalid_hvac_mode",
            )
        _LOGGER.debug("Hysen: [%s] Setting HVAC mode to %s", self._host, hvac_mode)
        if hvac_mode == HVACMode.OFF:
            success = await self._async_try_command(
                "Error in set_power",
                self.coordinator.device.set_power,
                POWER_STATE_HASS_TO_HYSEN[STATE_OFF],
            )
        else:
            success = await self._async_try_command(
                "Error in set_power",
                self.coordinator.device.set_power,
                POWER_STATE_HASS_TO_HYSEN[STATE_ON],
            )
            if success:
                success = await self._async_try_command(
                    "Error in set_operation_mode",
                    self.coordinator.device.set_operation_mode,
                    MODE_HASS_TO_HYSEN[hvac_mode],
                )
        if success:
            await self.coordinator.async_refresh()
            self.async_write_ha_state()

    async def async_set_fan_mode(self, fan_mode):
        """Set the fan mode.

        Args:
            fan_mode (str): The desired fan mode (e.g., low, medium, high, auto).
        """
        _LOGGER.debug("Hysen: [%s] fan modes are %s", self._host, self.fan_modes)
        _LOGGER.debug("Hysen: [%s] Requested fan mode is %s", self._host, fan_mode)
        valid_modes = self.fan_modes
        if fan_mode == FAN_AUTO and self.hvac_mode == HVACMode.FAN_ONLY:
            _LOGGER.error("Hysen: [%s] fan mode %s is not allowed when HVAC mode is fan_only. Valid fan modes are: %s", self._host, fan_mode, ", ".join(valid_modes))
            raise ServiceValidationError(
                f"Hysen: Fan mode {fan_mode} is not allowed when HVAC mode is fan_only. Set HVAC mode to off, heat, or cool first.",
                translation_domain=DOMAIN,
                translation_key="auto_fan_with_fan_only",
            )
        if fan_mode not in valid_modes:
            _LOGGER.error("Hysen: [%s] fan mode %s is not valid. Valid fan modes are: %s", self._host, fan_mode, ", ".join(valid_modes))
            raise ServiceValidationError(
                f"Hysen: Invalid fan mode: {fan_mode}. Valid fan modes are: {valid_modes}.",
                translation_domain=DOMAIN,
                translation_key="invalid_hvac_mode",
            )
        _LOGGER.debug("[%s] Setting fan mode to %s, Current hvac_mode: %s", self._host, fan_mode, self.hvac_mode)
        if fan_mode == FAN_AUTO and self.hvac_mode == HVACMode.FAN_ONLY:
            _LOGGER.error("[%s] Fan mode %s is not allowed when HVAC mode is fan_only. Valid fan modes are: %s", self._host, fan_mode, ", ".join(FAN_MODES_MANUAL))
            raise ServiceValidationError(
                f"Fan mode {fan_mode} is not allowed when HVAC mode is fan_only. Valid fan modes are: {', '.join(FAN_MODES_MANUAL)}",
                translation_domain=DOMAIN,
                translation_key="invalid_fan_mode",
            )
        success = await self._async_try_command(
            "Error in set_fan_mode",
            self.coordinator.device.set_fan_mode,
            FAN_HASS_TO_HYSEN[fan_mode],
        )
        if success:
            await self.coordinator.async_refresh()
            self.async_write_ha_state()

    async def async_set_preset_mode(self, preset_mode):
        """Set the preset mode.

        Args:
            preset_mode (str): The desired preset mode (e.g., today, workdays, full week).
        """
        _LOGGER.debug("[%s] Setting preset mode to %s", self._host, preset_mode)
        success = await self._async_try_command(
            "Error in set_weekly_schedule",
            self.coordinator.device.set_weekly_schedule,
            PRESET_HASS_TO_HYSEN[preset_mode],
        )
        if success:
            await self.coordinator.async_refresh()
            self.async_write_ha_state()
