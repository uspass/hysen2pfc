"""
Button platform for the Hysen 2 Pipe Fan Coil integration.

Provides a button entity that synchronises the device's internal clock to
the current system time (including seconds and weekday). Also registers a
service so that a specific time can be set programmatically.
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


async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities) -> None:
    """Set up the button entity and register the set_time service.

    Args:
        hass: The Home Assistant instance.
        config_entry: The config entry representing the device.
        async_add_entities: Callback used to register new entities with HA.
    """
    device_data = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([
        HysenSetTimeNowButton(device_data),
    ])

    # Register an entity service so automations can set an explicit time
    # instead of always using "now".
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_SET_TIME,
        {
            vol.Required(ATTR_DEVICE_TIME): str,
            vol.Required(ATTR_DEVICE_WEEKDAY): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=7)
            ),
        },
        "async_set_time",
    )


class HysenSetTimeNowButton(HysenEntity, ButtonEntity):
    """Button that synchronises the device clock to the current system time.

    Pressing the button reads the current local time and weekday and
    sends them to the device via the Hysen set_time command. This is
    useful after a power failure restores the device but leaves its
    internal clock incorrect.
    """

    def __init__(self, device_data: dict) -> None:
        """Initialise the button entity.

        Args:
            device_data: Device-specific data dict from hass.data[DOMAIN].
        """
        super().__init__(device_data["coordinator"], device_data)
        self._attr_unique_id = f"{device_data['mac']}_set_time_now_button"
        self._attr_name = f"{device_data['name']} Device Time Now"
        self._attr_icon = "mdi:clock"

    async def async_press(self) -> None:
        """Handle a button press — set device time to the current moment.

        Reads the local wall-clock time and calls async_set_time. Logs
        success or failure at the appropriate level.
        """
        _LOGGER.debug("[%s] Setting device time to current time", self._host)
        current_time = datetime.now()
        time_str = f"{current_time.hour}:{current_time.minute:02d}:{current_time.second:02d}"
        weekday = current_time.isoweekday()  # 1=Monday … 7=Sunday

        success = await self.async_set_time(time_str, weekday)
        if success:
            _LOGGER.info(
                "[%s] Successfully set device time to %s, weekday %s",
                self._host, time_str, weekday,
            )
        else:
            _LOGGER.error("[%s] Failed to set device time", self._host)

    async def async_set_time(self, device_time: str, device_weekday: int) -> bool:
        """Set the device clock to the given time and weekday.

        This is also the handler for the hysen2pfc.set_time entity service,
        which allows automations to set a specific time rather than "now".

        Args:
            device_time: Time string in HH:MM:SS format.
            device_weekday: ISO weekday number (1=Monday, 7=Sunday).

        Returns:
            True if the command was accepted by the device, False otherwise.
        """
        _LOGGER.debug(
            "[%s] Setting time to %s, weekday to %s",
            self._host, device_time, device_weekday,
        )
        hour, minute, second = map(int, str(device_time).split(":"))
        success = await self._async_try_command(
            "Error in set_time",
            self.coordinator.device.set_time,
            hour, minute, second, device_weekday,
        )
        return success
