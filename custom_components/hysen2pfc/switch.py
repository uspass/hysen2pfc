"""
Support for Hysen 2 Pipe Fan Coil Controller switches.

This module provides switches for fan control, frost protection, and schedule slots.
"""

import logging
import asyncio
import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.components.switch import SwitchEntity
from .const import (
    DOMAIN,
    DATA_KEY_FAN_CONTROL,
    DATA_KEY_FROST_PROTECTION,
    DATA_KEY_SLOT1_START_ENABLE,
    DATA_KEY_SLOT1_STOP_ENABLE,
    DATA_KEY_SLOT2_START_ENABLE,
    DATA_KEY_SLOT2_STOP_ENABLE,
    STATE_ON,
    STATE_OFF,
    ATTR_FAN_CONTROL,
    ATTR_FROST_PROTECTION,
    ATTR_SLOT1_START_ENABLE,
    ATTR_SLOT1_STOP_ENABLE,
    ATTR_SLOT2_START_ENABLE,
    ATTR_SLOT2_STOP_ENABLE,
    SERVICE_SET_FROST_PROTECTION,
    SERVICE_SET_FAN_CONTROL,
    SERVICE_SET_FROST_PROTECTION,
    SERVICE_SET_SLOT1_START_ENABLE,
    SERVICE_SET_SLOT1_STOP_ENABLE,
    SERVICE_SET_SLOT2_START_ENABLE,
    SERVICE_SET_SLOT2_STOP_ENABLE,
    FAN_CONTROL_HASS_TO_HYSEN,
    FROST_PROTECTION_HASS_TO_HYSEN,
    SLOT_ENABLED_HASS_TO_HYSEN,
)
from .entity import HysenEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities):
    """Set up the Hysen switches from a config entry.

    Initializes and adds the switch entities for the device, and registers services.

    Args:
        hass: The Home Assistant instance.
        config_entry: The configuration entry containing device details.
        async_add_entities: Callback to add entities asynchronously.

    Returns:
        None
    """
    device_data = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([
        HysenFanControlSwitch(device_data),
        HysenFrostProtectionSwitch(device_data),
        HysenSlot1StartEnableSwitch(device_data),
        HysenSlot1StopEnableSwitch(device_data),
        HysenSlot2StartEnableSwitch(device_data),
        HysenSlot2StopEnableSwitch(device_data),
    ])

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_SET_FAN_CONTROL,
        {vol.Required(ATTR_FAN_CONTROL): vol.In([STATE_ON, STATE_OFF])},
        "async_set_fan_control",
    )
    platform.async_register_entity_service(
        SERVICE_SET_FROST_PROTECTION,
        {vol.Required(ATTR_FROST_PROTECTION): vol.In([STATE_ON, STATE_OFF])},
        "async_set_frost_protection",
    )
    platform.async_register_entity_service(
        SERVICE_SET_SLOT1_START_ENABLE,
        {vol.Required(ATTR_SLOT1_START_ENABLE): vol.In([STATE_ON, STATE_OFF])},
        "async_set_slot1_start_enable",
    )
    platform.async_register_entity_service(
        SERVICE_SET_SLOT1_STOP_ENABLE,
        {vol.Required(ATTR_SLOT1_STOP_ENABLE): vol.In([STATE_ON, STATE_OFF])},
        "async_set_slot1_stop_enable",
    )
    platform.async_register_entity_service(
        SERVICE_SET_SLOT2_START_ENABLE,
        {vol.Required(ATTR_SLOT2_START_ENABLE): vol.In([STATE_ON, STATE_OFF])},
        "async_set_slot2_start_enable",
    )
    platform.async_register_entity_service(
        SERVICE_SET_SLOT2_STOP_ENABLE,
        {vol.Required(ATTR_SLOT2_STOP_ENABLE): vol.In([STATE_ON, STATE_OFF])},
        "async_set_slot2_stop_enable",
    )

