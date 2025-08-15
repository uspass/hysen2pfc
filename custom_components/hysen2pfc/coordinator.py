"""
DataUpdateCoordinator for Hysen 2 Pipe Fan Coil integration.
"""

import logging
from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from .const import (
    DOMAIN,
    DATA_KEY_FWVERSION,
    DATA_KEY_KEY_LOCK,
    DATA_KEY_VALVE_STATE,
    DATA_KEY_POWER_STATE,
    DATA_KEY_HVAC_MODE,
    DATA_KEY_FAN_MODE,
    DATA_KEY_ROOM_TEMP,
    DATA_KEY_TARGET_TEMP,
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
    DATA_KEY_PRESET_MODE,
    DATA_KEY_SLOT1_START_ENABLE,
    DATA_KEY_SLOT1_START_TIME,
    DATA_KEY_SLOT1_STOP_ENABLE,
    DATA_KEY_SLOT1_STOP_TIME,
    DATA_KEY_SLOT2_START_ENABLE,
    DATA_KEY_SLOT2_START_TIME,
    DATA_KEY_SLOT2_STOP_ENABLE,
    DATA_KEY_SLOT2_STOP_TIME,
    DATA_KEY_TIME_VALVE_ON,
    MODE_HYSEN_TO_HASS,
    FAN_HYSEN_TO_HASS,
    PRESET_HYSEN_TO_HASS,
    KEY_LOCK_HYSEN_TO_HASS,
    VALVE_STATE_HYSEN_TO_HASS,
    POWER_STATE_HYSEN_TO_HASS,
    SLOT_ENABLED_HYSEN_TO_HASS,
    HYSTERESIS_HYSEN_TO_HASS,
    FAN_CONTROL_HYSEN_TO_HASS,
    FROST_PROTECTION_HYSEN_TO_HASS,
)

_LOGGER = logging.getLogger(__name__)

class HysenCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Hysen device data.

    Periodically updates device status and maps it to Home Assistant-compatible formats.
    """

    def __init__(self, hass: HomeAssistant, device, host):
        """Initialize the Hysen coordinator.

        Args:
            hass: The Home Assistant instance.
            device: The Hysen2PipeFanCoilDevice instance to communicate with.
            host: The host address of the device.
        """
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{host}",
            update_interval=timedelta(seconds=30),
        )
        self.device = device
        self.host = host

    async def _async_update_data(self):
        """Fetch data from the Hysen device.

        Retrieves the latest device status and maps it to Home Assistant-compatible formats.

        Returns:
            dict: A dictionary containing the updated device data.

        Raises:
            UpdateFailed: If communication with the device fails.
        """
        _LOGGER.debug("Fetching data for device at %s", self.host)
        try:
            await self.hass.async_add_executor_job(self.device.get_device_status)
            data = {
                DATA_KEY_FWVERSION: self.device.fwversion,
                DATA_KEY_KEY_LOCK: KEY_LOCK_HYSEN_TO_HASS.get(self.device.key_lock_type),
                DATA_KEY_VALVE_STATE: VALVE_STATE_HYSEN_TO_HASS.get(self.device.valve_state),
                DATA_KEY_POWER_STATE: POWER_STATE_HYSEN_TO_HASS.get(self.device.power_state),
                DATA_KEY_HVAC_MODE: MODE_HYSEN_TO_HASS.get(self.device.operation_mode),
                DATA_KEY_FAN_MODE: FAN_HYSEN_TO_HASS.get(self.device.fan_mode),
                DATA_KEY_PRESET_MODE: PRESET_HYSEN_TO_HASS.get(self.device.schedule),
                DATA_KEY_ROOM_TEMP: self.device.room_temp,
                DATA_KEY_TARGET_TEMP: self.device.target_temp,
                DATA_KEY_HYSTERESIS: HYSTERESIS_HYSEN_TO_HASS.get(self.device.hysteresis),
                DATA_KEY_CALIBRATION: self.device.calibration,
                DATA_KEY_COOLING_MAX_TEMP: self.device.cooling_max_temp,
                DATA_KEY_COOLING_MIN_TEMP: self.device.cooling_min_temp,
                DATA_KEY_HEATING_MAX_TEMP: self.device.heating_max_temp,
                DATA_KEY_HEATING_MIN_TEMP: self.device.heating_min_temp,
                DATA_KEY_FAN_CONTROL: FAN_CONTROL_HYSEN_TO_HASS.get(self.device.fan_control),
                DATA_KEY_FROST_PROTECTION: FROST_PROTECTION_HYSEN_TO_HASS.get(self.device.frost_protection),
                DATA_KEY_CLOCK_HOUR: self.device.clock_hour,
                DATA_KEY_CLOCK_MINUTE: self.device.clock_minute,
                DATA_KEY_CLOCK_SECOND: self.device.clock_second,
                DATA_KEY_CLOCK_WEEKDAY: self.device.clock_weekday,
                DATA_KEY_SLOT1_START_ENABLE: SLOT_ENABLED_HYSEN_TO_HASS.get(self.device.period1_start_enabled),
                DATA_KEY_SLOT1_START_TIME: f"{self.device.period1_start_hour}:{self.device.period1_start_min:02d}",
                DATA_KEY_SLOT1_STOP_ENABLE: SLOT_ENABLED_HYSEN_TO_HASS.get(self.device.period1_end_enabled),
                DATA_KEY_SLOT1_STOP_TIME: f"{self.device.period1_end_hour}:{self.device.period1_end_min:02d}",
                DATA_KEY_SLOT2_START_ENABLE: SLOT_ENABLED_HYSEN_TO_HASS.get(self.device.period2_start_enabled),
                DATA_KEY_SLOT2_START_TIME: f"{self.device.period2_start_hour}:{self.device.period2_start_min:02d}",
                DATA_KEY_SLOT2_STOP_ENABLE: SLOT_ENABLED_HYSEN_TO_HASS.get(self.device.period2_end_enabled),
                DATA_KEY_SLOT2_STOP_TIME: f"{self.device.period2_end_hour}:{self.device.period2_end_min:02d}",
                DATA_KEY_TIME_VALVE_ON: self.device.time_valve_on,
            }
            _LOGGER.debug("Updated coordinator data for %s: %s", self.host, data)
            return data
        except Exception as exc:
            _LOGGER.error("Failed to update device data for %s: %s", self.host, exc)
            raise UpdateFailed(f"Error communicating with device: {exc}") from exc