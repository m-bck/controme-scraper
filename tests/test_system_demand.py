"""
Integration tests for system-wide heating demand calculation via the Gateway model.
Requires a live Controme system and credentials stored in keyring.
"""

import logging
import pytest

from controme_scraper.models import Gateway

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def rooms_and_gateway(controller):
    rooms = controller.get_rooms()
    gateway = Gateway(
        gateway_id="main",
        name="Controme Gateway",
        ip_address=controller.host.replace("http://", "").rstrip("/"),
        firmware_version="Unknown",
        rooms=rooms,
    )
    return rooms, gateway


@pytest.mark.integration
def test_gateway_metrics(rooms_and_gateway):
    """Verify basic gateway aggregate metrics are populated."""
    rooms, gateway = rooms_and_gateway

    assert gateway.total_rooms is not None
    assert gateway.total_rooms == len(rooms)
    assert gateway.active_heating_rooms is not None
    assert 0 <= gateway.active_heating_rooms <= gateway.total_rooms

    logger.info(f"Gateway: {gateway.name}, rooms={gateway.total_rooms}, heating={gateway.active_heating_rooms}")
    print(f"\nGateway: {gateway.name}")
    print(f"Total rooms: {gateway.total_rooms}")
    print(f"Active heating rooms: {gateway.active_heating_rooms}")


@pytest.mark.integration
def test_system_average_valve_position(rooms_and_gateway):
    """Verify the system-wide average valve position is a valid percentage."""
    rooms, gateway = rooms_and_gateway

    avg = gateway.system_average_valve_position
    assert avg is not None
    assert 0 <= avg <= 100

    print(f"\nSystem average valve position: {avg}%")
    print(f"Heating demand: {gateway.system_heating_demand}")


@pytest.mark.integration
def test_room_valve_data(rooms_and_gateway):
    """Verify each room exposes consistent valve position data."""
    rooms, _ = rooms_and_gateway

    assert len(rooms) > 0

    for room in rooms:
        print(f"\n{'Heating' if room.is_heating else 'Idle':7} | {room.name}")
        print(f"  Target: {room.target_temperature}°C  Current: {room.current_temperature}°C")
        print(f"  Valves: {room.valve_positions}  Avg: {room.average_valve_position}%")

        assert room.valve_positions is not None
        assert room.average_valve_position is not None
        assert 0 <= room.average_valve_position <= 100


@pytest.mark.integration
def test_valve_aggregate_statistics(rooms_and_gateway):
    """Verify cross-room valve statistics are self-consistent."""
    rooms, gateway = rooms_and_gateway

    all_valves = []
    for room in rooms:
        if room.valve_positions:
            all_valves.extend(room.valve_positions)

    assert len(all_valves) > 0

    print(f"\nTotal valves: {len(all_valves)}")
    print(f"Min: {min(all_valves)}%  Max: {max(all_valves)}%")
    print(f"System avg: {gateway.system_average_valve_position}%")
    print(f"Open valves (>0%): {sum(1 for v in all_valves if v > 0)}/{len(all_valves)}")

    assert min(all_valves) >= 0
    assert max(all_valves) <= 100
