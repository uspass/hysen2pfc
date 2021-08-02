"""
Support for Hysen 2 Pipe Fan Coil Controller.
Hysen HY03AC-1-Wifi device and derivative
"""

import asyncio
from functools import partial
import binascii
import logging
import voluptuous as vol
from homeassistant.helpers import config_validation as cv, entity_platform, service
from datetime import datetime

from homeassistant.components.climate import (
    PLATFORM_SCHEMA, 
    ClimateEntity
)

from homeassistant.components.climate.const import (
    DOMAIN,
    ATTR_HVAC_MODE,
    CURRENT_HVAC_OFF,
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_COOL,
    CURRENT_HVAC_FAN,
    CURRENT_HVAC_IDLE,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH,
    FAN_AUTO,
    HVAC_MODE_OFF,
    HVAC_MODE_HEAT,
    HVAC_MODE_COOL,
    HVAC_MODE_FAN_ONLY,
    PRESET_NONE,
    SERVICE_SET_HVAC_MODE,
    SERVICE_SET_TEMPERATURE ,
    SUPPORT_FAN_MODE,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_TEMPERATURE
)

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
    STATE_ON,
    STATE_OFF,
    STATE_LOCKED,
    STATE_UNLOCKED,
    STATE_OPEN,
    STATE_CLOSED,
    TEMP_CELSIUS
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

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Hysen 2 Pipe Fan Coil Thermostat"

PRESET_SCHEDULED = "Scheduled"
PRESET_MANUAL    = "Manual"

STATE_ALL_UNLOCKED      = "unlocked"
STATE_POWER_UNLOCKED    = "power_unlocked"
STATE_ALL_LOCKED        = "locked"

STATE_HYSTERESIS_HALVE  = "0.5"
STATE_HYSTERESIS_WHOLE  = "1"

STATE_SCHEDULE_MANUAL   = "manual"
STATE_SCHEDULE_12345    = "12345"
STATE_SCHEDULE_123456   = "123456"
STATE_SCHEDULE_1234567  = "1234567"

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

HYSTERESIS_MODES = [
    STATE_HYSTERESIS_HALVE,
    STATE_HYSTERESIS_WHOLE 
]

HVAC_MODES = [
    HVAC_MODE_OFF,
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT, 
    HVAC_MODE_FAN_ONLY
]

FAN_MODES = [
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH,
    FAN_AUTO
]

FAN_MODES_FAN_ONLY = [
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH
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
    HYSEN2PFC_SCHEDULE_TODAY   : STATE_SCHEDULE_MANUAL,
    HYSEN2PFC_SCHEDULE_12345   : STATE_SCHEDULE_12345,
    HYSEN2PFC_SCHEDULE_123456  : STATE_SCHEDULE_123456,
    HYSEN2PFC_SCHEDULE_1234567 : STATE_SCHEDULE_1234567,
}

HASS_SCHEDULE_TO_HYSEN = {
    STATE_SCHEDULE_MANUAL  : HYSEN2PFC_SCHEDULE_TODAY,
    STATE_SCHEDULE_12345   : HYSEN2PFC_SCHEDULE_12345,
    STATE_SCHEDULE_123456  : HYSEN2PFC_SCHEDULE_123456,
    STATE_SCHEDULE_1234567 : HYSEN2PFC_SCHEDULE_1234567,
}

HYSEN_MODE_TO_HASS = {
    HYSEN2PFC_MODE_FAN  : HVAC_MODE_FAN_ONLY,
    HYSEN2PFC_MODE_COOL : HVAC_MODE_COOL,
    HYSEN2PFC_MODE_HEAT : HVAC_MODE_HEAT,
}

