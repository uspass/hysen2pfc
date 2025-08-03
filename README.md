# Hysen 2 Pipe Fan Coil Integration

This integration enables control of Hysen 2 Pipe Fan Coil thermostats (model HY03AC-1-Wifi and derivatives) within Home Assistant. It supports the default Thermostat card and custom Lovelace configurations, providing extensive control over HVAC modes, fan settings, temperature limits, and scheduling.

## Features

- **HVAC Modes**: Supports `off`, `cool`, `heat`, and `fan_only` modes. The `fan_only` mode is available when the fan mode is set to `low`, `medium`, or `high`.
- **Temperature Control**: Adjust target temperature (10–40°C), cooling/heating min/max temperatures, and calibration (-5.0 to 5.0°C).
- **Fan Control**: Set fan modes to `low`, `medium`, `high`, or `auto`. In `fan_only` mode, only `low`, `medium`, and `high` are available.
- **Scheduling**: Configure weekly schedules (`Today`, `Workdays`, `Sixdays`, `Fullweek`) and two daily periods for automated operation.
- **Additional Features**: Key lock (`unlocked`, `power_unlocked`, `locked`), frost protection, hysteresis (0.5°C or 1°C), and device time synchronization.
- **Services**: Comprehensive services for automation, including `set_key_lock`, `set_hvac_mode`, `set_temperature`, `set_schedule`, and more.

## Installation

HACS installation is not yet supported. To install the Hysen 2 Pipe Fan Coil integration manually:

1. **Download the Integration**:
   - Clone or download the repository from [GitHub](https://github.com/uspass/hysen2pfc).
   - Copy the `hysen2pfc` folder to your Home Assistant configuration directory under `custom_components/`.

2. **Restart Home Assistant**:
   - Restart Home Assistant to load the integration.

3. **Add the Integration**:
   - Go to **Settings > Devices & Services > Add Integration** in Home Assistant.
   - Search for and select "Hysen 2 Pipe Fan Coil".
   - Enter the device’s IP address, MAC address (format: XX:XX:XX:XX:XX:XX), and optional settings (name, timeout, clock sync, sync hour).

## Configuration

Configuration is managed via the Home Assistant UI. Required fields include:

- **IP Address**: The device’s network IP (e.g., `192.168.1.100`).
- **MAC Address**: The device’s MAC address (e.g., `XX:XX:XX:XX:XX:XX`).
- **Optional Settings**:
  - **Name**: Custom name (default: `Hysen 2 Pipe Fan Coil Thermostat`).
  - **Timeout**: Connection timeout in seconds (default: 10).
  - **Sync Clock**: Enable/disable automatic clock sync (default: enabled).
  - **Sync Hour**: Hour for daily clock sync (0–23, default: 4).

Example configuration (for reference, entered via UI):

```yaml
host: 192.168.1.100
mac: XX:XX:XX:XX:XX:XX
name: Living Room Thermostat
timeout: 10
sync_clock: true
sync_hour: 4
```

## Device Behavior

- **HVAC Modes**: When fan mode is `auto`, available modes are `off`, `cool`, and `heat`. When set to `low`, `medium`, or `high`, `fan_only` is also available.
- **Temperature Limits**: Independent min/max temperatures for cooling (10–40°C) and heating (10–40°C) modes.
- **Fan Modes**: In `fan_only` mode, only `low`, `medium`, and `high` are supported. In other modes, `auto` is also available.
- **Schedules**: Supports four preset schedules and two daily periods for automated control.

## Lovelace Card

Use the default Thermostat card for basic control:

```yaml
type: thermostat
entity: climate.hysen_2_pipe_fan_coil
```

To display additional attributes (e.g., `key_lock`, `weekly_schedule`, `hysteresis`), use an entities card:

```yaml
type: entities
entities:
  - entity: climate.hysen_2_pipe_fan_coil
    type: attribute
    attribute: key_lock
  - entity: climate.hysen_2_pipe_fan_coil
    type: attribute
    attribute: weekly_schedule
  - entity: climate.hysen_2_pipe_fan_coil
    type: attribute
    attribute: hysteresis
```

## Services

The integration provides services for advanced control, usable in automations or scripts. Examples:

- **Set Key Lock**:
  ```yaml
  service: hysen2pfc.set_key_lock
  target:
    entity_id: climate.hysen_2_pipe_fan_coil
  data:
    key_lock: locked
  ```

- **Set HVAC Mode**:
  ```yaml
  service: hysen2pfc.set_hvac_mode
  target:
    entity_id: climate.hysen_2_pipe_fan_coil
  data:
    hvac_mode: cool
  ```

- **Set Temperature**:
  ```yaml
  service: hysen2pfc.set_temperature
  target:
    entity_id: climate.hysen_2_pipe_fan_coil
  data:
    temperature: 22
  ```

- **Set Cooling Minimum Temperature**:
  ```yaml
  service: hysen2pfc.set_cooling_min_temp
  target:
    entity_id: climate.hysen_2_pipe_fan_coil
  data:
    min_temp: 16
  ```

- **Set Schedule**:
  ```yaml
  service: hysen2pfc.set_schedule
  target:
    entity_id: climate.hysen_2_pipe_fan_coil
  data:
    weekly_schedule: Workdays
    period1_enabled: true
    period1_start_time: "08:00"
    period1_end_time: "17:00"
    period2_enabled: false
  ```

See `services.yaml` for a complete list of services and parameters.

## Supported Services

- `set_key_lock`: Options: `unlocked`, `power_unlocked`, `locked`.
- `set_hvac_mode`: Options: `off`, `heat`, `cool`, `fan_only`.
- `set_temperature`: Range: 10–40°C.
- `turn_on` / `turn_off`: Power control.
- `set_hysteresis`: Options: 0.5°C, 1°C.
- `set_calibration`: Range: -5.0 to 5.0°C.
- `set_cooling_max_temp` / `set_cooling_min_temp`: Range: 10–40°C.
- `set_heating_max_temp` / `set_heating_min_temp`: Range: 10–40°C.
- `set_fan_control`: Options: `on`, `off`.
- `set_frost_protection`: Options: `on`, `off`.
- `set_time`: Set device time or sync to system time.
- `set_schedule`: Configure weekly/daily schedules.
- `set_fan_mode`: Options: `low`, `medium`, `high`, `auto`.

## Requirements

- Python library: `hysen==0.4.12`.

## Support

For issues or feature requests, open a ticket on the [GitHub repository](https://github.com/uspass/hysen2pfc/issues).

## License

Licensed under the MIT License. See `LICENSE` for details.
