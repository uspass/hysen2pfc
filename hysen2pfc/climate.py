"""
Support for Hysen 2 Pipe Fan Coil Controller.
Hysen HY03AC-1-Wifi device and derivative
"""

import asyncio
from functools import partial
import binascii
import logging
import voluptuous as vol
from datetime import datetime
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_TEMPERATURE,
    CONF_HOST,
    CONF_MAC,
    CONF_NAME,
    CONF_TIMEOUT,
    PRECISION_WHOLE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    UnitOfTemperature
)
from homeassistant.components.climate import (
    PLATFORM_SCHEMA,
    ClimateEntity,
    ClimateEntityFeature
)
from homeassistant.components.climate.const import (
    DOMAIN,
    ATTR_HVAC_MODE,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH,
    FAN_AUTO,
    HVACAction,
    HVACMode,
    PRESET_NONE,
    SERVICE_SET_HVAC_MODE,
    SERVICE_SET_TEMPERATURE
)
from .const import (
    DATA_KEY,
    DEFAULT_NAME,
    CONF_SYNC_CLOCK,
    CONF_SYNC_HOUR,
    DEFAULT_TIMEOUT,
    DEFAULT_SYNC_CLOCK,
    DEFAULT_SYNC_HOUR,
    STATE_ON,
    STATE_OFF,
    STATE_OPEN,
    STATE_CLOSED,
    STATE_ALL_UNLOCKED,
    STATE_POWER_UNLOCKED,
    STATE_ALL_LOCKED,
    STATE_HYSTERESIS_HALVE,
    STATE_HYSTERESIS_WHOLE,
    PRESET_TODAY,
    PRESET_WORKDAYS,
    PRESET_SIXDAYS,
    PRESET_FULLWEEK,
    ATTR_FWVERSION,
    ATTR_KEY_LOCK,
    ATTR_POWER_STATE,
    ATTR_VALVE_STATE,
    ATTR_HYSTERESIS,
    ATTR_CALIBRATION,
    ATTR_LIMIT_TEMP,
    ATTR_COOLING_MAX_TEMP,
    ATTR_COOLING_MIN_TEMP,
    ATTR_HEATING_MAX_TEMP,
    ATTR_HEATING_MIN_TEMP,
    ATTR_FAN_CONTROL,
    ATTR_FROST_PROTECTION,
    ATTR_TIME_NOW,
    ATTR_DEVICE_TIME,
    ATTR_DEVICE_WEEKDAY,
    ATTR_WEEKLY_SCHEDULE,
    ATTR_PERIOD1_ENABLED,
    ATTR_PERIOD1_START_TIME,
    ATTR_PERIOD1_END_TIME,
    ATTR_PERIOD2_ENABLED,
    ATTR_PERIOD2_START_TIME,
    ATTR_PERIOD2_END_TIME,
    ATTR_TIME_VALVE_ON,
    SERVICE_SET_KEY_LOCK,
    SERVICE_SET_HYSTERESIS,
    SERVICE_SET_CALIBRATION,
    SERVICE_SET_COOLING_MAX_TEMP,
    SERVICE_SET_COOLING_MIN_TEMP,
    SERVICE_SET_HEATING_MAX_TEMP,
    SERVICE_SET_HEATING_MIN_TEMP,
    SERVICE_SET_FAN_CONTROL,
    SERVICE_SET_FROST_PROTECTION,
    SERVICE_SET_TIME,
    SERVICE_SET_SCHEDULE,
    HYSTERESIS_MODES,
    FAN_MODES,
    FAN_MODES_FAN_ONLY
)
from hysen import (
    Hysen2PipeFanCoilDevice,
    HYSEN2PFC_KEY_LOCK_OFF,
    HYSEN2PFC_KEY_LOCK_ON,
    HYSEN2PFC_KEY_ALL_UNLOCKED,
    HYSEN2PFC_KEY_POWER_UNLOCKED,
    HYSEN2PFC_KEY_ALL_LOCKED,
    HYSEN2PFC_POWER_OFF,
    HYSEN2PFC_POWER_ON,
    HYSEN2PFC_VALVE_OFF,
    HYSEN2PFC_VALVE_ON,
    HYSEN2PFC_HYSTERESIS_HALVE,
    HYSEN2PFC_HYSTERESIS_WHOLE,
    HYSEN2PFC_CALIBRATION_MIN,
    HYSEN2PFC_CALIBRATION_MAX,
    HYSEN2PFC_FAN_LOW,
    HYSEN2PFC_FAN_MEDIUM,
    HYSEN2PFC_FAN_HIGH,
    HYSEN2PFC_FAN_AUTO,
    HYSEN2PFC_MODE_FAN,
    HYSEN2PFC_MODE_COOL,
    HYSEN2PFC_MODE_HEAT,
    HYSEN2PFC_FAN_CONTROL_ON,
    HYSEN2PFC_FAN_CONTROL_OFF,
    HYSEN2PFC_FROST_PROTECTION_OFF,
    HYSEN2PFC_FROST_PROTECTION_ON,
    HYSEN2PFC_SCHEDULE_TODAY,
    HYSEN2PFC_SCHEDULE_12345,
    HYSEN2PFC_SCHEDULE_123456,
    HYSEN2PFC_SCHEDULE_1234567,
    HYSEN2PFC_PERIOD_DISABLED,
    HYSEN2PFC_PERIOD_ENABLED,
    HYSEN2PFC_COOLING_MAX_TEMP,
    HYSEN2PFC_COOLING_MIN_TEMP,
    HYSEN2PFC_HEATING_MAX_TEMP,
    HYSEN2PFC_HEATING_MIN_TEMP,
    HYSEN2PFC_MAX_TEMP,
    HYSEN2PFC_MIN_TEMP,
    HYSEN2PFC_WEEKDAY_MONDAY,
    HYSEN2PFC_WEEKDAY_SUNDAY
)

