"""
Base entity for Hysen 2 Pipe Fan Coil integration.
"""

from homeassistant.helpers.entity import Entity
from .const import DOMAIN

class HysenEntity(Entity):
    """Base class for Hysen entities.

    Provides common functionality and initialization for all Hysen entities
    in the Home Assistant integration.
    """

    def __init__(self, coordinator, device_data):
        """Initialize the Hysen entity.

        Args:
            coordinator: The HysenCoordinator instance managing device updates.
            device_data: Dictionary containing device-specific data (e.g., host, mac, name).
        """
        super().__init__()
        self.coordinator = coordinator
        self._host = device_data["host"]
        self._mac = device_data["mac"]
        fwversion = coordinator.data.get("fwversion")
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._mac)},
            "name": device_data["name"],
            "manufacturer": "Hysen",
            "model": "HY03AC-1-Wifi",
            "sw_version": fwversion if fwversion is not None else "Unknown",
        }

    async def async_added_to_hass(self):
        """Run when entity is added to Home Assistant.

        Subscribes to coordinator updates to ensure the entity state is
        updated when new data is available.

        Returns:
            None
        """
        await super().async_added_to_hass()
        # Subscribe to coordinator updates
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def _async_try_command(self, error_msg, func, *args):
        """Try to execute a command on the Hysen device.

        Args:
            error_msg: The error message to log if the command fails.
            func: The function to execute.
            *args: Variable arguments to pass to the function.

        Returns:
            bool: True if the command was successful, False otherwise.
        """
        try:
            await self.hass.async_add_executor_job(func, *args)
            await self.coordinator.async_request_refresh()
            return True
        except Exception as exc:
            self.coordinator.logger.error("[%s] %s: %s", self._host, error_msg, exc)
            return False

    @property
    def available(self):
        """Check if the entity is available.

        Returns:
            bool: True if the coordinator's last update was successful, False otherwise.
        """
        return self.coordinator.last_update_success

    async def async_update(self):
        """Update the entity's state.

        Requests a refresh of the coordinator to fetch the latest device data.

        Returns:
            None
        """
        await self.coordinator.async_request_refresh()