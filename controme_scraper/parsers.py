"""
Optimized parsers for Controme AJAX endpoints.
These parsers create HomeAssistant-optimized data models from HTML responses.
"""

import re
from typing import List, Optional
from datetime import datetime
from bs4 import BeautifulSoup

from .models import Room, Thermostat, Sensor, SensorType

# LOGGING________________________________________________________________________________
from .logging_config import configure_logging

logger = configure_logging(__name__)


def parse_room_temperature_html(room_id: int, html: str, floor_name: Optional[str] = None) -> Optional[Room]:
    """
    Parse the m_raum_temp_html/{id}/ endpoint response.
    
    Args:
        room_id: The room ID
        html: HTML fragment from the endpoint
        floor_name: Optional floor name
        
    Returns:
        Room object or None if parsing fails
    """
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract room name
        room_name_elem = soup.find('span', class_='room_name')
        room_name = room_name_elem.get_text(strip=True) if room_name_elem else f"Room {room_id}"
        
        # Extract icon
        icon_elem = soup.find('span', class_='room_icon')
        icon = None
        if icon_elem:
            img = icon_elem.find('img')
            if img:
                icon = img.get('src', '')
        
        # Extract target temperature (Zieltemperatur)
        # Look for span with class 'ziel' that has an ID (not the empty slider marker)
        target_temp = None
        for span in soup.find_all('span', class_='ziel'):
            if span.get('id') and span.get_text(strip=True):
                try:
                    target_temp = float(span.get_text(strip=True))
                    break
                except ValueError:
                    continue
        
        # Also try 'soll' class for backward compatibility
        if target_temp is None:
            for span in soup.find_all('span', class_='soll'):
                if span.get('id') and span.get_text(strip=True):
                    try:
                        target_temp = float(span.get_text(strip=True))
                        break
                    except ValueError:
                        # Try value attribute
                        value_attr = span.get('value')
                        if value_attr:
                            try:
                                target_temp = float(value_attr)
                                break
                            except ValueError:
                                continue
        
        # Extract current temperature - class 'temp bold underline' or similar
        current_temp = None
        temp_elem = soup.find('span', class_='temp')
        if temp_elem:
            try:
                current_temp = float(temp_elem.get_text(strip=True))
            except ValueError:
                logger.debug(f"Could not parse current temp: {temp_elem.get_text()}")
        
        # Extract temperature offset
        offset = None
        offset_elem = soup.find('span', class_='heat5_room_offset')
        if offset_elem:
            try:
                offset_text = offset_elem.get_text(strip=True)
                offset = float(offset_text)
            except ValueError:
                logger.debug(f"Could not parse offset: {offset_text}")
        
        # Extract valve positions from beam-width-value inputs
        valve_positions = []
        beam_inputs = soup.find_all('input', class_='beam-width-value')
        for inp in beam_inputs:
            try:
                pos = int(inp.get('value', 0))
                valve_positions.append(pos)
            except (ValueError, TypeError):
                pass
        
        # Check if this is a valid room with actual data
        # Empty/unused room slots have no current_temp and no target_temp
        if current_temp is None and target_temp is None:
            logger.debug(f"Room {room_id} appears to be an empty/unused slot")
            return None
        
        room = Room(
            room_id=room_id,
            name=room_name,
            current_temperature=current_temp,
            target_temperature=target_temp,
            target_temperature_offset=offset,
            icon=icon,
            floor_name=floor_name,
            valve_positions=valve_positions,
        )
        
        logger.debug(f"Parsed room: {room}")
        return room
        
    except Exception as e:
        logger.error(f"Failed to parse room {room_id} HTML: {e}")
        return None


