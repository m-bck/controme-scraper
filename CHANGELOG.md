# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- HVAC mode support (Heat/Off)
- Preset mode support (Controme presets)
- Improved error handling
- Configuration options UI

## [1.0.0] - 2025-11-17

### Added
- Initial public release
- Climate entities for all thermostats with assigned rooms
- Temperature setting via local API (`POST /m_raum/{room_id}/`)
- System sensors:
  - System heating demand (average valve position)
  - Active heating thermostats count
- Number entities:
  - Display brightness (0-30)
  - Sensor offset (-5.0 to +5.0°C)
- Switch entities:
  - Thermostat lock
- Select entities:
  - Room assignment for thermostats
- Multi-house support (house_id parameter)
- Device registry integration:
  - Gateway device for system overview
  - Thermostat devices with diagnostic sensors
- Coordinator-based data updates (60s interval)
- Config flow for easy setup
- Full HACS compatibility
- Comprehensive documentation

### Technical Details
- Local polling integration (no cloud)
- HTML scraping of Controme web interface
- Session-based authentication
- Automatic data refresh after changes
- Valve position tracking with hydraulic balancing support
- Return flow temperature sensors

### Documentation
- README with feature overview and installation
- DISCLAIMER with legal notices
- LICENSE (MIT with trademark notice)
- HACS integration guide
- Project status documentation

### Notes
- **Unofficial community integration**
- Not affiliated with Controme GmbH
- "Controme" and "Smart-Heat-OS" are trademarks of Controme GmbH
- For official support, see https://support.controme.com/api

## [0.9.0] - 2025-11-15 (Pre-release)

### Added
- Basic climate entities (read-only)
- System sensor entities
- Initial coordinator implementation
- Config flow MVP

### Changed
- Migrated from room-based to thermostat-based entities
- Improved data parsing and models

### Fixed
- Session management issues
- Data update coordination

## [0.5.0] - 2025-11-10 (Early Development)

### Added
- Core library structure
- Web client for API communication
- HTML parsing for room and thermostat data
- Basic models (Room, Thermostat, Sensor)

### Notes
- Internal development version
- Not released publicly

---

## Version History Summary

| Version | Date | Status | Notes |
|---------|------|--------|-------|
| 1.0.0 | 2025-11-17 | ✅ Stable | First public release |
| 0.9.0 | 2025-11-15 | 🧪 Beta | Pre-release testing |
| 0.5.0 | 2025-11-10 | 🔧 Dev | Initial development |

## Upgrade Notes

### From 0.9.x to 1.0.0
- No breaking changes
- Entities will be automatically migrated
- Backup your Home Assistant configuration before updating

## Deprecation Notices

None currently.

## Security Advisories

None currently.

---

**For detailed technical changes, see [commit history](https://github.com/maxibick/controme_scraper/commits/main).**
