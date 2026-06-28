"""
Sensor platform for the Hysen 2 Pipe Fan Coil integration.

Provides the following sensors:
- HysenTimeValveOnSensor  — cumulative seconds the valve has been open.
- HysenDeviceTimeSensor   — the device's internal clock (date/time/weekday).
- HysenIPSensor           — device IP address (diagnostic).
- HysenMACSensor          — device MAC address (diagnostic).
"""

import logging
from homeassistant.core import HomeAssistant
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import EntityCategory
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

# Maps the device's numeric weekday (starting from HYSEN2PFC_WEEKDAY_MONDAY)
# to a human-readable name used in the Device Time sensor state.
WEEKDAY_MAP = {
    HYSEN2PFC_WEEKDAY_MONDAY: "Monday",
    HYSEN2PFC_WEEKDAY_MONDAY + 1: "Tuesday",
    HYSEN2PFC_WEEKDAY_MONDAY + 2: "Wednesday",
    HYSEN2PFC_WEEKDAY_MONDAY + 3: "Thursday",
    HYSEN2PFC_WEEKDAY_MONDAY + 4: "Friday",
    HYSEN2PFC_WEEKDAY_MONDAY + 5: "Saturday",
    HYSEN2PFC_WEEKDAY_SUNDAY: "Sunday",
}


async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities) -> None:
    """Set up sensor entities for a config entry.

    Args:
        hass: The Home Assistant instance.
        config_entry: The config entry representing the device.
        async_add_entities: Callback used to register new entities with HA.
    """
    device_data = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([
        HysenTimeValveOnSensor(device_data),
        HysenDeviceTimeSensor(device_data),
        HysenIPSensor(device_data),
        HysenMACSensor(device_data),
    ])


class HysenTimeValveOnSensor(HysenEntity, SensorEntity):
    """Sensor reporting how long the valve has been open (in seconds).

    The device firmware increments an internal counter while the valve is
    open. This sensor exposes that counter; it is useful for monitoring
    energy usage patterns and detecting stuck-open valves.
    """

    def __init__(self, device_data: dict) -> None:
        """Initialise the time-valve-on sensor.

        Args:
            device_data: Device-specific data dict from hass.data[DOMAIN].
        """
        super().__init__(device_data["coordinator"], device_data)
        self._attr_unique_id = f"{device_data['mac']}_time_valve_on"
        self._attr_name = f"{device_data['name']} Time Valve On"
        self._attr_native_unit_of_measurement = UnitOfTime.SECONDS
        self._attr_icon = "mdi:timer"
        self._attr_device_class = SensorDeviceClass.DURATION

    @property
    def native_value(self):
        """Return the cumulative valve-open time in seconds.

        Returns:
            Integer seconds, or None if the value is not yet available.
        """
        return self.coordinator.data.get(DATA_KEY_TIME_VALVE_ON)


class HysenDeviceTimeSensor(HysenEntity, SensorEntity):
    """Sensor showing the device's internal clock as a formatted string.

    State format: "Weekday HH:MM:SS" (e.g. "Monday 14:05:30").
    Extra state attributes expose individual components (hour, minute,
    second, weekday, weekday_name) for use in templates and automations.

    Note: The device clock is read once per coordinator poll (default 30 s),
    so the displayed time will lag by up to that interval.
    """

    def __init__(self, device_data: dict) -> None:
        """Initialise the device time sensor.

        Args:
            device_data: Device-specific data dict from hass.data[DOMAIN].
        """
        super().__init__(device_data["coordinator"], device_data)
        self._attr_unique_id = f"{device_data['mac']}_device_time"
        self._attr_name = f"{device_data['name']} Device Time"
        self._attr_icon = "mdi:clock"

    @property
    def native_value(self):
        """Return the device time as a human-readable string.

        Returns:
            String in the format "Weekday HH:MM:SS", or None if any
            component is missing from the coordinator data.
        """
        hour = self.coordinator.data.get(DATA_KEY_CLOCK_HOUR)
        minute = self.coordinator.data.get(DATA_KEY_CLOCK_MINUTE)
        second = self.coordinator.data.get(DATA_KEY_CLOCK_SECOND)
        weekday = self.coordinator.data.get(DATA_KEY_CLOCK_WEEKDAY)

        if None in (hour, minute, second, weekday):
            return None

        time_str = f"{hour:02d}:{minute:02d}:{second:02d}"
        weekday_str = WEEKDAY_MAP.get(weekday, "Unknown")
        return f"{weekday_str} {time_str}"

    @property
    def extra_state_attributes(self) -> dict:
        """Return individual time components as separate attributes.

        Exposes hour, minute, second, weekday (numeric) and weekday_name
        so that templates can compare or format individual fields without
        parsing the state string.

        Returns:
            Dict with time component keys, or an empty dict if data is
            incomplete.
        """
        hour = self.coordinator.data.get(DATA_KEY_CLOCK_HOUR)
        minute = self.coordinator.data.get(DATA_KEY_CLOCK_MINUTE)
        second = self.coordinator.data.get(DATA_KEY_CLOCK_SECOND)
        weekday = self.coordinator.data.get(DATA_KEY_CLOCK_WEEKDAY)

        if None in (hour, minute, second, weekday):
            return {}

        return {
            "hour": hour,
            "minute": minute,
            "second": second,
            "weekday": weekday,
            "weekday_name": WEEKDAY_MAP.get(weekday, "Unknown"),
        }


class HysenIPSensor(HysenEntity, SensorEntity):
    """Diagnostic sensor exposing the configured device IP address.

    The value is static (taken from the config entry) and never changes
    unless the integration is reconfigured. Marked as DIAGNOSTIC so it
    is hidden by default but visible when the user enables hidden entities.
    """

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:ip-network"
    _attr_should_poll = False  # Value never changes between coordinator polls

    def __init__(self, device_data: dict) -> None:
        """Initialise the IP address sensor.

        Args:
            device_data: Device-specific data dict from hass.data[DOMAIN].
        """
        super().__init__(device_data["coordinator"], device_data)
        self._attr_unique_id = f"{device_data['mac']}_ip_address"
        self._attr_name = f"{device_data['name']} IP Address"

    @property
    def native_value(self) -> str:
        """Return the device IP address as configured.

        Returns:
            IP address string (e.g. '192.168.1.100').
        """
        return self._host


class HysenMACSensor(HysenEntity, SensorEntity):
    """Diagnostic sensor exposing the device MAC address.

    The value is static (taken from the config entry). Marked as
    DIAGNOSTIC so it is hidden by default.
    """

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:network"
    _attr_should_poll = False  # Value never changes

    def __init__(self, device_data: dict) -> None:
        """Initialise the MAC address sensor.

        Args:
            device_data: Device-specific data dict from hass.data[DOMAIN].
        """
        super().__init__(device_data["coordinator"], device_data)
        self._attr_unique_id = f"{device_data['mac']}_mac_address"
        self._attr_name = f"{device_data['name']} MAC Address"

    @property
    def native_value(self) -> str:
        """Return the device MAC address.

        Returns:
            MAC address string in 'aa:bb:cc:dd:ee:ff' format.
        """
        return self._mac