def parse_sensor_overview_html(html: str) -> List[Sensor]:
    """
    Parse the sensorenuebersicht endpoint response.
    
    Args:
        html: Full HTML page from sensor overview
        
    Returns:
        List of Sensor objects
    """
    sensors = []
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all floor sections
        floor_divs = soup.find_all('div', class_='ui-collapsible')
        
        for floor_div in floor_divs:
            # Extract floor name
            floor_elem = floor_div.find('span', class_='floor_name')
            floor_name = floor_elem.get_text(strip=True) if floor_elem else None
            
            # Find all room lists within this floor
            room_lists = floor_div.find_all('ul', class_='room_list')
            
            for room_ul in room_lists:
                # Extract room name
                room_elem = room_ul.find('span', class_='room_name')
                room_name = room_elem.get_text(strip=True) if room_elem else None
                
                # Extract room ID from data-id attribute
                room_id = room_ul.get('data-id')
                if room_id:
                    try:
                        room_id = int(room_id)
                    except ValueError:
                        room_id = None
                
                # Find all sensors in this room
                sensor_list = room_ul.find_all('li')
                
                for sensor_li in sensor_list:
                    link = sensor_li.find('a')
                    if not link:
                        continue
                    
                    # Extract sensor name and value
                    sensor_text = link.get_text(strip=True)
                    value_elem = link.find('small', class_='no-link')
                    
                    if not value_elem:
                        continue
                    
                    try:
                        value = float(value_elem.get_text(strip=True))
                    except ValueError:
                        logger.warning(f"Could not parse sensor value: {value_elem.get_text()}")
                        continue
                    
                    # Clean sensor name (remove value from text)
                    sensor_name = sensor_text.replace(value_elem.get_text(strip=True), '').strip()
                    
                    # Determine sensor type
                    sensor_type = SensorType.TEMPERATURE
                    if 'rücklauf' in sensor_name.lower() or 'rl ' in sensor_name.lower():
                        sensor_type = SensorType.RETURN_FLOW
                    
                    # Generate sensor ID from name
                    sensor_id = re.sub(r'[^a-z0-9_]', '_', sensor_name.lower()).strip('_')
                    
                    sensor = Sensor(
                        sensor_id=sensor_id,
                        name=sensor_name,
                        sensor_type=sensor_type,
                        room_id=room_id,
                        room_name=room_name,
                        floor_name=floor_name,
                        value=value,
                        unit="°C",
                        last_update=datetime.now(),
                    )
                    
                    sensors.append(sensor)
                    logger.debug(f"Parsed sensor: {sensor}")
        
        logger.info(f"Parsed {len(sensors)} sensors from overview")
        return sensors
        
    except Exception as e:
        logger.error(f"Failed to parse sensor overview HTML: {e}")
        return []