DEVICE_MIN_TEMP         = HYSEN2PFC_MIN_TEMP
DEVICE_MAX_TEMP         = HYSEN2PFC_MAX_TEMP
DEVICE_CALIBRATION_MIN  = HYSEN2PFC_CALIBRATION_MIN
DEVICE_CALIBRATION_MAX  = HYSEN2PFC_CALIBRATION_MAX
DEVICE_COOLING_MAX_TEMP = HYSEN2PFC_COOLING_MAX_TEMP
DEVICE_COOLING_MIN_TEMP = HYSEN2PFC_COOLING_MIN_TEMP
DEVICE_HEATING_MAX_TEMP = HYSEN2PFC_HEATING_MAX_TEMP
DEVICE_HEATING_MIN_TEMP = HYSEN2PFC_HEATING_MIN_TEMP
DEVICE_WEEKDAY_MONDAY   = HYSEN2PFC_WEEKDAY_MONDAY
DEVICE_WEEKDAY_SUNDAY   = HYSEN2PFC_WEEKDAY_SUNDAY

HVAC_MODES = [
    HVACMode.OFF,
    HVACMode.COOL,
    HVACMode.HEAT,
    HVACMode.FAN_ONLY
]

HYSEN_KEY_LOCK_TO_HASS = {
    HYSEN2PFC_KEY_ALL_UNLOCKED   : STATE_ALL_UNLOCKED,
    HYSEN2PFC_KEY_POWER_UNLOCKED : STATE_POWER_UNLOCKED,
    HYSEN2PFC_KEY_ALL_LOCKED     : STATE_ALL_LOCKED,
}

HASS_KEY_LOCK_TO_HYSEN = {
    STATE_ALL_UNLOCKED   : HYSEN2PFC_KEY_ALL_UNLOCKED,
    STATE_POWER_UNLOCKED : HYSEN2PFC_KEY_POWER_UNLOCKED,
    STATE_ALL_LOCKED     : HYSEN2PFC_KEY_ALL_LOCKED,
}

HYSEN_POWER_STATE_TO_HASS = {
    HYSEN2PFC_POWER_ON  : STATE_ON,
    HYSEN2PFC_POWER_OFF : STATE_OFF,
}

HASS_POWER_STATE_TO_HYSEN = {
    STATE_ON  : HYSEN2PFC_POWER_ON,
    STATE_OFF : HYSEN2PFC_POWER_OFF,
}

HYSEN_VALVE_STATE_TO_HASS = {
    HYSEN2PFC_VALVE_ON  : STATE_OPEN,
    HYSEN2PFC_VALVE_OFF : STATE_CLOSED,
}

HYSEN_HYSTERESIS_TO_HASS = {
    HYSEN2PFC_HYSTERESIS_HALVE : STATE_HYSTERESIS_HALVE,
    HYSEN2PFC_HYSTERESIS_WHOLE : STATE_HYSTERESIS_WHOLE,
}

HASS_HYSTERESIS_TO_HYSEN = {
    STATE_HYSTERESIS_HALVE : HYSEN2PFC_HYSTERESIS_HALVE,
    STATE_HYSTERESIS_WHOLE : HYSEN2PFC_HYSTERESIS_WHOLE,
}

HYSEN_FAN_CONTROL_TO_HASS = {
    HYSEN2PFC_FAN_CONTROL_ON  : STATE_ON,
    HYSEN2PFC_FAN_CONTROL_OFF : STATE_OFF,
}

HASS_FAN_CONTROL_TO_HYSEN = {
    STATE_ON  : HYSEN2PFC_FAN_CONTROL_ON,
    STATE_OFF : HYSEN2PFC_FAN_CONTROL_OFF,
}

