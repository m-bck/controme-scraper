# Controme Scraper - Python Library

**UNOFFICIAL** Python client library for Controme Smart-Heat-OS heating control systems.

> 🔄 **Repository Split**: This repository contains only the Python library. For the Home Assistant integration, see: [controme_ha](https://github.com/m-bck/controme_ha)

**Not affiliated with, endorsed by, or supported by Controme GmbH.**

---

## ⚠️ Important Legal Notice

This integration accesses your **local** Controme system through its web interface.

- ✅ **For personal use only** - Use at your own risk
- ✅ **Your own system** - Only access systems you own
- ⚠️ **No warranty** - The author is not responsible for any damage or issues
- ℹ️ **Official API available** - Controme offers an official API: https://support.controme.com/api

**"Controme" and "Smart-Heat-OS" are trademarks of Controme GmbH.**

---

## 📦 Installation

```bash
pip install controme-scraper
```

Or for development:

```bash
git clone https://github.com/m-bck/controme-scraper.git
cd controme_scraper
pip install -e .
```

## 🚀 Quick Start

```python
from controme_scraper import ContromeController

# Initialize controller
controller = ContromeController(
    host="http://192.168.1.10",
    username="admin",
    password="your_password",
    house_id=1
)

# Get all rooms
rooms = controller.get_rooms()
for room in rooms:
    print(f"{room.name}: {room.current_temperature}°C → {room.target_temperature}°C")
    print(f"  Valves: {room.valve_positions}")
    print(f"  Heating: {'ON' if room.is_heating else 'OFF'}")

# Get thermostats
thermostats = controller.get_thermostats()
for thermostat in thermostats:
    print(f"{thermostat.name}: {thermostat.current_temperature}°C")

# Get sensors
sensors = controller.get_sensors()
for sensor in sensors:
    print(f"{sensor.name}: {sensor.value}{sensor.unit}")

# Set room temperature
controller.web_client.set_room_temperature(room_id=1, temperature=22.5)
```

## 📁 Module Structure

```
controme_scraper/
├── __init__.py                # Package exports
├── controller.py              # Main ContromeController class
├── models.py                  # Data models (Room, Thermostat, Sensor, Gateway)
├── parsers.py                 # HTML parsers for Controme web interface
├── web_client.py              # HTTP client for API calls
├── session_manager.py         # Session management with encryption
├── url_constants.py           # API endpoint URLs
├── logging_config.py          # Logging configuration
└── encryption_utils/          # Credential encryption utilities

tests/
├── test_controller.py         # Controller tests
├── test_models.py             # Model tests
├── test_parsers.py            # Parser tests (with real HTML fixtures)
├── test_web_client.py         # Web client tests
└── fixtures/                  # Real HTML fixtures from Controme system
```

## ✨ Features

- 🔐 **Session Management** - Automatic login and session handling with encrypted credentials
- 🌡️ **Temperature Control** - Read and set target temperatures (0.5°C precision)
- 📊 **Real-time Data** - Current temperatures, valve positions, heating status
- 🏠 **Multi-House Support** - Manage multiple houses in one Controme system
- 🔧 **Hydraulic Balancing** - Access max valve positions from gateway hardware config
- 📈 **System Metrics** - System heating demand, boiler status, return flow temperatures
- 🏷️ **Complete Models** - Full Python dataclasses for all entities (Room, Thermostat, Sensor, Gateway)
- 📦 **Type Hints** - Full type annotation support for modern Python development
- 🧪 **Well Tested** - Comprehensive test suite with real HTML fixtures

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=controme_scraper --cov-report=term-missing

# Run specific test file
pytest tests/test_parsers.py -v
```

## 🏠 Home Assistant Integration

For a ready-to-use Home Assistant custom component, see: [controme_ha](https://github.com/m-bck/controme_ha)

## 📚 Documentation

For detailed API documentation and advanced usage, see [README_PYPI.md](README_PYPI.md)

## 🛠️ Development

### Setup

```bash
# Clone repository
git clone https://github.com/m-bck/controme-scraper.git
cd controme_scraper

# Create virtual environment
python3 -m venv env
source env/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

### Contributing

Contributions are welcome! Please ensure:
- All tests pass: `pytest`
- Code is formatted: `black .`
- Type hints are included
- Tests are added for new features

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 📧 Support

- **Issues**: https://github.com/m-bck/controme-scraper/issues
- **Repository**: https://github.com/m-bck/controme-scraper

## ⚠️ Disclaimer

This is an unofficial library and is not affiliated with, endorsed by, or supported by Controme GmbH.
Use at your own risk. See [DISCLAIMER.md](DISCLAIMER.md) for full details.