def parse_thermostat_html(device_id: str, html: str) -> Optional[Thermostat]:
    """
    Parse the m_setup/1/rf/?d=RFAktor*{id} endpoint response.
    
    Args:
        device_id: The device ID (e.g., "RFAktor*1")
        html: HTML fragment from the endpoint
        
    Returns:
        Thermostat object or None if parsing fails
    """
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract MAC address from header
        mac_address = None
        header = soup.find('h3')
        if header:
            header_text = header.get_text()
            mac_match = re.search(r'ID ([0-9a-f:]+)', header_text)
            if mac_match:
                mac_address = mac_match.group(1)
        
        # Helper function to get input value
        def get_input_value(input_id: str, default=None):
            elem = soup.find('input', id=input_id)
            if elem:
                if elem.get('type') == 'checkbox':
                    return elem.has_attr('checked')
                return elem.get('value', default)
            return default
        
        # Helper function to get select value
        def get_select_value(select_id: str, default=None):
            select = soup.find('select', id=select_id)
            if select:
                selected = select.find('option', selected=True)
                if selected:
                    return selected.get_text(strip=True)
            return default
        
        # Extract name
        name = get_input_value(f'{device_id}_desc')
        
        # Extract device type
        device_type = get_select_value(f'{device_id}_type')
        
        # Extract room assignment
        room_assignment = get_select_value(f'{device_id}_raum')
        room_id = None
        room_name = None
        floor_name = None
        if room_assignment and room_assignment != '---':
            # Parse "Erdgeschoss / Badezimmer"
            parts = room_assignment.split('/')
            if len(parts) == 2:
                floor_name = parts[0].strip()
                room_name = parts[1].strip()
            # Try to extract room_id from select option value
            select = soup.find('select', id=f'{device_id}_raum')
            if select:
                selected = select.find('option', selected=True)
                if selected:
                    try:
                        room_id = int(selected.get('value'))
                    except (ValueError, TypeError):
                        pass
        
        # Extract configuration
        locked = get_input_value(f'{device_id}_lock', False)
        is_main_sensor = get_input_value(f'{device_id}_mainsensor', False)
        temp_mode_temporary = get_input_value(f'{device_id}_switchmode', False)
        
        # Extract numeric settings
        try:
            sensor_offset = float(get_input_value(f'{device_id}_sensoroffset', 0.0))
        except (ValueError, TypeError):
            sensor_offset = 0.0
        
        try:
            display_brightness = int(get_input_value(f'{device_id}_dispBright', 0))
        except (ValueError, TypeError):
            display_brightness = 0
        
        try:
            send_interval = int(get_input_value(f'{device_id}_sendInterval', 60))
        except (ValueError, TypeError):
            send_interval = 60
        
        try:
            temperature_deviation = float(get_input_value(f'{device_id}_deviation', 0.0))
        except (ValueError, TypeError):
            temperature_deviation = 0.0
        
        try:
            force_send_count = int(get_input_value(f'{device_id}_forceWlan', 1))
        except (ValueError, TypeError):
            force_send_count = 1
        
        battery_saving_mode = get_input_value(f'{device_id}_dynamicBatSavingRc', False)
        
        # Extract status from the "Letzte Übertragung" paragraph
        last_update = None
        current_temp = None
        target_temp = None
        humidity = None
        firmware_version = None
        power_source = None
        
        # Find the status paragraph
        status_p = None
        for p in soup.find_all('p'):
            if 'Letzte Übertragung' in p.get_text() or 'Letzte &Uuml;bertragung' in str(p):
                status_p = p
                break
        
        if status_p:
            status_text = status_p.get_text()
            
            # Parse date/time
            date_match = re.search(r'(\d{2}\.\d{2}\.\d{4})\s*-\s*(\d{2}:\d{2})', status_text)
            if date_match:
                try:
                    last_update = datetime.strptime(
                        f"{date_match.group(1)} {date_match.group(2)}", 
                        "%d.%m.%Y %H:%M"
                    )
                except ValueError:
                    pass
            
            # Parse temperatures
            soll_match = re.search(r'Solltemperatur:\s*([\d.]+)', status_text)
            if soll_match:
                try:
                    target_temp = float(soll_match.group(1))
                except ValueError:
                    pass
            
            ist_match = re.search(r'Isttemperatur:\s*([\d.]+)', status_text)
            if ist_match:
                try:
                    current_temp = float(ist_match.group(1))
                except ValueError:
                    pass
            
            # Parse humidity
            humidity_match = re.search(r'Luftfeuchtigkeit:\s*(\d+)%', status_text)
            if humidity_match:
                try:
                    humidity = int(humidity_match.group(1))
                except ValueError:
                    pass
            
            # Parse firmware version
            version_match = re.search(r'RC Version:\s*([\d.]+)', status_text)
            if version_match:
                firmware_version = version_match.group(1)
            
            # Parse power source
            if 'Festanschluss' in status_text:
                power_source = "Festanschluss"
            elif 'Batterie' in status_text:
                power_source = "Batterie"
            
            # Parse type if not from select
            if not device_type:
                type_match = re.search(r'Typ:\s*(\w+)', status_text)
                if type_match:
                    device_type = type_match.group(1)
        
        # Check connection status from header icons
        is_connected = False
        if header:
            # Look for green checkmarks or status indicators
            status_spans = header.find_all('span', style=re.compile(r'color:\s*green', re.I))
            is_connected = len(status_spans) > 0
        
        thermostat = Thermostat(
            device_id=device_id,
            mac_address=mac_address,
            description=name or "",
            assigned_room_id=room_id,
            room_name=room_name,
            floor_name=floor_name,
            current_temperature=current_temp,
            target_temperature=target_temp,
            humidity=humidity,
            device_type=device_type or "hktControme",
            firmware_version=firmware_version,
            power_source=power_source,
            locked=locked,
            is_main_sensor=is_main_sensor,
            temp_mode_temporary=temp_mode_temporary,
            sensor_offset=sensor_offset,
            display_brightness=display_brightness,
            send_interval=send_interval,
            deviation=temperature_deviation,
            force_send_count=force_send_count,
            battery_saving_mode=battery_saving_mode,
            last_update=last_update,
            is_connected=is_connected,
        )
        
        logger.debug(f"Parsed thermostat: {thermostat}")
        return thermostat
        
    except Exception as e:
        logger.error(f"Failed to parse thermostat {device_id} HTML: {e}")
        return None


