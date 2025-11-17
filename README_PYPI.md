# Controme Scraper

**UNOFFICIAL** Python client library for [Controme Smart-Heat-OS](https://www.controme.com/) heating control systems.

> ⚠️ **DISCLAIMER**: This is an unofficial, community-developed library. It is NOT affiliated with, endorsed by, or supported by Controme GmbH. "Controme" and "Smart-Heat-OS" are trademarks of Controme GmbH.

## Features

- 🔐 **Session Management** - Automatic login and session handling with encryption
- 🌡️ **Temperature Control** - Read and set target temperatures for rooms
- 📊 **Real-time Data** - Access current temperatures, valve positions, and heating status
- 🏠 **Multi-House Support** - Manage multiple houses in one Controme system
- 📈 **System Metrics** - Retrieve heating demand, boiler status, and sensor data
- 🔧 **Complete Models** - Full Python dataclasses for all Controme entities

## Installation

```bash
pip install controme-scraper
```

## Quick Start

```python
from controme_scraper import ContromeController

# Initialize the controller
controller = ContromeController(
    host="http://192.168.1.10",
    username="your_username",
    password="your_password",
    house_id=1  # Optional, default is 1
)

# Get all rooms with real-time data
rooms = controller.get_rooms()
for room in rooms:
    print(f"{room.name}: {room.current_temperature}°C → {room.target_temperature}°C")
    if room.is_heating:
        print(f"  🔥 Heating (avg valve: {room.average_valve_position:.0f}%)")

# Set target temperature for a room
controller.web_client.set_room_temperature(room_id=1, temperature=22.5)

# Get sensors
sensors = controller.get_sensors()
for sensor in sensors:
    print(f"{sensor.name}: {sensor.value}{sensor.unit}")
```

## Core Components

### ContromeController

Main entry point for interacting with the Controme system.

```python
controller = ContromeController(host, username, password, house_id=1)

# Get structured data
rooms = controller.get_rooms()              # List[Room]
thermostats = controller.get_thermostats()  # List[Thermostat]
sensors = controller.get_sensors()          # List[Sensor]

# Access individual items
room = controller.get_room(room_id=1)       # Single Room
thermostat = controller.get_thermostat(device_num=1)  # Single Thermostat
```

### Models

All data is returned as typed Python dataclasses:

- **Room**: Complete room data with temperatures, valves, heating status
  - `current_temperature`, `target_temperature`, `offset_temperature`
  - `valve_positions`, `max_valve_positions`, `return_flow_temperatures`
  - `is_heating`, `average_valve_position`
- **Thermostat**: Thermostat device with configuration and status
  - `name`, `device_num`, `current_temperature`
  - `assigned_room_id`, `room_name`, `floor_name`
  - Full configuration options (12 parameters)
- **Sensor**: Temperature/humidity/brightness sensors
  - `name`, `value`, `unit`, `sensor_type`
  - Types: temperature, humidity, brightness, return_flow
- **Gateway**: System gateway for calculating heating demand
  - `system_average_valve_position`, `max_system_demand`
  - `rooms_heating_count`, `total_rooms`

### WebClient

Low-level API client for direct HTTP requests:

```python
client = controller.web_client

# Temperature control (0.5°C precision)
client.set_room_temperature(room_id=1, temperature=22.5)

# Get parsed data (returns Model objects)
rooms = client.get_rooms()                  # List[Room]
thermostats = client.get_thermostats()      # List[Thermostat]
sensors = client.get_sensors()              # List[Sensor]

# Get gateway hardware configuration
max_positions = client.get_gateway_hardware()  # dict[int, int]

# Get actuator configuration mappings
room_output_map, rl_output_map = client.get_actuator_config(house_id=1)
```

## Multi-House Support

If your Controme system manages multiple houses:

```python
# House 1
controller_house1 = ContromeController(host, user, password, house_id=1)
rooms_house1 = controller_house1.get_rooms()

# House 2
controller_house2 = ContromeController(host, user, password, house_id=2)
rooms_house2 = controller_house2.get_rooms()
```

## Session Management

Sessions are automatically managed and cached locally:
- Encrypted session storage
- Automatic re-authentication on expiry
- Session validation before requests

Session files are stored as: `{hash(username+password)}.session`

## Error Handling

```python
try:
    controller = ContromeController(host, username, password)
    rooms = controller.get_rooms()
except Exception as e:
    print(f"Connection failed: {e}")
```

## Requirements

- Python 3.10+
- `requests` - HTTP client
- `beautifulsoup4` - HTML parsing
- `pycryptodome` - Session encryption

## Use Cases

- **Home Assistant Integration** - Build custom climate entities and sensors
- **Automation Scripts** - Create temperature schedules based on time or presence
- **Monitoring** - Track heating performance and valve positions over time
- **Analytics** - Analyze heating patterns, efficiency, and hydraulic balancing
- **Energy Management** - Calculate heating demand and optimize system performance
- **Multi-House Management** - Control multiple properties from one script

## Home Assistant Integration

For a ready-to-use Home Assistant integration, see:
[controme_ha](https://github.com/m-bck/controme_ha)

## Legal Notice

This library accesses the **local web interface** of your Controme heating control system. It does NOT use any official API.

**Use at your own risk.** The authors are not responsible for:
- Damage to your heating system
- Incorrect temperature settings
- Data loss or corruption
- Warranty violations

**Recommended:** Use only for personal, non-commercial purposes in your own home.

For official API access, contact: [Controme GmbH](https://support.controme.com/api)

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please open an issue or pull request on GitHub.

## Links

- **GitHub Repository**: https://github.com/m-bck/controme-scraper
- **Home Assistant Integration**: https://github.com/m-bck/controme_ha
- **PyPI Package**: https://pypi.org/project/controme-scraper/
- **Controme Official Website**: https://www.controme.com/
- **Controme Official API**: https://controme.com/api
