"""
Config flow for the Hysen 2 Pipe Fan Coil integration.

Setup flow (user-initiated)
---------------------------
Step 1 — user      : User enters the device IP address and a display name.
                     On submission the integration attempts to auto-detect the
                     MAC address by sending a dummy UDP packet to the IP (which
                     forces an ARP resolution) and then reading /proc/net/arp.
Step 2 — mac       : Shown only when auto-detection fails. User enters the
                     MAC address manually (found on device label or DHCP list).
Step 3 — confirm   : Shows detected/entered host and MAC. User can adjust the
                     display name. On confirmation, initialises the device and
                     creates the config entry.

Setup flow (zeroconf)
---------------------
If the device advertises itself via mDNS, async_step_zeroconf extracts the host
and MAC directly from the discovery info, then jumps to the confirm step.

Options flow
------------
Hysen2pfcOptionsFlowHandler exposes timeout, poll interval (update_interval),
clock sync enable (sync_clock) and sync hour (sync_hour). Saving options
triggers a full config entry reload so that the coordinator and device are
recreated with the new settings.
"""

import logging
import binascii
import socket
import time as _time
import voluptuous as vol
from datetime import datetime
from typing import Any, Dict, List, Optional
from hysen import Hysen2PipeFanCoilDevice
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo
from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_MAC,
    CONF_NAME,
    CONF_TIMEOUT,
    CONF_SYNC_CLOCK,
    CONF_SYNC_HOUR,
    CONF_UPDATE_INTERVAL,
    DEFAULT_NAME,
    DEFAULT_TIMEOUT,
    DEFAULT_SYNC_CLOCK,
    DEFAULT_SYNC_HOUR,
    DEFAULT_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

# Initial form: only IP and name — MAC is auto-detected
DATA_SCHEMA_HOST = vol.Schema({
    vol.Required(CONF_HOST): str,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): int,
})

# Shown only when MAC auto-detection fails
DATA_SCHEMA_MAC = vol.Schema({
    vol.Required(CONF_MAC): str,
})

# Full manual schema (fallback / zeroconf confirm)
DATA_SCHEMA_FULL = vol.Schema({
    vol.Required(CONF_HOST): str,
    vol.Required(CONF_MAC): str,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): int,
})


def _get_mac_for_ip(host: str) -> Optional[str]:
    """Detect the MAC address for a given IP.

    Sends a UDP packet to the target IP to ensure it appears in the ARP
    cache, then reads /proc/net/arp to retrieve the MAC address.

    Returns the MAC string in 'aa:bb:cc:dd:ee:ff' format, or None.
    """
    # Trigger ARP resolution by sending a dummy UDP packet to the host
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1.0)
        sock.sendto(b"\x00", (host, 80))
        sock.close()
    except Exception:
        pass

    # Give the kernel a moment to populate the ARP table
    _time.sleep(0.5)

    # Read /proc/net/arp for the specific IP
    try:
        with open("/proc/net/arp") as f:
            for line in f.readlines()[1:]:  # skip header line
                parts = line.split()
                if len(parts) >= 4 and parts[0] == host:
                    mac = parts[3]
                    if mac and mac != "00:00:00:00:00:00":
                        _LOGGER.debug("ARP lookup: %s → %s", host, mac)
                        return mac
    except Exception as exc:
        _LOGGER.debug("ARP lookup failed for %s: %s", host, exc)

    _LOGGER.debug("No ARP entry found for %s", host)
    return None


