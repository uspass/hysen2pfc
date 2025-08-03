# Constants for Hysen 2 Pipe Fan Coil Integration

# Domain and default name
DOMAIN = "hysen2pfc"
DEFAULT_NAME = "Hysen 2 Pipe Fan Coil Thermostat"
DATA_KEY = "climate.hysen2pfc"

# Configuration keys specific to this integration
CONF_SYNC_CLOCK = "sync_clock"
CONF_SYNC_HOUR = "sync_hour"

# Default configuration values
DEFAULT_TIMEOUT = 10
DEFAULT_SYNC_CLOCK = True
DEFAULT_SYNC_HOUR = 4

# Device states
STATE_ON = "on"
STATE_OFF = "off"
STATE_OPEN = "open"
STATE_CLOSED = "closed"
STATE_ALL_UNLOCKED = "unlocked"
STATE_POWER_UNLOCKED = "power_unlocked"
STATE_ALL_LOCKED = "locked"
STATE_HYSTERESIS_HALVE = "0.5"
STATE_HYSTERESIS_WHOLE = "1"
PRESET_TODAY = "Today"
PRESET_WORKDAYS = "Workdays"
PRESET_SIXDAYS = "Sixdays"
PRESET_FULLWEEK = "Fullweek"

# Attribute keys
ATTR_FWVERSION = "fwversion"
ATTR_KEY_LOCK = "key_lock"
ATTR_POWER_STATE = "power_state"
ATTR_VALVE_STATE = "valve_state"
ATTR_HYSTERESIS = "hysteresis"
ATTR_CALIBRATION = "calibration"
ATTR_LIMIT_TEMP = "temp"
ATTR_COOLING_MAX_TEMP = "cooling_max_temp"
ATTR_COOLING_MIN_TEMP = "cooling_min_temp"
ATTR_HEATING_MAX_TEMP = "heating_max_temp"
ATTR_HEATING_MIN_TEMP = "heating_min_temp"
ATTR_FAN_CONTROL = "fan_control"
ATTR_FROST_PROTECTION = "frost_protection"
ATTR_TIME_NOW = "now"
ATTR_DEVICE_TIME = "time"
ATTR_DEVICE_WEEKDAY = "weekday"
ATTR_WEEKLY_SCHEDULE = "weekly_schedule"
ATTR_PERIOD1_ENABLED = "period1_enabled"
ATTR_PERIOD1_START_TIME = "period1_start_time"
ATTR_PERIOD1_END_TIME = "period1_end_time"
ATTR_PERIOD2_ENABLED = "period2_enabled"
ATTR_PERIOD2_START_TIME = "period2_start_time"
ATTR_PERIOD2_END_TIME = "period2_end_time"
ATTR_TIME_VALVE_ON = "time_valve_on"

# Service names
SERVICE_SET_KEY_LOCK = "set_key_lock"
SERVICE_SET_HYSTERESIS = "set_hysteresis"
SERVICE_SET_CALIBRATION = "set_calibration"
SERVICE_SET_COOLING_MAX_TEMP = "set_cooling_max_temp"
SERVICE_SET_COOLING_MIN_TEMP = "set_cooling_min_temp"
SERVICE_SET_HEATING_MAX_TEMP = "set_heating_max_temp"
SERVICE_SET_HEATING_MIN_TEMP = "set_heating_min_temp"
SERVICE_SET_FAN_CONTROL = "set_fan_control"
SERVICE_SET_FROST_PROTECTION = "set_frost_protection"
SERVICE_SET_TIME = "set_time"
SERVICE_SET_SCHEDULE = "set_schedule"

# Hysteresis modes
HYSTERESIS_MODES = [
    STATE_HYSTERESIS_HALVE,
    STATE_HYSTERESIS_WHOLE
]

# Fan modes
FAN_MODES = [
    "low",
    "medium",
    "high",
    "auto"
]

# Fan modes for fan-only operation
FAN_MODES_FAN_ONLY = [
    "low",
    "medium",
    "high"
]
