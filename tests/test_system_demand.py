#!/usr/bin/env python3
"""
Test script for system-wide heating demand calculation.
Demonstrates the Gateway's system_average_valve_position attribute.
"""

from controme_scraper.controller import ContromeController
from controme_scraper.models import Gateway
import keyring
from datetime import datetime


def print_separator(char='=', length=70):
    print(char * length)


def print_section(title):
    print(f"\n{title}")
    print_separator('-')


def main():
    # Load credentials from keychain
    host = keyring.get_password('controme_scraper', 'host')
    user = keyring.get_password('controme_scraper', 'user')
    password = keyring.get_password('controme_scraper', 'password')
    
    # Initialize controller
    controller = ContromeController(host=host, username=user, password=password)
    
    # Header
    print_separator('=')
    print(f"🏠 CONTROME SYSTEM HEATING DEMAND ANALYSIS")
    print(f"⏰ Live-Abfrage: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print_separator('=')
    
    # Get all rooms
    print("\n📊 Lade Raumdaten...")
    rooms = controller.get_rooms()
    
    # Create Gateway object with rooms
    gateway = Gateway(
        gateway_id="main",
        name="Controme Gateway",
        ip_address=host.replace("http://", "").rstrip("/"),
        firmware_version="Unknown",
        rooms=rooms
    )
    
    # Display system-wide metrics
    print_section("🔥 SYSTEM-ÜBERSICHT")
    print(f"Gateway: {gateway.name}")
    print(f"IP-Adresse: {gateway.ip_address}")
    print(f"Räume gesamt: {gateway.total_rooms}")
    print(f"Aktiv heizend: {gateway.active_heating_rooms}")
    print(f"\n🎯 Durchschnittliche Ventilposition: {gateway.system_average_valve_position}%")
    print(f"📈 Heizbedarf: {gateway.system_heating_demand}")
    
    # Display individual room details
    print_section("📍 RAUM-DETAILS")
    
    for room in rooms:
        heating_icon = "🔥" if room.is_heating else "❄️"
        print(f"\n{heating_icon} {room.name}")
        print(f"   Ziel: {room.target_temperature}°C | Aktuell: {room.current_temperature}°C")
        print(f"   Ventile: {room.valve_positions} → Ø {room.average_valve_position}%")
    
    # System statistics
    print_section("📈 STATISTIKEN")
    
    all_valves = []
    for room in rooms:
        if room.valve_positions:
            all_valves.extend(room.valve_positions)
    
    if all_valves:
        print(f"Gesamtzahl Ventile: {len(all_valves)}")
        print(f"Minimum: {min(all_valves)}%")
        print(f"Maximum: {max(all_valves)}%")
        print(f"Durchschnitt: {gateway.system_average_valve_position}%")
        print(f"Offene Ventile (>0%): {sum(1 for v in all_valves if v > 0)}/{len(all_valves)}")
    
    # Heating recommendation
    print_section("💡 EMPFEHLUNG")
    
    avg_valve = gateway.system_average_valve_position
    if avg_valve is None:
        print("⚠️  Keine Daten verfügbar")
    elif avg_valve < 10:
        print("✅ Sehr geringer Heizbedarf - Heizung könnte reduziert werden")
    elif avg_valve < 30:
        print("✅ Geringer Heizbedarf - Heizung läuft effizient")
    elif avg_valve < 50:
        print("⚠️  Mittlerer Heizbedarf - Heizung arbeitet normal")
    elif avg_valve < 70:
        print("🔥 Hoher Heizbedarf - Heizung könnte optimiert werden")
    else:
        print("🔥 Sehr hoher Heizbedarf - Vorlauftemperatur prüfen!")
    
    print_separator('=')
    print()


if __name__ == "__main__":
    main()
