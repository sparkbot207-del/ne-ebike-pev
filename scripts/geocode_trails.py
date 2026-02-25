#!/usr/bin/env python3
"""
Geocode rail trail start/end cities to add startLat/startLng/endLat/endLng.
Uses Nominatim (free, 1 req/sec rate limit).
"""
import json
import time
import urllib.request
import urllib.parse
import os

DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'rail_trails.json')

# State name mapping for geocoding context
STATE_NAMES = {
    'CT': 'Connecticut', 'ME': 'Maine', 'MA': 'Massachusetts',
    'NH': 'New Hampshire', 'RI': 'Rhode Island', 'VT': 'Vermont',
    'NY': 'New York'
}

geocode_cache = {}

def geocode(city, state_abbr):
    """Geocode a city name with state context using Nominatim."""
    state = STATE_NAMES.get(state_abbr, state_abbr)
    key = f"{city}, {state}"
    
    if key in geocode_cache:
        return geocode_cache[key]
    
    params = urllib.parse.urlencode({
        'q': f"{city}, {state}, USA",
        'format': 'json',
        'limit': 1,
        'countrycodes': 'us'
    })
    
    url = f"https://nominatim.openstreetmap.org/search?{params}"
    req = urllib.request.Request(url, headers={
        'Accept': 'application/json'
    })
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            if data:
                result = (float(data[0]['lat']), float(data[0]['lon']))
                geocode_cache[key] = result
                return result
            else:
                print(f"  ⚠️  No results for: {key}")
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
    
    for i, trail in enumerate(trails):
        cities = trail.get('cities', '')
        state = trail.get('state', '')
        
        if ' to ' in cities:
            parts = cities.split(' to ', 1)
            start_city = parts[0].strip()
            end_city = parts[1].strip()
            
            print(f"[{i+1}/{len(trails)}] {trail['name']}: {start_city} → {end_city} ({state})")
            
            # Geocode start
            time.sleep(1.1)  # Rate limit
            start = geocode(start_city, state)
            
            # Geocode end
            time.sleep(1.1)  # Rate limit
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
        else:
            # Single city — use existing lat/lng as both start and end
            trail['startLat'] = trail['lat']
            trail['startLng'] = trail['lng']
            trail['endLat'] = trail['lat']
            trail['endLng'] = trail['lng']
            skipped += 1
    
    # Save updated data
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n{'='*50}")
    print(f"Done! Updated: {updated}, Single-city (kept center): {skipped}, Failed: {failed}")
    print(f"Geocode cache hits: {len(geocode_cache)} unique cities")


if __name__ == '__main__':
    main()
