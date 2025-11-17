"""
Data models optimized for Home Assistant integration.

These models follow Home Assistant's entity model where each device has:
- unique_id: Unique identifier for the entity
- name: Human-readable name
- state: Current state/value
- attributes: Additional information as dict
- device_info: Information about the physical device

References:
- https://developers.home-assistant.io/docs/core/entity/
- https://developers.home-assistant.io/docs/core/entity/climate/
- https://developers.home-assistant.io/docs/core/entity/sensor/
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class ThermostatMode(Enum):
    """Operating modes for thermostat"""
    HEAT = "heat"
    OFF = "off"
    AUTO = "auto"


class SensorType(Enum):
    """Types of sensors"""
    TEMPERATURE = "temperature"
    RETURN_FLOW = "return_flow"
    HUMIDITY = "humidity"
    VALVE_POSITION = "valve_position"


@dataclass
class Device:
    """Base device information for Home Assistant device registry"""
    identifiers: str  # Unique identifier (e.g., MAC address, device ID)
    name: str
    manufacturer: str = "Controme"
    model: Optional[str] = None
    sw_version: Optional[str] = None
    
    def to_device_info(self) -> Dict[str, Any]:
        """Convert to Home Assistant device_info format"""
        return {
            "identifiers": {("controme", self.identifiers)},
            "name": self.name,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "sw_version": self.sw_version,
        }


@dataclass
class Room:
    """
    Represents a room in the Controme system.
    Maps to Home Assistant Climate entity.
    
    This is the primary interface for room temperature control in Home Assistant.
    A room may have multiple thermostats and valve actuators, but is presented
    as a single climate entity to the user.
    """
    # Identifiers
    room_id: int
    name: str
    
    # Temperature data
    current_temperature: Optional[float] = None  # Isttemperatur
    target_temperature: Optional[float] = None   # Solltemperatur (Zieltemperatur)
    target_temperature_offset: Optional[float] = None  # Temperature offset applied
    
    # Room metadata
    icon: Optional[str] = None  # Icon path from Controme
    floor_name: Optional[str] = None
    
    # Valve/actuator data (aggregated from all actuators in room)
    valve_positions: List[int] = field(default_factory=list)  # Stellmotor positions (0-100%)
    max_valve_positions: List[int] = field(default_factory=list)  # Max positions from hydraulic balancing (0-99%)
    return_flow_temperatures: List[Optional[float]] = field(default_factory=list)  # Return flow temps per valve (°C)
    
    # Associated thermostats (for device linking)
    thermostat_ids: List[str] = field(default_factory=list)  # List of thermostat device_ids
    
    # Home Assistant specific
    hvac_mode: ThermostatMode = ThermostatMode.HEAT
    preset_mode: Optional[str] = None  # e.g., "Herbst", "Winter", "Sommer"
    
    @property
    def unique_id(self) -> str:
        """Unique identifier for Home Assistant Climate entity"""
        return f"controme_room_{self.room_id}"
    
    @property
    def average_valve_position(self) -> Optional[int]:
        """
        Average valve position across all actuators in the room.
        Useful indicator of heating demand.
        """
        if not self.valve_positions:
            return None
        return int(sum(self.valve_positions) / len(self.valve_positions))
    
    @property
    def relative_valve_positions(self) -> List[float]:
        """
        Valve positions relative to their hydraulic balancing max (0-100%).
        This shows the true demand accounting for system balancing.
        
        Example: A valve at 70% of max 76% = 92.1% relative demand
        """
        if not self.valve_positions or not self.max_valve_positions:
            return []
        
        if len(self.valve_positions) != len(self.max_valve_positions):
            return []
        
        return [
            (current / max_pos * 100) if max_pos > 0 else 0
            for current, max_pos in zip(self.valve_positions, self.max_valve_positions)
        ]
    
    @property
    def average_relative_valve_position(self) -> Optional[float]:
        """
        Average relative valve position (accounts for hydraulic balancing).
        Better indicator of true heating demand than absolute average.
        """
        relative_positions = self.relative_valve_positions
        if not relative_positions:
            return None
        return sum(relative_positions) / len(relative_positions)
    
    @property
    def is_heating(self) -> bool:
        """Check if room is actively heating (any valve open)"""
        if not self.valve_positions:
            return False
        return any(pos > 0 for pos in self.valve_positions)
    
    @property
    def device_info(self) -> Dict[str, Any]:
        """
        Device information for Home Assistant device registry.
        Groups all room entities under one device.
        """
        return {
            "identifiers": {("controme", f"room_{self.room_id}")},
            "name": self.name,
            "manufacturer": "Controme",
            "model": "Room Climate Control",
            "suggested_area": self.floor_name,
        }
    
    @property
    def attributes(self) -> Dict[str, Any]:
        """Additional attributes for Home Assistant Climate entity"""
        attrs = {
            "room_id": self.room_id,
            "floor": self.floor_name,
            "valve_positions": self.valve_positions,
            "average_valve_position": self.average_valve_position,
            "is_heating": self.is_heating,
            "target_offset": self.target_temperature_offset,
            "icon": self.icon,
            "preset_mode": self.preset_mode,
            "thermostat_count": len(self.thermostat_ids),
            "valve_count": len(self.valve_positions),
        }
        
        # Add relative positions if hydraulic balancing data available
        if self.max_valve_positions:
            attrs["max_valve_positions"] = self.max_valve_positions
            attrs["relative_valve_positions"] = [round(p, 1) for p in self.relative_valve_positions]
            if self.average_relative_valve_position is not None:
                attrs["average_relative_valve_position"] = round(self.average_relative_valve_position, 1)
        
        # Add return flow temperatures if available
        if self.return_flow_temperatures:
            attrs["return_flow_temperatures"] = self.return_flow_temperatures
        
        return attrs
    
    def __repr__(self) -> str:
        heating_status = "🔥" if self.is_heating else "❄️"
        return (f"Room(id={self.room_id}, name='{self.name}', "
                f"current={self.current_temperature}°C, target={self.target_temperature}°C, "
                f"valves={self.average_valve_position}% {heating_status})")


@dataclass
class Thermostat:
    """
    Represents a Controme Raumcontroller (thermostat device).
    
    NOW THIS IS THE PRIMARY CLIMATE ENTITY in Home Assistant.
    Each thermostat becomes a climate entity with all its configuration options.
    The room is now just an attribute of the thermostat.
    
    This provides:
    - Climate entity for temperature control
    - All 12 configurable options as attributes/entities
    - Battery/signal status sensors
    - Firmware information
    - Associated valve positions and return flow temps
    """
    # Identifiers
    device_id: str  # e.g., "RFAktor*1"
    mac_address: Optional[str] = None
    description: str = ""  # Display name (e.g., "RT Bad")
    
    # Room assignment
    assigned_room_id: Optional[int] = None  # Which room this thermostat controls
    room_name: Optional[str] = None
    floor_name: Optional[str] = None
    
    # Current state
    current_temperature: Optional[float] = None
    target_temperature: Optional[float] = None
    humidity: Optional[int] = None  # 0-100%
    
    # Configuration Options (all 12 configurable settings)
    # These are now the primary configuration interface in HA
    device_type: str = "hktControme"  # undef, hktGenius, hkt, hktControme, hkteTRV
    sensor_offset: float = 0.0  # Temperature calibration: -5.0 to +5.0°C
    display_brightness: int = 15  # Display brightness: 0-30
    send_interval: int = 60  # Update frequency: 60-3600 seconds
    deviation: float = 0.0  # Temperature change threshold: 0.0-0.5°C
    force_send_count: int = 1  # Force send count: 0-10
    locked: bool = False  # Prevent changes at thermostat
    is_main_sensor: bool = False  # Determines room target temperature
    temp_mode_temporary: bool = False  # Temperature changes only temporary
    battery_saving_mode: bool = False  # Dynamic battery saving mode
    
    # Additional device info
    firmware_version: Optional[str] = None
    power_source: Optional[str] = None  # "Festanschluss", "Batterie"
    
    # Status
    last_update: Optional[datetime] = None
    battery_level: Optional[int] = None  # 0-100%
    signal_strength: Optional[str] = None  # wifi/radio signal
    is_connected: bool = False
    
    # Associated valve/actuator data
    valve_positions: List[int] = field(default_factory=list)  # Current positions (0-100%)
    max_valve_positions: List[int] = field(default_factory=list)  # Max from hydraulic balancing
    return_flow_temperatures: List[Optional[float]] = field(default_factory=list)  # Return flow temps per valve
    
    # Home Assistant specific
    hvac_mode: ThermostatMode = ThermostatMode.HEAT
    preset_mode: Optional[str] = None
    
    @property
    def unique_id(self) -> str:
        """Unique identifier for Home Assistant Climate entity"""
        if self.mac_address:
            return f"controme_thermostat_{self.mac_address.replace(':', '')}"
        return f"controme_thermostat_{self.device_id.replace('*', '_')}"
    
    @property
    def name(self) -> str:
        """Display name for Home Assistant entity"""
        return self.description or f"Thermostat {self.device_id}"
    
    @property
    def device_info(self) -> Dict[str, Any]:
        """
        Device information for Home Assistant device registry.
        Each thermostat is now its own primary device.
        """
        device = Device(
            identifiers=self.mac_address or self.device_id,
            name=self.name,
            model=self.device_type or "Controme Raumcontroller",
            sw_version=self.firmware_version,
        )
        device_info = device.to_device_info()
        
        # Add suggested area from room/floor
        if self.room_name:
            device_info["suggested_area"] = self.room_name
        elif self.floor_name:
            device_info["suggested_area"] = self.floor_name
        
        return device_info
    
    @property
    def average_valve_position(self) -> Optional[int]:
        """Average valve position across all actuators controlled by this thermostat"""
        if not self.valve_positions:
            return None
        return int(sum(self.valve_positions) / len(self.valve_positions))
    
    @property
    def relative_valve_positions(self) -> List[float]:
        """Valve positions relative to hydraulic balancing max (0-100%)"""
        if not self.valve_positions or not self.max_valve_positions:
            return []
        
        if len(self.valve_positions) != len(self.max_valve_positions):
            return []
        
        return [
            (current / max_pos * 100) if max_pos > 0 else 0
            for current, max_pos in zip(self.valve_positions, self.max_valve_positions)
        ]
    
    @property
    def average_relative_valve_position(self) -> Optional[float]:
        """Average relative valve position (accounts for hydraulic balancing)"""
        relative_positions = self.relative_valve_positions
        if not relative_positions:
            return None
        return sum(relative_positions) / len(relative_positions)
    
    @property
    def is_heating(self) -> bool:
        """Check if thermostat is actively heating (any valve open)"""
        if not self.valve_positions:
            return False
        return any(pos > 0 for pos in self.valve_positions)
    
    @property
    def attributes(self) -> Dict[str, Any]:
        """
        Additional attributes for Home Assistant Climate entity.
        All 12 configuration options plus status information.
        """
        attrs = {
            # Identity
            "device_id": self.device_id,
            "mac_address": self.mac_address,
            
            # Room assignment
            "room_id": self.assigned_room_id,
            "room_name": self.room_name,
            "floor": self.floor_name,
            
            # Configuration Options (12 total)
            "device_type": self.device_type,
            "sensor_offset": self.sensor_offset,
            "display_brightness": self.display_brightness,
            "send_interval": self.send_interval,
            "deviation": self.deviation,
            "force_send_count": self.force_send_count,
            "locked": self.locked,
            "is_main_sensor": self.is_main_sensor,
            "temp_mode_temporary": self.temp_mode_temporary,
            "battery_saving_mode": self.battery_saving_mode,
            
            # Status
            "power_source": self.power_source,
            "battery_level": self.battery_level,
            "signal_strength": self.signal_strength,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "firmware_version": self.firmware_version,
            "is_connected": self.is_connected,
            
            # Valve data
            "valve_positions": self.valve_positions,
            "average_valve_position": self.average_valve_position,
            "valve_count": len(self.valve_positions),
            "is_heating": self.is_heating,
        }
        
        # Add relative positions if hydraulic balancing data available
        if self.max_valve_positions:
            attrs["max_valve_positions"] = self.max_valve_positions
            attrs["relative_valve_positions"] = [round(p, 1) for p in self.relative_valve_positions]
            if self.average_relative_valve_position is not None:
                attrs["average_relative_valve_position"] = round(self.average_relative_valve_position, 1)
        
        # Add return flow temperatures if available
        if self.return_flow_temperatures:
            attrs["return_flow_temperatures"] = self.return_flow_temperatures
        
        return attrs
    
    @property
    def is_battery_powered(self) -> bool:
        """Check if device is battery powered"""
        return self.power_source and "Batterie" in self.power_source
    
    def __repr__(self) -> str:
        heating_status = "🔥" if self.is_heating else "❄️"
        return (f"Thermostat(id={self.device_id}, name='{self.description}', "
                f"current={self.current_temperature}°C, target={self.target_temperature}°C, "
                f"valves={self.average_valve_position}% {heating_status})")
    
    def get_sensors(self) -> List[Dict[str, Any]]:
        """
        Returns list of sensor definitions for Home Assistant.
        These sensors will be created under this thermostat device.
        """
        sensors = []
        
        # Battery level sensor (only for battery-powered devices)
        if self.is_battery_powered and self.battery_level is not None:
            sensors.append({
                "key": "battery",
                "name": f"{self.name} Battery",
                "value": self.battery_level,
                "unit": "%",
                "device_class": "battery",
                "state_class": "measurement",
            })
        
        # Signal strength sensor
        if self.signal_strength:
            sensors.append({
                "key": "signal_strength",
                "name": f"{self.name} Signal Strength",
                "value": self.signal_strength,
                "device_class": "signal_strength",
            })
        
        # Connection status sensor
        sensors.append({
            "key": "connection",
            "name": f"{self.name} Connection",
            "value": "connected" if self.is_connected else "disconnected",
            "device_class": "connectivity",
        })
        
        # Temperature sensor (current reading from thermostat)
        if self.current_temperature is not None:
            sensors.append({
                "key": "temperature",
                "name": f"{self.name} Temperature",
                "value": self.current_temperature,
                "unit": "°C",
                "device_class": "temperature",
                "state_class": "measurement",
            })
        
        # Humidity sensor
        if self.humidity is not None and self.humidity > 0:
            sensors.append({
                "key": "humidity",
                "name": f"{self.name} Humidity",
                "value": self.humidity,
                "unit": "%",
                "device_class": "humidity",
                "state_class": "measurement",
            })
        
        return sensors
    
    @property
    def is_battery_powered(self) -> bool:
        """Check if device is battery powered"""
        return self.power_source and "batterie" in self.power_source.lower()
    
    def __repr__(self) -> str:
        return (f"Thermostat(id={self.device_id}, name='{self.name}', "
                f"room='{self.room_name}', temp={self.current_temperature}°C)")


@dataclass
class Sensor:
    """
    Represents a temperature sensor (e.g., Rücklaufsensor).
    Maps to Home Assistant Sensor entity.
    
    These sensors are created as standalone entities but can be linked
    to the Room device for better organization.
    """
    # Identifiers
    sensor_id: str  # Generated from name or unique ID
    name: str
    sensor_type: SensorType
    
    # Location (for linking to Room device)
    room_id: Optional[int] = None
    room_name: Optional[str] = None
    floor_name: Optional[str] = None
    
    # Current value
    value: Optional[float] = None
    unit: str = "°C"
    
    # Metadata
    last_update: Optional[datetime] = None
    
    @property
    def unique_id(self) -> str:
        """Unique identifier for Home Assistant Sensor entity"""
        return f"controme_sensor_{self.sensor_id}"
    
    @property
    def device_class(self) -> str:
        """Home Assistant device class"""
        if self.sensor_type == SensorType.TEMPERATURE:
            return "temperature"
        elif self.sensor_type == SensorType.RETURN_FLOW:
            return "temperature"
        elif self.sensor_type == SensorType.HUMIDITY:
            return "humidity"
        elif self.sensor_type == SensorType.VALVE_POSITION:
            return "none"
        return "none"
    
    @property
    def state_class(self) -> str:
        """Home Assistant state class for statistics"""
        return "measurement"
    
    @property
    def device_info(self) -> Optional[Dict[str, Any]]:
        """
        Link sensor to Room device if room_id is available.
        This groups the sensor under the room in HA's device view.
        """
        if self.room_id:
            return {
                "identifiers": {("controme", f"room_{self.room_id}")},
                "name": self.room_name or f"Room {self.room_id}",
                "manufacturer": "Controme",
                "model": "Room Climate Control",
                "suggested_area": self.floor_name,
            }
        return None
    
    @property
    def attributes(self) -> Dict[str, Any]:
        """Additional attributes for Home Assistant Sensor entity"""
        return {
            "sensor_id": self.sensor_id,
            "room_id": self.room_id,
            "room_name": self.room_name,
            "floor": self.floor_name,
            "sensor_type": self.sensor_type.value,
            "last_update": self.last_update.isoformat() if self.last_update else None,
        }
    
    def __repr__(self) -> str:
        location = f"{self.room_name}" if self.room_name else "unassigned"
        return f"Sensor('{self.name}' @ {location}, {self.value}{self.unit})"


@dataclass
class Gateway:
    """
    Represents a Controme Gateway.
    Maps to Home Assistant device for grouping.
    
    The gateway provides system-wide metrics like overall heating demand
    based on average valve positions across all rooms.
    """
    gateway_id: str
    name: str
    ip_address: Optional[str] = None
    firmware_version: Optional[str] = None
    
    # System-wide heating metrics
    rooms: List['Room'] = None
    
    @property
    def unique_id(self) -> str:
        """Unique identifier for Home Assistant"""
        return f"controme_gateway_{self.gateway_id}"
    
    @property
    def device_info(self) -> Dict[str, Any]:
        """Device information for Home Assistant device registry"""
        device = Device(
            identifiers=self.gateway_id,
            name=self.name,
            model="Controme Gateway",
            sw_version=self.firmware_version,
        )
        return device.to_device_info()
    
    @property
    def system_average_valve_position(self) -> Optional[float]:
        """
        Calculate average valve position across all rooms in the system.
        This represents the overall heating demand of the entire building.
        
        Returns:
            Average valve position (0-100%) or None if no rooms available
        """
        if not self.rooms:
            return None
        
        # Collect all valve positions from all rooms
        all_valve_positions = []
        for room in self.rooms:
            if room.valve_positions:
                all_valve_positions.extend(room.valve_positions)
        
        if not all_valve_positions:
            return None
        
        return round(sum(all_valve_positions) / len(all_valve_positions), 1)
    
    @property
    def system_average_relative_valve_position(self) -> Optional[float]:
        """
        Calculate average RELATIVE valve position across all rooms.
        This accounts for hydraulic balancing and shows true system demand.
        
        Example: If valves are at [70% of 76%, 80% of 99%] this shows true demand
        better than simple average which would ignore balancing limits.
        
        Returns:
            Average relative valve position (0-100%) or None if unavailable
        """
        if not self.rooms:
            return None
        
        # Collect all relative valve positions from all rooms
        all_relative_positions = []
        for room in self.rooms:
            relative_positions = room.relative_valve_positions
            if relative_positions:
                all_relative_positions.extend(relative_positions)
        
        if not all_relative_positions:
            return None
        
        return round(sum(all_relative_positions) / len(all_relative_positions), 1)
    
    @property
    def system_heating_demand(self) -> str:
        """
        Human-readable heating demand status.
        Uses relative valve position if available (accounts for hydraulic balancing),
        otherwise falls back to absolute position.
        """
        # Prefer relative position for more accurate demand assessment
        avg = self.system_average_relative_valve_position
        if avg is None:
            avg = self.system_average_valve_position
        
        if avg is None:
            return "Unknown"
        elif avg < 10:
            return "Very Low"
        elif avg < 30:
            return "Low"
        elif avg < 50:
            return "Medium"
        elif avg < 70:
            return "High"
        else:
            return "Very High"
    
    @property
    def active_heating_rooms(self) -> int:
        """Count of rooms currently actively heating (valve > 0%)"""
        if not self.rooms:
            return 0
        return sum(1 for room in self.rooms if room.is_heating)
    
    @property
    def total_rooms(self) -> int:
        """Total number of rooms in the system"""
        return len(self.rooms) if self.rooms else 0
    
    @property
    def attributes(self) -> Dict[str, Any]:
        """Additional attributes for Home Assistant"""
        attrs = {
            "gateway_id": self.gateway_id,
            "ip_address": self.ip_address,
            "firmware_version": self.firmware_version,
            "total_rooms": self.total_rooms,
            "active_heating_rooms": self.active_heating_rooms,
            "system_average_valve_position": self.system_average_valve_position,
            "system_heating_demand": self.system_heating_demand,
        }
        
        # Add relative position if available
        if self.system_average_relative_valve_position is not None:
            attrs["system_average_relative_valve_position"] = self.system_average_relative_valve_position
        
        return attrs
    
    def __repr__(self) -> str:
        demand = f", demand={self.system_heating_demand}" if self.rooms else ""
        return f"Gateway('{self.name}', {self.active_heating_rooms}/{self.total_rooms} heating{demand})"