class HysenFanControlSwitch(HysenEntity, SwitchEntity):
    """Representation of a Hysen Fan Control switch.

    Controls whether the fan is enabled or disabled.
    """

    def __init__(self, device_data):
        """Initialize the switch.

        Args:
            device_data: Dictionary containing device-specific data (e.g., mac, name, coordinator).
        """
        super().__init__(device_data["coordinator"], device_data)
        self._attr_unique_id = f"{device_data['mac']}_fan_control"
        self._attr_name = f"{device_data['name']} Fan Control"

    @property
    def is_on(self):
        """Return true if the switch is on.

        Returns:
            bool: True if fan control is on, False otherwise.
        """
        return self.coordinator.data.get(DATA_KEY_FAN_CONTROL) == STATE_ON

    @property
    def icon(self):
        """Return the icon based on the switch state.

        Returns:
            str: The Material Design Icon (MDI) for the fan control state.
        """
        return "mdi:fan" if self.is_on else "mdi:fan-off"

    async def async_turn_on(self, **kwargs):
        """Turn the switch on.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            None
        """
        _LOGGER.debug("[%s] Turning on fan control", self._host)
        success = await self._async_try_command(
            "Error in set_fan_control",
            self.coordinator.device.set_fan_control,
            FAN_CONTROL_HASS_TO_HYSEN[STATE_ON],
        )
        if success:
            # Delay to allow device to stabilize
            await asyncio.sleep(0.2)
            # Force an immediate update to fetch the latest device state
            await self.coordinator.async_refresh()
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            None
        """
        _LOGGER.debug("[%s] Turning off fan control", self._host)
        success = await self._async_try_command(
            "Error in set_fan_control",
            self.coordinator.device.set_fan_control,
            FAN_CONTROL_HASS_TO_HYSEN[STATE_OFF],
        )
        if success:
            # Delay to allow device to stabilize
            await asyncio.sleep(0.2)
            # Force an immediate update to fetch the latest device state
            await self.coordinator.async_refresh()
            self.async_write_ha_state()

    async def async_set_fan_control(self, fan_control):
        """Set the fan control state.

        Args:
            fan_control: The state to set (on or off).

        Returns:
            None
        """
        _LOGGER.debug("[%s] Setting fan control to %s", self._host, fan_control)
        success = await self._async_try_command(
            "Error in set_fan_control",
            self.coordinator.device.set_fan_control,
            FAN_CONTROL_HASS_TO_HYSEN[fan_control],
        )
        if success:
            # Delay to allow device to stabilize
            await asyncio.sleep(0.2)
            # Force an immediate update to fetch the latest device state
            await self.coordinator.async_refresh()
            self.async_write_ha_state()

class HysenFrostProtectionSwitch(HysenEntity, SwitchEntity):
    """Representation of a Hysen Frost Protection switch.

    Controls whether frost protection is enabled or disabled.
    """

    def __init__(self, device_data):
        """Initialize the switch.

        Args:
            device_data: Dictionary containing device-specific data (e.g., mac, name, coordinator).
        """
        super().__init__(device_data["coordinator"], device_data)
        self._attr_unique_id = f"{device_data['mac']}_frost_protection"
        self._attr_name = f"{device_data['name']} Frost Protection"

    @property
    def is_on(self):
        """Return true if the switch is on.

        Returns:
            bool: True if frost protection is on, False otherwise.
        """
        return self.coordinator.data.get(DATA_KEY_FROST_PROTECTION) == STATE_ON

    @property
    def icon(self):
        """Return the icon based on the switch state.

        Returns:
            str: The Material Design Icon (MDI) for the frost protection state.
        """
        return "mdi:snowflake" if self.is_on else "mdi:snowflake-off"

    async def async_turn_on(self, **kwargs):
        """Turn the switch on.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            None
        """
        _LOGGER.debug("[%s] Turning on frost protection", self._host)
        success = await self._async_try_command(
            "Error in set_frost_protection",
            self.coordinator.device.set_frost_protection,
            FROST_PROTECTION_HASS_TO_HYSEN[STATE_ON],
        )
        if success:
            # Delay to allow device to stabilize
            await asyncio.sleep(0.2)
            # Force an immediate update to fetch the latest device state
            await self.coordinator.async_refresh()
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            None
        """
        _LOGGER.debug("[%s] Turning off frost protection", self._host)
        success = await self._async_try_command(
            "Error in set_frost_protection",
            self.coordinator.device.set_frost_protection,
            FROST_PROTECTION_HASS_TO_HYSEN[STATE_OFF],
        )
        if success:
            # Delay to allow device to stabilize
            await asyncio.sleep(0.2)
            # Force an immediate update to fetch the latest device state
            await self.coordinator.async_refresh()
            self.async_write_ha_state()

    async def async_set_frost_protection(self, frost_protection):
        """Set the frost protection state.

        Args:
            frost_protection: The state to set (on or off).

        Returns:
            None
        """
        _LOGGER.debug("[%s] Setting frost protection to %s", self._host, frost_protection)
        success = await self._async_try_command(
            "Error in set_frost_protection",
            self.coordinator.device.set_frost_protection,
            FROST_PROTECTION_HASS_TO_HYSEN[frost_protection],
        )
        if success:
            # Delay to allow device to stabilize
            await asyncio.sleep(0.2)
            # Force an immediate update to fetch the latest device state
            await self.coordinator.async_refresh()
            self.async_write_ha_state()

