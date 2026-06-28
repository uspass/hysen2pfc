"""
DataUpdateCoordinator for the Hysen 2 Pipe Fan Coil integration.

The coordinator is the single point of contact with the physical device.
All platform entities share one coordinator instance per device and receive
state updates through HA's listener mechanism rather than by polling the
device individually.
"""

import asyncio
import logging
from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import (
    DOMAIN,
    DATA_KEY_FWVERSION,
    DATA_KEY_KEY_LOCK,
    DATA_KEY_VALVE_STATE,
    DATA_KEY_POWER_STATE,
    DATA_KEY_HVAC_MODE,
    DATA_KEY_HVAC_MODES,
    DATA_KEY_FAN_MODE,
    DATA_KEY_FAN_MODES,
    DATA_KEY_HVAC_ACTION,
    DATA_KEY_CURRENT_TEMP,
    DATA_KEY_TARGET_TEMP,
    DATA_KEY_HYSTERESIS,
    DATA_KEY_CALIBRATION,
    DATA_KEY_MIN_TEMP,
    DATA_KEY_MAX_TEMP,
    DATA_KEY_COOLING_MAX_TEMP,
    DATA_KEY_COOLING_MIN_TEMP,
    DATA_KEY_HEATING_MAX_TEMP,
    DATA_KEY_HEATING_MIN_TEMP,
    DATA_KEY_FAN_CONTROL,
    DATA_KEY_FROST_PROTECTION,
    DATA_KEY_CLOCK_HOUR,
    DATA_KEY_CLOCK_MINUTE,
    DATA_KEY_CLOCK_SECOND,
    DATA_KEY_CLOCK_WEEKDAY,
    DATA_KEY_PRESET_MODE,
    DATA_KEY_SLOT1_START_ENABLE,
    DATA_KEY_SLOT1_START_TIME,
    DATA_KEY_SLOT1_STOP_ENABLE,
    DATA_KEY_SLOT1_STOP_TIME,
    DATA_KEY_SLOT2_START_ENABLE,
    DATA_KEY_SLOT2_START_TIME,
    DATA_KEY_SLOT2_STOP_ENABLE,
    DATA_KEY_SLOT2_STOP_TIME,
    DATA_KEY_TIME_VALVE_ON,
    HVACMode,
    HVACAction,
    STATE_OFF,
    STATE_OPEN,
    HVAC_MODES_NO_FAN,
    HVAC_MODES,
    HVAC_MODES_COOL,
    HVAC_MODES_HEAT,
    HVAC_MODES_FAN_ONLY,
    FAN_AUTO,
    FAN_MODES_MANUAL,
    FAN_MODES,
    MODE_HYSEN_TO_HASS,
    FAN_HYSEN_TO_HASS,
    PRESET_HYSEN_TO_HASS,
    KEY_LOCK_HYSEN_TO_HASS,
    VALVE_STATE_HYSEN_TO_HASS,
    POWER_STATE_HYSEN_TO_HASS,
    SLOT_ENABLED_HYSEN_TO_HASS,
    HYSTERESIS_HYSEN_TO_HASS,
    FAN_CONTROL_HYSEN_TO_HASS,
    FROST_PROTECTION_HYSEN_TO_HASS,
)

_LOGGER = logging.getLogger(__name__)

# Number of additional attempts after the first failure before giving up.
_RETRY_COUNT = 2
# Base delay between retries in seconds; multiplied by (attempt + 1) for
# simple exponential backoff: 0.5 s, 1.0 s.
_RETRY_DELAY = 0.5


