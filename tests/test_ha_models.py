#!/usr/bin/env python3
"""
Test script for the new HomeAssistant-optimized data models and parsers.
This demonstrates how the data will be structured for Home Assistant integration.
"""

import logging
import keyring
import json
from controme_scraper.controller import ContromeController

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def print_room_info(room):
    """Pretty print room information"""
    print(f"\n{'='*80}")
    print(f"ROOM: {room.name}")
    print(f"{'='*80}")
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


def print_thermostat_info(thermostat):
    """Pretty print thermostat information"""
    print(f"\n{'='*80}")
    print(f"THERMOSTAT: {thermostat.name}")
    print(f"{'='*80}")
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


def print_sensor_info(sensor):
    """Pretty print sensor information"""
    print(f"  • {sensor.name}: {sensor.value}{sensor.unit} (Room: {sensor.room_name})")


def main():
    """Main function"""
    print("\n" + "="*80)
    print("CONTROME - HOME ASSISTANT INTEGRATION TEST")
    print("="*80)
    
    # Load credentials
    host = keyring.get_password("controme_scraper", "host")
    user = keyring.get_password("controme_scraper", "user")
    password = keyring.get_password("controme_scraper", "password")
    
    if not all([host, user, password]):
        logger.error("Credentials not found in Keychain. Please run setup_credentials.py first.")
        return
    
    # Initialize controller
    logger.info("Initializing Controme Controller...")
    controller = ContromeController(host=host, username=user, password=password)
    
    # Test menu
    print("\nWhat would you like to test?")
    print("  1. Get all rooms")
    print("  2. Get all thermostats")
    print("  3. Get all sensors")
    print("  4. Get everything")
    print("  5. Export to JSON (for Home Assistant)")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    if choice in ['1', '4']:
        print(f"\n{'='*80}")
        print("FETCHING ROOMS...")
        print(f"{'='*80}")
        rooms = controller.get_rooms()
        logger.info(f"Found {len(rooms)} rooms")
        
        for room in rooms:
            print_room_info(room)
    
    if choice in ['2', '4']:
        print(f"\n{'='*80}")
        print("FETCHING THERMOSTATS...")
        print(f"{'='*80}")
        thermostats = controller.get_thermostats()
        logger.info(f"Found {len(thermostats)} thermostats")
        
        for thermostat in thermostats:
            print_thermostat_info(thermostat)
    
    if choice in ['3', '4']:
        print(f"\n{'='*80}")
        print("FETCHING SENSORS...")
        print(f"{'='*80}")
        sensors = controller.get_sensors()
        logger.info(f"Found {len(sensors)} sensors")
        
        print("\nSensors by room:")
        current_room = None
        for sensor in sorted(sensors, key=lambda s: (s.floor_name or '', s.room_name or '', s.name)):
            if sensor.room_name != current_room:
                current_room = sensor.room_name
                print(f"\n{sensor.floor_name} / {sensor.room_name}:")
            print_sensor_info(sensor)
    
    if choice == '5':
        print(f"\n{'='*80}")
        print("EXPORTING TO JSON...")
        print(f"{'='*80}")
        
        rooms = controller.get_rooms()
        thermostats = controller.get_thermostats()
        sensors = controller.get_sensors()
        
        data = {
            "rooms": [
                {
                    "unique_id": room.unique_id,
                    "name": room.name,
                    "room_id": room.room_id,
                    "current_temperature": room.current_temperature,
                    "target_temperature": room.target_temperature,
                    "attributes": room.attributes,
                }
                for room in rooms
            ],
            "thermostats": [
                {
                    "unique_id": thermostat.unique_id,
                    "name": thermostat.name,
                    "device_id": thermostat.device_id,
                    "mac_address": thermostat.mac_address,
                    "room_name": thermostat.room_name,
                    "current_temperature": thermostat.current_temperature,
                    "target_temperature": thermostat.target_temperature,
                    "device_info": thermostat.device_info,
                    "attributes": thermostat.attributes,
                }
                for thermostat in thermostats
            ],
            "sensors": [
                {
                    "unique_id": sensor.unique_id,
                    "name": sensor.name,
                    "device_class": sensor.device_class,
                    "state_class": sensor.state_class,
                    "value": sensor.value,
                    "unit": sensor.unit,
                    "attributes": sensor.attributes,
                }
                for sensor in sensors
            ]
        }
        
        filename = "controme_export.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n✅ Exported to {filename}")
        print(f"   - {len(rooms)} rooms")
        print(f"   - {len(thermostats)} thermostats")
        print(f"   - {len(sensors)} sensors")
        print("\nThis JSON structure is ready for Home Assistant integration!")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