class HysenSlot1StartEnableSwitch(HysenEntity, SwitchEntity):
    """Representation of a Hysen Slot 1 Start Enable switch.

    Controls whether the start of schedule slot 1 is enabled.
    """

    def __init__(self, device_data):
        """Initialize the switch.

        Args:
            device_data: Dictionary containing device-specific data (e.g., mac, name, coordinator).
        """
        super().__init__(device_data["coordinator"], device_data)
        self._attr_unique_id = f"{device_data['mac']}_slot1_start_enable"
        self._attr_name = f"{device_data['name']} Slot 1 Start Enable"

    @property
    def is_on(self):
        """Return true if the switch is on.

        Returns:
            bool: True if slot 1 start is enabled, False otherwise.
        """
        return self.coordinator.data.get(DATA_KEY_SLOT1_START_ENABLE) == STATE_ON

    @property
    def icon(self):
        """Return the icon based on the switch state.

        Returns:
            str: The Material Design Icon (MDI) for the slot enable state.
        """
        return "mdi:calendar-clock" if self.is_on else "mdi:calendar-remove"

    async def async_turn_on(self, **kwargs):
        """Turn the switch on.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            None
        """
        _LOGGER.debug("[%s] Turning on slot 1 start", self._host)
        success = await self._async_try_command(
            "Error in set_daily_schedule",
            self.coordinator.device.set_daily_schedule,
            SLOT_ENABLED_HASS_TO_HYSEN[True],
            None, None,
            None,
            None, None,
            None,
            None, None,
            None,
            None, None,
        )
        if success:
            # Delay to allow device to stabilize
            await asyncio.sleep(0.2)
            # Force an immediate update to fetch the latest device state
            await self.coordinator.async_refresh()
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            None
        """
        _LOGGER.debug("[%s] Turning off slot 1 start", self._host)
        success = await self._async_try_command(
            "Error in set_daily_schedule",
            self.coordinator.device.set_daily_schedule,
            SLOT_ENABLED_HASS_TO_HYSEN[False],
            None, None,
            None,
            None, None,
            None,
            None, None,
            None,
            None, None,
        )
        if success:
            # Delay to allow device to stabilize
            await asyncio.sleep(0.2)
            # Force an immediate update to fetch the latest device state
            await self.coordinator.async_refresh()
            self.async_write_ha_state()

    async def async_set_slot1_start_enable(self, slot1_start_enable):
        """Set the slot 1 start enable state.

        Args:
            slot1_start_enable: The state to set (on or off).

        Returns:
            None
        """
        _LOGGER.debug("[%s] Setting slot 1 start enable to %s", self._host, slot1_start_enable)
        success = await self._async_try_command(
            "Error in set_daily_schedule",
            self.coordinator.device.set_daily_schedule,
            SLOT_ENABLED_HASS_TO_HYSEN[slot1_start_enable == STATE_ON],
            None, None,
            None,
            None, None,
            None,
            None, None,
            None,
            None, None,
        )
        if success:
            # Delay to allow device to stabilize
            await asyncio.sleep(0.2)
            # Force an immediate update to fetch the latest device state
            await self.coordinator.async_refresh()
            self.async_write_ha_state()

class HysenSlot1StopEnableSwitch(HysenEntity, SwitchEntity):
    """Representation of a Hysen Slot 1 Stop Enable switch.

    Controls whether the stop of schedule slot 1 is enabled.
    """

    def __init__(self, device_data):
        """Initialize the switch.

        Args:
            device_data: Dictionary containing device-specific data (e.g., mac, name, coordinator).
        """
        super().__init__(device_data["coordinator"], device_data)
        self._attr_unique_id = f"{device_data['mac']}_slot1_stop_enable"
        self._attr_name = f"{device_data['name']} Slot 1 Stop Enable"

    @property
    def is_on(self):
        """Return true if the switch is on.

        Returns:
            bool: True if slot 1 stop is enabled, False otherwise.
        """
        return self.coordinator.data.get(DATA_KEY_SLOT1_STOP_ENABLE) == STATE_ON

    @property
    def icon(self):
        """Return the icon based on the switch state.

        Returns:
            str: The Material Design Icon (MDI) for the slot enable state.
        """
        return "mdi:calendar-clock" if self.is_on else "mdi:calendar-remove"

    async def async_turn_on(self, **kwargs):
        """Turn the switch on.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            None
        """
        _LOGGER.debug("[%s] Turning on slot 1 stop", self._host)
        success = await self._async_try_command(
            "Error in set_daily_schedule",
            self.coordinator.device.set_daily_schedule,
            None,
            None, None,
            SLOT_ENABLED_HASS_TO_HYSEN[True],
            None, None,
            None,
            None, None,
            None,
            None, None,
        )
        if success:
            # Delay to allow device to stabilize
            await asyncio.sleep(0.2)
            # Force an immediate update to fetch the latest device state
            await self.coordinator.async_refresh()
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            None
        """
        _LOGGER.debug("[%s] Turning off slot 1 stop", self._host)
        success = await self._async_try_command(
            "Error in set_daily_schedule",
            self.coordinator.device.set_daily_schedule,
            None,
            None, None,
            SLOT_ENABLED_HASS_TO_HYSEN[False],
            None, None,
            None,
            None, None,
            None,
            None, None,
        )
        if success:
            # Delay to allow device to stabilize
            await asyncio.sleep(0.2)
            # Force an immediate update to fetch the latest device state
            await self.coordinator.async_refresh()
            self.async_write_ha_state()

    async def async_set_slot1_stop_enable(self, slot1_stop_enable):
        """Set the slot 1 stop enable state.

        Args:
            slot1_stop_enable: The state to set (on or off).

        Returns:
            None
        """
        _LOGGER.debug("[%s] Setting slot 1 stop enable to %s", self._host, slot1_stop_enable)
        success = await self._async_try_command(
            "Error in set_daily_schedule",
            self.coordinator.device.set_daily_schedule,
            None,
            None, None,
            SLOT_ENABLED_HASS_TO_HYSEN[slot1_stop_enable == STATE_ON],
            None, None,
            None,
            None, None,
            None,
            None, None,
        )
        if success:
            # Delay to allow device to stabilize
            await asyncio.sleep(0.2)
            # Force an immediate update to fetch the latest device state
            await self.coordinator.async_refresh()
            self.async_write_ha_state()

