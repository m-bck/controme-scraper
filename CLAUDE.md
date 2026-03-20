# CLAUDE.md — AI Assistant Guide for controme-scraper

## Project Overview

`controme-scraper` is an **unofficial Python library** for interacting with [Controme Smart-Heat-OS](https://www.controme.com/) heating systems via local network scraping. It is **not** affiliated with Controme GmbH.

The library is designed primarily for **Home Assistant integration**: all data models carry `unique_id`, `device_info`, and `attributes` properties compatible with HA's entity registry.

---

## Repository Structure

```
controme_scraper/           # Main package
├── __init__.py             # Package exports and version
├── controller.py           # ContromeController — primary public API
├── models.py               # Dataclasses: Room, Thermostat, Sensor, Gateway
├── parsers.py              # BeautifulSoup HTML + JSON parsers
├── web_client.py           # Low-level HTTP client (requests-based)
├── session_manager.py      # Session auth + AES-encrypted session caching
├── url_constants.py        # All API endpoint path constants
├── logging_config.py       # Logger factory
├── py.typed                # PEP 561 marker (typed package)
└── encryption_utils/
    └── encryption_utils.py # AES-256-CBC encrypt/decrypt helpers

tests/
├── test_ha_models.py           # Interactive integration test for all HA models
├── test_max_valve_positions.py # Hydraulic balancing / valve position tests
└── test_system_demand.py       # System-wide heating demand metrics tests

.github/workflows/
├── tests.yml               # CI: pytest matrix on Python 3.10–3.12
└── publish-to-pypi.yml     # CD: build and publish on release
```

---

## Architecture & Key Concepts

### Layer diagram

```
User code / Home Assistant
        ↓
ContromeController  (controller.py)   ← primary entry point
        ↓
WebClient           (web_client.py)   ← all HTTP calls, url_constants
        ↓
SessionManager      (session_manager.py) ← authentication & session cache
        ↓
Parsers             (parsers.py)      ← HTML / JSON → raw dicts
        ↓
Models              (models.py)       ← typed dataclasses returned to callers
```

### ContromeController (`controller.py`)

Public API consumed by users and Home Assistant integrations:

| Method | Description |
|--------|-------------|
| `__init__(host, username, password, house_id=1)` | Initialize; creates WebClient & SessionManager |
| `get_rooms(include_max_positions, include_return_flow)` | Fetch all rooms (with optional enhancements) |
| `get_room(room_id)` | Fetch a single room |
| `get_thermostats(include_config, include_valve_data)` | Fetch all thermostats |
| `get_thermostat(device_num)` | Fetch a single thermostat |
| `get_sensors()` | Fetch all sensors |

Internal helpers `_assign_max_positions_to_rooms()` and `_assign_return_flow_to_rooms()` enrich room objects after fetching.

### Data Models (`models.py`)

All are dataclasses with full type hints.

| Class | Represents | Key HA properties |
|-------|-----------|-------------------|
| `Room` | A heating zone/room | `unique_id`, `average_valve_position`, `relative_valve_positions`, `is_heating`, `device_info`, `attributes` |
| `Thermostat` | A physical thermostat device | `unique_id`, `get_sensors()`, `device_info` |
| `Sensor` | A temperature / valve / humidity sensor | `unique_id`, `device_class`, `state_class`, `device_info` |
| `Gateway` | The Controme gateway (system-level) | `system_heating_demand`, `active_heating_rooms`, `system_average_valve_position` |

**Hydraulic balancing:** `Room` and `Thermostat` both carry `max_valve_positions` (hardware limits). `relative_valve_positions` normalises raw valve values against these limits. `Gateway.system_average_relative_valve_position` aggregates across all rooms.

**Heating demand levels** (Gateway): `"Very Low"` (<10%), `"Low"` (<30%), `"Medium"` (<50%), `"High"` (<70%), `"Very High"` (≥70%).

### Parsers (`parsers.py`)

Pure functions; each takes raw HTML/dict and returns Python dicts or dataclass instances. No side effects.

| Function | Input | Returns |
|----------|-------|---------|
| `parse_room_temperature_html()` | Room AJAX HTML | Room dict |
| `parse_sensor_overview_html()` | Sensor page HTML | List of Sensor dicts |
| `parse_thermostat_html()` | Thermostat AJAX HTML | Thermostat dict |
| `parse_thermostat_config()` | Config HTML | 12-key config dict |
| `parse_gateway_hardware()` | Hardware JSON | Max valve position dicts |
| `parse_actuator_config()` | Actuator JSON | Room-to-output mappings |

### WebClient (`web_client.py`)

All HTTP calls go through `_get_site(url, params)`. Session is obtained from `SessionManager` on first use. Key methods:

- `get_rooms()`, `get_room(room_id)`
- `get_thermostats()`, `get_thermostat(device_id, include_config)`
- `get_thermostat_config(device_id)`
- `get_sensors()`
- `set_room_temperature(room_id, temperature)` — 0.5 °C precision
- `set_thermostat_parameter(device_id, type, value)`
- `get_gateway_hardware(house_id)` — max valve positions
- `get_actuator_config(house_id)` — actuator-to-room mappings

### SessionManager (`session_manager.py`)

- Authenticates via POST to `LOGIN` URL.
- Persists `requests.Session` to disk as an AES-256-CBC encrypted pickle (via `encryption_utils`).
- Filename is a SHA-256 hash of `{url}:{user}:{password}` — one file per credential set.
- On startup: loads file → validates session → re-authenticates if invalid.

### URL Constants (`url_constants.py`)

All API path segments live here. Combine with host prefix in `WebClient`. Current endpoints:

```python
LOGIN      = "accounts/m_login/"
STARTSEITE = "raumregelung-pro/"   # session validation
SENSOREN   = "sensorenuebersicht"
HARDWARE   = "m_setup/1/hardware/"
# Dynamic (f-strings): m_raum_temp_html/{id}/, m_setup/{house_id}/rf/, etc.
```

---

## Development Workflow

### Setup

```bash
pip install -e ".[dev]"
```

This installs the package in editable mode plus all dev tools (`pytest`, `pytest-cov`, `black`, `ruff`).

### Running Tests

```bash
pytest tests/ -v --cov=controme_scraper --cov-report=term-missing
```

Note: Integration tests (`test_ha_models.py`, `test_system_demand.py`) require live credentials stored via `keyring`. They are meant for manual interactive use against a real Controme gateway.

### Formatting

```bash
black .
```

Line length: **120 characters** (configured in `pyproject.toml`).

### Linting

```bash
ruff check .
```

### CI

GitHub Actions runs tests on push/PR to `main` across Python 3.10, 3.11, 3.12. Coverage is uploaded to Codecov (Python 3.10 only).

---

## Code Conventions

1. **Type hints everywhere.** All public methods must have full parameter and return type annotations.
2. **Dataclasses for models.** Use `@dataclass` (not plain dicts) for all data returned to callers.
3. **Pure parsers.** Parser functions must not perform I/O or have side effects — they transform raw strings/dicts to structured data.
4. **URL constants, not magic strings.** Add new endpoints to `url_constants.py`; never hardcode paths in `web_client.py`.
5. **Home Assistant compatibility.** Any new model that represents a device or entity must provide `unique_id`, `device_info`, and `attributes` properties following HA conventions.
6. **120-char line length.** Enforced by `black`; do not exceed.
7. **No external state in parsers or models.** `WebClient` and `SessionManager` may hold state; parsers and models must not.
8. **Encryption for persisted secrets.** Never store credentials or sessions in plaintext files.

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `requests` | >=2.31.0 | HTTP client |
| `beautifulsoup4` | >=4.12.0 | HTML parsing |
| `pycryptodome` | >=3.19.0 | AES-256-CBC session encryption |
| `pytest` | >=7.4.0 | Testing |
| `pytest-cov` | >=4.1.0 | Coverage reporting |
| `black` | >=23.7.0 | Formatting |
| `ruff` | >=0.0.285 | Linting |

---

## Package Publishing

Version is defined in `pyproject.toml`. To release:

1. Update `version` in `pyproject.toml`.
2. Add entry to `CHANGELOG.md`.
3. Create a GitHub Release — the `publish-to-pypi.yml` workflow triggers automatically and uploads to PyPI using the `PYPI_API_TOKEN` secret.

See `PYPI_UPLOAD.md` for manual publishing instructions.

---

## Important Caveats for AI Assistants

- **Unofficial / scraping-based:** The library reverse-engineers Controme's web UI. HTML structure may change without notice; parsers may need updating.
- **No official API docs:** All endpoint knowledge comes from observation. Treat `parsers.py` as the source of truth for response structure.
- **Avoid breaking HA compatibility:** The `unique_id`, `device_info`, and `attributes` properties on models are consumed by downstream HA integrations — changing their shape is a breaking change.
- **Session encryption is intentional:** Do not simplify away the AES encryption on persisted sessions; it stores authentication cookies.
- **Multi-house support:** `house_id` defaults to `1` but may differ. Always thread it through rather than hardcoding.
- **Temperature precision:** `set_room_temperature` rounds to the nearest 0.5 °C — preserve this behaviour.
