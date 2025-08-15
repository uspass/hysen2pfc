# Hysen 2 Pipe Fan Coil Controller Integration for Home Assistant

This Home Assistant integration provides support for the Hysen HY03AC-1-Wifi 2 Pipe Fan Coil Controller and its derivatives, which are based on Broadlink technology (not Tuya). It enables control and monitoring of HVAC modes, fan modes, temperature settings, scheduling, and other advanced features through Home Assistant.

## Features

- **Climate Control**: Supports HVAC modes (`heat`, `cool`, `fan_only`, `off`), fan modes (`low`, `medium`, `high`, `auto`), and temperature settings (10–40°C).
- **Binary Sensor**: Monitors valve state (`open` or `closed`).
- **Button**: Synchronizes the device time to the current system time, including seconds.
- **Number**: Adjusts temperature calibration (-5.0 to 5.0°C) and dynamic min/max temperatures based on HVAC mode.
- **Select**: Configures hysteresis (0.5°C or 1.0°C) and key lock (Unlocked, Locked Except Power, Locked).
- **Sensor**: Monitors room temperature, firmware version, valve on duration, and device time/weekday.
- **Switch**: Controls fan enable/disable, frost protection, and schedule slot enable states.
- **Time**: Sets start/stop times for two programmable schedule slots.
- **Advanced Features**:
  - Key lock (Unlocked, Locked Except Power, Locked).
  - Temperature calibration (-5.0 to 5.0°C).
  - Hysteresis settings (0.5°C or 1.0°C).
  - Frost protection and fan control (on/off).
  - Weekly scheduling with two programmable time slots.
  - Device time and weekday synchronization.
- **Custom Services**: Provides services to set HVAC mode, fan mode, preset mode, temperature, and other device parameters.
- **Zeroconf Discovery**: Automatically detects Hysen devices on the network using Broadlink's protocol. (work in progress)
- **Local Polling**: Uses local network communication via Broadlink protocol for reliable control and updates.
- **Lovelace Thermostat Card**: Integrates seamlessly with the default Home Assistant Thermostat card in Lovelace, providing a user-friendly interface to control HVAC modes, set temperatures, and adjust fan modes directly from the dashboard.

## Installation

1. **Via HACS (Home Assistant Community Store)**:
   - Add this repository as a custom repository in HACS:
     - URL: `https://github.com/uspass/hysen2pfc`
     - Category: Integration
   - Search for "Hysen 2 Pipe Fan Coil" in HACS and install it.
   - Restart Home Assistant after installation.

2. **Manual Installation**:
   - Copy the `hysen2pfc` folder to your Home Assistant `custom_components` directory (e.g., `config/custom_components/hysen2pfc`).
   - Restart Home Assistant.

## Configuration

### Via Home Assistant UI
1. After installation, go to **Settings > Devices & Services** in Home Assistant.
2. Click **Add Integration** and search for "Hysen 2 Pipe Fan Coil".
3. If the device is discovered via Zeroconf (using Broadlink protocol), confirm the device details (host, MAC, name).
4. Alternatively, manually enter the device's IP address, MAC address, name, and timeout (default: 10 seconds).
5. Submit the configuration to add the device.

### Example Configuration
```yaml
hysen2pfc:
  host: "192.168.1.100"
  mac: "00:1A:2B:3C:4D:5E"
  name: "Living Room Hysen"
  timeout: 10
```

## Supported Platforms

- **Climate**: Main entity for controlling HVAC modes, fan modes, temperature, and presets.
- **Binary Sensor**: Valve state sensor (`open` or `closed`).
- **Button**: Device time synchronization to current system time.
- **Number**: Temperature calibration and dynamic min/max temperature settings based on HVAC mode.
- **Select**: Key lock and hysteresis settings.
- **Sensor**: Room temperature, firmware version, valve on duration, and device time/weekday.
- **Switch**: Fan control, frost protection, and schedule slot enable states.
- **Time**: Scheduling slots for start/stop times.

## Lovelace Thermostat Card

The integration works out-of-the-box with the default Home Assistant Thermostat card in Lovelace. To add the Thermostat card to your dashboard:

1. Go to your Lovelace dashboard and click **Edit Dashboard**.
2. Click **Add Card** and select **Thermostat**.
3. Configure the card by selecting the Hysen climate entity (e.g., `climate.living_room_hysen`).
4. Customize the card settings as needed (e.g., show/hide fan modes or temperature controls).
5. Save the card to display the thermostat interface, allowing you to adjust the target temperature, HVAC mode, and fan mode directly from the dashboard.

Example Lovelace configuration:
```yaml
type: thermostat
entity: climate.living_room_hysen
name: Living Room Thermostat
```

## Additional Lovelace Cards for Other Entities

To fully leverage the integration's features, you can add Lovelace cards for the additional entities:

- **Entities Card for Switches and Selects**:
  Display and control switches (e.g., fan control, frost protection, schedule slots) and select entities (e.g., key lock, hysteresis).
  ```yaml
  type: entities
  entities:
    - entity: switch.living_room_hysen_fan_control
    - entity: switch.living_room_hysen_frost_protection
    - entity: select.living_room_hysen_key_lock
    - entity: select.living_room_hysen_hysteresis
    - entity: switch.living_room_hysen_slot1_start_enable
    - entity: switch.living_room_hysen_slot1_stop_enable
    - entity: switch.living_room_hysen_slot2_start_enable
    - entity: switch.living_room_hysen_slot2_stop_enable
  title: Hysen Controls
  ```

