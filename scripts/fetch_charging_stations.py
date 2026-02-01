#!/usr/bin/env python3
"""
Fetch EV Charging Stations from NREL Alternative Fuel Data Center API
Free API - uses DEMO_KEY for testing, get your own key for production.

API Docs: https://developer.nrel.gov/docs/transportation/alt-fuel-stations-v1/
"""

import json
import requests
from datetime import datetime
import os

# Get API key from environment or use demo key
API_KEY = os.environ.get('NREL_API_KEY', 'DEMO_KEY')
BASE_URL = "https://developer.nrel.gov/api/alt-fuel-stations/v1.json"

# New England states
NE_STATES = ['CT', 'MA', 'ME', 'NH', 'RI', 'VT']

# Connector types relevant for e-bikes
# NEMA connectors work with most e-bike chargers
# J1772 works with adapters
EBIKE_RELEVANT_CONNECTORS = [
    'NEMA515',   # Standard 120V wall outlet
    'NEMA520',   # 120V 20A outlet  
    'NEMA1450',  # 240V outlet (dryer plug)
    'J1772',     # Level 2 (with adapter)
]

def fetch_all_stations():
    """Fetch all electric charging stations in New England."""
    
    params = {
        'api_key': API_KEY,
        'status': 'E',  # Existing/operational only
        'fuel_type': 'ELEC',
        'state': ','.join(NE_STATES),
        'access': 'public',
        'limit': 'all'  # Get all results
    }
    
    print(f"Fetching charging stations from NREL API...")
    print(f"States: {', '.join(NE_STATES)}")
    
    response = requests.get(BASE_URL, params=params)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None
    
    data = response.json()
    print(f"Found {data['total_results']} stations")
    
    return data

def process_stations(data):
    """Process raw API data into our format."""
    
    stations = []
    
    for station in data.get('fuel_stations', []):
        # Determine connector types
        connectors = station.get('ev_connector_types', [])
        
        # Check if any e-bike friendly connectors
        has_nema = any(c.startswith('NEMA') for c in connectors)
        has_j1772 = 'J1772' in connectors
        
        # Categorize for our use
        if has_nema:
            charger_type = 'NEMA'
            icon = '🔌'
        elif has_j1772:
            charger_type = 'J1772'
            icon = '⚡'
        else:
            charger_type = 'Other'
            icon = '🔋'
        
        processed = {
            'id': station['id'],
            'name': station.get('station_name', 'Unknown'),
            'address': station.get('street_address', ''),
            'city': station.get('city', ''),
            'state': station.get('state', ''),
            'zip': station.get('zip', ''),
            'lat': station.get('latitude'),
            'lng': station.get('longitude'),
            'phone': station.get('station_phone'),
            'hours': station.get('access_days_time', ''),
            'pricing': station.get('ev_pricing', 'Unknown'),
            'network': station.get('ev_network', 'Non-Networked'),
            'connectors': connectors,
            'chargerType': charger_type,
            'icon': icon,
            'level1Count': station.get('ev_level1_evse_num', 0) or 0,
            'level2Count': station.get('ev_level2_evse_num', 0) or 0,
            'dcFastCount': station.get('ev_dc_fast_num', 0) or 0,
            'facilityType': station.get('facility_type', ''),
            'lastConfirmed': station.get('date_last_confirmed', ''),
        }
        
        stations.append(processed)
    
    return stations

def filter_ebike_friendly(stations):
    """Filter to stations most useful for e-bikes."""
    
    ebike_friendly = []
    
    for station in stations:
        connectors = station.get('connectors', [])
        
        # Must have NEMA or J1772
        has_relevant = any(
            any(c.startswith(prefix) for prefix in ['NEMA', 'J1772'])
            for c in connectors
        )
        
        if has_relevant:
            ebike_friendly.append(station)
    
    return ebike_friendly

def save_stations(stations, output_path):
    """Save processed stations to JSON."""
    
    # Count by state
    by_state = {}
    for s in stations:
        state = s.get('state', 'Unknown')
        by_state[state] = by_state.get(state, 0) + 1
    
    # Count by type
    by_type = {}
    for s in stations:
        t = s.get('chargerType', 'Unknown')
        by_type[t] = by_type.get(t, 0) + 1
    
    output = {
        'stations': stations,
        'metadata': {
            'lastUpdated': datetime.now().isoformat(),
            'source': 'NREL Alternative Fuel Data Center',
            'sourceUrl': 'https://afdc.energy.gov/stations/',
            'totalStations': len(stations),
            'byState': by_state,
            'byType': by_type
        }
    }
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nSaved {len(stations)} stations to {output_path}")
    print(f"\nBy state:")
    for state, count in sorted(by_state.items()):
        print(f"  {state}: {count}")
    print(f"\nBy type:")
    for t, count in sorted(by_type.items()):
        print(f"  {t}: {count}")

def main():
    print("=" * 60)
    print("NREL Charging Station Fetcher for NE E-Bike Community")
    print("=" * 60)
    print()
    
    # Fetch all stations
    data = fetch_all_stations()
    if not data:
        return
    
    # Process into our format
    stations = process_stations(data)
    print(f"Processed {len(stations)} stations")
    
    # Save all stations
    save_stations(stations, 'data/charging_stations_all.json')
    
    # Filter to e-bike friendly and save
    ebike_friendly = filter_ebike_friendly(stations)
    save_stations(ebike_friendly, 'data/charging_stations.json')
    
    print(f"\nE-bike friendly stations: {len(ebike_friendly)}")

if __name__ == "__main__":
    main()