class HysenCoordinator(DataUpdateCoordinator):
    """Coordinator that polls the Hysen device and distributes data to entities.

    Fetches the full device status on every update interval and translates
    Hysen library constants into HA-compatible values. Derived state (e.g.
    the currently applicable HVAC mode list, HVAC action) is computed here
    so that entity classes remain thin.

    Transient network errors are retried up to _RETRY_COUNT times before
    raising UpdateFailed, which marks all entities as unavailable.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        device,
        host: str,
        config_entry,
        update_interval: int = 30,
    ) -> None:
        """Initialise the coordinator.

        Args:
            hass: The Home Assistant instance.
            device: A Hysen2PipeFanCoilDevice instance for the physical device.
            host: IP address string used for logging.
            config_entry: The ConfigEntry this coordinator belongs to; stored
                by DataUpdateCoordinator as self.config_entry.
            update_interval: Polling interval in seconds (default 30).
        """
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{host}",
            update_interval=timedelta(seconds=update_interval),
            config_entry=config_entry,
        )
        self.device = device
        self.host = host

    async def _async_update_data(self) -> dict:
        """Fetch and translate the full device status.

        Runs the blocking get_device_status call in the executor and maps
        all raw Hysen values to HA-compatible types. Retries up to
        _RETRY_COUNT times on failure before raising UpdateFailed.

        Returns:
            A dict keyed by DATA_KEY_* constants containing the current
            device state ready for consumption by entity properties.

        Raises:
            UpdateFailed: If communication with the device fails on all
                attempts, marking all entities as unavailable.
        """
        _LOGGER.debug("Fetching data for device at %s", self.host)
        last_exc: Exception | None = None

        for attempt in range(_RETRY_COUNT + 1):
            try:
                # get_device_status is blocking (UDP socket I/O) so it must
                # run in a thread pool executor to avoid stalling the event loop.
                await self.hass.async_add_executor_job(self.device.get_device_status)

                _power_state = POWER_STATE_HYSEN_TO_HASS.get(self.device.power_state)
                _operation_mode = MODE_HYSEN_TO_HASS.get(self.device.operation_mode)
                _valve_state = VALVE_STATE_HYSEN_TO_HASS.get(self.device.valve_state)

                # Derive hvac_mode: when the device is off the mode is HVACMode.OFF
                # regardless of the underlying operation mode stored in the device.
                if _power_state == STATE_OFF:
                    _hvac_mode = HVACMode.OFF
                else:
                    _hvac_mode = _operation_mode

                _fan_mode = FAN_HYSEN_TO_HASS.get(self.device.fan_mode)

                # Build the list of selectable HVAC modes for the climate card.
                # When the device is off, only the current operation mode is
                # shown so the user "turns on in the current mode" — this is
                # intentional UX to avoid inadvertently switching modes.
                if _power_state == STATE_OFF:
                    if _operation_mode == HVACMode.COOL:
                        _hvac_modes = HVAC_MODES_COOL
                    elif _operation_mode == HVACMode.HEAT:
                        _hvac_modes = HVAC_MODES_HEAT
                    else:
                        _hvac_modes = HVAC_MODES_FAN_ONLY
                else:
                    if _operation_mode == HVACMode.FAN_ONLY:
                        # All modes available in fan-only; no temperature target.
                        _hvac_modes = HVAC_MODES
                    elif _fan_mode == FAN_AUTO:
                        # FAN_ONLY is incompatible with auto fan — exclude it.
                        _hvac_modes = HVAC_MODES_NO_FAN
                    else:
                        _hvac_modes = HVAC_MODES

                # Fan-only mode does not support the auto fan speed.
                if _operation_mode == HVACMode.FAN_ONLY:
                    _fan_modes = FAN_MODES_MANUAL
                else:
                    _fan_modes = FAN_MODES

                # Derive the HVAC action (what the device is actually doing now).
                if _power_state == STATE_OFF:
                    _hvac_action = HVACAction.OFF
                else:
                    _hvac_action = HVACAction.IDLE
                    if _hvac_mode == HVACMode.HEAT and _valve_state == STATE_OPEN:
                        _hvac_action = HVACAction.HEATING
                    elif _hvac_mode == HVACMode.COOL and _valve_state == STATE_OPEN:
                        _hvac_action = HVACAction.COOLING
                    elif _hvac_mode == HVACMode.FAN_ONLY:
                        _hvac_action = HVACAction.FAN

                # Temperature limits depend on the active mode.
                _cooling_min_temp = self.device.cooling_min_temp
                _cooling_max_temp = self.device.cooling_max_temp
                _heating_min_temp = self.device.heating_min_temp
                _heating_max_temp = self.device.heating_max_temp
                if _hvac_mode == HVACMode.COOL:
                    _min_temp = _cooling_min_temp
                    _max_temp = _cooling_max_temp
                else:
                    _min_temp = _heating_min_temp
                    _max_temp = _heating_max_temp

                data = {
                    DATA_KEY_FWVERSION: self.device.fwversion,
                    DATA_KEY_KEY_LOCK: KEY_LOCK_HYSEN_TO_HASS.get(self.device.key_lock_type),
                    DATA_KEY_VALVE_STATE: _valve_state,
                    DATA_KEY_POWER_STATE: _power_state,
                    DATA_KEY_HVAC_MODE: _hvac_mode,
                    DATA_KEY_HVAC_MODES: _hvac_modes,
                    DATA_KEY_FAN_MODE: _fan_mode,
                    DATA_KEY_FAN_MODES: _fan_modes,
                    DATA_KEY_HVAC_ACTION: _hvac_action,
                    DATA_KEY_PRESET_MODE: PRESET_HYSEN_TO_HASS.get(self.device.schedule),
                    DATA_KEY_CURRENT_TEMP: self.device.room_temp,
                    DATA_KEY_TARGET_TEMP: self.device.target_temp,
                    DATA_KEY_HYSTERESIS: HYSTERESIS_HYSEN_TO_HASS.get(self.device.hysteresis),
                    DATA_KEY_CALIBRATION: self.device.calibration,
                    DATA_KEY_MIN_TEMP: _min_temp,
                    DATA_KEY_MAX_TEMP: _max_temp,
                    DATA_KEY_COOLING_MIN_TEMP: _cooling_min_temp,
                    DATA_KEY_COOLING_MAX_TEMP: _cooling_max_temp,
                    DATA_KEY_HEATING_MIN_TEMP: _heating_min_temp,
                    DATA_KEY_HEATING_MAX_TEMP: _heating_max_temp,
                    DATA_KEY_FAN_CONTROL: FAN_CONTROL_HYSEN_TO_HASS.get(self.device.fan_control),
                    DATA_KEY_FROST_PROTECTION: FROST_PROTECTION_HYSEN_TO_HASS.get(self.device.frost_protection),
                    DATA_KEY_CLOCK_HOUR: self.device.clock_hour,
                    DATA_KEY_CLOCK_MINUTE: self.device.clock_minute,
                    DATA_KEY_CLOCK_SECOND: self.device.clock_second,
                    DATA_KEY_CLOCK_WEEKDAY: self.device.clock_weekday,
                    # Slot enable values are stored as booleans (True/False).
                    DATA_KEY_SLOT1_START_ENABLE: SLOT_ENABLED_HYSEN_TO_HASS.get(self.device.period1_start_enabled),
                    DATA_KEY_SLOT1_START_TIME: f"{self.device.period1_start_hour}:{self.device.period1_start_min:02d}",
                    DATA_KEY_SLOT1_STOP_ENABLE: SLOT_ENABLED_HYSEN_TO_HASS.get(self.device.period1_end_enabled),
                    DATA_KEY_SLOT1_STOP_TIME: f"{self.device.period1_end_hour}:{self.device.period1_end_min:02d}",
                    DATA_KEY_SLOT2_START_ENABLE: SLOT_ENABLED_HYSEN_TO_HASS.get(self.device.period2_start_enabled),
                    DATA_KEY_SLOT2_START_TIME: f"{self.device.period2_start_hour}:{self.device.period2_start_min:02d}",
                    DATA_KEY_SLOT2_STOP_ENABLE: SLOT_ENABLED_HYSEN_TO_HASS.get(self.device.period2_end_enabled),
                    DATA_KEY_SLOT2_STOP_TIME: f"{self.device.period2_end_hour}:{self.device.period2_end_min:02d}",
                    DATA_KEY_TIME_VALVE_ON: self.device.time_valve_on,
                }
                _LOGGER.debug("Updated coordinator data for %s: %s", self.host, data)
                return data

            except Exception as exc:
                last_exc = exc
                if attempt < _RETRY_COUNT:
                    delay = _RETRY_DELAY * (attempt + 1)
                    _LOGGER.warning(
                        "Failed to fetch data for %s (attempt %d/%d): %s — retrying in %.1fs",
                        self.host, attempt + 1, _RETRY_COUNT + 1, exc, delay,
                    )
                    await asyncio.sleep(delay)
                else:
                    _LOGGER.error(
                        "Failed to update device data for %s after %d attempts: %s",
                        self.host, _RETRY_COUNT + 1, exc,
                    )

        raise UpdateFailed(f"Error communicating with device: {last_exc}") from last_exc