- **Entities Card for Time Entities**:
  Configure schedule slot start/stop times.
  ```yaml
  type: entities
  entities:
    - entity: time.living_room_hysen_slot1_start_time
    - entity: time.living_room_hysen_slot1_stop_time
    - entity: time.living_room_hysen_slot2_start_time
    - entity: time.living_room_hysen_slot2_stop_time
  title: Hysen Schedule
  ```

- **Entities Card for Sensors and Button**:
  Monitor sensor values (e.g., valve on duration, device time) and trigger the time synchronization button.
  ```yaml
  type: entities
  entities:
    - entity: sensor.living_room_hysen_time_valve_on
    - entity: sensor.living_room_hysen_device_time
    - entity: button.living_room_hysen_device_time_now
  title: Hysen Sensors
  ```

- **Number Slider for Calibration and Temperature Limits**:
  Adjust temperature calibration and min/max temperatures.
  ```yaml
  type: entities
  entities:
    - entity: number.living_room_hysen_sensor_calibration
      name: Calibration
    - entity: number.living_room_hysen_max_temp
      name: Max Temperature
    - entity: number.living_room_hysen_min_temp
      name: Min Temperature
  title: Hysen Temperature Settings
  ```

## Services

The integration provides custom services to control the device. Below are some key services:

- **`hysen2pfc.set_hvac_mode`**:
  - Sets the HVAC mode (`off`, `heat`, `cool`, `fan_only`).
  - Example:
    ```yaml
    service: hysen2pfc.set_hvac_mode
    target:
      entity_id: climate.living_room_hysen
    data:
      hvac_mode: heat
    ```

- **`hysen2pfc.set_fan_mode`**:
  - Sets the fan mode (`low`, `medium`, `high`, `auto`).
  - Example:
    ```yaml
    service: hysen2pfc.set_fan_mode
    data:
      entity_id: climate.living_room_hysen
      fan_mode: low
    ```

- **`hysen2pfc.set_temperature`**:
  - Sets the target temperature (10–40°C).
  - Example:
    ```yaml
    service: hysen2pfc.set_temperature
    target:
      entity_id: climate.living_room_hysen
    data:
      temperature: 22
    ```

- **`hysen2pfc.set_preset_mode`**:
  - Sets the preset mode (`Today`, `Workdays`, `Sixdays`, `Fullweek`).
  - Example:
    ```yaml
    service: hysen2pfc.set_preset_mode
    data:
      entity_id: climate.living_room_hysen
      preset_mode: Workdays
    ```

- **`hysen2pfc.set_time`**:
  - Sets the device time and weekday.
  - Example:
    ```yaml
    service: hysen2pfc.set_time
    data:
      entity_id: button.living_room_hysen_device_time_now
      device_time: "14:30:00"
      device_weekday: 1
    ```

- **`hysen2pfc.set_hysteresis`**:
  - Sets the hysteresis value (`0.5` or `1.0`).
  - Example:
    ```yaml
    service: hysen2pfc.set_hysteresis
    data:
      entity_id: select.living_room_hysen_hysteresis
      hysteresis: "0.5"
    ```

- **`hysen2pfc.set_slot1_start_time`**:
  - Sets the start time for schedule slot 1.
  - Example:
    ```yaml
    service: hysen2pfc.set_slot1_start_time
    data:
      entity_id: time.living_room_hysen_slot1_start_time
      slot1_start_time: "08:00"
    ```

For a full list of services, refer to `services.yaml` in the repository.

## Requirements

- Home Assistant 2023.11 or later.
- Python package: `hysen==0.4.12` (automatically installed).

## Known Limitations

- The integration relies on local network communication via Broadlink protocol and requires the device to be accessible on the network.
- The `fan_only` HVAC mode is not supported when the fan mode is set to `auto`. Set the fan mode to `low`, `medium`, or `high` first.
- The `auto` fan mode is not supported when the HVAC mode is set to `fan_only`. Set the HVAC mode to `heat` or `cool` first.
- The integration polls the device every 30 seconds to update the state.
- This integration is designed for Hysen devices using Broadlink protocol (e.g., HY03AC-1-Wifi). Hysen models with Tuya firmware (e.g., HY03AC-4-Wifi) are not supported.

## Debugging

To enable debug logging for this integration:
1. Add the following to your Home Assistant `configuration.yaml`:
   ```yaml
   logger:
     default: info
     logs:
       custom_components.hysen2pfc: debug
   ```
2. Restart Home Assistant to apply the changes.

## Contributing

Contributions are welcome! Please:
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m 'Add your feature'`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a pull request.

## Issues

Report bugs or request features via the [GitHub Issues page](https://github.com/uspass/hysen2pfc/issues).

## License

This integration is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Credits

Developed by [@uspass](https://github.com/uspass). Thanks to the Home Assistant community for their support and contributions.