def parse_thermostat_config(device_id: str, html: str) -> Optional[dict]:
    """
    Parse the thermostat configuration page to extract all 12 configurable options.
    
    Args:
        device_id: Device ID (e.g., "RFAktor*1")
        html: HTML from /m_setup/1/rf/?d=RFAktor*{ID}
        
    Returns:
        Dictionary with all configuration values or None if parsing fails
        Example: {
            "description": "RT Bad",
            "sensor_offset": 0.0,
            "display_brightness": 15,
            "send_interval": 60,
            "deviation": 0.0,
            "force_send_count": 1,
            "device_type": "hktControme",
            "assigned_room_id": 3,
            "locked": False,
            "is_main_sensor": False,
            "temp_mode_temporary": False,
            "battery_saving_mode": False
        }
    """
    try:
        soup = BeautifulSoup(html, 'html.parser')
        config = {}
        
        # Extract device ID number from format "RFAktor*1"
        device_num = device_id.split('*')[-1] if '*' in device_id else device_id
        
        # 1. Description (Text)
        desc_input = soup.find('input', {'name': f'RFAktor*{device_num}_desc'})
        config['description'] = desc_input.get('value', '') if desc_input else ''
        
        # 2. Sensor Offset (Number: -5 to +5)
        offset_input = soup.find('input', {'name': f'RFAktor*{device_num}_sensoroffset'})
        if offset_input:
            try:
                config['sensor_offset'] = float(offset_input.get('value', 0.0))
            except ValueError:
                config['sensor_offset'] = 0.0
        else:
            config['sensor_offset'] = 0.0
        
        # 3. Display Brightness (Number: 0-30)
        bright_input = soup.find('input', {'name': f'RFAktor*{device_num}_dispBright'})
        if bright_input:
            try:
                config['display_brightness'] = int(bright_input.get('value', 15))
            except ValueError:
                config['display_brightness'] = 15
        else:
            config['display_brightness'] = 15
        
        # 4. Send Interval (Number: 60-3600 seconds)
        interval_input = soup.find('input', {'name': f'RFAktor*{device_num}_sendInterval'})
        if interval_input:
            try:
                config['send_interval'] = int(interval_input.get('value', 60))
            except ValueError:
                config['send_interval'] = 60
        else:
            config['send_interval'] = 60
        
        # 5. Temperature Deviation (Number: 0.0-0.5)
        deviation_input = soup.find('input', {'name': f'RFAktor*{device_num}_deviation'})
        if deviation_input:
            try:
                config['deviation'] = float(deviation_input.get('value', 0.0))
            except ValueError:
                config['deviation'] = 0.0
        else:
            config['deviation'] = 0.0
        
        # 6. Force Send Count (Number: 0-10)
        force_input = soup.find('input', {'name': f'RFAktor*{device_num}_forceWlan'})
        if force_input:
            try:
                config['force_send_count'] = int(force_input.get('value', 1))
            except ValueError:
                config['force_send_count'] = 1
        else:
            config['force_send_count'] = 1
        
        # 7. Device Type (Select)
        type_select = soup.find('select', {'name': f'RFAktor*{device_num}_type'})
        if type_select:
            selected_option = type_select.find('option', selected=True)
            config['device_type'] = selected_option.get('value', 'hktControme') if selected_option else 'hktControme'
        else:
            config['device_type'] = 'hktControme'
        
        # 8. Assigned Room ID (Select)
        room_select = soup.find('select', {'name': f'RFAktor*{device_num}_raum'})
        if room_select:
            selected_option = room_select.find('option', selected=True)
            if selected_option:
                room_val = selected_option.get('value', 'undef')
                if room_val != 'undef':
                    try:
                        config['assigned_room_id'] = int(room_val)
                    except ValueError:
                        config['assigned_room_id'] = None
                else:
                    config['assigned_room_id'] = None
            else:
                config['assigned_room_id'] = None
        else:
            config['assigned_room_id'] = None
        
        # 9. Locked (Checkbox)
        lock_input = soup.find('input', {'name': f'RFAktor*{device_num}_lock', 'type': 'checkbox'})
        config['locked'] = lock_input is not None and lock_input.get('checked') is not None
        
        # 10. Main Sensor (Checkbox)
        main_input = soup.find('input', {'name': f'RFAktor*{device_num}_mainsensor', 'type': 'checkbox'})
        config['is_main_sensor'] = main_input is not None and main_input.get('checked') is not None
        
        # 11. Temporary Mode / Switch Mode (Checkbox)
        switch_input = soup.find('input', {'name': f'RFAktor*{device_num}_switchmode', 'type': 'checkbox'})
        config['temp_mode_temporary'] = switch_input is not None and switch_input.get('checked') is not None
        
        # 12. Battery Saving Mode (Checkbox)
        battery_input = soup.find('input', {'name': f'RFAktor*{device_num}_dynamicBatSavingRc', 'type': 'checkbox'})
        config['battery_saving_mode'] = battery_input is not None and battery_input.get('checked') is not None
        
        logger.debug(f"Parsed thermostat config for {device_id}: {config}")
        return config
        
    except Exception as e:
        logger.error(f"Failed to parse thermostat config for {device_id}: {e}")
        return None