class HysenSlot2StartEnableSwitch(HysenEntity, SwitchEntity):
    """Representation of a Hysen Slot 2 Start Enable switch.

    Controls whether the start of schedule slot 2 is enabled.
    """

    def __init__(self, device_data):
        """Initialize the switch.

        Args:
            device_data: Dictionary containing device-specific data (e.g., mac, name, coordinator).
        """
        super().__init__(device_data["coordinator"], device_data)
        self._attr_unique_id = f"{device_data['mac']}_slot2_start_enable"
        self._attr_name = f"{device_data['name']} Slot 2 Start Enable"

    @property
    def is_on(self):
        """Return true if the switch is on.

        Returns:
            bool: True if slot 2 start is enabled, False otherwise.
        """
        return self.coordinator.data.get(DATA_KEY_SLOT2_START_ENABLE) == STATE_ON

    @property
    def icon(self):
        """Return the icon based on the switch state.

        Returns:
            str: The Material Design Icon (MDI) for the slot enable state.
        """
        return "mdi:calendar-clock" if self.is_on else "mdi:calendar-remove"

    async def async_turn_on(self, **kwargs):
        """Turn the switch on.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            None
        """
        _LOGGER.debug("[%s] Turning on slot 2 start", self._host)
        success = await self._async_try_command(
            "Error in set_daily_schedule",
            self.coordinator.device.set_daily_schedule,
            None,
            None, None,
            None,
            None, None,
            SLOT_ENABLED_HASS_TO_HYSEN[True],
            None, None,
            None,
            None, None,
        )
        if success:
            # Delay to allow device to stabilize
            await asyncio.sleep(0.2)
            # Force an immediate update to fetch the latest device state
            await self.coordinator.async_refresh()
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            None
        """
        _LOGGER.debug("[%s] Turning off slot 2 start", self._host)
        success = await self._async_try_command(
            "Error in set_daily_schedule",
            self.coordinator.device.set_daily_schedule,
            None,
            None, None,
            None,
            None, None,
            SLOT_ENABLED_HASS_TO_HYSEN[False],
            None, None,
            None,
            None, None,
        )
        if success:
            # Delay to allow device to stabilize
            await asyncio.sleep(0.2)
            # Force an immediate update to fetch the latest device state
            await self.coordinator.async_refresh()
            self.async_write_ha_state()

    async def async_set_slot2_start_enable(self, slot2_start_enable):
        """Set the slot 2 start enable state.

        Args:
            slot2_start_enable: The state to set (on or off).

        Returns:
            None
        """
        _LOGGER.debug("[%s] Setting slot 2 start enable to %s", self._host, slot2_start_enable)
        success = await self._async_try_command(
            "Error in set_daily_schedule",
            self.coordinator.device.set_daily_schedule,
            None,
            None, None,
            None,
            None, None,
            SLOT_ENABLED_HASS_TO_HYSEN[slot2_start_enable == STATE_ON],
            None, None,
            None,
            None, None,
        )
        if success:
            # Delay to allow device to stabilize
            await asyncio.sleep(0.2)
            # Force an immediate update to fetch the latest device state
            await self.coordinator.async_refresh()
            self.async_write_ha_state()

class HysenSlot2StopEnableSwitch(HysenEntity, SwitchEntity):
    """Representation of a Hysen Slot 2 Stop Enable switch.

    Controls whether the stop of schedule slot 2 is enabled.
    """

    def __init__(self, device_data):
        """Initialize the switch.

        Args:
            device_data: Dictionary containing device-specific data (e.g., mac, name, coordinator).
        """
        super().__init__(device_data["coordinator"], device_data)
        self._attr_unique_id = f"{device_data['mac']}_slot2_stop_enable"
        self._attr_name = f"{device_data['name']} Slot 2 Stop Enable"

    @property
    def is_on(self):
        """Return true if the switch is on.

        Returns:
            bool: True if slot 2 stop is enabled, False otherwise.
        """
        return self.coordinator.data.get(DATA_KEY_SLOT2_STOP_ENABLE) == STATE_ON

    @property
    def icon(self):
        """Return the icon based on the switch state.

        Returns:
            str: The Material Design Icon (MDI) for the slot enable state.
        """
        return "mdi:calendar-clock" if self.is_on else "mdi:calendar-remove"

    async def async_turn_on(self, **kwargs):
        """Turn the switch on.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            None
        """
        _LOGGER.debug("[%s] Turning on slot 2 stop", self._host)
        success = await self._async_try_command(
            "Error in set_daily_schedule",
            self.coordinator.device.set_daily_schedule,
            None,
            None, None,
            None,
            None, None,
            None,
            None, None,
            SLOT_ENABLED_HASS_TO_HYSEN[True],
            None, None,
        )
        if success:
            # Delay to allow device to stabilize
            await asyncio.sleep(0.2)
            # Force an immediate update to fetch the latest device state
            await self.coordinator.async_refresh()
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            None
        """
        _LOGGER.debug("[%s] Turning off slot 2 stop", self._host)
        success = await self._async_try_command(
            "Error in set_daily_schedule",
            self.coordinator.device.set_daily_schedule,
            None,
            None, None,
            None,
            None, None,
            None,
            None, None,
            SLOT_ENABLED_HASS_TO_HYSEN[False],
            None, None,
        )
        if success:
            # Delay to allow device to stabilize
            await asyncio.sleep(0.2)
            # Force an immediate update to fetch the latest device state
            await self.coordinator.async_refresh()
            self.async_write_ha_state()

    async def async_set_slot2_stop_enable(self, slot2_stop_enable):
        """Set the slot 2 stop enable state.

        Args:
            slot2_stop_enable: The state to set (on or off).

        Returns:
            None
        """
        _LOGGER.debug("[%s] Setting slot 2 stop enable to %s", self._host, slot2_stop_enable)
        success = await self._async_try_command(
            "Error in set_daily_schedule",
            self.coordinator.device.set_daily_schedule,
            None,
            None, None,
            None,
            None, None,
            None,
            None, None,
            SLOT_ENABLED_HASS_TO_HYSEN[slot2_stop_enable == STATE_ON],
            None, None,
        )
        if success:
            # Delay to allow device to stabilize
            await asyncio.sleep(0.2)
            # Force an immediate update to fetch the latest device state
            await self.coordinator.async_refresh()
            self.async_write_ha_state()