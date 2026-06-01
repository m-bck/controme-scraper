"""
Integration tests for the HomeAssistant-optimized data models.
Requires a live Controme system and credentials stored in keyring.
"""

import logging
import pytest

logger = logging.getLogger(__name__)


def _print_room_info(room):
    print(f"\n{'=' * 80}")
    print(f"ROOM: {room.name}")
    print(f"{'=' * 80}")
    print(f"  ID: {room.room_id}")
    print(f"  Unique ID (HA): {room.unique_id}")
    print(f"  Floor: {room.floor_name}")
    print(f"  Current Temp: {room.current_temperature}°C")
    print(f"  Target Temp: {room.target_temperature}°C")
    print(f"  Offset: {room.target_temperature_offset}°C")
    print(f"  Valve Positions: {room.valve_positions}")
    print(f"  Avg Valve Position: {room.average_valve_position}%")
    print(f"  Icon: {room.icon}")
    print(f"\n  Home Assistant Attributes:")
    for key, value in room.attributes.items():
        print(f"    {key}: {value}")


def _print_thermostat_info(thermostat):
    print(f"\n{'=' * 80}")
    print(f"THERMOSTAT: {thermostat.name}")
    print(f"{'=' * 80}")
    print(f"  Device ID: {thermostat.device_id}")
    print(f"  Unique ID (HA): {thermostat.unique_id}")
    print(f"  MAC Address: {thermostat.mac_address}")
    print(f"  Room: {thermostat.room_name} ({thermostat.floor_name})")
    print(f"  Current Temp: {thermostat.current_temperature}°C")
    print(f"  Target Temp: {thermostat.target_temperature}°C")
    print(f"  Humidity: {thermostat.humidity}%")
    print(f"  Firmware: {thermostat.firmware_version}")
    print(f"  Power Source: {thermostat.power_source}")
    print(f"  Battery Powered: {thermostat.is_battery_powered}")
    print(f"  Connected: {thermostat.is_connected}")
    print(f"  Last Update: {thermostat.last_update}")
    print(f"\n  Configuration:")
    print(f"    Locked: {thermostat.locked}")
    print(f"    Main Sensor: {thermostat.is_main_sensor}")
    print(f"    Sensor Offset: {thermostat.sensor_offset}°C")
    print(f"    Display Brightness: {thermostat.display_brightness}")
    print(f"    Send Interval: {thermostat.send_interval}s")
    print(f"    Battery Saving: {thermostat.battery_saving_mode}")
    print(f"\n  Home Assistant Device Info:")
    for key, value in thermostat.device_info.items():
        print(f"    {key}: {value}")


def _print_sensor_info(sensor):
    print(f"  - {sensor.name}: {sensor.value}{sensor.unit} (Room: {sensor.room_name})")


@pytest.mark.integration
def test_rooms(controller):
    """Fetch all rooms and validate core model fields."""
    rooms = controller.get_rooms()
    logger.info(f"Found {len(rooms)} rooms")

    assert rooms is not None
    assert len(rooms) > 0

    for room in rooms:
        assert room.room_id is not None
        assert room.name is not None
        assert room.unique_id is not None
        assert room.attributes is not None
        _print_room_info(room)


@pytest.mark.integration
def test_thermostats(controller):
    """Fetch all thermostats and validate core model fields."""
    thermostats = controller.get_thermostats()
    logger.info(f"Found {len(thermostats)} thermostats")

    assert thermostats is not None
    assert len(thermostats) > 0

    for thermostat in thermostats:
        assert thermostat.device_id is not None
        assert thermostat.name is not None
        assert thermostat.unique_id is not None
        assert thermostat.device_info is not None
        assert thermostat.attributes is not None
        _print_thermostat_info(thermostat)


@pytest.mark.integration
def test_sensors(controller):
    """Fetch all sensors and validate core model fields."""
    sensors = controller.get_sensors()
    logger.info(f"Found {len(sensors)} sensors")

    assert sensors is not None
    assert len(sensors) > 0

    print("\nSensors by room:")
    current_room = None
    for sensor in sorted(sensors, key=lambda s: (s.floor_name or "", s.room_name or "", s.name)):
        if sensor.room_name != current_room:
            current_room = sensor.room_name
            print(f"\n{sensor.floor_name} / {sensor.room_name}:")
        _print_sensor_info(sensor)

    for sensor in sensors:
        assert sensor.unique_id is not None
        assert sensor.name is not None
        assert sensor.device_class is not None
        assert sensor.state_class is not None
        assert sensor.unit is not None
        assert sensor.attributes is not None
