"""
Support for Hysen 2 Pipe Fan Coil Controller button entity.
This module provides a button to set the device time to the current system time, including seconds.
"""

import logging
import voluptuous as vol
from datetime import datetime
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.components.button import ButtonEntity
from .const import (
    DOMAIN, 
    ATTR_DEVICE_TIME, 
    ATTR_DEVICE_WEEKDAY,
    SERVICE_SET_TIME, 
)
from .entity import HysenEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities):
    """Set up the Hysen button entity from a config entry.

    Args:
        hass: The Home Assistant instance.
        config_entry: The configuration entry containing device details.
        async_add_entities: Callback to add entities asynchronously.

    Returns:
        None
    """
    device_data = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([
        HysenSetTimeNowButton(device_data),
    ])

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_SET_TIME,
        {
            vol.Required(ATTR_DEVICE_TIME): str,
            vol.Required(ATTR_DEVICE_WEEKDAY): vol.All(vol.Coerce(int), vol.Range(min=1, max=7)),
        },
        "async_set_time",
    )

class HysenSetTimeNowButton(HysenEntity, ButtonEntity):
    """Representation of a Hysen button to set the device time to now."""

    def __init__(self, device_data):
        """Initialize the button entity.

        Args:
            device_data: Dictionary containing device-specific data.
        """
        super().__init__(device_data["coordinator"], device_data)
        self._attr_unique_id = f"{device_data['mac']}_set_time_now_button"
        self._attr_name = f"{device_data['name']} Device Time Now"
        self._attr_icon = "mdi:clock"
        self._host = device_data["host"]
        self._mac = device_data["mac"]

    async def async_press(self):
        """Handle the button press to set the device time to now.

        Returns:
            None
        """
        _LOGGER.debug("[%s] Setting device time to current time", self._host)
        current_time = datetime.now()
        time_str = f"{current_time.hour}:{current_time.minute:02d}:{current_time.second:02d}"
        weekday = current_time.isoweekday()

        success = await self.async_set_time(time_str, weekday)
        if success:
            _LOGGER.info("[%s] Successfully set device time to %s, weekday %s", self._host, time_str, weekday)
            await self.coordinator.async_refresh()
            self.async_write_ha_state()
        else:
            _LOGGER.error("[%s] Failed to set device time", self._host)

    async def async_set_time(self, time_now, device_weekday):
        """Set the device time and weekday.

        Args:
            time_now: The time string in HH:MM:SS format.
            device_weekday: The weekday (1-7).

        Returns:
            bool: True if successful, False otherwise.
        """
        _LOGGER.debug("[%s] Setting time to %s, weekday to %s", self._host, time_now, device_weekday)
        hour, minute, second = map(int, str(time_now).split(":"))
        success = await self._async_try_command(
            "Error in set_time",
            self.coordinator.device.set_time,
            hour,
            minute,
            second,
            device_weekday,
        )
        return success