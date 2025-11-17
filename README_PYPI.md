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

# Get system overview
system = controller.get_system_data()
print(f"Heating demand: {system.heating_demand}%")
print(f"Rooms heating: {system.rooms_heating_count}/{system.total_rooms}")
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
gateway = controller.get_gateway()          # Gateway (system status)
```

### Models

All data is returned as typed Python dataclasses:

- **Room**: Complete room data with temperatures, valves, sensors
- **Thermostat**: Thermostat device with configuration and status
- **Sensor**: Temperature/humidity sensors with current readings
- **Gateway**: System gateway with overall status and metrics

### WebClient

Low-level API client for direct HTTP requests:

```python
client = controller.web_client

# Temperature control
client.set_room_temperature(room_id=1, temperature=22.5)

# Raw API access
thermostats = client.get_thermostats()      # JSON response
rooms = client.get_rooms()                  # JSON response
sensors = client.get_sensors()              # JSON response
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

- **Home Assistant Integration** - Build custom components
- **Automation Scripts** - Create temperature schedules
- **Monitoring** - Track heating performance
- **Analytics** - Analyze heating patterns and efficiency

## Home Assistant Integration

For a ready-to-use Home Assistant integration, see:
[controme_ha](https://github.com/maxibick/controme_ha)

## Legal Notice

This library accesses the **local web interface** of your Controme heating control system. It does NOT use any official API.

**Use at your own risk.** The authors are not responsible for:
- Damage to your heating system
- Incorrect temperature settings
- Data loss or corruption
- Warranty violations

**Recommended:** Use only for personal, non-commercial purposes in your own home.

For official API access, contact: [Controme GmbH](https://controme.com/api)

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please open an issue or pull request on GitHub.

## Links

- **GitHub Repository**: https://github.com/maxibick/controme_scraper
- **Home Assistant Integration**: https://github.com/maxibick/controme_ha
- **Controme Official Website**: https://www.controme.com/
- **Controme Official API**: https://controme.com/api
