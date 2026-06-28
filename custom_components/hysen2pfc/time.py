"""
Time platform for the Hysen 2 Pipe Fan Coil integration.

Provides four TimeEntity instances for setting the start and stop times of
the two daily schedule slots:

- HysenSlot1StartTime — when the device turns on for period 1.
- HysenSlot1StopTime  — when the device turns off after period 1.
- HysenSlot2StartTime — when the device turns on for period 2.
- HysenSlot2StopTime  — when the device turns off after period 2.

Whether each slot is active is controlled by the corresponding switch
entities (HysenSlot*EnableSwitch). Each entity also registers a service
for automation use.

Argument layout for device.set_daily_schedule:
  (slot1_start_en, slot1_start_h, slot1_start_m,
   slot1_stop_en,  slot1_stop_h,  slot1_stop_m,
   slot2_start_en, slot2_start_h, slot2_start_m,
   slot2_stop_en,  slot2_stop_h,  slot2_stop_m)
Pass None for any argument that should remain unchanged.
"""

import logging
import voluptuous as vol
from datetime import time
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.components.time import TimeEntity
from .const import (
    DOMAIN,
    DATA_KEY_SLOT1_START_TIME,
    DATA_KEY_SLOT1_STOP_TIME,
    DATA_KEY_SLOT2_START_TIME,
    DATA_KEY_SLOT2_STOP_TIME,
    ATTR_SLOT1_START_TIME,
    ATTR_SLOT1_STOP_TIME,
    ATTR_SLOT2_START_TIME,
    ATTR_SLOT2_STOP_TIME,
    SERVICE_SET_SLOT1_START_TIME,
    SERVICE_SET_SLOT1_STOP_TIME,
    SERVICE_SET_SLOT2_START_TIME,
    SERVICE_SET_SLOT2_STOP_TIME,
)
from .entity import HysenEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities):
    """Set up the Hysen time entities from a config entry."""
    device_data = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([
        HysenSlot1StartTime(device_data),
        HysenSlot1StopTime(device_data),
        HysenSlot2StartTime(device_data),
        HysenSlot2StopTime(device_data),
    ])

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_SET_SLOT1_START_TIME,
        {vol.Required(ATTR_SLOT1_START_TIME): str},
        "async_set_slot1_start_time",
    )
    platform.async_register_entity_service(
        SERVICE_SET_SLOT1_STOP_TIME,
        {vol.Required(ATTR_SLOT1_STOP_TIME): str},
        "async_set_slot1_stop_time",
    )
    platform.async_register_entity_service(
        SERVICE_SET_SLOT2_START_TIME,
        {vol.Required(ATTR_SLOT2_START_TIME): str},
        "async_set_slot2_start_time",
    )
    platform.async_register_entity_service(
        SERVICE_SET_SLOT2_STOP_TIME,
        {vol.Required(ATTR_SLOT2_STOP_TIME): str},
        "async_set_slot2_stop_time",
    )


def _parse_time(time_str):
    """Parse 'H:MM' coordinator string to datetime.time, or None."""
    if not time_str:
        return None
    hour, minute = map(int, time_str.split(":"))
    return time(hour, minute)


class HysenSlot1StartTime(HysenEntity, TimeEntity):
    """Start time for schedule slot 1."""

    def __init__(self, device_data):
        super().__init__(device_data["coordinator"], device_data)
        self._attr_unique_id = f"{device_data['mac']}_slot1_start_time"
        self._attr_name = f"{device_data['name']} Slot 1 Start Time"
        self._attr_icon = "mdi:clock-start"

    @property
    def native_value(self):
        return _parse_time(self.coordinator.data.get(DATA_KEY_SLOT1_START_TIME))

    async def async_set_value(self, value: time):
        _LOGGER.debug("[%s] Setting slot 1 start time to %s", self._host, value)
        await self._async_try_command(
            "Error in set_daily_schedule",
            self.coordinator.device.set_daily_schedule,
            None, value.hour, value.minute,
            None, None, None,
            None, None, None,
            None, None, None,
        )

    async def async_set_slot1_start_time(self, slot1_start_time):
        hour, minute = map(int, slot1_start_time.split(":"))
        await self.async_set_value(time(hour, minute))


class HysenSlot1StopTime(HysenEntity, TimeEntity):
    """Stop time for schedule slot 1."""

    def __init__(self, device_data):
        super().__init__(device_data["coordinator"], device_data)
        self._attr_unique_id = f"{device_data['mac']}_slot1_stop_time"
        self._attr_name = f"{device_data['name']} Slot 1 Stop Time"
        self._attr_icon = "mdi:clock-end"

    @property
    def native_value(self):
        return _parse_time(self.coordinator.data.get(DATA_KEY_SLOT1_STOP_TIME))

    async def async_set_value(self, value: time):
        _LOGGER.debug("[%s] Setting slot 1 stop time to %s", self._host, value)
        await self._async_try_command(
            "Error in set_daily_schedule",
            self.coordinator.device.set_daily_schedule,
            None, None, None,
            None, value.hour, value.minute,
            None, None, None,
            None, None, None,
        )

    async def async_set_slot1_stop_time(self, slot1_stop_time):
        hour, minute = map(int, slot1_stop_time.split(":"))
        await self.async_set_value(time(hour, minute))


class HysenSlot2StartTime(HysenEntity, TimeEntity):
    """Start time for schedule slot 2."""

    def __init__(self, device_data):
        super().__init__(device_data["coordinator"], device_data)
        self._attr_unique_id = f"{device_data['mac']}_slot2_start_time"
        self._attr_name = f"{device_data['name']} Slot 2 Start Time"
        self._attr_icon = "mdi:clock-start"

    @property
    def native_value(self):
        return _parse_time(self.coordinator.data.get(DATA_KEY_SLOT2_START_TIME))

    async def async_set_value(self, value: time):
        _LOGGER.debug("[%s] Setting slot 2 start time to %s", self._host, value)
        await self._async_try_command(
            "Error in set_daily_schedule",
            self.coordinator.device.set_daily_schedule,
            None, None, None,
            None, None, None,
            None, value.hour, value.minute,
            None, None, None,
        )

    async def async_set_slot2_start_time(self, slot2_start_time):
        hour, minute = map(int, slot2_start_time.split(":"))
        await self.async_set_value(time(hour, minute))


class HysenSlot2StopTime(HysenEntity, TimeEntity):
    """Stop time for schedule slot 2."""

    def __init__(self, device_data):
        super().__init__(device_data["coordinator"], device_data)
        self._attr_unique_id = f"{device_data['mac']}_slot2_stop_time"
        self._attr_name = f"{device_data['name']} Slot 2 Stop Time"
        self._attr_icon = "mdi:clock-end"

    @property
    def native_value(self):
        return _parse_time(self.coordinator.data.get(DATA_KEY_SLOT2_STOP_TIME))

    async def async_set_value(self, value: time):
        _LOGGER.debug("[%s] Setting slot 2 stop time to %s", self._host, value)
        await self._async_try_command(
            "Error in set_daily_schedule",
            self.coordinator.device.set_daily_schedule,
            None, None, None,
            None, None, None,
            None, None, None,
            None, value.hour, value.minute,
        )

    async def async_set_slot2_stop_time(self, slot2_stop_time):
        hour, minute = map(int, slot2_stop_time.split(":"))
        await self.async_set_value(time(hour, minute))
