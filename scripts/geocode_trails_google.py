#!/usr/bin/env python3
"""
Geocode rail trail start/end cities using Google Geocoding API.
Only geocodes trails with "City A to City B" pattern that are missing coordinates.
"""
import json
import urllib.request
import urllib.parse
import os

DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'rail_trails.json')
API_KEY = 'AIzaSyDEt2OQDTUrF39gN-BD9pdgOyKBeHusuww'

STATE_NAMES = {
    'CT': 'Connecticut', 'ME': 'Maine', 'MA': 'Massachusetts',
    'NH': 'New Hampshire', 'RI': 'Rhode Island', 'VT': 'Vermont',
    'NY': 'New York'
}

geocode_cache = {}

def geocode(city, state_abbr):
    state = STATE_NAMES.get(state_abbr, state_abbr)
    key = f"{city}, {state}"
    
    if key in geocode_cache:
        return geocode_cache[key]
    
    params = urllib.parse.urlencode({
        'address': f"{city}, {state}, USA",
        'key': API_KEY
    })
    
    url = f"https://maps.googleapis.com/maps/api/geocode/json?{params}"
    req = urllib.request.Request(url)
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            if data['status'] == 'OK' and data['results']:
                loc = data['results'][0]['geometry']['location']
                result = (loc['lat'], loc['lng'])
                geocode_cache[key] = result
                return result
            else:
                print(f"  ⚠️  No results for: {key} (status: {data['status']})")
                geocode_cache[key] = None
                return None
    except Exception as e:
        print(f"  ❌ Error geocoding {key}: {e}")
        geocode_cache[key] = None
        return None


def main():
    with open(DATA_FILE) as f:
        data = json.load(f)
    
    trails = data['trails']
    updated = 0
    skipped = 0
    failed = 0
    already_done = 0
    
    for i, trail in enumerate(trails):
        cities = trail.get('cities', '')
        state = trail.get('state', '')
        
        if ' to ' not in cities:
            # Single city — use existing lat/lng
            trail['startLat'] = trail['lat']
            trail['startLng'] = trail['lng']
            trail['endLat'] = trail['lat']
            trail['endLng'] = trail['lng']
            skipped += 1
            continue
        
        # Skip if already geocoded
        if trail.get('startLat') and trail.get('endLat') and trail['startLat'] != trail['lat']:
            already_done += 1
            continue
        
        parts = cities.split(' to ', 1)
        start_city = parts[0].strip()
        end_city = parts[1].strip()
        
        print(f"[{i+1}/{len(trails)}] {trail['name']}: {start_city} → {end_city} ({state})")
        
        start = geocode(start_city, state)
        end = geocode(end_city, state)
        
        if start and end:
            trail['startLat'] = round(start[0], 6)
            trail['startLng'] = round(start[1], 6)
            trail['endLat'] = round(end[0], 6)
            trail['endLng'] = round(end[1], 6)
            updated += 1
            print(f"  ✅ ({start[0]:.4f},{start[1]:.4f}) → ({end[0]:.4f},{end[1]:.4f})")
        else:
            failed += 1
    
    # Save updated data
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n{'='*50}")
    print(f"Geocoded: {updated}")
    print(f"Single-city (center point): {skipped}")
    print(f"Already done: {already_done}")
    print(f"Failed: {failed}")
    print(f"Unique cities cached: {len(geocode_cache)}")


if __name__ == '__main__':
    main()
