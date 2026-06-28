"""
Binary sensor platform for the Hysen 2 Pipe Fan Coil integration.

Provides a single binary sensor that reflects the current state of the
water valve (open / closed). The valve is opened by the device when active
heating or cooling is required, and closes when the setpoint is reached.
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


async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities) -> None:
    """Set up binary sensor entities for a config entry.

    Args:
        hass: The Home Assistant instance.
        config_entry: The config entry representing the device.
        async_add_entities: Callback used to register new entities with HA.
    """
    device_data = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([
        HysenValveStateSensor(device_data),
    ])


class HysenValveStateSensor(HysenEntity, BinarySensorEntity):
    """Binary sensor representing the water valve state.

    State is True (on) when the valve is open, meaning the device is
    actively passing hot or chilled water through the fan coil unit.
    Uses BinarySensorDeviceClass.OPENING so HA automatically selects
    the appropriate icon and state label.
    """

    def __init__(self, device_data: dict) -> None:
        """Initialise the valve state binary sensor.

        Args:
            device_data: Device-specific data dict from hass.data[DOMAIN].
        """
        super().__init__(device_data["coordinator"], device_data)
        self._attr_unique_id = f"{device_data['mac']}_valve_state"
        self._attr_name = f"{device_data['name']} Valve State"
        self._attr_device_class = BinarySensorDeviceClass.OPENING

    @property
    def is_on(self) -> bool:
        """Return True when the valve is open (water is flowing).

        Returns:
            True if the coordinator reports the valve state as STATE_OPEN.
        """
        state = self.coordinator.data.get(DATA_KEY_VALVE_STATE)
        return state == STATE_OPEN