HASS_MODE_TO_HYSEN = {
    HVAC_MODE_FAN_ONLY : HYSEN2PFC_MODE_FAN,
    HVAC_MODE_COOL     : HYSEN2PFC_MODE_COOL,
    HVAC_MODE_HEAT     : HYSEN2PFC_MODE_HEAT,
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

DATA_KEY = 'climate.hysen2pfc'

ATTR_FWVERSION               = 'fwversion'
ATTR_KEY_LOCK                = 'key_lock'
ATTR_POWER_STATE             = 'power_state'
ATTR_VALVE_STATE             = 'valve_state'
ATTR_HYSTERESIS              = 'hysteresis'
ATTR_CALIBRATION             = 'calibration'
ATTR_LIMIT_TEMP              = 'temp'
ATTR_COOLING_MAX_TEMP        = 'cooling_max_temp'
ATTR_COOLING_MIN_TEMP        = 'cooling_min_temp'
ATTR_HEATING_MAX_TEMP        = 'heating_max_temp'
ATTR_HEATING_MIN_TEMP        = 'heating_min_temp'
ATTR_FAN_CONTROL             = 'fan_control'
ATTR_FROST_PROTECTION        = 'frost_protection'
ATTR_TIME_NOW                = 'now'
ATTR_DEVICE_TIME             = 'time'
ATTR_DEVICE_WEEKDAY          = 'weekday'
ATTR_WEEKLY_SCHEDULE         = 'weekly_schedule'
ATTR_PERIOD1_ENABLED         = 'period1_enabled'
ATTR_PERIOD1_START_TIME      = 'period1_start_time'
ATTR_PERIOD1_END_TIME        = 'period1_end_time'
ATTR_PERIOD2_ENABLED         = 'period2_enabled'
ATTR_PERIOD2_START_TIME      = 'period2_start_time'
ATTR_PERIOD2_END_TIME        = 'period2_end_time'
ATTR_TIME_VALVE_ON           = 'time_valve_on'

SERVICE_SET_KEY_LOCK         = 'set_key_lock'
SERVICE_SET_HYSTERESIS       = 'set_hysteresis'
SERVICE_SET_CALIBRATION      = 'set_calibration'
SERVICE_SET_COOLING_MAX_TEMP = 'set_cooling_max_temp'
SERVICE_SET_COOLING_MIN_TEMP = 'set_cooling_min_temp'
SERVICE_SET_HEATING_MAX_TEMP = 'set_heating_max_temp'
SERVICE_SET_HEATING_MIN_TEMP = 'set_heating_min_temp'
SERVICE_SET_FAN_CONTROL      = 'set_fan_control'
SERVICE_SET_FROST_PROTECTION = 'set_frost_protection'
SERVICE_SET_TIME             = 'set_time'
SERVICE_SET_SCHEDULE         = 'set_schedule'

CONF_SYNC_CLOCK = 'sync_clock'
CONF_SYNC_HOUR = 'sync_hour'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default = DEFAULT_NAME): cv.string,
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_MAC): cv.string,
        vol.Optional(CONF_TIMEOUT, default = 10): cv.positive_int,
        vol.Optional(CONF_SYNC_CLOCK, default = False): cv.boolean,
        vol.Optional(CONF_SYNC_HOUR, default = 4): cv.positive_int,
    }
)

