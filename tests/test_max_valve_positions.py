"""
Integration tests for max valve positions and hydraulic balancing functionality.
Requires a live Controme system and credentials stored in keyring.
"""

import logging
import pytest

from controme_scraper.models import Gateway

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def rooms_with_max(controller):
    return controller.get_rooms(include_max_positions=True)


@pytest.mark.integration
def test_max_valve_positions(rooms_with_max):
    """All rooms must have max_valve_positions with a count matching valve_positions."""
    rooms = rooms_with_max

    assert len(rooms) > 0

    for room in rooms:
        assert room.max_valve_positions, f"Room {room.name} should have max_valve_positions"
        assert len(room.max_valve_positions) == len(room.valve_positions), (
            f"Room {room.name} should have same number of max_positions as valve_positions"
        )
        for max_pos in room.max_valve_positions:
            assert 1 <= max_pos <= 99, f"Max position {max_pos} should be between 1 and 99"

    print(f"\nAll {len(rooms)} rooms have correct max_valve_positions")


@pytest.mark.integration
def test_relative_valve_positions(rooms_with_max):
    """Relative valve positions must be in [0, 100] and match manual calculation."""
    rooms = rooms_with_max

    for room in rooms:
        if not (room.valve_positions and room.max_valve_positions):
            continue

        relative_positions = room.relative_valve_positions

        assert len(relative_positions) == len(room.valve_positions)

        for rel_pos in relative_positions:
            assert 0 <= rel_pos <= 100, f"Relative position {rel_pos} should be 0-100%"

        for i, (current, max_pos) in enumerate(zip(room.valve_positions, room.max_valve_positions)):
            expected = (current / max_pos * 100) if max_pos > 0 else 0
            actual = relative_positions[i]
            assert abs(expected - actual) < 0.1, (
                f"Relative position mismatch in room {room.name}: expected {expected}, got {actual}"
            )

    print("All relative valve positions calculated correctly")


@pytest.mark.integration
def test_system_relative_demand(controller, rooms_with_max):
    """Both absolute and relative system averages must be present and the demand label must be set."""
    gateway = Gateway(
        gateway_id="test_gateway",
        name="Test Gateway",
        ip_address=controller.host,
        rooms=rooms_with_max,
    )

    abs_avg = gateway.system_average_valve_position
    rel_avg = gateway.system_average_relative_valve_position

    assert abs_avg is not None, "Absolute average should exist"
    assert rel_avg is not None, "Relative average should exist"
    assert gateway.system_heating_demand != "Unknown"

    print(f"\nSystem demand: {abs_avg}% absolute, {rel_avg}% relative")
    print(f"Heating demand label: {gateway.system_heating_demand}")


@pytest.mark.integration
def test_hydraulic_balancing_detection(rooms_with_max):
    """At least some valves should be limited below 99%, indicating hydraulic balancing."""
    rooms = rooms_with_max

    balanced_valves = 0
    total_valves = 0

    for room in rooms:
        for max_pos in room.max_valve_positions:
            total_valves += 1
            if max_pos < 99:
                balanced_valves += 1

    print(f"\nHydraulic balancing: {balanced_valves}/{total_valves} valves are limited")

    assert total_valves > 0, "Expected at least one valve"
    assert balanced_valves > 0, "Expected at least some valves with hydraulic balancing"