HYSEN_FROST_PROTECTION_TO_HASS = {
    HYSEN2PFC_FROST_PROTECTION_ON   : STATE_ON,
    HYSEN2PFC_FROST_PROTECTION_OFF  : STATE_OFF,
}

HASS_FROST_PROTECTION_TO_HYSEN = {
    STATE_ON  : HYSEN2PFC_FROST_PROTECTION_ON,
    STATE_OFF : HYSEN2PFC_FROST_PROTECTION_OFF,
}

HYSEN_SCHEDULE_TO_HASS = {
    HYSEN2PFC_SCHEDULE_TODAY   : PRESET_TODAY,
    HYSEN2PFC_SCHEDULE_12345   : PRESET_WORKDAYS,
    HYSEN2PFC_SCHEDULE_123456  : PRESET_SIXDAYS,
    HYSEN2PFC_SCHEDULE_1234567 : PRESET_FULLWEEK,
}

HASS_SCHEDULE_TO_HYSEN = {
    PRESET_TODAY    : HYSEN2PFC_SCHEDULE_TODAY,
    PRESET_WORKDAYS : HYSEN2PFC_SCHEDULE_12345,
    PRESET_SIXDAYS  : HYSEN2PFC_SCHEDULE_123456,
    PRESET_FULLWEEK : HYSEN2PFC_SCHEDULE_1234567,
}

HYSEN_MODE_TO_HASS = {
    HYSEN2PFC_MODE_FAN  : HVACMode.FAN_ONLY,
    HYSEN2PFC_MODE_COOL : HVACMode.COOL,
    HYSEN2PFC_MODE_HEAT : HVACMode.HEAT,
}

HASS_MODE_TO_HYSEN = {
    HVACMode.FAN_ONLY : HYSEN2PFC_MODE_FAN,
    HVACMode.COOL     : HYSEN2PFC_MODE_COOL,
    HVACMode.HEAT     : HYSEN2PFC_MODE_HEAT,
}

HYSEN_FAN_TO_HASS = {
    HYSEN2PFC_FAN_LOW    : FAN_LOW,
    HYSEN2PFC_FAN_MEDIUM : FAN_MEDIUM,
    HYSEN2PFC_FAN_HIGH   : FAN_HIGH,
    HYSEN2PFC_FAN_AUTO   : FAN_AUTO,
}

HASS_FAN_TO_HYSEN = {
    FAN_LOW          : HYSEN2PFC_FAN_LOW,
    FAN_MEDIUM       : HYSEN2PFC_FAN_MEDIUM,
    FAN_HIGH         : HYSEN2PFC_FAN_HIGH,
    FAN_AUTO         : HYSEN2PFC_FAN_AUTO,
}

HYSEN_PERIOD_ENABLED_TO_HASS = {
    HYSEN2PFC_PERIOD_ENABLED  : True,
    HYSEN2PFC_PERIOD_DISABLED : False,
}

