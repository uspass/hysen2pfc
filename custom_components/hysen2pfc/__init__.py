"""
Hysen 2 Pipe Fan Coil Controller — Home Assistant integration.

Entry points
------------
async_setup          Called once when the integration is first loaded. Initialises
                     hass.data[DOMAIN] and registers the four custom climate services
                     (set_hvac_mode, set_temperature, set_fan_mode, set_preset_mode).
                     Services are guarded with has_service() so they are registered
                     exactly once even when multiple devices are configured.

async_setup_entry    Called for each config entry (one per physical device). Creates
                     a Hysen2PipeFanCoilDevice, builds the HysenCoordinator, performs
                     the first refresh, then forwards setup to all platform modules.
                     Also registers an options-update listener so that changes made
                     in the options flow trigger a full entry reload.

async_unload_entry   Unloads all platforms and removes the device from hass.data.
                     When the last device is removed the custom services are also
                     unregistered.

Custom services
---------------
The standard HA climate services (climate.set_hvac_mode etc.) do not respect the
dynamic mode lists that the coordinator provides. These custom services replicate
that behaviour with the same validation logic used by the climate entity, so that
automations see the same constraints as the UI.
"""

import logging
import binascii
import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryNotReady, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from hysen import Hysen2PipeFanCoilDevice
from .const import (
    DOMAIN,
    PLATFORMS,
    CONF_HOST, 
    CONF_MAC, 
    CONF_NAME, 
    CONF_TIMEOUT,
    CONF_SYNC_CLOCK,
    CONF_SYNC_HOUR,
    CONF_UPDATE_INTERVAL,
    DEFAULT_NAME, 
    DEFAULT_TIMEOUT,
    DEFAULT_MIN_TEMP,
    DEFAULT_MAX_TEMP,
    DEFAULT_SYNC_CLOCK,
    DEFAULT_SYNC_HOUR,
    DEFAULT_UPDATE_INTERVAL,
    ATTR_ENTITY_ID,
    ATTR_HVAC_MODE,
    ATTR_TEMPERATURE,
    ATTR_FAN_MODE,
    ATTR_PRESET_MODE,
    ATTR_MIN_TEMP,
    ATTR_MAX_TEMP,
    HVAC_MODES,
    HVAC_MODES_NO_FAN,
    FAN_AUTO,
    FAN_MODES,
    FAN_MODES_MANUAL,
    PRESET_MODES,
    SERVICE_SET_TEMPERATURE,
    SERVICE_SET_HVAC_MODE,
    SERVICE_SET_FAN_MODE,
    SERVICE_SET_PRESET_MODE,
    HVACMode,
)
from .coordinator import HysenCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Hysen2pfc integration.

    Initializes the integration and prepares the domain data in Home Assistant.

    Args:
        hass: The Home Assistant instance.
        config: Configuration data for the integration.

    Returns:
        bool: True if setup is successful, False otherwise.
    """
    _LOGGER.info("Initializing Hysen2pfc integration")
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Hysen2pfc from a config entry.

    Initializes the Hysen device, coordinator, and platform entities based on the config entry.

    Args:
        hass: The Home Assistant instance.
        entry: The configuration entry containing device details.

    Returns:
        bool: True if setup is successful, raises ConfigEntryNotReady on failure.
    """
    host = entry.data[CONF_HOST]
    mac = entry.data[CONF_MAC]
    name = entry.data.get(CONF_NAME, DEFAULT_NAME)
    hass.data.setdefault(DOMAIN, {})
    timeout = entry.options.get(CONF_TIMEOUT, entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT))
    sync_clock = entry.options.get(CONF_SYNC_CLOCK, DEFAULT_SYNC_CLOCK)
    sync_hour = entry.options.get(CONF_SYNC_HOUR, DEFAULT_SYNC_HOUR)
    update_interval = entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)

    _LOGGER.info("Starting setup for device '%s' (MAC: %s, Host: %s, Entry ID: %s)", name, mac, host, entry.entry_id)

    try:
        mac_bytes = binascii.unhexlify(mac.replace(":", ""))
        device = Hysen2PipeFanCoilDevice(
            host=(host, 80),
            mac=mac_bytes,
            timeout=timeout,
            sync_clock=sync_clock,
            sync_hour=sync_hour,
        )
        _LOGGER.debug("Initialized Hysen device at %s (MAC: %s)", host, mac)
    except Exception as e:
        _LOGGER.error("Failed to initialize Hysen device at %s: %s", host, e)
        raise ConfigEntryNotReady from e

    coordinator = HysenCoordinator(hass, device, host, entry, update_interval=update_interval)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "host": host,
        "mac": mac,
        "name": name,
        "timeout": timeout,
        "coordinator": coordinator,
    }

    entry.async_on_unload(entry.add_update_listener(_async_options_updated))

    # Register custom service for set_hvac_mode
    async def async_set_hvac_mode_handler(service_call):
        """Handle the hysen2pfc.set_hvac_mode service call.

        Processes the service call to set the HVAC mode for Hysen climate entities.
        Validates the provided entity_id(s) and hvac_mode, then calls the climate.set_hvac_mode
        service for each valid entity.

        Args:
            service_call (homeassistant.core.ServiceCall): The service call object containing
                the domain, service, data, and context of the call. Expects 'entity_id' (string or list)
                and 'hvac_mode' (string) in service_call.data.

        Raises:
            ServiceValidationError: If entity_id or hvac_mode is missing, invalid, or if no valid entity IDs are provided.
            HomeAssistantError: If the climate.set_hvac_mode service call fails for any entity.

        Example:
            Service call data:
            service: hysen2pfc.set_hvac_mode
            target:
              entity_id: climate.office
            data:
              hvac_mode: heat
            or
            service: hysen2pfc.set_hvac_mode
            data:
              entity_id: climate.office
              hvac_mode: heat
        """
        entity_ids = service_call.data.get('entity_id')
        hvac_mode = service_call.data.get(ATTR_HVAC_MODE)
        
        # Check for missing or None values
        if entity_ids is None:
            _LOGGER.error("Missing or invalid entity_id (%s)", 
                          entity_ids)
            raise ServiceValidationError(
                f"Missing or invalid entity_id ({entity_ids})",
                translation_domain=DOMAIN,
                translation_key="missing_or_invalid_entity_id",
            )
        if hvac_mode is None:
            _LOGGER.error("Missing or invalid hvac_mode: (%s)", 
                          hvac_mode)
            raise ServiceValidationError(
                f"Missing or invalid hvac_mode {hvac_mode}",
                translation_domain=DOMAIN,
                translation_key="missing_or_invalid_hvac_mode",
            )

        # Ensure entity_ids is a list
        if isinstance(entity_ids, str):
            entity_ids = [entity_ids]
        elif not isinstance(entity_ids, list):
            _LOGGER.error("entity_id must be a string or list of strings, got %s (type: %s)", 
                          entity_ids, type(entity_ids))
            raise ServiceValidationError(
                f"entity_id must be a string or list of strings, got {entity_ids}",
                translation_domain=DOMAIN,
                translation_key="invalid_entity_id_type",
            )
        
        # Validate each entity_id
        valid_entity_ids = []
        for entity_id in entity_ids:
            if not isinstance(entity_id, str):
                _LOGGER.error("Invalid entity_id: %s is not a string (type: %s)", entity_id, type(entity_id))
                continue
            if not entity_id.startswith("climate."):
                _LOGGER.error("Invalid entity_id: %s does not belong to climate domain", entity_id)
                continue

            # Check fan mode for fan_only HVAC mode
            if hvac_mode == HVACMode.FAN_ONLY:
                entity_state = hass.states.get(entity_id)
                _LOGGER.debug("Get entity_state: %s, entity_state.attributes.get(ATTR_FAN_MODE): %s", 
                              entity_state, entity_state.attributes.get(ATTR_FAN_MODE) if entity_state else None)
                if entity_state and entity_state.attributes.get(ATTR_FAN_MODE) == FAN_AUTO:
                    _LOGGER.error("[%s] HVAC mode %s is not allowed when fan mode is auto. Valid fan modes are: %s", 
                                  entity_id, hvac_mode, ", ".join(FAN_MODES_MANUAL))
                    raise ServiceValidationError(
                        f"HVAC mode {hvac_mode} is not allowed when fan mode is auto. Set fan mode to low, medium, or high first.",
                        translation_domain=DOMAIN,
                        translation_key="fan_only_with_auto_fan",
                    )

            valid_entity_ids.append(entity_id)
        
        if not valid_entity_ids:
            _LOGGER.error("No valid entity IDs provided")
            raise ServiceValidationError(
                "No valid entity IDs provided",
                translation_domain=DOMAIN,
                translation_key="no_valid_entity_ids",
            )
        
        # Process valid entity_ids
        for entity_id in valid_entity_ids:
            try:
                await hass.services.async_call(
                    'climate',
                    SERVICE_SET_HVAC_MODE,
                    {'entity_id': entity_id, 'hvac_mode': hvac_mode},
                    context=service_call.context
                )
                _LOGGER.debug("Called climate.set_hvac_mode for %s with hvac_mode %s", entity_id, hvac_mode)
            except Exception as e:
                _LOGGER.error("Failed to set hvac mode for %s: %s", entity_id, e)
                raise

    if not hass.services.has_service(DOMAIN, SERVICE_SET_HVAC_MODE):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_HVAC_MODE,
            async_set_hvac_mode_handler,
            schema=vol.Schema({
                vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
                vol.Required(ATTR_HVAC_MODE): cv.string,  # Validate as string, check in async_set_hvac_mode
            })
        )

    # Register custom service for set_temperature
    async def async_set_temperature_handler(service_call):
        """Handle the hysen2pfc.set_temperature service call.

        Processes the service call to set the target temperature for Hysen climate entities.
        Validates the provided entity_id(s) and temperature against the entity's min_temp and max_temp,
        then calls the climate.set_temperature service for each valid entity.

        Args:
            service_call (homeassistant.core.ServiceCall): The service call object containing
                the domain, service, data, and context of the call. Expects 'entity_id' (string or list)
                and 'temperature' (float) in service_call.data.

        Raises:
            ServiceValidationError: If entity_id or temperature is missing, invalid, or if no valid entity IDs are provided.
            HomeAssistantError: If the climate.set_temperature service call fails for any entity.

        Example:
            Service call data:
            service: hysen2pfc.set_temperature
            target:
              entity_id: climate.office
            data:
              temperature: 22
            or
            service: hysen2pfc.set_temperature
            data:
              entity_id: climate.office
              temperature: 22
        """
        entity_ids = service_call.data.get('entity_id')
        temperature = service_call.data.get(ATTR_TEMPERATURE)
        
        # Check for missing or None values
        if entity_ids is None:
            _LOGGER.error("Missing or invalid entity_id (%s)", 
                          entity_ids)
            raise ServiceValidationError(
                f"Missing or invalid entity_id ({entity_ids})",
                translation_domain=DOMAIN,
                translation_key="missing_or_invalid_entity_id",
            )
        if temperature is None:
            _LOGGER.error("Missing or invalid temperature (%s)", 
                          temperature)
            raise ServiceValidationError(
                f"Missing or invalid temperature ({temperature})",
                translation_domain=DOMAIN,
                translation_key="missing_or_invalid_temperature",
            )
        
        # Ensure entity_ids is a list
        if isinstance(entity_ids, str):
            entity_ids = [entity_ids]
        elif not isinstance(entity_ids, list):
            _LOGGER.error("entity_id must be a string or list of strings, got %s (type: %s)", 
                          entity_ids, type(entity_ids))
            raise ServiceValidationError(
                f"entity_id must be a string or list of strings, got {entity_ids}",
                translation_domain=DOMAIN,
                translation_key="invalid_entity_id_type",
            )
        
        # Validate each entity_id and temperature
        valid_entity_ids = []
        for entity_id in entity_ids:
            if not isinstance(entity_id, str):
                _LOGGER.error("Invalid entity_id: %s is not a string (type: %s)", entity_id, type(entity_id))
                continue
            if not entity_id.startswith("climate."):
                _LOGGER.error("Invalid entity_id: %s does not belong to climate domain", entity_id)
                continue

            # Check temperature range
            entity_state = hass.states.get(entity_id)
            if not entity_state:
                _LOGGER.error("Entity %s not found", entity_id)
                continue
            min_temp = entity_state.attributes.get(ATTR_MIN_TEMP, DEFAULT_MIN_TEMP)
            max_temp = entity_state.attributes.get(ATTR_MAX_TEMP, DEFAULT_MAX_TEMP)
            try:
                temp_value = float(temperature)
                if temp_value < min_temp or temp_value > max_temp:
                    _LOGGER.error(
                        "[%s] Temperature %s is out of range. Valid range is %s to %s",
                        entity_id, temp_value, min_temp, max_temp
                    )
                    raise ServiceValidationError(
                        f"Temperature {temp_value} is out of range for {entity_id}. Valid range is {min_temp} to {max_temp}.",
                        translation_domain=DOMAIN,
                        translation_key="temperature_out_of_range",
                    )
                valid_entity_ids.append(entity_id)
            except (TypeError, ValueError):
                _LOGGER.error("Invalid temperature type: %s (expected a number)", temperature)
                raise ServiceValidationError(
                    f"Invalid temperature type: {temperature} (expected a number)",
                    translation_domain=DOMAIN,
                    translation_key="invalid_temperature_type",
                )
        
        if not valid_entity_ids:
            _LOGGER.error("No valid entity IDs provided")
            raise ServiceValidationError(
                "No valid entity IDs provided",
                translation_domain=DOMAIN,
                translation_key="no_valid_entity_ids",
            )
        
        # Process valid entity_ids
        for entity_id in valid_entity_ids:
            try:
                await hass.services.async_call(
                    'climate',
                    SERVICE_SET_TEMPERATURE,
                    {'entity_id': entity_id, 'temperature': temp_value},
                    context=service_call.context
                )
                _LOGGER.debug("Called climate.set_temperature for %s with temperature %s", entity_id, temperature)
            except Exception as e:
                _LOGGER.error("Failed to set temperature for %s: %s", entity_id, e)
                raise

    if not hass.services.has_service(DOMAIN, SERVICE_SET_TEMPERATURE):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_TEMPERATURE,
            async_set_temperature_handler,
            schema=vol.Schema({
                vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
                vol.Required(ATTR_TEMPERATURE): cv.positive_float,  # Accept positive float, validation in async_set_temperature
            })
        )

    # Register custom service for set_fan_mode
    async def async_set_fan_mode_handler(service_call):
        """Handle the hysen2pfc.set_fan_mode service call.

        Processes the service call to set the fan mode for Hysen climate entities.
        Validates the provided entity_id(s) and fan_mode, then calls the climate.set_fan_mode
        service for each valid entity.

        Args:
            service_call (homeassistant.core.ServiceCall): The service call object containing
                the domain, service, data, and context of the call. Expects 'entity_id' (string or list)
                and 'fan_mode' (string) in service_call.data.

        Raises:
            ServiceValidationError: If entity_id or fan_mode is missing, invalid, or if no valid entity IDs are provided.
            HomeAssistantError: If the climate.set_fan_mode service call fails for any entity.

        Example:
            Service call data:
            service: hysen2pfc.set_fan_mode
            target:
              entity_id: climate.office
            data:
              fan_mode: low
            or
            service: hysen2pfc.set_fan_mode
            data:
              entity_id: climate.office
              fan_mode: low
        """
        entity_ids = service_call.data.get('entity_id')
        fan_mode = service_call.data.get(ATTR_FAN_MODE)
        
        # Check for missing or None values
        if entity_ids is None:
            _LOGGER.error("Missing or invalid entity_id (%s)", 
                          entity_ids)
            raise ServiceValidationError(
                f"Missing or invalid entity_id ({entity_ids})",
                translation_domain=DOMAIN,
                translation_key="missing_or_invalid_entity_id",
            )
        if fan_mode is None:
            _LOGGER.error("Missing or invalid fan_mode (%s)", 
                          fan_mode)
            raise ServiceValidationError(
                f"Missing or invalid fan_mode: {fan_mode}",
                translation_domain=DOMAIN,
                translation_key="missing_or_invalid_fan_mode",
            )

        # Ensure entity_ids is a list
        if isinstance(entity_ids, str):
            entity_ids = [entity_ids]
        elif not isinstance(entity_ids, list):
            _LOGGER.error("entity_id must be a string or list of strings, got %s (type: %s)", 
                          entity_ids, type(entity_ids))
            raise ServiceValidationError(
                f"entity_id must be a string or list of strings, got {entity_ids}",
                translation_domain=DOMAIN,
                translation_key="invalid_entity_id_type",
            )

        # Validate each entity_id
        valid_entity_ids = []
        for entity_id in entity_ids:
            if not isinstance(entity_id, str):
                _LOGGER.error("Invalid entity_id: %s is not a string (type: %s)", entity_id, type(entity_id))
                continue
            if not entity_id.startswith("climate."):
                _LOGGER.error("Invalid entity_id: %s does not belong to climate domain", entity_id)
                continue

            # Check HVAC mode for auto fan mode
            if fan_mode == FAN_AUTO:
                entity_state = hass.states.get(entity_id)
                _LOGGER.debug("Get entity_state: %s, entity_state.attributes.get(ATTR_HVAC_MODE): %s", 
                              entity_state, entity_state.attributes.get(ATTR_HVAC_MODE) if entity_state else None)
                if entity_state and entity_state.attributes.get(ATTR_HVAC_MODE) == HVACMode.FAN_ONLY:
                    _LOGGER.error("[%s] fan mode %s is not allowed when HVAC mode is fan_only. Valid HVAC modes are: %s", 
                                  entity_id, fan_mode, ", ".join(HVAC_MODES_NO_FAN))
                    raise ServiceValidationError(
                        f"fan mode {fan_mode} is not allowed when HVAC mode is fan_only. Set HVAC mode to off, heat, or cool first.",
                        translation_domain=DOMAIN,
                        translation_key="auto_fan_with_fan_only",
                    )

            valid_entity_ids.append(entity_id)

        if not valid_entity_ids:
            _LOGGER.error("No valid entity IDs provided")
            raise ServiceValidationError(
                "No valid entity IDs provided",
                translation_domain=DOMAIN,
                translation_key="no_valid_entity_ids",
            )
        
        # Process valid entity_ids
        for entity_id in valid_entity_ids:
            try:
                await hass.services.async_call(
                    'climate',
                    SERVICE_SET_FAN_MODE,
                    {'entity_id': entity_id, 'fan_mode': fan_mode},
                    context=service_call.context
                )
                _LOGGER.debug("Called climate.set_fan_mode for %s with fan_mode %s", entity_id, fan_mode)
            except Exception as e:
                _LOGGER.error("Failed to set fan mode for %s: %s", entity_id, e)
                raise

    if not hass.services.has_service(DOMAIN, SERVICE_SET_FAN_MODE):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_FAN_MODE,
            async_set_fan_mode_handler,
            schema=vol.Schema({
                vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
    #            vol.Required(ATTR_FAN_MODE): vol.In(["low", "medium", "high", "auto"])
                vol.Required(ATTR_FAN_MODE): cv.string,  # Validate as string, check in async_set_hvac_mode
            })
        )

    # Register custom service for set_preset_mode
    async def async_set_preset_mode_handler(service_call):
        """Handle the hysen2pfc.set_preset_mode service call.

        Processes the service call to set the preset mode for Hysen climate entities.
        Validates the provided entity_id(s) and preset_mode, then calls the climate.set_preset_mode
        service for each valid entity.

        Args:
            service_call (homeassistant.core.ServiceCall): The service call object containing
                the domain, service, data, and context of the call. Expects 'entity_id' (string or list)
                and 'preset_mode' (string) in service_call.data.

        Raises:
            ServiceValidationError: If entity_id or preset_mode is missing, invalid, or if no valid entity IDs are provided.
            HomeAssistantError: If the climate.set_preset_mode service call fails for any entity.

        Example:
            Service call data:
            service: hysen2pfc.set_preset_mode
            target:
              entity_id: climate.office
            data:
              preset_mode: Today
            or
            service: hysen2pfc.set_preset_mode
            data:
              entity_id: climate.office
              preset_mode: Today
        """

        entity_ids = service_call.data.get('entity_id')
        preset_mode = service_call.data.get(ATTR_PRESET_MODE)
        
        # Check for missing or None values
        if entity_ids is None:
            _LOGGER.error("Missing or invalid entity_id (%s)", 
                          entity_ids)
            raise ServiceValidationError(
                f"Missing or invalid entity_id ({entity_ids})",
                translation_domain=DOMAIN,
                translation_key="missing_or_invalid_entity_id",
            )
        if preset_mode is None:
            _LOGGER.error("Missing or invalid preset_mode (%s)", 
                          preset_mode)
            raise ServiceValidationError(
                f"Missing or invalid preset_mode ({preset_mode})",
                translation_domain=DOMAIN,
                translation_key="missing_or_invalid_preset_mode",
            )
        
        # Ensure entity_ids is a list
        if isinstance(entity_ids, str):
            entity_ids = [entity_ids]
        elif not isinstance(entity_ids, list):
            _LOGGER.error("entity_id must be a string or list of strings, got %s (type: %s)", 
                          entity_ids, type(entity_ids))
            raise ServiceValidationError(
                f"entity_id must be a string or list of strings, got {entity_ids}",
                translation_domain=DOMAIN,
                translation_key="invalid_entity_id_type",
            )
        
        # Validate each entity_id
        valid_entity_ids = []
        for entity_id in entity_ids:
            if not isinstance(entity_id, str):
                _LOGGER.error("Invalid entity_id: %s is not a string (type: %s)", entity_id, type(entity_id))
                continue
            if not entity_id.startswith("climate."):
                _LOGGER.error("Invalid entity_id: %s does not belong to climate domain", entity_id)
                continue
            valid_entity_ids.append(entity_id)
        
        if not valid_entity_ids:
            _LOGGER.error("No valid entity IDs provided")
            raise ServiceValidationError(
                "No valid entity IDs provided",
                translation_domain=DOMAIN,
                translation_key="no_valid_entity_ids",
            )
        
        # Process valid entity_ids
        for entity_id in valid_entity_ids:
            try:
                await hass.services.async_call(
                    'climate',
                    SERVICE_SET_PRESET_MODE,
                    {'entity_id': entity_id, 'preset_mode': preset_mode},
                    context=service_call.context
                )
                _LOGGER.debug("Called climate.set_preset_mode for %s with preset %s", entity_id, preset_mode)
            except Exception as e:
                _LOGGER.error("Failed to set preset mode for %s: %s", entity_id, e)
                raise

    # Register the service with updated schema
    if not hass.services.has_service(DOMAIN, SERVICE_SET_PRESET_MODE):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_PRESET_MODE,
            async_set_preset_mode_handler,
            schema=vol.Schema({
                vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
                vol.Required(ATTR_PRESET_MODE): cv.string,  # Validate as string, check in async_set_preset_mode
            })
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.debug("Forwarding setup to %s platforms for MAC %s", PLATFORMS, mac)

    _LOGGER.info("Completed setup for device with MAC %s", mac)
    return True

async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when options are updated."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a Hysen config entry.

    Removes the device and its associated platforms from Home Assistant.

    Args:
        hass: The Home Assistant instance.
        entry: The configuration entry to unload.

    Returns:
        bool: True if unloading is successful, False otherwise.
    """
    mac = entry.data[CONF_MAC]
    _LOGGER.debug("Unloading config entry for device with MAC %s", mac)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        # Remove custom services only when the last config entry is removed
        if not hass.data[DOMAIN]:
            for service_name in [
                SERVICE_SET_HVAC_MODE,
                SERVICE_SET_TEMPERATURE,
                SERVICE_SET_FAN_MODE,
                SERVICE_SET_PRESET_MODE,
            ]:
                hass.services.async_remove(DOMAIN, service_name)
    return unload_ok
