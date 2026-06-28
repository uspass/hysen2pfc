"""
Base entity class for the Hysen 2 Pipe Fan Coil integration.

All platform entities (climate, switch, sensor, etc.) inherit from
HysenEntity, which wires them up to the shared HysenCoordinator and
provides the common _async_try_command helper for sending device commands.
"""

import asyncio
import logging
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.core import callback
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class HysenEntity(CoordinatorEntity):
    """Base class for all Hysen 2 Pipe Fan Coil entities.

    Inheriting from CoordinatorEntity provides:
    - Automatic subscription/unsubscription to coordinator updates.
    - available property tied to coordinator.last_update_success.
    - should_poll = False (updates are push-based via the coordinator).
    - _handle_coordinator_update callback invoked on every coordinator refresh.

    Subclasses that maintain local _attr_* fields (e.g. HysenClimate) should
    override _handle_coordinator_update to re-sync those fields and call
    self.async_write_ha_state().
    """

    def __init__(self, coordinator, device_data: dict) -> None:
        """Initialise the entity and populate shared device information.

        Args:
            coordinator: The HysenCoordinator instance shared by all entities
                for this physical device.
            device_data: Dict with keys 'host', 'mac', 'name', 'coordinator'
                populated by async_setup_entry in __init__.py.
        """
        super().__init__(coordinator)
        self._host: str = device_data["host"]
        self._mac: str = device_data["mac"]

        fwversion = coordinator.data.get("fwversion")

        # Build the device info dict once; all entities for the same MAC share
        # the same device entry in HA's device registry.
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._mac)},
            # CONNECTION_NETWORK_MAC lets HA correlate this device with other
            # integrations that discover it by MAC (e.g. network scanner).
            "connections": {(CONNECTION_NETWORK_MAC, self._mac)},
            "name": device_data["name"],
            "manufacturer": "Hysen",
            "model": "HY03AC-1-Wifi",
            "sw_version": str(fwversion) if fwversion is not None else "Unknown",
            # configuration_url adds an "Open device UI" link in the device panel.
            "configuration_url": f"http://{self._host}",
        }

    async def _async_try_command(self, error_msg: str, func, *args) -> bool:
        """Execute a blocking device command in the executor and refresh state.

        Runs the provided callable in a thread pool executor (to avoid
        blocking the event loop), waits 200 ms for the device to stabilise,
        then triggers an immediate coordinator refresh so that all entities
        reflect the new state.

        Args:
            error_msg: Message logged at ERROR level if the command fails.
            func: Blocking callable (e.g. device.set_fan_mode).
            *args: Positional arguments forwarded to func.

        Returns:
            True if the command succeeded, False otherwise.
        """
        try:
            await self.hass.async_add_executor_job(func, *args)
            # Allow the device firmware to apply the change before polling.
            await asyncio.sleep(0.2)
            # async_refresh is immediate (not debounced), ensuring all
            # entities update in the same event loop cycle.
            await self.coordinator.async_refresh()
            return True
        except Exception as exc:
            _LOGGER.error("[%s] %s: %s", self._host, error_msg, exc)
            return False