async def async_setup_platform(hass, config, async_add_entities, discovery_info = None):
    """Set up the Hysen HVACR thermostat platform."""
    if DATA_KEY not in hass.data:
        hass.data[DATA_KEY] = {}

    name = config.get(CONF_NAME)
    host = config.get(CONF_HOST)
    mac_addr = binascii.unhexlify(config.get(CONF_MAC).encode().replace(b':', b''))
    timeout = config.get(CONF_TIMEOUT)
    sync_clock = config.get(CONF_SYNC_CLOCK)
    sync_hour = config.get(CONF_SYNC_HOUR)

    hysen_device = Hysen2PipeFanCoilDevice((host, 80), mac_addr, timeout, sync_clock, sync_hour)
    
    device = Hysen2PipeFanCoil(name, hysen_device, host)
    hass.data[DATA_KEY][host] = device

    async_add_entities([device], update_before_add = True)

    platform = entity_platform.current_platform.get()

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
            vol.Required(ATTR_HVAC_MODE): vol.In([HVAC_MODE_OFF, HVAC_MODE_COOL, HVAC_MODE_HEAT, HVAC_MODE_FAN_ONLY]),
        },
        Hysen2PipeFanCoil.async_set_hvac_mode.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_SET_TEMPERATURE,
        {
            vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
            vol.Required(ATTR_TEMPERATURE): vol.All(
                vol.Coerce(int), vol.Clamp(min = DEVICE_MIN_TEMP, max = DEVICE_MAX_TEMP)
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
                vol.Coerce(float), vol.Clamp(min = DEVICE_CALIBRATION_MIN, max = DEVICE_CALIBRATION_MAX)
            ),
        },
        Hysen2PipeFanCoil.async_set_calibration.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_SET_COOLING_MAX_TEMP,
        {
            vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
            vol.Required(ATTR_LIMIT_TEMP): vol.All(
                vol.Coerce(int), vol.Clamp(min = DEVICE_COOLING_MIN_TEMP, max = DEVICE_COOLING_MAX_TEMP)
            ),
        },
        Hysen2PipeFanCoil.async_set_cooling_max_temp.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_SET_COOLING_MIN_TEMP,
        {
            vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
            vol.Required(ATTR_LIMIT_TEMP): vol.All(
                vol.Coerce(int), vol.Clamp(min = DEVICE_COOLING_MIN_TEMP, max = DEVICE_COOLING_MAX_TEMP)
            ),
        },
        Hysen2PipeFanCoil.async_set_cooling_min_temp.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_SET_HEATING_MAX_TEMP,
        {
            vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
            vol.Required(ATTR_LIMIT_TEMP): vol.All(
                vol.Coerce(int), vol.Clamp(min = DEVICE_HEATING_MIN_TEMP, max = DEVICE_HEATING_MAX_TEMP)
            ),
        },
        Hysen2PipeFanCoil.async_set_heating_max_temp.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_SET_HEATING_MIN_TEMP,
        {
            vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
            vol.Required(ATTR_LIMIT_TEMP): vol.All(
                vol.Coerce(int), vol.Clamp(min = DEVICE_HEATING_MIN_TEMP, max = DEVICE_HEATING_MAX_TEMP)
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
            vol.Required(ATTR_FROST_PROTECTION):  vol.In([STATE_ON, STATE_OFF]),
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
                vol.Coerce(int), vol.Clamp(min = DEVICE_WEEKDAY_MONDAY, max = DEVICE_WEEKDAY_SUNDAY)
            ),
        },
        Hysen2PipeFanCoil.async_set_time.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_SET_SCHEDULE,
        {
            vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
            vol.Optional(ATTR_WEEKLY_SCHEDULE): vol.In([STATE_SCHEDULE_MANUAL, STATE_SCHEDULE_12345, STATE_SCHEDULE_123456, STATE_SCHEDULE_1234567]),
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

    def __init__(self, name, hysen_device, host):
        """Initialize the Hysen HVACR device."""
        self._name = name
        self._hysen_device = hysen_device
        self._host = host

        self._available = False

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id
        
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
        return TEMP_CELSIUS

    @property
    def hvac_mode(self):
        """Return the current operation mode."""
        if self.is_on:
            return self._hvac_mode
        else:
            return HVAC_MODE_OFF

    @property
    def hvac_modes(self):
        """Return the list of available operation modes."""
        if self.is_on:
            if self.fan_mode == FAN_AUTO:
                return [HVAC_MODE_OFF, HVAC_MODE_COOL, HVAC_MODE_HEAT]
            else:
                return [HVAC_MODE_OFF, HVAC_MODE_COOL, HVAC_MODE_HEAT, HVAC_MODE_FAN_ONLY]
        else:
            return [HVAC_MODE_OFF]

    @property
    def hvac_action(self):
        """Return the current running hvac operation."""
        if self.is_on:
            if self.hvac_mode == HVAC_MODE_FAN_ONLY:
                return CURRENT_HVAC_FAN
            if self._valve_state == STATE_CLOSED:
                return CURRENT_HVAC_IDLE
            if self.hvac_mode == HVAC_MODE_HEAT:
                return CURRENT_HVAC_HEAT
            else:
                return CURRENT_HVAC_COOL
        else:
            return CURRENT_HVAC_OFF
#TODO verify
    @property
    def preset_mode(self):
        """Return the current preset mode, e.g., manual, scheduled."""
        # check if is set to manual
        if self._schedule == STATE_SCHEDULE_MANUAL:
            if self.is_on:
                return PRESET_MANUAL
            else:
                return PRESET_NONE
        else:
            return PRESET_SCHEDULED

    @property
    def preset_modes(self):
        """Return a list of available preset modes."""
        if self.is_on:
            return [STATE_SCHEDULE_MANUAL, STATE_SCHEDULE_12345, STATE_SCHEDULE_123456, STATE_SCHEDULE_1234567]
        else:
            return [PRESET_NONE]
#        if self._schedule == STATE_SCHEDULE_MANUAL:
#            if self.is_on:
#                return [PRESET_MANUAL]
#            else:
#                return [PRESET_NONE]
#        else:
#            return [PRESET_SCHEDULED]

    @property
    def current_temperature(self):
        """Return the sensor temperature."""
        return self._room_temp

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        if self.is_on and self.hvac_mode != HVAC_MODE_FAN_ONLY:
            return self._target_temp
        else:
            return None
         
    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        if self.is_on and self.hvac_mode != HVAC_MODE_FAN_ONLY:
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
        if self.hvac_mode == HVAC_MODE_OFF:
            return None
        elif self.hvac_mode == HVAC_MODE_FAN_ONLY:
            return FAN_MODES_FAN_ONLY
        else:
            return FAN_MODES

    @property
    def supported_features(self):
        """Returns the list of supported features."""
        if self.hvac_mode == HVAC_MODE_FAN_ONLY:
            return SUPPORT_FAN_MODE | SUPPORT_PRESET_MODE
        else:
            return SUPPORT_FAN_MODE | SUPPORT_PRESET_MODE | SUPPORT_TARGET_TEMPERATURE

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def min_temp(self):
        """Returns the minimum supported temperature."""
        if self.hvac_mode == HVAC_MODE_FAN_ONLY:
            return None
        elif self.hvac_mode == HVAC_MODE_HEAT:
            return self._heating_min_temp
        else:
            return self._cooling_min_temp

    @property
    def max_temp(self):
        """Returns the maximum supported temperature."""
        if self.hvac_mode == HVAC_MODE_FAN_ONLY:
            return None
        elif self.hvac_mode == HVAC_MODE_HEAT:
            return self._heating_max_temp
        else:
            return self._cooling_max_temp

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._power_state == STATE_ON

    @property
    def device_state_attributes(self):
        """Return the specific state attributes of the device."""
        attrs = {}
        if self._available:
            attrs.update({
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
            })
        return attrs

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temp = int(kwargs.get(ATTR_TEMPERATURE))
        await self._async_try_command(
            "Error in set_temperature",
            self._hysen_device.set_target_temp,
            temp)

    async def async_set_fan_mode(self, fan_mode):
        """Set fan speed."""
        if fan_mode not in FAN_MODES:
            _LOGGER.error("[%s] Error in async_set_fan_mode. Unknown fan mode \'%s\'.",
                self._host,
                fan_mode)
            return
        await self._async_try_command(
            "Error in set_fan_mode",
            self._hysen_device.set_fan_mode,
            HASS_FAN_TO_HYSEN[fan_mode])
        
    async def async_set_hvac_mode(self, hvac_mode):
        """Set hvac mode."""
        if hvac_mode not in HVAC_MODES:
            _LOGGER.error("[%s] Error in async_set_hvac_mode. Unknown hvac mode \'%s\'.",
                self._host,
                hvac_mode)
            return
        if hvac_mode == HVAC_MODE_OFF:
            if self.is_on:
                await self.async_turn_off()
            else:
                # make sure it will not be in HVAC_MODE_FAN_ONLY and FAN_AUTO
                if hvac_mode == HVAC_MODE_FAN_ONLY and self.fan_mode == FAN_AUTO:
                    await self.async_set_fan_mode(FAN_LOW)
                # check if it is in scheduled mode
                if self.preset_mode == PRESET_SCHEDULED:
                    await self.async_set_schedule(STATE_SCHEDULE_MANUAL, 
                                                  None, None, None, None, None, None)
                await self.async_turn_on()
        else:
            await self._async_try_command(
                "Error in set_operation_mode",
                self._hysen_device.set_operation_mode,
                HASS_MODE_TO_HYSEN[hvac_mode])

    async def async_set_preset_mode(self, preset_mode):
        """Set preset mode."""
        await self.async_set_schedule(preset_mode, 
                                      None, None, None, None, None, None)
        return

    async def async_turn_on(self):
        """Turn device on."""
        await self._async_try_command(
            "Error in turn_on",
            self._hysen_device.set_power,
            HASS_POWER_STATE_TO_HYSEN[STATE_ON])

    async def async_turn_off(self):
        """Turn device off."""
        await self._async_try_command(
            "Error in turn_off",
            self._hysen_device.set_power,
            HASS_POWER_STATE_TO_HYSEN[STATE_OFF])

    async def async_set_key_lock(self, key_lock):
        """Set key lock 
           unlocked = Unlocked 
           power_unlocked = All buttons locked except Power
           locked = All buttons locked"""
        await self._async_try_command(
            "Error in set_key_lock",
            self._hysen_device.set_key_lock,
            HASS_KEY_LOCK_TO_HYSEN[key_lock])

    async def async_set_hysteresis(self, hysteresis):
        """Set hysteresis. 
           0.5 = 0.5 degree Celsius hysteresis
           1 = 1 degree Celsius hysteresis"""
        await self._async_try_command(
            "Error in set_hysteresis",
            self._hysen_device.set_hysteresis,
            HASS_HYSTERESIS_TO_HYSEN[hysteresis])

    async def async_set_calibration(self, calibration):
        """Set temperature calibration. 
           Range -5~+5 degree Celsius in 0.1 degree Celsius step."""
        await self._async_try_command(
            "Error in set_calibration",
            self._hysen_device.set_calibration,
            calibration)

    async def async_set_cooling_max_temp(self, temp):
        """Set cooling upper limit."""
        await self._async_try_command(
            "Error in set_cooling_max_temp",
            self._hysen_device.set_cooling_max_temp,
            temp)

    async def async_set_cooling_min_temp(self, temp):
        """Set cooling lower limit."""
        await self._async_try_command(
            "Error in set_cooling_min_temp",
            self._hysen_device.set_cooling_min_temp,
            temp)

    async def async_set_heating_max_temp(self, temp):
        """Set heating upper limit."""
        await self._async_try_command(
            "Error in set_heating_max_temp",
            self._hysen_device.set_heating_max_temp,
            temp)

    async def async_set_heating_min_temp(self, temp):
        """Set heating lower limit."""
        await self._async_try_command(
            "Error in set_heating_min_temp",
            self._hysen_device.set_heating_min_temp,
            temp)

    async def async_set_fan_control(self, fan_control):
        """Set fan coil control mode 
           Off = Fan is stopped when target temp reached 
           On = Fan continues spinning when target temp reached."""
        await self._async_try_command(
            "Error in set_fan_control",
            self._hysen_device.set_fan_control,
            HASS_FAN_CONTROL_TO_HYSEN[fan_control])

    async def async_set_frost_protection(self, frost_protection):
        """Set frost_protection 
        Off = No frost protection 
        On = Keeps the room temp between 5 to 7 degree when device is turned off."""
        await self._async_try_command(
            "Error in set_frost_protection",
            self._hysen_device.set_frost_protection,
            HASS_FROST_PROTECTION_TO_HYSEN[frost_protection])

    async def async_set_time(self, now = None, time = None, weekday = None):
        """Set device time or to system time."""
        await self._async_try_command(
            "Error in set_time",
            self._hysen_device.set_time,
            datetime.now().hour if now else (None if time is None else time.hour),
            datetime.now().minute if now else (None if time is None else time.minute),
            datetime.now().second if now else (None if time is None else time.second),
            datetime.now().isoweekday() if now else weekday)

    async def async_set_schedule(
                                 self, 
                                 weekly_schedule = None,
                                 period1_enabled = None,
                                 period1_start_time = None,
                                 period1_end_time = None,
                                 period2_enabled = None,
                                 period2_start_time = None,
                                 period2_end_time = None
                                ):
        """Set schedule ."""
        """Set weekly schedule mode 
           today = Daily schedule valid for today 
           12345 = Daily schedule valid from Monday to Friday
           123456 = Daily schedule valid from Monday to Saturday 
           1234567 = Daily schedule valid from Monday to Sunday
           Set daily schedule in 2 periods"""
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
            _LOGGER.error("[%s] %s %s: %s", self._host, self._name, mask_error, exc)
            self._available = False

    async def async_update(self):
        """Get the latest state from the device."""
        await self._async_try_command(
            "Error in get_device_status",
            self._hysen_device.get_device_status)
        self._unique_id = self._hysen_device.unique_id
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

