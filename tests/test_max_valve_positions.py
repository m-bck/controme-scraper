"""
Test for max valve positions and hydraulic balancing functionality.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from controme_scraper.controller import ContromeController
from controme_scraper.models import Gateway
import keyring


def test_max_valve_positions():
    """Test that max valve positions are correctly fetched and assigned."""
    host = keyring.get_password('controme_scraper', 'host')
    user = keyring.get_password('controme_scraper', 'user')
    password = keyring.get_password('controme_scraper', 'password')
    
    controller = ContromeController(host=host, username=user, password=password)
    
    # Fetch rooms with max positions
    rooms = controller.get_rooms(include_max_positions=True)
    
    # Verify all rooms have max positions
    for room in rooms:
        assert room.max_valve_positions, f"Room {room.name} should have max_valve_positions"
        assert len(room.max_valve_positions) == len(room.valve_positions), \
            f"Room {room.name} should have same number of max_positions as valve_positions"
        
        # Verify all max positions are reasonable (1-99%)
        for max_pos in room.max_valve_positions:
            assert 1 <= max_pos <= 99, f"Max position {max_pos} should be between 1 and 99"
    
    print("✅ All rooms have correct max_valve_positions")


def test_relative_valve_positions():
    """Test that relative valve positions are calculated correctly."""
    host = keyring.get_password('controme_scraper', 'host')
    user = keyring.get_password('controme_scraper', 'user')
    password = keyring.get_password('controme_scraper', 'password')
    
    controller = ContromeController(host=host, username=user, password=password)
    rooms = controller.get_rooms(include_max_positions=True)
    
    for room in rooms:
        if room.valve_positions and room.max_valve_positions:
            relative_positions = room.relative_valve_positions
            
            # Should have same count
            assert len(relative_positions) == len(room.valve_positions)
            
            # All relative positions should be 0-100%
            for rel_pos in relative_positions:
                assert 0 <= rel_pos <= 100, f"Relative position {rel_pos} should be 0-100%"
            
            # Calculate manually and verify
            for i, (current, max_pos) in enumerate(zip(room.valve_positions, room.max_valve_positions)):
                expected = (current / max_pos * 100) if max_pos > 0 else 0
                actual = relative_positions[i]
                assert abs(expected - actual) < 0.1, \
                    f"Relative position calculation incorrect: expected {expected}, got {actual}"
    
    print("✅ All relative valve positions calculated correctly")


def test_system_relative_demand():
    """Test that system-wide relative demand is calculated."""
    host = keyring.get_password('controme_scraper', 'host')
    user = keyring.get_password('controme_scraper', 'user')
    password = keyring.get_password('controme_scraper', 'password')
    
    controller = ContromeController(host=host, username=user, password=password)
    rooms = controller.get_rooms(include_max_positions=True)
    
    gateway = Gateway(
        gateway_id='test_gateway',
        name='Test Gateway',
        ip_address=host,
        rooms=rooms
    )
    
    # Verify both absolute and relative averages exist
    abs_avg = gateway.system_average_valve_position
    rel_avg = gateway.system_average_relative_valve_position
    
    assert abs_avg is not None, "Absolute average should exist"
    assert rel_avg is not None, "Relative average should exist"
    
    # Relative should typically be higher (valves closer to their limits)
    print(f"System demand: {abs_avg}% absolute, {rel_avg}% relative")
    print(f"Heating demand: {gateway.system_heating_demand}")
    
    # Verify demand is based on relative position
    assert gateway.system_heating_demand != "Unknown"
    
    print("✅ System relative demand calculated correctly")


def test_hydraulic_balancing_detection():
    """Test that we can detect hydraulic balancing (max < 99%)."""
    host = keyring.get_password('controme_scraper', 'host')
    user = keyring.get_password('controme_scraper', 'user')
    password = keyring.get_password('controme_scraper', 'password')
    
    controller = ContromeController(host=host, username=user, password=password)
    rooms = controller.get_rooms(include_max_positions=True)
    
    # Count valves with hydraulic balancing
    balanced_valves = 0
    total_valves = 0
    
    for room in rooms:
        for max_pos in room.max_valve_positions:
            total_valves += 1
            if max_pos < 99:
                balanced_valves += 1
    
    print(f"Hydraulic balancing: {balanced_valves}/{total_valves} valves are limited")
    
    # We expect at least some valves to have hydraulic balancing
    assert balanced_valves > 0, "Expected at least some valves with hydraulic balancing"
    
    print("✅ Hydraulic balancing detected")


if __name__ == '__main__':
    print("Testing max valve positions and hydraulic balancing...\n")
    
    test_max_valve_positions()
    test_relative_valve_positions()
    test_system_relative_demand()
    test_hydraulic_balancing_detection()
    
    print("\n🎉 All tests passed!")