class Hysen2pfcConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hysen 2 Pipe Fan Coil Controller."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self._discovered_device: Dict[str, Any] = {}

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Show the initial form: IP address and device name.

        On submit, tries to auto-detect the MAC address via ARP.
        If auto-detection succeeds, proceeds directly to confirmation.
        If it fails, moves to async_step_mac for manual MAC entry.
        """
        errors: Dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            name = user_input.get(CONF_NAME, DEFAULT_NAME)
            timeout = user_input.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)

            # Check for existing entry with same host
            for entry in self._async_current_entries():
                if entry.data.get(CONF_HOST) == host:
                    return self.async_abort(reason="already_configured")

            self._discovered_device = {
                CONF_HOST: host,
                CONF_NAME: name,
                CONF_TIMEOUT: timeout,
            }

            # Try to auto-detect MAC
            mac = await self.hass.async_add_executor_job(_get_mac_for_ip, host)
            if mac:
                self._discovered_device[CONF_MAC] = mac
                _LOGGER.debug("Auto-detected MAC %s for %s", mac, host)
                return await self.async_step_confirm()

            # MAC not found — ask user
            _LOGGER.debug("MAC not found for %s, asking user", host)
            return await self.async_step_mac()

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA_HOST,
            errors=errors,
        )

    async def async_step_mac(self, user_input: Optional[Dict[str, Any]] = None):
        """Ask for MAC address when auto-detection fails."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            mac = user_input[CONF_MAC].strip()
            # Normalize and validate
            mac_clean = mac.replace(":", "").replace("-", "").lower()
            try:
                binascii.unhexlify(mac_clean)
            except binascii.Error:
                errors["base"] = "invalid_mac"
                return self.async_show_form(
                    step_id="mac",
                    data_schema=DATA_SCHEMA_MAC,
                    errors=errors,
                    description_placeholders={"host": self._discovered_device[CONF_HOST]},
                )
            mac_colon = ":".join(mac_clean[i:i+2] for i in range(0, 12, 2))
            self._discovered_device[CONF_MAC] = mac_colon
            return await self.async_step_confirm()

        return self.async_show_form(
            step_id="mac",
            data_schema=DATA_SCHEMA_MAC,
            errors=errors,
            description_placeholders={"host": self._discovered_device[CONF_HOST]},
        )

    async def async_step_confirm(self, user_input: Optional[Dict[str, Any]] = None):
        """Show discovered/entered device for confirmation before creating entry."""
        errors: Dict[str, str] = {}
        host = self._discovered_device[CONF_HOST]
        mac = self._discovered_device[CONF_MAC]
        name = self._discovered_device.get(CONF_NAME, DEFAULT_NAME)
        timeout = self._discovered_device.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)

        if user_input is not None:
            # User confirmed (optionally changed name)
            name = user_input.get(CONF_NAME, name)
            mac_clean = mac.replace(":", "").lower()
            try:
                mac_bytes = binascii.unhexlify(mac_clean)
            except binascii.Error:
                errors["base"] = "invalid_mac"
                return self.async_show_form(
                    step_id="confirm",
                    data_schema=vol.Schema({vol.Optional(CONF_NAME, default=name): str}),
                    errors=errors,
                    description_placeholders={"host": host, "mac": mac},
                )

            for entry in self._async_current_entries():
                if entry.data.get(CONF_MAC) == mac:
                    return self.async_abort(reason="already_configured")

            try:
                device = Hysen2PipeFanCoilDevice(
                    host=(host, 80),
                    mac=mac_bytes,
                    timeout=timeout,
                    sync_clock=DEFAULT_SYNC_CLOCK,
                    sync_hour=DEFAULT_SYNC_HOUR,
                )
                _LOGGER.debug("Initialized device at %s (MAC: %s)", host, mac)
            except Exception as e:
                _LOGGER.error("Failed to initialize device at %s: %s", host, e)
                errors["base"] = "cannot_connect"
                return self.async_show_form(
                    step_id="confirm",
                    data_schema=vol.Schema({vol.Optional(CONF_NAME, default=name): str}),
                    errors=errors,
                    description_placeholders={"host": host, "mac": mac},
                )

            await self.async_set_unique_id(mac)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=name,
                data={
                    CONF_HOST: host,
                    CONF_MAC: mac,
                    CONF_NAME: name,
                    CONF_TIMEOUT: timeout,
                },
            )

        # Show confirmation form — user can change name only
        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({
                vol.Optional(CONF_NAME, default=name): str,
            }),
            description_placeholders={"host": host, "mac": mac},
        )

    async def async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo):
        """Handle zeroconf discovery of a Hysen device."""
        host = discovery_info.host
        mac = discovery_info.properties.get("mac", "").replace(":", "").lower()
        if not mac:
            return self.async_abort(reason="no_mac")

        try:
            binascii.unhexlify(mac)
        except binascii.Error as e:
            _LOGGER.error("Invalid MAC address from zeroconf %s: %s", mac, e)
            return self.async_abort(reason="invalid_mac")

        mac_colon = ":".join(mac[i:i+2] for i in range(0, 12, 2))

        for entry in self._async_current_entries():
            if entry.data.get(CONF_MAC) == mac_colon:
                return self.async_abort(reason="already_configured")

        self._discovered_device = {
            CONF_HOST: host,
            CONF_MAC: mac_colon,
            CONF_NAME: discovery_info.name or DEFAULT_NAME,
            CONF_TIMEOUT: DEFAULT_TIMEOUT,
        }

        await self.async_set_unique_id(mac_colon)
        self._abort_if_unique_id_configured()
        return await self.async_step_confirm()

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow handler."""
        return Hysen2pfcOptionsFlowHandler(config_entry)


class Hysen2pfcOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Hysen 2 Pipe Fan Coil Controller."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize the options flow handler."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: Optional[Dict[str, Any]] = None):
        """Manage device options configuration."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        opts = self.config_entry.options
        data = self.config_entry.data

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    CONF_TIMEOUT,
                    default=opts.get(CONF_TIMEOUT, data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)),
                ): int,
                vol.Optional(
                    CONF_UPDATE_INTERVAL,
                    default=opts.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
                ): vol.All(vol.Coerce(int), vol.Range(min=10, max=300)),
                vol.Optional(
                    CONF_SYNC_CLOCK,
                    default=opts.get(CONF_SYNC_CLOCK, DEFAULT_SYNC_CLOCK),
                ): bool,
                vol.Optional(
                    CONF_SYNC_HOUR,
                    default=opts.get(CONF_SYNC_HOUR, DEFAULT_SYNC_HOUR),
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=23)),
            }),
        )
