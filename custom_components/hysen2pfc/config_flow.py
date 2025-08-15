"""
Configuration flow for Hysen 2 Pipe Fan Coil Controller.

This module handles the setup and discovery of Hysen devices.
"""

import logging
import binascii
import voluptuous as vol
from typing import Any, Dict, Optional
from hysen import Hysen2PipeFanCoilDevice
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo
from .const import (
    DOMAIN, 
    CONF_HOST, 
    CONF_MAC, 
    CONF_NAME, 
    CONF_TIMEOUT,
    DEFAULT_NAME, 
    DEFAULT_TIMEOUT,
    DEFAULT_SYNC_CLOCK,
    DEFAULT_SYNC_HOUR,
)

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): str,
    vol.Required(CONF_MAC): str,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): int,
})

class Hysen2pfcConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hysen 2 Pipe Fan Coil Controller.

    Manages user-initiated and zeroconf-based configuration of Hysen devices.
    """

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize the Hysen configuration flow.

        Sets up the initial state for the config flow, including storage for
        discovered device information.
        """
        self._discovered_device: Dict[str, Any] = {}

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Handle the initial step of user-initiated configuration.

        Validates user input, checks for existing configurations, and initializes
        the Hysen device.

        Args:
            user_input: Dictionary containing user-provided configuration data.

        Returns:
            Dict: The result of the configuration step (form, abort, or create entry).
        """
        errors: Dict[str, str] = {}
        if user_input is not None:
            # Normalize MAC address
            mac = user_input[CONF_MAC].replace(":", "").lower()
            try:
                mac_bytes = binascii.unhexlify(mac)
            except binascii.Error as e:
                _LOGGER.error("Invalid MAC address %s: %s", user_input[CONF_MAC], e)
                errors["base"] = "invalid_mac"
                return self.async_show_form(
                    step_id="user",
                    data_schema=DATA_SCHEMA,
                    errors=errors,
                )

            # Check for existing config entry with the same MAC
            for entry in self._async_current_entries():
                if entry.data.get(CONF_MAC) == user_input[CONF_MAC]:
                    return self.async_abort(reason="already_configured")

            try:
                # Initialize device (connection is handled by constructor)
                device = Hysen2PipeFanCoilDevice(
                    host=(user_input[CONF_HOST], 80),
                    mac=mac_bytes,
                    timeout=user_input[CONF_TIMEOUT],
                    sync_clock=DEFAULT_SYNC_CLOCK,
                    sync_hour=DEFAULT_SYNC_HOUR,
                )
                _LOGGER.debug("Initialized device at %s (MAC: %s)", user_input[CONF_HOST], user_input[CONF_MAC])
            except Exception as e:
                _LOGGER.error("Failed to initialize device at %s: %s", user_input[CONF_HOST], e)
                errors["base"] = "cannot_connect"
            else:
                # Set unique ID based on MAC address (store as colon-separated for registry)
                await self.async_set_unique_id(user_input[CONF_MAC])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_MAC: user_input[CONF_MAC],
                        CONF_NAME: user_input[CONF_NAME],
                        CONF_TIMEOUT: user_input[CONF_TIMEOUT],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo):
        """Handle zeroconf discovery of a Hysen device.

        Processes zeroconf discovery data to initialize a configuration flow.

        Args:
            discovery_info: Zeroconf discovery information for the device.

        Returns:
            Dict: The result of the discovery step (abort or proceed to confirmation).
        """
        host = discovery_info.host
        mac = discovery_info.properties.get("mac", "").replace(":", "").lower()
        if not mac:
            return self.async_abort(reason="no_mac")

        # Normalize MAC address
        try:
            mac_bytes = binascii.unhexlify(mac)
        except binascii.Error as e:
            _LOGGER.error("Invalid MAC address from zeroconf %s: %s", mac, e)
            return self.async_abort(reason="invalid_mac")

        # Store colon-separated MAC for config entry
        mac_colon = ":".join(mac[i:i+2] for i in range(0, 12, 2))

        # Check for existing config entry with the same MAC
        for entry in self._async_current_entries():
            if entry.data.get(CONF_MAC) == mac_colon:
                return self.async_abort(reason="already_configured")

        self._discovered_device = {
            CONF_HOST: host,
            CONF_MAC: mac_colon,
            CONF_NAME: discovery_info.name or DEFAULT_NAME,
            CONF_TIMEOUT: DEFAULT_TIMEOUT,
        }

        # Set unique ID based on MAC address
        await self.async_set_unique_id(mac_colon)
        self._abort_if_unique_id_configured()

        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(self, user_input: Optional[Dict[str, Any]] = None):
        """Handle confirmation step for user-confirmed devices.

        Allows the user to confirm or modify discovered device settings.

        Args:
            user_input: Dictionary containing user-confirmed or modified configuration data.

        Returns:
            Dict: The result of the confirmation step (form or create entry).
        """
        errors: Dict[str, str] = {}
        if user_input is not None:
            try:
                mac_bytes = binascii.unhexlify(self._discovered_device[CONF_MAC].replace(":", ""))
                device = Hysen2PipeFanCoilDevice(
                    host=(self._discovered_device[CONF_HOST], 80),
                    mac=mac_bytes,
                    timeout=self._discovered_device[CONF_TIMEOUT],
                    sync_clock=DEFAULT_SYNC_CLOCK,
                    sync_hour=DEFAULT_SYNC_HOUR,
                )
                _LOGGER.debug("Initialized device at %s (MAC: %s)", self._discovered_device[CONF_HOST], self._discovered_device[CONF_MAC])
            except Exception as e:
                _LOGGER.error("Failed to initialize device at %s: %s", self._discovered_device[CONF_HOST], e)
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=user_input.get(CONF_NAME, self._discovered_device[CONF_NAME]),
                    data={
                        CONF_HOST: self._discovered_device[CONF_HOST],
                        CONF_MAC: self._discovered_device[CONF_MAC],
                        CONF_NAME: user_input.get(CONF_NAME, self._discovered_device[CONF_NAME]),
                        CONF_TIMEOUT: self._discovered_device[CONF_TIMEOUT],
                    },
                )

        return self.async_show_form(
            step_id="zeroconf_confirm",
            data_schema=vol.Schema({
                vol.Optional(CONF_NAME, default=self._discovered_device[CONF_NAME]): str,
            }),
            errors=errors,
            description_placeholders={
                "host": self._discovered_device[CONF_HOST],
                "mac": self._discovered_device[CONF_MAC],
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow handler for the Hysen configuration.

        Args:
            config_entry: The configuration entry for the device.

        Returns:
            Hysen2pfcOptionsFlowHandler: The options flow handler instance.
        """
        return Hysen2pfcOptionsFlowHandler(config_entry)

class Hysen2pfcOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Hysen 2 Pipe Fan Coil Controller.

    Manages configuration options for an existing Hysen device.
    """

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize the options flow handler.

        Args:
            config_entry: The configuration entry for the device.
        """
        self.config_entry = config_entry

    async def async_step_init(self, user_input: Optional[Dict[str, Any]] = None):
        """Manage device options configuration.

        Allows the user to modify options such as timeout.

        Args:
            user_input: Dictionary containing user-provided option updates.

        Returns:
            Dict: The result of the options configuration step (form or create entry).
        """
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    CONF_TIMEOUT,
                    default=self.config_entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
                ): int,
            }),
        )
