# Controme Scraper - Python Library

**UNOFFICIAL** Python client library for Controme Smart-Heat-OS heating control systems.

> 🔄 **Repository Split**: This repository now contains only the Python library. For the Home Assistant integration, see: [controme_ha](https://github.com/maxibick/controme_ha)  
**Not affiliated with, endorsed by, or supported by Controme GmbH.**

Python-Bibliothek und Home Assistant Custom Component für Controme Smart-Heat-OS Heizungssteuerungen.

---

## ⚠️ Important Legal Notice

This integration accesses your **local** Controme system through its web interface.

- ✅ **For personal use only** - Use at your own risk
- ✅ **Your own system** - Only access systems you own
- ⚠️ **No warranty** - The author is not responsible for any damage or issues
- ℹ️ **Official API available** - Controme offers an official API: https://controme.com/api

**"Controme" and "Smart-Heat-OS" are trademarks of Controme GmbH.**

---

## 🏠 Home Assistant Integration

Die vollständige Custom Component befindet sich in `custom_components/controme/`.

### Schnellstart

```bash
pip install -e .
```

Siehe [HOMEASSISTANT_INTEGRATION.md](HOMEASSISTANT_INTEGRATION.md) für Details.

## 📦 Python Bibliothek

Das `controme_scraper` Modul kann auch standalone verwendet werden:

```python
from controme_scraper import ContromeController

controller = ContromeController(
    host="http://192.168.1.10",
    username="user",
    password="pass"
)

# Räume abrufen
rooms = controller.get_rooms()
for room in rooms:
    print(f"{room.name}: {room.current_temperature}°C → {room.target_temperature}°C")

# System-Heizbedarf
from controme_scraper.models import Gateway
gateway = Gateway(gateway_id="main", name="Gateway", rooms=rooms)
print(f"Heizbedarf: {gateway.system_average_valve_position}%")
```

## 📁 Projekt-Struktur

```
controme_scraper/              # Python Library (Core)
├── heizung.py                 # Main Controller API
├── models.py                  # Data Models (Room, Thermostat, etc.)
├── parsers.py                 # HTML Parser für AJAX Endpoints
├── web_client.py              # HTTP Client
└── session_manager.py         # Session Management mit Verschlüsselung

custom_components/controme/    # Home Assistant Integration
├── manifest.json              # Integration Metadata
├── __init__.py                # Setup & Entry Management
├── config_flow.py             # UI Configuration
├── coordinator.py             # Data Update Coordinator
├── climate.py                 # Climate Entities (Räume)
├── sensor.py                  # System Sensors
└── controme_scraper/          # Library (embedded)

tests/                         # Test-Skripte
├── test_ha_models.py          # Test der HA-optimierten Models
├── test_room_parser.py        # Test des Room Parsers
└── test_system_demand.py      # Test des System-Heizbedarfs

archive/                       # Alte Entwicklungs-Skripte
```

## Installation

```bash
pip install controme-scraper
```

## Features

- 🔐 **Session Management** - Automatic login and session handling
- 🌡️ **Temperature Control** - Read and set target temperatures
- 📊 **Real-time Data** - Current temperatures, valve positions, heating status
- 🏠 **Multi-House Support** - Manage multiple houses
- 📈 **System Metrics** - Heating demand, boiler status, sensor data
- 🔧 **Complete Models** - Full Python dataclasses for all entities
- 📦 **Type Hints** - Full type annotation support

## 🚀 Installation

### Requirements

```bash
pip install -r requirements.txt
```

### Credentials (macOS Keychain)

```bash
python setup_credentials.py
```

Oder manuell in Python:
```python
import keyring
keyring.set_password('controme_scraper', 'host', 'http://192.168.1.10')
keyring.set_password('controme_scraper', 'user', 'username')
keyring.set_password('controme_scraper', 'password', 'password')
```

## 🧪 Tests

```bash
# Test der Models und Parser
python test_ha_models.py

# Test des System-Heizbedarfs
python test_system_demand.py

# Test des Room Parsers
python test_room_parser.py
```



## Quick Start

```python
from controme_scraper import ContromeController

# Initialize controller
controller = ContromeController(
    host="http://192.168.1.10",
    username="your_username",
    password="your_password",
    house_id=1
)

# Get all rooms with data
rooms = controller.get_rooms()
for room in rooms:
    print(f"{room.name}: {room.current_temperature}°C → {room.target_temperature}°C")

# Set temperature
controller.web_client.set_room_temperature(room_id=1, temperature=22.5)
```

## Home Assistant Integration

For a ready-to-use Home Assistant integration, see: [controme_ha](https://github.com/maxibick/controme_ha)

## Documentation

For full API documentation, see [README_PYPI.md](README_PYPI.md)

## 🛠️ Entwicklung

### Projekt-Setup

```bash
# Virtual Environment erstellen
python3 -m venv env
source env/bin/activate

# Dependencies installieren
pip install -r requirements.txt

# Credentials konfigurieren
python setup_credentials.py
```

### Nach Code-Änderungen

```bash
```

## 🔧 Bekannte Limitierungen

- ⚠️ **Temperatur-Steuerung** nur lesend (API Endpoint für Schreiben fehlt noch)
- ⚠️ **Preset-Modi** noch nicht extrahiert (in Room HTML vorhanden)
- ⚠️ **Gateway Info** (Firmware, etc.) noch nicht implementiert

## 📝 Lizenz

MIT License

## 🙏 Danksagung

Entwickelt für Controme Smart-Heat-OS Heizungssteuerungen.

## 📧 Support

- **Issues**: https://github.com/maxibick/controme_scraper/issues
- **Repository**: https://github.com/maxibick/controme_scraper
