"""
Support for Hysen 2 Pipe Fan Coil Controller select entities.

This module provides select entities for setting the hysteresis and key lock values.
"""

import logging
import asyncio
import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.components.select import SelectEntity
from .const import (
    DOMAIN,
    DATA_KEY_HYSTERESIS,
    DATA_KEY_KEY_LOCK,
    ATTR_HYSTERESIS,
    ATTR_KEY_LOCK,
    SERVICE_SET_HYSTERESIS,
    SERVICE_SET_KEY_LOCK,
    STATE_HYSTERESIS_HALVE,
    STATE_HYSTERESIS_WHOLE,
    STATE_UNLOCKED,
    STATE_LOCKED_EXCEPT_POWER,
    STATE_LOCKED,
    HYSTERESIS_HASS_TO_HYSEN,
    KEY_LOCK_HASS_TO_HYSEN,
)
from .entity import HysenEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities):
    """Set up the Hysen select entities from a config entry.

    Initializes and adds the select entities for the device, and registers services.

    Args:
        hass: The Home Assistant instance.
        config_entry: The configuration entry containing device details.
        async_add_entities: Callback to add entities asynchronously.

    Returns:
        None
    """
    device_data = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([
        HysenHysteresisSelect(device_data),
        HysenKeyLockSelect(device_data),
    ])

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_SET_HYSTERESIS,
        {vol.Required(ATTR_HYSTERESIS): vol.In([STATE_HYSTERESIS_HALVE, STATE_HYSTERESIS_WHOLE])},
        "async_set_hysteresis",
    )
    platform.async_register_entity_service(
        SERVICE_SET_KEY_LOCK,
        {vol.Required(ATTR_KEY_LOCK): vol.In([STATE_UNLOCKED, STATE_LOCKED_EXCEPT_POWER, STATE_LOCKED])},
        "async_set_key_lock",
    )

class HysenHysteresisSelect(HysenEntity, SelectEntity):
    """Representation of a Hysen Hysteresis select entity.

    Allows selection of hysteresis mode (half or whole degree).
    """

    def __init__(self, device_data):
        """Initialize the select entity.

        Args:
            device_data: Dictionary containing device-specific data (e.g., mac, name, coordinator).
        """
        super().__init__(device_data["coordinator"], device_data)
        self._attr_unique_id = f"{device_data['mac']}_hysteresis"
        self._attr_name = f"{device_data['name']} Hysteresis"
        self._attr_options = [STATE_HYSTERESIS_HALVE, STATE_HYSTERESIS_WHOLE]
        self._attr_icon = "mdi:thermometer"

    @property
    def current_option(self):
        """Return the current selected hysteresis option.

        Returns:
            str: The current hysteresis state.
        """
        return self.coordinator.data.get(DATA_KEY_HYSTERESIS)

    async def async_select_option(self, option: str):
        """Set the hysteresis option.

        Args:
            option: The hysteresis option to set.

        Returns:
            None
        """
        _LOGGER.debug("[%s] Setting hysteresis to %s", self._host, option)
        success = await self._async_try_command(
            "Error in set_hysteresis",
            self.coordinator.device.set_hysteresis,
            HYSTERESIS_HASS_TO_HYSEN[option],
        )
        if success:
            # Delay to allow device to stabilize
            await asyncio.sleep(0.2)
            # Force an immediate update to fetch the latest device state
            await self.coordinator.async_refresh()
            self.async_write_ha_state()

    async def async_set_hysteresis(self, hysteresis):
        """Set the hysteresis state (for service calls).

        Args:
            hysteresis: The hysteresis value to set.

        Returns:
            None
        """
        await self.async_select_option(hysteresis)

class HysenKeyLockSelect(HysenEntity, SelectEntity):
    """Representation of a Hysen Key Lock select entity.

    Allows selection of key lock modes.
    """

    def __init__(self, device_data):
        """Initialize the select entity.

        Args:
            device_data: Dictionary containing device-specific data (e.g., mac, name, coordinator).
        """
        super().__init__(device_data["coordinator"], device_data)
        self._attr_unique_id = f"{device_data['mac']}_key_lock"
        self._attr_name = f"{device_data['name']} Key Lock"
        self._attr_options = [STATE_UNLOCKED, STATE_LOCKED_EXCEPT_POWER, STATE_LOCKED]

    @property
    def icon(self):
        """Return the icon based on the current key lock state.

        Returns:
            str: The Material Design Icon (MDI) for the key lock state.
        """
        icons = {
            STATE_UNLOCKED: "mdi:lock-open-variant",
            STATE_LOCKED_EXCEPT_POWER: "mdi:lock-open",
            STATE_LOCKED: "mdi:lock",
        }
        return icons.get(self.current_option, "mdi:lock")

    @property
    def current_option(self):
        """Return the current selected key lock option.

        Returns:
            str: The current key lock state.
        """
        return self.coordinator.data.get(DATA_KEY_KEY_LOCK)

    async def async_select_option(self, option: str):
        """Set the key lock option.

        Args:
            option: The key lock option to set.

        Returns:
            None
        """
        _LOGGER.debug("[%s] Setting key lock to %s", self._host, option)
        success = await self._async_try_command(
            "Error in set_key_lock",
            self.coordinator.device.set_key_lock,
            KEY_LOCK_HASS_TO_HYSEN[option],
        )
        if success:
            # Delay to allow device to stabilize
            await asyncio.sleep(0.2)
            # Force an immediate update to fetch the latest device state
            await self.coordinator.async_refresh()
            self.async_write_ha_state()

    async def async_set_key_lock(self, key_lock):
        """Set the key lock state (for service calls).

        Args:
            key_lock: The key lock value to set.

        Returns:
            None
        """
        await self.async_select_option(key_lock)