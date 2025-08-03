"""
Configuration flow for Hysen 2 Pipe Fan Coil integration.
"""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_NAME, CONF_TIMEOUT
from homeassistant.helpers.device_registry import async_get as async_get_device_registry
from .const import (
    DOMAIN,
    DEFAULT_NAME,
    CONF_SYNC_CLOCK,
    CONF_SYNC_HOUR,
    DEFAULT_TIMEOUT,
    DEFAULT_SYNC_CLOCK,
    DEFAULT_SYNC_HOUR,
    HYSTERESIS_MODES,
)

class Hysen2PipeFanCoilConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hysen 2 Pipe Fan Coil."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                mac = user_input[CONF_MAC].replace(":", "").lower()
                if len(mac) != 12 or not all(c in "0123456789abcdef" for c in mac):
                    errors[CONF_MAC] = "invalid_mac"
                else:
                    # Verifică dacă există deja un dispozitiv cu acest MAC
                    device_registry = async_get_device_registry(self.hass)
                    existing_device = device_registry.async_get_device(
                        identifiers={(DOMAIN, mac)}
                    )
                    if existing_device:
                        errors["base"] = "device_already_configured"
                    else:
                        await self.async_set_unique_id(mac)
                        self._abort_if_unique_id_configured(updates={
                            CONF_HOST: user_input[CONF_HOST],
                            CONF_NAME: user_input.get(CONF_NAME, DEFAULT_NAME),
                            CONF_TIMEOUT: user_input.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
                            CONF_SYNC_CLOCK: user_input.get(CONF_SYNC_CLOCK, DEFAULT_SYNC_CLOCK),
                            CONF_SYNC_HOUR: user_input.get(CONF_SYNC_HOUR, DEFAULT_SYNC_HOUR),
                        })
                        return self.async_create_entry(
                            title=user_input.get(CONF_NAME, DEFAULT_NAME),
                            data={
                                CONF_NAME: user_input.get(CONF_NAME, DEFAULT_NAME),
                                CONF_HOST: user_input[CONF_HOST],
                                CONF_MAC: user_input[CONF_MAC],
                                CONF_TIMEOUT: user_input.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
                                CONF_SYNC_CLOCK: user_input.get(CONF_SYNC_CLOCK, DEFAULT_SYNC_CLOCK),
                                CONF_SYNC_HOUR: user_input.get(CONF_SYNC_HOUR, DEFAULT_SYNC_HOUR),
                            }
                        )
            except Exception as e:
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_MAC): str,
                    vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
                    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): int,
                    vol.Optional(CONF_SYNC_CLOCK, default=DEFAULT_SYNC_CLOCK): bool,
                    vol.Optional(CONF_SYNC_HOUR, default=DEFAULT_SYNC_HOUR): int,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Hysen 2 Pipe Fan Coil."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_NAME,
                        default=self.config_entry.data.get(CONF_NAME, DEFAULT_NAME),
                    ): str,
                    vol.Optional(
                        CONF_TIMEOUT,
                        default=self.config_entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
                    ): int,
                    vol.Optional(
                        CONF_SYNC_CLOCK,
                        default=self.config_entry.data.get(CONF_SYNC_CLOCK, DEFAULT_SYNC_CLOCK),
                    ): bool,
                    vol.Optional(
                        CONF_SYNC_HOUR,
                        default=self.config_entry.data.get(CONF_SYNC_HOUR, DEFAULT_SYNC_HOUR),
                    ): int,
                }
            ),
        )