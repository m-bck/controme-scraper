from typing import Any, Dict, List, Optional
import requests
from .models import Room, Thermostat, Sensor
from .parsers import (
    parse_room_temperature_html,
    parse_thermostat_html,
    parse_sensor_overview_html,
    parse_gateway_hardware,
    parse_actuator_config
)
from .url_constants import Urls

# LOGGING________________________________________________________________________________
from .logging_config import configure_logging

logger = configure_logging(__name__)

class WebClient:
    def __init__(self, url: str, session: requests.Session, house_id: int = 1):
        """
        Initializes the WebClient with the given URL and requests.Session.

        Args:
            url (str): The base URL for making requests.
            session (requests.Session): The session for making requests.
            house_id (int): The house ID in the Controme system (default: 1).
        """
        self._url = url
        self._session = session
        self._house_id = house_id

    def _get_site(self, url: str, params: Dict[str, Any] = None) -> str:
        """
        Retrieves the content of a webpage with the specified URL and optional GET parameters.

        Args:
            url (str): The specific URL to retrieve.
            params (Dict[str, Any], optional): A dictionary of GET parameters to include in the request. Defaults to None.

        Returns:
            str: The content of the requested URL as a string.
        """
        if self._session is None:
            logger.warning("logon first.")
            return
        
        try:
            response = self._session.get(f"{self._url}{url}", params=params)
            response.raise_for_status() # raise an exception for HTTP errors (4xx or 5xx)
            logger.debug("url: %s; response code: %s", response.url, response.status_code)
            return response.text
        except requests.exceptions.HTTPError as e:
            logger.error("HTTP error occurred: %s", e)
        except requests.exceptions.RequestException as e:
            logger.error("An error occurred: %s", e)

    def get_rooms(self, max_rooms: int = 20) -> List[Room]:
        """
        Retrieves a list of Room objects using optimized AJAX endpoints.
        This is the new HomeAssistant-optimized method.

        Args:
            max_rooms: Maximum number of rooms to check (default 20)

        Returns:
            List[Room]: A list of Room objects.
        """
        rooms: List[Room] = []
        consecutive_empty = 0
        max_consecutive_empty = 3  # Stop after 3 consecutive empty rooms
        
        for room_id in range(1, max_rooms + 1):
            room = self.get_room(room_id)
            if room is None:
                consecutive_empty += 1
                if consecutive_empty >= max_consecutive_empty:
                    logger.debug(f"Stopping room discovery after {consecutive_empty} consecutive empty rooms")
                    break
            else:
                consecutive_empty = 0  # Reset counter
                rooms.append(room)
        
        logger.info(f"Found {len(rooms)} rooms")
        return rooms
    
    def get_room(self, room_id: int, floor_name: Optional[str] = None) -> Optional[Room]:
        """
        Retrieves a single Room by ID using the AJAX endpoint.

        Args:
            room_id: The ID of the room
            floor_name: Optional floor name for the room

        Returns:
            Room: A Room object if found, otherwise None.
        """
        url = f"m_raum_temp_html/{room_id}/"
        html = self._get_site(url)
        
        if html and len(html) > 100:  # Basic sanity check
            return parse_room_temperature_html(room_id, html, floor_name)
        
        logger.debug(f"Room {room_id} not found or returned empty response")
        return None
    
    def get_sensors(self) -> List[Sensor]:
        """
        Retrieves all sensors using the sensor overview endpoint.
        This is the new HomeAssistant-optimized method.

        Returns:
            List[Sensor]: A list of Sensor objects.
        """
        html = self._get_site(Urls.SENSOREN.value)
        if html:
            return parse_sensor_overview_html(html)
        return []
    
    def get_thermostats(self, max_devices: int = 20, include_config: bool = True) -> List[Thermostat]:
        """
        Retrieves a list of Thermostat objects.
        This is the new HomeAssistant-optimized method.

        Args:
            max_devices: Maximum number of devices to check (default 20)
            include_config: If True, also fetch configuration from RF config page

        Returns:
            List[Thermostat]: A list of Thermostat objects.
        """
        thermostats: List[Thermostat] = []
        
        for device_id in range(1, max_devices + 1):
            thermostat = self.get_thermostat(device_id, include_config=include_config)
            if thermostat is None:
                # Continue checking a few more in case of gaps
                continue
            thermostats.append(thermostat)
        
        logger.info(f"Found {len(thermostats)} thermostats")
        return thermostats
    
    def get_thermostat(self, device_num: int, include_config: bool = True) -> Optional[Thermostat]:
        """
        Retrieves a single Thermostat by device number.

        Args:
            device_num: The device number (will be converted to RFAktor*N format)
            include_config: If True, also fetch configuration from RF config page

        Returns:
            Thermostat: A Thermostat object if found, otherwise None.
        """
        device_id = f"RFAktor*{device_num}"
        params = {"d": device_id}
        url = f"m_setup/{self._house_id}/rf/"
        html = self._get_site(url, params=params)
        
        if not html or len(html) < 100:
            logger.debug(f"Thermostat {device_id} not found or returned empty response")
            return None
        
        # Parse basic thermostat info
        thermostat = parse_thermostat_html(device_id, html)
        if not thermostat:
            return None
        
        # Optionally fetch and merge configuration
        if include_config:
            config = self.get_thermostat_config(device_id)
            if config:
                # Update thermostat with config values
                thermostat.description = config.get('description', thermostat.description or '')
                thermostat.sensor_offset = config.get('sensor_offset', 0.0)
                thermostat.display_brightness = config.get('display_brightness', 15)
                thermostat.send_interval = config.get('send_interval', 60)
                thermostat.deviation = config.get('deviation', 0.0)
                thermostat.force_send_count = config.get('force_send_count', 1)
                thermostat.device_type = config.get('device_type', 'hktControme')
                thermostat.assigned_room_id = config.get('assigned_room_id')
                thermostat.locked = config.get('locked', False)
                thermostat.is_main_sensor = config.get('is_main_sensor', False)
                thermostat.temp_mode_temporary = config.get('temp_mode_temporary', False)
                thermostat.battery_saving_mode = config.get('battery_saving_mode', False)
        
        return thermostat
    
    def get_thermostat_config(self, device_id: str) -> Optional[dict]:
        """
        Retrieves thermostat configuration from /m_setup/1/rf/ endpoint.

        Args:
            device_id: The device ID (e.g., "RFAktor*1")

        Returns:
            dict: Configuration dictionary with all 12 options, or None if failed
        """
        from .parsers import parse_thermostat_config
        
        params = {"d": device_id}
        html = self._get_site("/m_setup/1/rf/", params=params)
        
        if html and len(html) > 100:
            return parse_thermostat_config(device_id, html)
        
        logger.warning(f"Could not fetch config for {device_id}")
        return None
    
    def set_thermostat_parameter(self, device_id: int, type: str, value: str) -> bool:
        """
        Updates a thermostat parameter with the specified type and value.

        Args:
            device_id (int): The device ID.
            type (str): The parameter type to be updated.
            value (str): The new parameter value.

        Returns:
            bool: True if the parameter was updated successfully, otherwise False.
        """
        params = {"dev": f"RFAktor*{device_id}", "type": type, "val": value}
        logger.debug("update parameter: %s", str(params))
        url = f"m_setup/{self._house_id}/rf/"
        response = self._get_site(url, params=params)
        return len(response) > 0
    
    def set_room_temperature(self, room_id: int, temperature: float) -> bool:
        """
        Sets the target temperature for a room.
        
        Args:
            room_id: The room ID
            temperature: Target temperature in °C (e.g., 21.5)
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Controme expects integer temperature (22 for 22°C)
        # Round to nearest 0.5°C
        temp_rounded = round(temperature * 2) / 2
        temp_value = int(temp_rounded)
        
        logger.debug(f"Setting room {room_id} temperature to {temp_value}°C")
        
        url = f"m_raum/{room_id}/"
        data = {"slidernumber": str(temp_value)}
        
        try:
            response = self._session.post(f"{self._url}{url}", data=data)
            response.raise_for_status()
            logger.info(f"Successfully set room {room_id} temperature to {temp_value}°C")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to set room temperature: {e}")
            return False
    
    def get_gateway_hardware(self, house_id: int = 1) -> Dict[int, int]:
        """
        Retrieves gateway hardware configuration including max valve positions.
        
        This fetches the hydraulic balancing configuration which shows the
        maximum allowed position for each valve output (1-14+).
        
        Args:
            house_id: House ID (default: 1)
        
        Returns:
            Dict[int, int]: Mapping of output number (1-based) to max position (0-99%)
                           Example: {1: 99, 2: 99, 3: 81, 4: 76, ...}
        """
        logger.debug(f"Gateway hardware config abrufen (house_id={house_id})")
        html = self._get_site(f"m_setup/{house_id}/hardware/gwedit/1/")
        if html:
            return parse_gateway_hardware(html)
        return {}
    
    def get_actuator_config(self, house_id: int = 1) -> tuple[Dict[int, List[int]], Dict[str, int]]:
        """
        Retrieves actuator configuration mappings from the Controme system.
        
        This fetches the output-to-room and RL-sensor-to-output mappings dynamically,
        eliminating the need for hardcoded configuration.
        
        Args:
            house_id: House ID (default: 1)
        
        Returns:
            Tuple of (room_output_mapping, rl_to_output):
            - room_output_mapping: Dict mapping room_id to list of output numbers
              Example: {1: [9, 10, 11, 12, 13, 14], 2: [8], 3: [7], ...}
            - rl_to_output: Dict mapping RL sensor number to output number
              Example: {'1.1': 1, '1.2': 2, '2.1': 8, ...}
        """
        logger.debug(f"Actuator config abrufen (house_id={house_id})")
        url = f"m_setup/{house_id}/hardware/ac/"
        
        try:
            response = self._session.get(f"{self._url}{url}")
            response.raise_for_status()
            json_data = response.json()
            return parse_actuator_config(json_data)
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch actuator config: {e}")
            return {}, {}
        except ValueError as e:
            logger.error(f"Failed to parse actuator config JSON: {e}")
            return {}, {}

    def set_room_temperature(self, room_id: int, temperature: float) -> bool:
        """
        Set the target temperature for a room.
        
        Args:
            room_id: The room ID to set temperature for
            temperature: Target temperature in Celsius (will be rounded to nearest 0.5°C)
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Round to nearest 0.5°C
        temp_rounded = round(temperature * 2) / 2
        
        logger.debug(f"Setting room {room_id} temperature to {temp_rounded}°C")
        url = f"m_raum/{room_id}/"
        data = {"slidernumber": str(int(temp_rounded))}
        
        try:
            response = self._session.post(f"{self._url}{url}", data=data)
            response.raise_for_status()
            logger.info(f"Successfully set room {room_id} temperature to {temp_rounded}°C")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to set room temperature: {e}")
            return False
