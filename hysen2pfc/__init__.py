"""
Hysen 2 Pipe Fan Coil Integration for Home Assistant.
"""

import binascii
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_NAME, CONF_TIMEOUT
from homeassistant.helpers.device_registry import DeviceRegistry, async_get as async_get_device_registry
from .const import (
    DATA_KEY,
    DEFAULT_NAME,
    CONF_SYNC_CLOCK,
    CONF_SYNC_HOUR,
    DEFAULT_TIMEOUT,
    DEFAULT_SYNC_CLOCK,
    DEFAULT_SYNC_HOUR,
    DOMAIN,
)
import logging
from hysen import Hysen2PipeFanCoilDevice

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Hysen2pfc component from YAML configuration."""
    hass.data.setdefault(DATA_KEY, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Hysen 2 Pipe Fan Coil from a config entry."""
    name = entry.data.get(CONF_NAME, DEFAULT_NAME)
    host = entry.data[CONF_HOST]
    mac_addr = binascii.unhexlify(entry.data[CONF_MAC].replace(":", ""))
    timeout = entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
    sync_clock = entry.data.get(CONF_SYNC_CLOCK, DEFAULT_SYNC_CLOCK)
    sync_hour = entry.data.get(CONF_SYNC_HOUR, DEFAULT_SYNC_HOUR)

    device = Hysen2PipeFanCoilDevice((host, 80), mac_addr, timeout, sync_clock, sync_hour)

    # Register the device in DeviceRegistry
    device_registry: DeviceRegistry = async_get_device_registry(hass)
    mac = entry.data[CONF_MAC].replace(":", "").lower()
    
    # Check if a device with the same MAC already exists.
    existing_device = device_registry.async_get_device(identifiers={(DOMAIN, mac)})
    if existing_device and existing_device.id != entry.entry_id:
        _LOGGER.warning("Device with MAC %s already exists in DeviceRegistry, removing old entry", mac)
        device_registry.async_remove_device(existing_device.id)

    device_entry = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, mac)},
        name=name,
        manufacturer="Hysen",
        model="HY03AC-1-Wifi",
        sw_version="Unknown",
        configuration_url=f"http://{host}",
    )

    # Check if there are devices with the "climate" domain and delete them.
    for dev in device_registry.devices.values():
        if (DOMAIN, mac) not in dev.identifiers and ("climate", mac) in dev.identifiers:
            _LOGGER.warning("Removing duplicate device with identifier ['climate', %s]", mac)
            device_registry.async_remove_device(dev.id)

    # Check if the device already exists in hass.data.
    if host in hass.data[DATA_KEY]:
        _LOGGER.warning("Device with host %s already exists, updating configuration", host)
        hass.data[DATA_KEY][host].update({
            "device": device,
            "name": name,
            "host": host,
            "device_id": device_entry.id,
        })
    else:
        hass.data[DATA_KEY][host] = {
            "device": device,
            "name": name,
            "host": host,
            "device_id": device_entry.id,
        }

    await hass.config_entries.async_forward_entry_setups(entry, ["climate"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["climate"])
    if unload_ok:
        hass.data[DATA_KEY].pop(entry.data[CONF_HOST], None)
    return unload_ok
