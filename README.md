# Hysen 2 Pipe Fan Coil Integration

This integration allows you to control a Hysen 2 Pipe Fan Coil thermostat in Home Assistant using the default Thermostat card.
Support for Hysen HY03AC-1-Wifi device and derivative.

## Installation

Copy hysen2pfc folder to config\custom_components. Restart Home Assistant.

## Configuration

Add to configuration.yaml:
```
climate:
  - platform: hysen2pfc
    name: Living
    host: 192.168.100.150
    mac: '78:0f:77:ea:72:2d'
    timeout: 10
    sync_clock: true
    sync_hour: 4
```

timeout, sync_clock and sync_hour are optional.

## Device Behavior

The Hysen 2 Pipe Fan Coil device has specific behavior regarding HVAC modes settings:

- **HVAC Modes**: When the fan mode is set to `auto`, the available HVAC modes are `off`, `cool`, and `heat`. When the fan mode is set to `low`, `medium`, or `high`, the `fan_only` HVAC mode becomes available in addition to `off`, `cool`, and `heat`.

## Lovelace Card

Use the default Thermostat card in Lovelace to control the device:

```yaml
type: thermostat
entity: climate.hysen_2_pipe_fan_coil
```

To display additional attributes like `key_lock` or `weekly_schedule`, use an `entities` card:

```yaml
type: entities
entities:
  - entity: climate.hysen_2_pipe_fan_coil
    type: attribute
    attribute: key_lock
  - entity: climate.hysen_2_pipe_fan_coil
    type: attribute
    attribute: weekly_schedule
```

## Services

The integration provides several services to control the device, such as `set_key_lock`, `set_hvac_mode`, `set_temperature`, and `set_schedule`. These can be used in automations or scripts. For example:

```yaml
service: hysen2pfc.set_key_lock
target:
  entity_id: climate.hysen_2_pipe_fan_coil
data:
  key_lock: locked
```

To set distinct minimum temperatures for cooling and heating:

```yaml
service: hysen2pfc.set_cooling_min_temp
target:
  entity_id: climate.hysen_2_pipe_fan_coil
data:
  min_temp: 16

service: hysen2pfc.set_heating_min_temp
target:
  entity_id: climate.hysen_2_pipe_fan_coil
data:
  min_temp: 10
```

See `services.yaml` for a full list of available services and their parameters.

## Support

For issues, please open a ticket on the GitHub repository.
