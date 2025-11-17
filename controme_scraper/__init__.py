"""
Controme Scraper - Python client library for Controme Smart-Heat-OS heating control systems.

This is an UNOFFICIAL library for interacting with Controme heating control systems
through their local web interface.

Basic Usage:
    >>> from controme_scraper import ContromeController
    >>> controller = ContromeController(
    ...     host="http://192.168.1.10",
    ...     username="your_username",
    ...     password="your_password",
    ...     house_id=1
    ... )
    >>> rooms = controller.get_rooms()
    >>> for room in rooms:
    ...     print(f"{room.name}: {room.current_temperature}°C")
"""

from .controller import ContromeController
from .web_client import WebClient
from .session_manager import SessionManager
from .models import (
    Room,
    Thermostat,
    Sensor,
    Gateway,
)

__version__ = "0.1.0"
__author__ = "m-bck"
__license__ = "MIT"

__all__ = [
    "ContromeController",
    "WebClient",
    "SessionManager",
    "Room",
    "Thermostat",
    "Sensor",
    "Gateway",
]
