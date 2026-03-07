# 🧺 Appliance Tracker for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/wroadd/ha-appliance-tracker)](https://github.com/wroadd/ha-appliance-tracker/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Know exactly when your laundry, dishes, or dryer are done.** No more guessing, no more forgotten loads.

Appliance Tracker monitors power consumption from any smart plug (Shelly, Zigbee, Z-Wave, etc.) and detects when your washing machine, dryer, or dishwasher starts, runs, and completes a cycle — then notifies you.

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/I2I11VKC85)

---

## ✨ Features

- **Smart state detection** — Tracks `Idle → Running → Finishing → Complete` using power consumption patterns
- **Appliance presets** — Optimized defaults for washing machines, dryers, and dishwashers
- **Configurable thresholds** — Fine-tune start/stop wattage and timing delays per appliance
- **Cycle history** — Tracks cycle count and last cycle duration, persisted across restarts
- **Binary sensor** — Simple on/off "Running" sensor for easy automations
- **Event firing** — Fires `appliance_tracker_cycle_complete` event for advanced automations
- **Multi-appliance** — Track as many appliances as you have smart plugs
- **Config flow UI** — Full GUI setup, no YAML needed
- **HACS compatible** — Easy install through HACS

## 📊 Created entities

For each configured appliance, the integration creates:

| Entity | Type | Description |
|--------|------|-------------|
| **State** | `sensor` | Current state: `idle`, `running`, `finishing`, `complete` |
| **Current power** | `sensor` | Real-time power reading (W) |
| **Cycle count** | `sensor` | Total completed cycles (persisted) |
| **Last cycle duration** | `sensor` | Duration of the last cycle (minutes) |
| **Last cycle energy** | `sensor` | Energy used in the last cycle (kWh) |
| **Running** | `binary_sensor` | `on` when appliance is running or finishing |

## 🔄 State machine

```
                    power ≥ start_threshold
                    (for start_delay)
    ┌──────┐  ─────────────────────────►  ┌─────────┐
    │ IDLE │                              │ RUNNING │
    └──────┘  ◄────────────────────────   └─────────┘
        ▲                                      │
        │                                      │ power < stop_threshold
        │                                      │ (for stop_delay)
        │                                      ▼
    ┌──────────┐  ◄──────────────────  ┌───────────┐
    │ COMPLETE │   power < stop for    │ FINISHING  │
    └──────────┘   finishing_delay     └───────────┘
                                            │
        │ auto-reset                        │ power ≥ start_threshold
        │ (complete_timeout)                │ → back to RUNNING
        ▼                                   │
      IDLE                                  ▼
                                         RUNNING
```

The **Finishing** state handles mid-cycle pauses (e.g., a washing machine pausing between wash and spin). If power spikes back up, it returns to Running instead of falsely completing.

## 📋 Default thresholds

| Appliance | Start threshold | Stop threshold |
|-----------|----------------|----------------|
| Washing machine | 10 W | 5 W |
| Dryer | 50 W | 10 W |
| Dishwasher | 10 W | 5 W |
| Custom | 10 W | 5 W |

## 🚀 Installation

### HACS (recommended)

1. Open HACS in your Home Assistant instance
2. Click **Integrations**
3. Click the **⋮** menu → **Custom repositories**
4. Add `https://github.com/wroadd/ha-appliance-tracker` as an **Integration**
5. Search for "Appliance Tracker" and install
6. Restart Home Assistant

### Manual installation

1. Download the [latest release](https://github.com/wroadd/ha-appliance-tracker/releases)
2. Copy the `custom_components/appliance_tracker` folder to your `config/custom_components/` directory
3. Restart Home Assistant

## ⚙️ Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Appliance Tracker**
3. Select your appliance type and power sensor:

   <!-- Screenshot placeholder: config_step1.png -->
   *Step 1: Name your appliance, select its type, and choose the power sensor.*

4. Adjust thresholds if needed (smart defaults are pre-filled):

   <!-- Screenshot placeholder: config_step2.png -->
   *Step 2: Fine-tune power thresholds and timing delays.*

5. Done! Your appliance will appear as a new device with all sensors.

## 🔔 Automation examples

### Notify when washing is done

```yaml
automation:
  - alias: "Washing machine done"
    trigger:
      - platform: state
        entity_id: sensor.washing_machine_state
        to: "complete"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "🧺 Washing done!"
          message: "Your laundry is ready. Cycle took {{ state_attr('sensor.washing_machine_last_cycle_duration', 'state') }} minutes."
```

### Using the event trigger

```yaml
automation:
  - alias: "Any appliance done"
    trigger:
      - platform: event
        event_type: appliance_tracker_cycle_complete
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "✅ {{ trigger.event.data.appliance_name }} done!"
          message: "Cycle #{{ trigger.event.data.cycle_count }} completed in {{ trigger.event.data.duration_minutes }} minutes."
```

### Flash a light when dryer is done

```yaml
automation:
  - alias: "Dryer done - flash light"
    trigger:
      - platform: state
        entity_id: binary_sensor.dryer_running
        from: "on"
        to: "off"
    action:
      - service: light.turn_on
        target:
          entity_id: light.laundry_room
        data:
          flash: short
```

## 🔧 Tips

- **Finding the right thresholds:** Check your power sensor's history graph while running a cycle. The start threshold should be above the standby power, and the stop threshold should catch the end-of-cycle drop.
- **Shelly plugs** work great — they report power with ~1 second resolution.
- **Zigbee smart plugs** (like IKEA TRÅDFRI, Sonoff ZBMINI) also work well with Zigbee2MQTT.
- **The finishing delay** is key for washing machines that pause between wash and spin cycles. Set it long enough to bridge those pauses (default 3 minutes).

## 🤝 Contributing

Contributions are welcome! Please open an issue first to discuss what you'd like to change.

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/I2I11VKC85)
