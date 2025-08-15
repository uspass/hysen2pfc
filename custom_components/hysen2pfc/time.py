"""
Support for Hysen 2 Pipe Fan Coil Controller time entities.

This module provides time entities for controlling the schedule slots.
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
    """Set up the Hysen time entities from a config entry.

    Initializes and adds the time entities for the device, and registers services.

    Args:
        hass: The Home Assistant instance.
        config_entry: The configuration entry containing device details.
        async_add_entities: Callback to add entities asynchronously.

    Returns:
        None
    """
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

class HysenSlot1StartTime(HysenEntity, TimeEntity):
    """Representation of a Hysen Slot 1 Start Time entity.

    Allows setting the start time for schedule slot 1.
    """

    def __init__(self, device_data):
        """Initialize the time entity.

        Args:
            device_data: Dictionary containing device-specific data (e.g., mac, name, coordinator).
        """
        super().__init__(device_data["coordinator"], device_data)
        self._attr_unique_id = f"{device_data['mac']}_slot1_start_time"
        self._attr_name = f"{device_data['name']} Slot 1 Start Time"
        self._attr_icon = "mdi:clock-start"

    @property
    def native_value(self):
        """Return the current time value.

        Returns:
            time: The current start time for slot 1, or None if not set.
        """
        time_str = self.coordinator.data.get(DATA_KEY_SLOT1_START_TIME)
        if time_str:
            hour, minute = map(int, time_str.split(":"))
            return time(hour, minute)
        return None

    async def async_set_value(self, value: time):
        """Set the slot 1 start time.

        Args:
            value: The time value to set.

        Returns:
            None
        """
        _LOGGER.debug("[%s] Setting slot 1 start time to %s", self._host, value)
        success = await self._async_try_command(
            "Error in set_daily_schedule",
            self.coordinator.device.set_daily_schedule,
            None,
            value.hour,
            value.minute,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        )
        if success:
            await self.coordinator.async_refresh()
            self.async_write_ha_state()

    async def async_set_slot1_start_time(self, slot1_start_time):
        """Set the slot 1 start time via service.

        Args:
            slot1_start_time: The time string in HH:MM format.

        Returns:
            None
        """
        _LOGGER.debug("[%s] Setting slot 1 start time to %s", self._host, slot1_start_time)
        hour, minute = map(int, slot1_start_time.split(":"))
        success = await self._async_try_command(
            "Error in set_daily_schedule",
            self.coordinator.device.set_daily_schedule,
            None,
            hour,
            minute,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        )
        if success:
            await self.coordinator.async_refresh()
            self.async_write_ha_state()

class HysenSlot1StopTime(HysenEntity, TimeEntity):
    """Representation of a Hysen Slot 1 Stop Time entity.

    Allows setting the stop time for schedule slot 1.
    """

    def __init__(self, device_data):
        """Initialize the time entity.

        Args:
            device_data: Dictionary containing device-specific data (e.g., mac, name, coordinator).
        """
        super().__init__(device_data["coordinator"], device_data)
        self._attr_unique_id = f"{device_data['mac']}_slot1_stop_time"
        self._attr_name = f"{device_data['name']} Slot 1 Stop Time"
        self._attr_icon = "mdi:clock-end"

    @property
    def native_value(self):
        """Return the current time value.

        Returns:
            time: The current stop time for slot 1, or None if not set.
        """
        time_str = self.coordinator.data.get(DATA_KEY_SLOT1_STOP_TIME)
        if time_str:
            hour, minute = map(int, time_str.split(":"))
            return time(hour, minute)
        return None

    async def async_set_value(self, value: time):
        """Set the slot 1 stop time.

        Args:
            value: The time value to set.

        Returns:
            None
        """
        _LOGGER.debug("[%s] Setting slot 1 stop time to %s", self._host, value)
        success = await self._async_try_command(
            "Error in set_daily_schedule",
            self.coordinator.device.set_daily_schedule,
            None,
            None,
            None,
            None,
            value.hour,
            value.minute,
            None,
            None,
            None,
            None,
            None,
            None,
        )
        if success:
            await self.coordinator.async_refresh()
            self.async_write_ha_state()

    async def async_set_slot1_stop_time(self, slot1_stop_time):
        """Set the slot 1 stop time via service.

        Args:
            slot1_stop_time: The time string in HH:MM format.

        Returns:
            None
        """
        _LOGGER.debug("[%s] Setting slot 1 stop time to %s", self._host, slot1_stop_time)
        hour, minute = map(int, slot1_stop_time.split(":"))
        success = await self._async_try_command(
            "Error in set_daily_schedule",
            self.coordinator.device.set_daily_schedule,
            None,
            None,
            None,
            None,
            hour,
            minute,
            None,
            None,
            None,
            None,
            None,
            None,
        )
        if success:
            await self.coordinator.async_refresh()
            self.async_write_ha_state()

class HysenSlot2StartTime(HysenEntity, TimeEntity):
    """Representation of a Hysen Slot 2 Start Time entity.

    Allows setting the start time for schedule slot 2.
    """

    def __init__(self, device_data):
        """Initialize the time entity.

        Args:
            device_data: Dictionary containing device-specific data (e.g., mac, name, coordinator).
        """
        super().__init__(device_data["coordinator"], device_data)
        self._attr_unique_id = f"{device_data['mac']}_slot2_start_time"
        self._attr_name = f"{device_data['name']} Slot 2 Start Time"
        self._attr_icon = "mdi:clock-start"

    @property
    def native_value(self):
        """Return the current time value.

        Returns:
            time: The current start time for slot 2, or None if not set.
        """
        time_str = self.coordinator.data.get(DATA_KEY_SLOT2_START_TIME)
        if time_str:
            hour, minute = map(int, time_str.split(":"))
            return time(hour, minute)
        return None

    async def async_set_value(self, value: time):
        """Set the slot 2 start time.

        Args:
            value: The time value to set.

        Returns:
            None
        """
        _LOGGER.debug("[%s] Setting slot 2 start time to %s", self._host, value)
        success = await self._async_try_command(
            "Error in set_daily_schedule",
            self.coordinator.device.set_daily_schedule,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            value.hour,
            value.minute,
            None,
            None,
            None,
        )
        if success:
            await self.coordinator.async_refresh()
            self.async_write_ha_state()

    async def async_set_slot2_start_time(self, slot2_start_time):
        """Set the slot 2 start time via service.

        Args:
            slot2_start_time: The time string in HH:MM format.

        Returns:
            None
        """
        _LOGGER.debug("[%s] Setting slot 2 start time to %s", self._host, slot2_start_time)
        hour, minute = map(int, slot2_start_time.split(":"))
        success = await self._async_try_command(
            "Error in set_daily_schedule",
            self.coordinator.device.set_daily_schedule,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            hour,
            minute,
            None,
            None,
            None,
        )
        if success:
            await self.coordinator.async_refresh()
            self.async_write_ha_state()

class HysenSlot2StopTime(HysenEntity, TimeEntity):
    """Representation of a Hysen Slot 2 Stop Time entity.

    Allows setting the stop time for schedule slot 2.
    """

    def __init__(self, device_data):
        """Initialize the time entity.

        Args:
            device_data: Dictionary containing device-specific data (e.g., mac, name, coordinator).
        """
        super().__init__(device_data["coordinator"], device_data)
        self._attr_unique_id = f"{device_data['mac']}_slot2_stop_time"
        self._attr_name = f"{device_data['name']} Slot 2 Stop Time"
        self._attr_icon = "mdi:clock-end"

    @property
    def native_value(self):
        """Return the current time value.

        Returns:
            time: The current stop time for slot 2, or None if not set.
        """
        time_str = self.coordinator.data.get(DATA_KEY_SLOT2_STOP_TIME)
        if time_str:
            hour, minute = map(int, time_str.split(":"))
            return time(hour, minute)
        return None

    async def async_set_value(self, value: time):
        """Set the slot 2 stop time.

        Args:
            value: The time value to set.

        Returns:
            None
        """
        _LOGGER.debug("[%s] Setting slot 2 stop time to %s", self._host, value)
        success = await self._async_try_command(
            "Error in set_daily_schedule",
            self.coordinator.device.set_daily_schedule,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            value.hour,
            value.minute,
        )
        if success:
            await self.coordinator.async_refresh()
            self.async_write_ha_state()

    async def async_set_slot2_stop_time(self, slot2_stop_time):
        """Set the slot 2 stop time via service.

        Args:
            slot2_stop_time: The time string in HH:MM format.

        Returns:
            None
        """
        _LOGGER.debug("[%s] Setting slot 2 stop time to %s", self._host, slot2_stop_time)
        hour, minute = map(int, slot2_stop_time.split(":"))
        success = await self._async_try_command(
            "Error in set_daily_schedule",
            self.coordinator.device.set_daily_schedule,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            hour,
            minute,
        )
        if success:
            await self.coordinator.async_refresh()
            self.async_write_ha_state()