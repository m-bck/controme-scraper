from typing import List
from .models import Room, Thermostat, Sensor
from .session_manager import SessionManager
from .url_constants import Urls
from .web_client import WebClient

# LOGGING________________________________________________________________________________
from .logging_config import configure_logging

logger = configure_logging(__name__)

# CLASS  ________________________________________________________________________________
class ContromeController:
    """
    A class to interact with a Controme heating control system.
    """

    def __init__(self, host: str, username: str, password: str, house_id: int = 1):
        """
        Initialize the :class:`ContromeController` instance.

        Args:
            host (str): The host address of the Controme system.
            username (str): The username for the Controme system.
            password (str): The password for the Controme system.
            house_id (int): The house ID in the Controme system (default: 1).
        """
        logger.info("Initialsiere Controme Heizungssteuerung auf Host %s (house_id=%d)", host, house_id)
        
        # Ensure host starts with http:// or https://
        if not host.startswith(('http://', 'https://')):
            host = f"http://{host}"
        
        # Ensure host ends with trailing slash
        if not host.endswith('/'):
            host = f"{host}/"
        self.host = host
        self.house_id = house_id
        
        self.session_manager = SessionManager(
            url=host,
            user=username,
            password=password,
        )
        self.web_client = WebClient(
            host, 
            self.session_manager.logon(login_url=Urls.LOGIN.value),
            house_id=house_id
        )

    # New HomeAssistant-optimized methods
    def get_rooms(self, include_max_positions: bool = True, include_return_flow: bool = True) -> List[Room]:
        """
        Retrieve all rooms as HomeAssistant-optimized Room objects.
        
        Args:
            include_max_positions: If True, fetch gateway hardware config
                                 to include hydraulic balancing max positions
            include_return_flow: If True, fetch return flow temperatures
                               and assign to valves

        :return: A list of Room objects.
        """
        rooms = self.web_client.get_rooms()
        
        # Fetch and assign max valve positions if requested
        if include_max_positions and rooms:
            max_positions = self.web_client.get_gateway_hardware()
            if max_positions:
                self._assign_max_positions_to_rooms(rooms, max_positions)
        
        # Fetch and assign return flow temperatures if requested
        if include_return_flow and rooms:
            sensors = self.web_client.get_sensors()
            return_flow_sensors = [s for s in sensors if s.sensor_type.value == 'return_flow']
            if return_flow_sensors:
                self._assign_return_flow_to_rooms(rooms, return_flow_sensors)
        
        return rooms
    
    def _assign_max_positions_to_rooms(self, rooms: List[Room], max_positions: dict[int, int]) -> None:
        """
        Assign max valve positions from gateway hardware to rooms.
        
        Uses dynamically fetched output-to-room mapping from the Controme system.
        
        Args:
            rooms: List of Room objects to update
            max_positions: Dict mapping output number to max position
        """
        # Fetch dynamic mapping from Controme system
        room_output_mapping, _ = self.web_client.get_actuator_config(house_id=self.house_id)
        
        if not room_output_mapping:
            logger.warning("No actuator config found, max positions will not be assigned")
            return
        
        for room in rooms:
            if room.room_id in room_output_mapping:
                output_nums = room_output_mapping[room.room_id]
                room.max_valve_positions = [
                    max_positions.get(out_num, 99)  # Default to 99% if not found
                    for out_num in output_nums
                ]
                logger.debug(
                    f"Assigned max positions to {room.name} (ID {room.room_id}): {room.max_valve_positions}"
                )
    
    def _assign_return_flow_to_rooms(self, rooms: List[Room], return_flow_sensors: List['Sensor']) -> None:
        """
        Assign return flow temperatures from sensors to room valves.
        
        Uses dynamically fetched RL-to-output mapping from the Controme system.
        
        Args:
            rooms: List of Room objects to update
            return_flow_sensors: List of return flow Sensor objects
        """
        import re
        
        # Fetch dynamic mappings from Controme system
        room_output_mapping, rl_to_output = self.web_client.get_actuator_config(house_id=self.house_id)
        
        if not rl_to_output:
            logger.warning("No actuator config found, return flow temps will not be assigned")
            return
        
        # Create mapping output number → temperature
        output_to_temp = {}
        for sensor in return_flow_sensors:
            # Extract RL number from sensor name
            match = re.search(r'RL ([\d.]+)', sensor.name)
            if match:
                rl_number = match.group(1)
                if rl_number in rl_to_output:
                    output_num = rl_to_output[rl_number]
                    output_to_temp[output_num] = sensor.value
                    logger.debug(f"RL {rl_number} → Output {output_num} = {sensor.value}°C")
        
        # Assign temperatures to rooms
        for room in rooms:
            if room.room_id in room_output_mapping:
                output_nums = room_output_mapping[room.room_id]
                room.return_flow_temperatures = [
                    output_to_temp.get(out_num)  # None if not found
                    for out_num in output_nums
                ]
                logger.debug(
                    f"Assigned return flow temps to {room.name} (ID {room.room_id}): {room.return_flow_temperatures}"
                )

    def get_room(self, room_id: int) -> Room:
        """
        Retrieve a specific room by ID.

        :param room_id: The room ID.
        :return: A Room object.
        """
        return self.web_client.get_room(room_id)

    def get_sensors(self) -> List[Sensor]:
        """
        Retrieve all sensors as HomeAssistant-optimized Sensor objects.

        :return: A list of Sensor objects.
        """
        return self.web_client.get_sensors()

    def get_thermostats(self, include_config: bool = True, include_valve_data: bool = True) -> List[Thermostat]:
        """
        Retrieve all thermostats as HomeAssistant-optimized Thermostat objects.
        
        Args:
            include_config: If True, fetch all 12 configuration options
            include_valve_data: If True, assign valve positions and return flow temps

        :return: A list of Thermostat objects.
        """
        thermostats = self.web_client.get_thermostats(include_config=include_config)
        
        if include_valve_data and thermostats:
            # Get rooms to access valve data
            rooms = self.get_rooms(include_max_positions=True, include_return_flow=True)
            
            # Assign valve data from rooms to thermostats
            for thermostat in thermostats:
                if thermostat.assigned_room_id:
                    room = next((r for r in rooms if r.room_id == thermostat.assigned_room_id), None)
                    if room:
                        thermostat.valve_positions = room.valve_positions
                        thermostat.max_valve_positions = room.max_valve_positions
                        thermostat.return_flow_temperatures = room.return_flow_temperatures
                        # Also update room name if not set
                        if not thermostat.room_name:
                            thermostat.room_name = room.name
                        if not thermostat.floor_name:
                            thermostat.floor_name = room.floor_name
        
        return thermostats

    def get_thermostat(self, device_num: int) -> Thermostat:
        """
        Retrieve a specific thermostat by device number.

        :param device_num: The device number.
        :return: A Thermostat object.
        """
        return self.web_client.get_thermostat(device_num)
