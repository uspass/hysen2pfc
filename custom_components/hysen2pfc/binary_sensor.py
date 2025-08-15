"""
Support for Hysen 2 Pipe Fan Coil Controller binary sensors.

This module provides a binary sensor for valve state.
"""

import logging
from homeassistant.core import HomeAssistant
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from .const import (
    DOMAIN,
    DATA_KEY_VALVE_STATE,
    STATE_OPEN,
)
from .entity import HysenEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities):
    """Set up the Hysen binary sensors from a config entry.

    Initializes and adds the binary sensor entities for the device.

    Args:
        hass: The Home Assistant instance.
        config_entry: The configuration entry containing device details.
        async_add_entities: Callback to add entities asynchronously.

    Returns:
        None
    """
    device_data = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([
        HysenValveStateSensor(device_data),
    ])

class HysenValveStateSensor(HysenEntity, BinarySensorEntity):
    """Representation of a Hysen Valve State binary sensor.

    Monitors whether the valve is open or closed.
    """

    def __init__(self, device_data):
        """Initialize the binary sensor.

        Args:
            device_data: Dictionary containing device-specific data (e.g., mac, name, coordinator).
        """
        super().__init__(device_data["coordinator"], device_data)
        self._attr_unique_id = f"{device_data['mac']}_valve_state"
        self._attr_name = f"{device_data['name']} Valve State"
        self._attr_device_class = BinarySensorDeviceClass.OPENING

    @property
    def is_on(self):
        """Return True if the binary sensor is on (open), False otherwise.

        Returns:
            bool: True if the valve is open, False otherwise.
        """
        state = self.coordinator.data.get(DATA_KEY_VALVE_STATE)
        return state == STATE_OPEN

    @property
    def icon(self):
        """Return the icon based on the valve state.

        Returns:
            str: The Material Design Icon (MDI) for the valve state.
        """
        return "mdi:valve-open" if self.is_on else "mdi:valve-closed"