HASS_PERIOD_ENABLED_TO_HYSEN = {
    True  : HYSEN2PFC_PERIOD_ENABLED,
    False : HYSEN2PFC_PERIOD_DISABLED,
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_MAC): cv.string,
        vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
        vol.Optional(CONF_SYNC_CLOCK, default=DEFAULT_SYNC_CLOCK): cv.boolean,
        vol.Optional(CONF_SYNC_HOUR, default=DEFAULT_SYNC_HOUR): cv.positive_int,
    }
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Hysen HVACR thermostat platform from a config entry."""
    if DATA_KEY not in hass.data:
        hass.data[DATA_KEY] = {}

    name = config_entry.data.get(CONF_NAME, DEFAULT_NAME)
    host = config_entry.data[CONF_HOST]
    mac_addr = binascii.unhexlify(config_entry.data[CONF_MAC].replace(":", ""))
    timeout = config_entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
    sync_clock = config_entry.data.get(CONF_SYNC_CLOCK, DEFAULT_SYNC_CLOCK)
    sync_hour = config_entry.data.get(CONF_SYNC_HOUR, DEFAULT_SYNC_HOUR)

    hysen_device = Hysen2PipeFanCoilDevice((host, 80), mac_addr, timeout, sync_clock, sync_hour)

    device_id = hass.data[DATA_KEY][host]["device_id"]
    device = Hysen2PipeFanCoil(name, hysen_device, host, device_id)
    async_add_entities([device], update_before_add=True)

    platform = entity_platform.async_get_current_platform()

    platform.async_register_entity_service(
        SERVICE_SET_KEY_LOCK,
        {
            vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
            vol.Required(ATTR_KEY_LOCK): vol.In([STATE_ALL_UNLOCKED, STATE_POWER_UNLOCKED, STATE_ALL_LOCKED]),
        },
        Hysen2PipeFanCoil.async_set_key_lock.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_SET_HVAC_MODE,
        {
            vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
            vol.Required(ATTR_HVAC_MODE): vol.In([HVACMode.OFF, HVACMode.COOL, HVACMode.HEAT, HVACMode.FAN_ONLY]),
        },
        Hysen2PipeFanCoil.async_set_hvac_mode.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_SET_TEMPERATURE,
        {
            vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
            vol.Required(ATTR_TEMPERATURE): vol.All(
                vol.Coerce(int), vol.Clamp(min=DEVICE_MIN_TEMP, max=DEVICE_MAX_TEMP)
            ),
        },
        Hysen2PipeFanCoil.async_set_temperature.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_TURN_ON,
        {
            vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
        },
        Hysen2PipeFanCoil.async_turn_on.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_TURN_OFF,
        {
            vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
        },
        Hysen2PipeFanCoil.async_turn_off.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_SET_HYSTERESIS,
        {
            vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
            vol.Required(ATTR_HYSTERESIS): vol.In([STATE_HYSTERESIS_HALVE, STATE_HYSTERESIS_WHOLE]),
        },
        Hysen2PipeFanCoil.async_set_hysteresis.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_SET_CALIBRATION,
        {
            vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
            vol.Required(ATTR_CALIBRATION): vol.All(
                vol.Coerce(float), vol.Clamp(min=DEVICE_CALIBRATION_MIN, max=DEVICE_CALIBRATION_MAX)
            ),
        },
        Hysen2PipeFanCoil.async_set_calibration.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_SET_COOLING_MAX_TEMP,
        {
            vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
            vol.Required(ATTR_LIMIT_TEMP): vol.All(
                vol.Coerce(int), vol.Clamp(min=DEVICE_COOLING_MIN_TEMP, max=DEVICE_COOLING_MAX_TEMP)
            ),
        },
        Hysen2PipeFanCoil.async_set_cooling_max_temp.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_SET_COOLING_MIN_TEMP,
        {
            vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
            vol.Required(ATTR_LIMIT_TEMP): vol.All(
                vol.Coerce(int), vol.Clamp(min=DEVICE_COOLING_MIN_TEMP, max=DEVICE_COOLING_MAX_TEMP)
            ),
        },
        Hysen2PipeFanCoil.async_set_cooling_min_temp.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_SET_HEATING_MAX_TEMP,
        {
            vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
            vol.Required(ATTR_LIMIT_TEMP): vol.All(
                vol.Coerce(int), vol.Clamp(min=DEVICE_HEATING_MIN_TEMP, max=DEVICE_HEATING_MAX_TEMP)
            ),
        },
        Hysen2PipeFanCoil.async_set_heating_max_temp.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_SET_HEATING_MIN_TEMP,
        {
            vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
            vol.Required(ATTR_LIMIT_TEMP): vol.All(
                vol.Coerce(int), vol.Clamp(min=DEVICE_HEATING_MIN_TEMP, max=DEVICE_HEATING_MAX_TEMP)
            ),
        },
        Hysen2PipeFanCoil.async_set_heating_min_temp.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_SET_FAN_CONTROL,
        {
            vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
            vol.Required(ATTR_FAN_CONTROL): vol.In([STATE_ON, STATE_OFF]),
        },
        Hysen2PipeFanCoil.async_set_fan_control.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_SET_FROST_PROTECTION,
        {
            vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
            vol.Required(ATTR_FROST_PROTECTION): vol.In([STATE_ON, STATE_OFF]),
        },
        Hysen2PipeFanCoil.async_set_frost_protection.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_SET_TIME,
        {
            vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
            vol.Optional(ATTR_TIME_NOW): cv.boolean,
            vol.Optional(ATTR_DEVICE_TIME): cv.time,
            vol.Optional(ATTR_DEVICE_WEEKDAY): vol.All(
                vol.Coerce(int), vol.Clamp(min=DEVICE_WEEKDAY_MONDAY, max=DEVICE_WEEKDAY_SUNDAY)
            ),
        },
        Hysen2PipeFanCoil.async_set_time.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_SET_SCHEDULE,
        {
            vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
            vol.Optional(ATTR_WEEKLY_SCHEDULE): vol.In([PRESET_TODAY, PRESET_WORKDAYS, PRESET_SIXDAYS, PRESET_FULLWEEK]),
            vol.Optional(ATTR_PERIOD1_ENABLED): cv.boolean,
            vol.Optional(ATTR_PERIOD1_START_TIME): cv.time,
            vol.Optional(ATTR_PERIOD1_END_TIME): cv.time,
            vol.Optional(ATTR_PERIOD2_ENABLED): cv.boolean,
            vol.Optional(ATTR_PERIOD2_START_TIME): cv.time,
            vol.Optional(ATTR_PERIOD2_END_TIME): cv.time,
        },
        Hysen2PipeFanCoil.async_set_schedule.__name__,
    )

class Hysen2PipeFanCoil(ClimateEntity):
    """Representation of a Hysen HVACR device."""

    def __init__(self, name, hysen_device, host, device_id):
        """Initialize the Hysen HVACR device."""
        self._name = name
        self._hysen_device = hysen_device
        self._host = host
        self._device_id = device_id
        self._power_state = STATE_OFF
        self._available = False
        self._enable_turn_on_off_backwards_compatibility = False
        self._unique_id = hysen_device.mac.hex().lower()
        # Initialize all attributes to avoid AttributeError
        self._fwversion = None
        self._key_lock = None
        self._valve_state = None
        self._hvac_mode = None
        self._fan_mode = None
        self._room_temp = None
        self._target_temp = None
        self._hysteresis = None
        self._calibration = None
        self._cooling_max_temp = None
        self._cooling_min_temp = None
        self._heating_max_temp = None
        self._heating_min_temp = None
        self._fan_control = None
        self._frost_protection = None
        self._device_time = None
        self._device_weekday = None
        self._unknown = None
        self._schedule = None
        self._period1_enabled = None
        self._period1_start_time = None
        self._period1_end_time = None
        self._period2_enabled = None
        self._period2_start_time = None
        self._period2_end_time = None
        self._time_valve_on = None

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id

    @property
    def device_info(self):
        """Return device information to link this entity to a device."""
        return {
            "identifiers": {("hysen2pfc", self._hysen_device.mac.hex().lower())},
            "name": self._name,
            "manufacturer": "Hysen",
            "model": "HY03AC-1-Wifi",
            "sw_version": getattr(self, "_fwversion", "Unknown"),
            "configuration_url": f"http://{self._host}",
        }

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def state(self):
        """Return current state."""
        return self.hvac_mode

    @property
    def precision(self):
        """Return the precision of the system."""
        return PRECISION_WHOLE

    @property
    def temperature_unit(self):
        """Return the unit of measurement which this thermostat uses."""
        return UnitOfTemperature.CELSIUS

    @property
    def hvac_mode(self):
        """Return the current operation mode."""
        if self.is_on:
            return self._hvac_mode
        else:
            return HVACMode.OFF

    @property
    def hvac_modes(self):
        """Return the list of available operation modes."""
        if self._fan_mode == FAN_AUTO:
            return [HVACMode.OFF, HVACMode.COOL, HVACMode.HEAT]
        else:
            return [HVACMode.OFF, HVACMode.COOL, HVACMode.HEAT, HVACMode.FAN_ONLY]

    @property
    def hvac_action(self):
        """Return the current running hvac operation."""
        if self.is_on:
            if self._hvac_mode == HVACMode.FAN_ONLY:
                return HVACAction.FAN
            if self._valve_state == STATE_CLOSED:
                return HVACAction.IDLE
            if self._hvac_mode == HVACMode.HEAT:
                return HVACAction.HEATING
            else:
                return HVACAction.COOLING
        else:
            return HVACAction.OFF

    @property
    def preset_mode(self):
        """Return the current preset mode."""
        if self.is_on:
            return self._schedule
        else:
            return PRESET_NONE

    @property
    def preset_modes(self):
        """Return a list of available preset modes."""
        if self.is_on:
            return [PRESET_TODAY, PRESET_WORKDAYS, PRESET_SIXDAYS, PRESET_FULLWEEK]
        else:
            return [PRESET_NONE]

    @property
    def current_temperature(self):
        """Return the sensor temperature."""
        return self._room_temp

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        if self.is_on and self._hvac_mode != HVACMode.FAN_ONLY:
            return self._target_temp
        else:
            return None

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        if self.is_on and self._hvac_mode != HVACMode.FAN_ONLY:
            return PRECISION_WHOLE
        else:
            return None

    @property
    def fan_mode(self):
        """Return the current fan setting."""
        return self._fan_mode

    @property
    def fan_modes(self):
        """Return the list of available fan modes."""
        if self._hvac_mode == HVACMode.OFF:
            return FAN_MODES
        elif self._hvac_mode == HVACMode.FAN_ONLY:
            return FAN_MODES_FAN_ONLY
        else:
            return FAN_MODES

    @property
    def supported_features(self):
        """Returns the list of supported features."""
        if self._hvac_mode == HVACMode.FAN_ONLY:
            return ClimateEntityFeature.FAN_MODE | ClimateEntityFeature.PRESET_MODE | ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF
        else:
            return ClimateEntityFeature.FAN_MODE | ClimateEntityFeature.PRESET_MODE | ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF | ClimateEntityFeature.TARGET_TEMPERATURE

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def min_temp(self):
        """Returns the minimum supported temperature."""
        if self._hvac_mode == HVACMode.FAN_ONLY:
            return None
        elif self._hvac_mode == HVACMode.HEAT:
            return self._heating_min_temp
        else:
            return self._cooling_min_temp

    @property
    def max_temp(self):
        """Returns the maximum supported temperature."""
        if self._hvac_mode == HVACMode.FAN_ONLY:
            return None
        elif self._hvac_mode == HVACMode.HEAT:
            return self._heating_max_temp
        else:
            return self._cooling_max_temp

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._power_state == STATE_ON

    @property
    def extra_state_attributes(self):
        """Return the specific state attributes of the device."""
        return {
            ATTR_FWVERSION: self._fwversion,
            ATTR_HVAC_MODE: self._hvac_mode,
            ATTR_KEY_LOCK: self._key_lock,
            ATTR_VALVE_STATE: self._valve_state,
            ATTR_POWER_STATE: self._power_state,
            ATTR_HYSTERESIS: self._hysteresis,
            ATTR_CALIBRATION: self._calibration,
            ATTR_COOLING_MAX_TEMP: self._cooling_max_temp,
            ATTR_COOLING_MIN_TEMP: self._cooling_min_temp,
            ATTR_HEATING_MAX_TEMP: self._heating_max_temp,
            ATTR_HEATING_MIN_TEMP: self._heating_min_temp,
            ATTR_FAN_CONTROL: self._fan_control,
            ATTR_FROST_PROTECTION: self._frost_protection,
            ATTR_DEVICE_TIME: self._device_time,
            ATTR_DEVICE_WEEKDAY: self._device_weekday,
            ATTR_WEEKLY_SCHEDULE: self._schedule,
            ATTR_PERIOD1_ENABLED: self._period1_enabled,
            ATTR_PERIOD1_START_TIME: self._period1_start_time,
            ATTR_PERIOD1_END_TIME: self._period1_end_time,
            ATTR_PERIOD2_ENABLED: self._period2_enabled,
            ATTR_PERIOD2_START_TIME: self._period2_start_time,
            ATTR_PERIOD2_END_TIME: self._period2_end_time,
            ATTR_TIME_VALVE_ON: self._time_valve_on,
        }

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temp = int(kwargs.get(ATTR_TEMPERATURE))
        _LOGGER.debug("[%s] Setting temperature to %s", self._host, temp)
        await self._async_try_command(
            "Error in set_temperature",
            self._hysen_device.set_target_temp,
            temp)

    async def async_set_fan_mode(self, fan_mode):
        """Set fan speed."""
        if fan_mode not in FAN_MODES:
            _LOGGER.error("[%s] Error in async_set_fan_mode. Unknown fan mode '%s'.", self._host, fan_mode)
            return
        _LOGGER.debug("[%s] Setting fan mode to %s", self._host, fan_mode)
        await self._async_try_command(
            "Error in set_fan_mode",
            self._hysen_device.set_fan_mode,
            HASS_FAN_TO_HYSEN[fan_mode])

    async def async_set_hvac_mode(self, hvac_mode):
        """Set hvac mode."""
        _LOGGER.debug("[%s] Attempting to set hvac_mode to '%s', current is_on: '%s', fan_mode: '%s'",
            self._host, hvac_mode, self.is_on, self._fan_mode)

        if hvac_mode not in HVAC_MODES:
            _LOGGER.error("[%s] Error in async_set_hvac_mode. Unknown hvac mode '%s'.", self._host, hvac_mode)
            return

        if hvac_mode == HVACMode.OFF:
            if self.is_on:
                _LOGGER.debug("[%s] Turning off device", self._host)
                await self.async_turn_off()
        else:
            if not self.is_on:
                _LOGGER.debug("[%s] Turning on device", self._host)
                await self.async_turn_on()
            if hvac_mode == HVACMode.FAN_ONLY and self._fan_mode == FAN_AUTO:
                _LOGGER.debug("[%s] Setting fan mode to low for fan_only", self._host)
                await self.async_set_fan_mode(FAN_LOW)
            if self.preset_mode != PRESET_TODAY:
                _LOGGER.debug("[%s] Setting schedule to manual", self._host)
                await self.async_set_schedule(PRESET_TODAY, None, None, None, None, None, None)
            _LOGGER.debug("[%s] Setting operation mode to %s", self._host, hvac_mode)
            await self._async_try_command(
                "Error in set_operation_mode",
                self._hysen_device.set_operation_mode,
                HASS_MODE_TO_HYSEN[hvac_mode])

    async def async_set_preset_mode(self, preset_mode):
        """Set preset mode."""
        _LOGGER.debug("[%s] Received request to set preset mode to '%s'", self._host, preset_mode)
        if preset_mode not in self.preset_modes:
            _LOGGER.error("[%s] Error in async_set_preset_mode. Unknown preset mode '%s'", self._host, preset_mode)
            return
        _LOGGER.debug("[%s] Setting preset mode to '%s'", self._host, preset_mode)
        await self.async_set_schedule(preset_mode, None, None, None, None, None, None)
        _LOGGER.debug("[%s] Updating state after setting preset mode", self._host)
        await self.async_update()

    async def async_turn_on(self):
        """Turn device on."""
        _LOGGER.debug("[%s] Turning on device", self._host)
        await self._async_try_command(
            "Error in turn_on",
            self._hysen_device.set_power,
            HASS_POWER_STATE_TO_HYSEN[STATE_ON])

    async def async_turn_off(self):
        """Turn device off."""
        _LOGGER.debug("[%s] Turning off device", self._host)
        await self._async_try_command(
            "Error in turn_off",
            self._hysen_device.set_power,
            HASS_POWER_STATE_TO_HYSEN[STATE_OFF])

    async def async_set_key_lock(self, key_lock):
        """Set key lock."""
        _LOGGER.debug("[%s] Setting key lock to %s", self._host, key_lock)
        await self._async_try_command(
            "Error in set_key_lock",
            self._hysen_device.set_key_lock,
            HASS_KEY_LOCK_TO_HYSEN[key_lock])

    async def async_set_hysteresis(self, hysteresis):
        """Set hysteresis."""
        _LOGGER.debug("[%s] Setting hysteresis to %s", self._host, hysteresis)
        await self._async_try_command(
            "Error in set_hysteresis",
            self._hysen_device.set_hysteresis,
            HASS_HYSTERESIS_TO_HYSEN[hysteresis])

    async def async_set_calibration(self, calibration):
        """Set temperature calibration."""
        _LOGGER.debug("[%s] Setting calibration to %s", self._host, calibration)
        await self._async_try_command(
            "Error in set_calibration",
            self._hysen_device.set_calibration,
            calibration)

    async def async_set_cooling_max_temp(self, temp):
        """Set cooling upper limit."""
        _LOGGER.debug("[%s] Setting cooling max temp to %s", self._host, temp)
        await self._async_try_command(
            "Error in set_cooling_max_temp",
            self._hysen_device.set_cooling_max_temp,
            temp)

    async def async_set_cooling_min_temp(self, temp):
        """Set cooling lower limit."""
        _LOGGER.debug("[%s] Setting cooling min temp to %s", self._host, temp)
        await self._async_try_command(
            "Error in set_cooling_min_temp",
            self._hysen_device.set_cooling_min_temp,
            temp)

    async def async_set_heating_max_temp(self, temp):
        """Set heating upper limit."""
        _LOGGER.debug("[%s] Setting heating max temp to %s", self._host, temp)
        await self._async_try_command(
            "Error in set_heating_max_temp",
            self._hysen_device.set_heating_max_temp,
            temp)

    async def async_set_heating_min_temp(self, temp):
        """Set heating lower limit."""
        _LOGGER.debug("[%s] Setting heating min temp to %s", self._host, temp)
        await self._async_try_command(
            "Error in set_heating_min_temp",
            self._hysen_device.set_heating_min_temp,
            temp)

    async def async_set_fan_control(self, fan_control):
        """Set fan coil control mode."""
        _LOGGER.debug("[%s] Setting fan control to %s", self._host, fan_control)
        await self._async_try_command(
            "Error in set_fan_control",
            self._hysen_device.set_fan_control,
            HASS_FAN_CONTROL_TO_HYSEN[fan_control])

    async def async_set_frost_protection(self, frost_protection):
        """Set frost protection."""
        _LOGGER.debug("[%s] Setting frost protection to %s", self._host, frost_protection)
        await self._async_try_command(
            "Error in set_frost_protection",
            self._hysen_device.set_frost_protection,
            HASS_FROST_PROTECTION_TO_HYSEN[frost_protection])

    async def async_set_time(self, now=None, time=None, weekday=None):
        """Set device time or to system time."""
        _LOGGER.debug("[%s] Setting time, now=%s, time=%s, weekday=%s", self._host, now, time, weekday)
        await self._async_try_command(
            "Error in set_time",
            self._hysen_device.set_time,
            datetime.now().hour if now else (None if time is None else time.hour),
            datetime.now().minute if now else (None if time is None else time.minute),
            datetime.now().second if now else (None if time is None else time.second),
            datetime.now().isoweekday() if now else weekday)

    async def async_set_schedule(
        self,
        weekly_schedule=None,
        period1_enabled=None,
        period1_start_time=None,
        period1_end_time=None,
        period2_enabled=None,
        period2_start_time=None,
        period2_end_time=None
    ):
        """Set schedule."""
        _LOGGER.debug("[%s] Setting schedule, weekly=%s", self._host, weekly_schedule)
        if weekly_schedule is not None:
            await self._async_try_command(
                "Error in set_weekly_schedule",
                self._hysen_device.set_weekly_schedule,
                HASS_SCHEDULE_TO_HYSEN[weekly_schedule])
        await self._async_try_command(
            "Error in set_daily_schedule",
            self._hysen_device.set_daily_schedule,
            None if period1_enabled is None else HASS_PERIOD_ENABLED_TO_HYSEN[period1_enabled],
            None if period1_start_time is None else period1_start_time.hour,
            None if period1_start_time is None else period1_start_time.minute,
            None if period1_enabled is None else HASS_PERIOD_ENABLED_TO_HYSEN[period1_enabled],
            None if period1_end_time is None else period1_end_time.hour,
            None if period1_end_time is None else period1_end_time.minute,
            None if period2_enabled is None else HASS_PERIOD_ENABLED_TO_HYSEN[period2_enabled],
            None if period2_start_time is None else period2_start_time.hour,
            None if period2_start_time is None else period2_start_time.minute,
            None if period2_enabled is None else HASS_PERIOD_ENABLED_TO_HYSEN[period2_enabled],
            None if period2_end_time is None else period2_end_time.hour,
            None if period2_end_time is None else period2_end_time.minute)

    async def _async_try_command(self, mask_error, func, *args, **kwargs):
        """Calls a device command and handle error messages."""
        self._available = True
        try:
            await self.hass.async_add_executor_job(partial(func, *args, **kwargs))
        except Exception as exc:
            _LOGGER.error("[%s] %s: %s", self._host, mask_error, exc)
            self._available = False

    async def async_update(self):
        """Get the latest state from the device."""
#        _LOGGER.debug("[%s] Updating device state", self._host)
        await self._async_try_command(
            "Error in get_device_status",
            self._hysen_device.get_device_status)
        if self._available:
            self._fwversion = self._hysen_device.fwversion
            self._key_lock = str(HYSEN_KEY_LOCK_TO_HASS[self._hysen_device.key_lock])
            self._valve_state = str(HYSEN_VALVE_STATE_TO_HASS[self._hysen_device.valve_state])
            self._power_state = str(HYSEN_POWER_STATE_TO_HASS[self._hysen_device.power_state])
            self._hvac_mode = str(HYSEN_MODE_TO_HASS[self._hysen_device.operation_mode])
            self._fan_mode = str(HYSEN_FAN_TO_HASS[self._hysen_device.fan_mode])
            self._room_temp = float(self._hysen_device.room_temp)
            self._target_temp = float(self._hysen_device.target_temp)
            self._hysteresis = str(HYSEN_HYSTERESIS_TO_HASS[self._hysen_device.hysteresis])
            self._calibration = float(self._hysen_device.calibration)
            self._cooling_max_temp = int(self._hysen_device.cooling_max_temp)
            self._cooling_min_temp = int(self._hysen_device.cooling_min_temp)
            self._heating_max_temp = int(self._hysen_device.heating_max_temp)
            self._heating_min_temp = int(self._hysen_device.heating_min_temp)
            self._fan_control = str(HYSEN_FAN_CONTROL_TO_HASS[self._hysen_device.fan_control])
            self._frost_protection = str(HYSEN_FROST_PROTECTION_TO_HASS[self._hysen_device.frost_protection])
            self._device_time = str(self._hysen_device.clock_hour).zfill(2) + ":" + str(self._hysen_device.clock_minute).zfill(2) + ":" + str(self._hysen_device.clock_second).zfill(2)
            self._device_weekday = int(self._hysen_device.clock_weekday)
            self._unknown = self._hysen_device.unknown
            self._schedule = str(HYSEN_SCHEDULE_TO_HASS[self._hysen_device.schedule])
            self._period1_enabled = str(HYSEN_PERIOD_ENABLED_TO_HASS[self._hysen_device.period1_start_enabled])
            self._period1_start_time = str(self._hysen_device.period1_start_hour).zfill(2) + ":" + str(self._hysen_device.period1_start_min).zfill(2)
            self._period1_end_time = str(self._hysen_device.period1_end_hour).zfill(2) + ":" + str(self._hysen_device.period1_end_min).zfill(2)
            self._period2_enabled = str(HYSEN_PERIOD_ENABLED_TO_HASS[self._hysen_device.period2_start_enabled])
            self._period2_start_time = str(self._hysen_device.period2_start_hour).zfill(2) + ":" + str(self._hysen_device.period2_start_min).zfill(2)
            self._period2_end_time = str(self._hysen_device.period2_end_hour).zfill(2) + ":" + str(self._hysen_device.period2_end_min).zfill(2)
            self._time_valve_on = int(self._hysen_device.time_valve_on)
#            _LOGGER.debug("[%s] State updated: hvac_mode=%s, fan_mode=%s, target_temp=%s, available=%s",
#                          self._host, self._hvac_mode, self._fan_mode, self._target_temp, self._available)
