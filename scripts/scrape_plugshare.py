#!/usr/bin/env python3
"""
PlugShare Scraper for New England E-Bike Charging Stations
Pulls J1772 (Level 2) and NEMA (wall outlet) charging locations.

Note: PlugShare has rate limits. Run sparingly and cache results.
"""

import json
import time
import requests
from datetime import datetime

# New England state bounding boxes (approximate)
NE_STATES = {
    "CT": {"name": "Connecticut", "bounds": {"sw_lat": 40.95, "sw_lng": -73.73, "ne_lat": 42.05, "ne_lng": -71.78}},
    "ME": {"name": "Maine", "bounds": {"sw_lat": 42.97, "sw_lng": -71.08, "ne_lat": 47.46, "ne_lng": -66.93}},
    "MA": {"name": "Massachusetts", "bounds": {"sw_lat": 41.24, "sw_lng": -73.50, "ne_lat": 42.89, "ne_lng": -69.93}},
    "NH": {"name": "New Hampshire", "bounds": {"sw_lat": 42.70, "sw_lng": -72.56, "ne_lat": 45.31, "ne_lng": -70.70}},
    "RI": {"name": "Rhode Island", "bounds": {"sw_lat": 41.15, "sw_lng": -71.86, "ne_lat": 42.02, "ne_lng": -71.12}},
    "VT": {"name": "Vermont", "bounds": {"sw_lat": 42.73, "sw_lng": -73.44, "ne_lat": 45.02, "ne_lng": -71.46}}
}

# Connector types we care about for e-bikes
# 1 = Wall Outlet (NEMA 5-15)
# 2 = J1772
# 6 = NEMA 14-50
CONNECTOR_TYPES = {
    1: "NEMA 5-15 (Wall Outlet)",
    2: "J1772",
    6: "NEMA 14-50"
}

def fetch_plugshare_data():
    """
    Fetch charging station data from PlugShare.
    
    Note: PlugShare's public API is limited. This uses their web endpoint
    which may require updates if they change their site structure.
    
    For production use, apply for their official API access.
    """
    
    # PlugShare uses a tile-based system. We'll use their directory pages instead.
    # The directory at https://www.plugshare.com/directory/us lists by state
    
    all_stations = []
    
    # For now, we'll create sample data structure that matches what we'd get from PlugShare
    # In production, this would make actual API calls or scrape the directory
    
    print("Note: PlugShare scraping requires API access or careful web scraping.")
    print("Creating sample data structure for development...")
    
    # Sample charging stations for demo purposes
    # These would be replaced with actual scraped data
    sample_stations = [
        {
            "id": "sample-1",
            "name": "Portland Public Library",
            "address": "5 Monument Square, Portland, ME",
            "lat": 43.6591,
            "lng": -70.2568,
            "state": "ME",
            "connectorType": "J1772",
            "connectorId": 2,
            "access": "Public",
            "hours": "24/7",
            "cost": "Free",
            "network": "ChargePoint"
        },
        {
            "id": "sample-2",
            "name": "Boston Common Garage",
            "address": "0 Charles St, Boston, MA",
            "lat": 42.3551,
            "lng": -71.0657,
            "state": "MA",
            "connectorType": "J1772",
            "connectorId": 2,
            "access": "Public",
            "hours": "24/7",
            "cost": "$2/hour",
            "network": "EVgo"
        },
        {
            "id": "sample-3", 
            "name": "Providence Place Mall",
            "address": "1 Providence Place, Providence, RI",
            "lat": 41.8301,
            "lng": -71.4150,
            "state": "RI",
            "connectorType": "J1772",
            "connectorId": 2,
            "access": "Public",
            "hours": "Mall hours",
            "cost": "Free while shopping",
            "network": "Tesla Destination"
        }
    ]
    
    return sample_stations

def save_charging_data(stations, output_file="data/charging_stations.json"):
    """Save charging station data to JSON file."""
    
    output = {
        "stations": stations,
        "metadata": {
            "lastUpdated": datetime.now().isoformat(),
            "source": "PlugShare (sample data - replace with actual scrape)",
            "connectorTypes": CONNECTOR_TYPES,
            "totalStations": len(stations),
            "byState": {}
        }
    }
    
    # Count by state
    for station in stations:
        state = station.get("state", "Unknown")
        if state not in output["metadata"]["byState"]:
            output["metadata"]["byState"][state] = 0
        output["metadata"]["byState"][state] += 1
    
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"Saved {len(stations)} stations to {output_file}")
    return output

def main():
    print("=" * 60)
    print("PlugShare Scraper for New England E-Bike Charging")
    print("=" * 60)
    print()
    
    stations = fetch_plugshare_data()
    save_charging_data(stations)
    
    print()
    print("To get real data:")
    print("1. Apply for PlugShare API access: https://company.plugshare.com/api.html")
    print("2. Or use Open Charge Map API (free): https://openchargemap.org/site/develop/api")
    print()

if __name__ == "__main__":
    main()