def parse_gateway_hardware(html: str) -> dict[int, int]:
    """
    Parse the gateway hardware configuration page to extract max valve positions.
    
    Args:
        html: HTML from /m_setup/1/hardware/gwedit/1/
        
    Returns:
        Dictionary mapping output number (1-based) to max position (0-99)
        Example: {1: 99, 2: 99, 3: 81, 4: 76, ...}
    """
    try:
        soup = BeautifulSoup(html, 'html.parser')
        max_positions = {}
        
        # Find all output range inputs
        # Format: <input type="range" name="out1" ... value="99" />
        for i in range(1, 21):  # Check outputs 1-20
            input_elem = soup.find('input', {'name': f'out{i}', 'type': 'range'})
            if input_elem and input_elem.get('value'):
                try:
                    max_pos = int(input_elem.get('value'))
                    max_positions[i] = max_pos
                    logger.debug(f"Output {i}: max position = {max_pos}%")
                except ValueError:
                    logger.warning(f"Could not parse max position for output {i}")
        
        logger.info(f"Parsed {len(max_positions)} output max positions")
        return max_positions
        
    except Exception as e:
        logger.error(f"Failed to parse gateway hardware HTML: {e}")
        return {}


def parse_actuator_config(json_data: dict) -> tuple[dict[int, list[int]], dict[str, int]]:
    """
    Parse the actuator configuration JSON to extract output-to-room and RL-to-output mappings.
    
    This replaces hardcoded mappings with dynamic configuration from the Controme system.
    
    Args:
        json_data: JSON from /m_setup/{house_id}/hardware/ac/ endpoint
                  Format: {"gateway_key": [[output_num, terminal, sensor_id, assignment, desc], ...]}
        
    Returns:
        Tuple of (room_output_mapping, rl_to_output):
        - room_output_mapping: Dict mapping room_id to list of output numbers
          Example: {1: [9, 10, 11, 12, 13, 14], 2: [8], 3: [7], ...}
        - rl_to_output: Dict mapping RL sensor number to output number
          Example: {'1.1': 1, '1.2': 2, '2.1': 8, ...}
    """
    try:
        room_output_mapping = {}
        rl_to_output = {}
        
        # Iterate through gateway configurations
        for gateway_key, outputs in json_data.items():
            logger.debug(f"Parsing actuator config for gateway: {gateway_key}")
            
            for output in outputs:
                if len(output) < 4:
                    # Skip unassigned outputs
                    continue
                
                output_num = output[0]      # 1, 2, 3, ...
                terminal = output[1]        # "Klemme 11 (12-, 13+)"
                sensor_id = output[2]       # "Sensor*2"
                assignment = output[3]      # "Raumregelung 7: Erdgeschoss/Büro RL 1.1 Büro"
                
                if not assignment:
                    continue
                
                # Extract room_id from "Raumregelung X:"
                room_match = re.search(r'Raumregelung (\d+):', assignment)
                if room_match:
                    room_id = int(room_match.group(1))
                    if room_id not in room_output_mapping:
                        room_output_mapping[room_id] = []
                    room_output_mapping[room_id].append(output_num)
                    logger.debug(f"Output {output_num} → Room {room_id}")
                
                # Extract RL sensor name from "RL X.Y"
                rl_match = re.search(r'RL ([\d.]+)', assignment)
                if rl_match:
                    rl_number = rl_match.group(1)
                    rl_to_output[rl_number] = output_num
                    logger.debug(f"RL {rl_number} → Output {output_num}")
        
        # Sort output lists for each room
        for room_id in room_output_mapping:
            room_output_mapping[room_id].sort()
        
        logger.info(f"Parsed actuator config: {len(room_output_mapping)} rooms, {len(rl_to_output)} RL sensors")
        return room_output_mapping, rl_to_output
        
    except Exception as e:
        logger.error(f"Failed to parse actuator config JSON: {e}")
        return {}, {}
