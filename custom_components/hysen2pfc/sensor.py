"""
Support for Hysen 2 Pipe Fan Coil Controller sensors.

This module provides sensors for valve state, time valve on, and device time.
"""

import logging
from homeassistant.core import HomeAssistant
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from .const import (
    DOMAIN,
    UnitOfTime,
    DATA_KEY_TIME_VALVE_ON,
    DATA_KEY_CLOCK_HOUR,
    DATA_KEY_CLOCK_MINUTE,
    DATA_KEY_CLOCK_SECOND,
    DATA_KEY_CLOCK_WEEKDAY,
    ATTR_TIME_VALVE_ON,
    HYSEN2PFC_WEEKDAY_MONDAY,
    HYSEN2PFC_WEEKDAY_SUNDAY,
)
from .entity import HysenEntity

_LOGGER = logging.getLogger(__name__)

# Mapping for weekday numbers to names
WEEKDAY_MAP = {
    HYSEN2PFC_WEEKDAY_MONDAY: "Monday",
    HYSEN2PFC_WEEKDAY_MONDAY + 1: "Tuesday",
    HYSEN2PFC_WEEKDAY_MONDAY + 2: "Wednesday",
    HYSEN2PFC_WEEKDAY_MONDAY + 3: "Thursday",
    HYSEN2PFC_WEEKDAY_MONDAY + 4: "Friday",
    HYSEN2PFC_WEEKDAY_MONDAY + 5: "Saturday",
    HYSEN2PFC_WEEKDAY_SUNDAY: "Sunday",
}

async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities):
    """Set up the Hysen sensors from a config entry.

    Initializes and adds the sensor entities for the device.

    Args:
        hass: The Home Assistant instance.
        config_entry: The configuration entry containing device details.
        async_add_entities: Callback to add entities asynchronously.

    Returns:
        None
    """
    device_data = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([
        HysenTimeValveOnSensor(device_data),
        HysenDeviceTimeSensor(device_data),
    ])

class HysenTimeValveOnSensor(HysenEntity, SensorEntity):
    """Representation of a Hysen Time Valve On sensor.

    Measures the duration the valve has been open.
    """

    def __init__(self, device_data):
        """Initialize the sensor.

        Args:
            device_data: Dictionary containing device-specific data (e.g., mac, name, coordinator).
        """
        super().__init__(device_data["coordinator"], device_data)
        self._attr_unique_id = f"{device_data['mac']}_time_valve_on"
        self._attr_name = f"{device_data['name']} Time Valve On"
        self._attr_native_unit_of_measurement = UnitOfTime.SECONDS
        self._attr_icon = "mdi:timer"
        self._attr_device_class = SensorDeviceClass.DURATION

    @property
    def native_value(self):
        """Return the state of the sensor.

        Returns:
            int: The time the valve has been on, in seconds.
        """
        return self.coordinator.data.get(DATA_KEY_TIME_VALVE_ON)

class HysenDeviceTimeSensor(HysenEntity, SensorEntity):
    """Representation of a Hysen Device Time sensor.

    Displays the current time and weekday on the device.
    """

    def __init__(self, device_data):
        """Initialize the sensor.

        Args:
            device_data: Dictionary containing device-specific data (e.g., mac, name, coordinator).
        """
        super().__init__(device_data["coordinator"], device_data)
        self._attr_unique_id = f"{device_data['mac']}_device_time"
        self._attr_name = f"{device_data['name']} Device Time"
        self._attr_icon = "mdi:clock"
#        self._attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self):
        """Return the current device time and weekday as a formatted string.

        Returns:
            str: Formatted string like "Weekday HH:MM:SS" or None if data is incomplete.
        """
        hour = self.coordinator.data.get(DATA_KEY_CLOCK_HOUR)
        minute = self.coordinator.data.get(DATA_KEY_CLOCK_MINUTE)
        second = self.coordinator.data.get(DATA_KEY_CLOCK_SECOND)
        weekday = self.coordinator.data.get(DATA_KEY_CLOCK_WEEKDAY)

        if None in (hour, minute, second, weekday):
            return None

        # Format time as HH:MM:SS
        time_str = f"{hour:02d}:{minute:02d}:{second:02d}"
        # Get weekday name
        weekday_str = WEEKDAY_MAP.get(weekday, "Unknown")
        return f"{weekday_str} {time_str}"