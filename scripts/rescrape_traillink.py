#!/usr/bin/env python3
"""
Re-scrape TrailLink for accurate trail endpoint data.
Extracts "Trail end points" field from each trail's page.
Then geocodes the endpoints using Google Geocoding API.
"""
import json
import urllib.request
import urllib.parse
import re
import time
import os
import sys

DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'rail_trails.json')
GOOGLE_API_KEY = 'AIzaSyDEt2OQDTUrF39gN-BD9pdgOyKBeHusuww'

geocode_cache = {}

def fetch_trail_endpoints(url):
    """Fetch trail page and extract endpoints."""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; NE-EBike-Planner/1.0)',
            'Accept': 'text/html'
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        
        # Extract "Trail end points:" from structured data
        match = re.search(r'Trail end points?:\s*</strong>\s*<span>(.*?)</span>', html, re.DOTALL)
        if match:
            raw = match.group(1).strip()
            raw = re.sub(r'&amp;', '&', raw)
            raw = re.sub(r'&nbsp;', ' ', raw)
            raw = re.sub(r'<[^>]+>', '', raw)
            raw = re.sub(r'\s+', ' ', raw).strip()
            return raw
        
        return None
    except Exception as e:
        return f"ERROR: {e}"


def parse_endpoints(raw_text, state):
    """Parse endpoint text into two location strings for geocoding."""
    if not raw_text or raw_text.startswith('ERROR'):
        return None, None
    
    # Try splitting on " and " or " to "
    # First check for parenthesized city names: "Address (City) and Address (City)"
    cities = re.findall(r'\(([^)]+)\)', raw_text)
    if len(cities) >= 2:
        return f"{cities[0]}, {state}", f"{cities[-1]}, {state}"
    
    # Try "X to Y" pattern
    if ' to ' in raw_text:
        parts = raw_text.split(' to ', 1)
        return f"{parts[0].strip()}, {state}", f"{parts[1].strip()}, {state}"
    
    # Try "X and Y" pattern  
    if ' and ' in raw_text:
        parts = raw_text.split(' and ', 1)
        return f"{parts[0].strip()}, {state}", f"{parts[1].strip()}, {state}"
    
    return None, None


def geocode(location):
    """Geocode a location string using Google Geocoding API."""
    if not location:
        return None
    
    # Clean up location for geocoding
    clean = re.sub(r'\b(about|approximately)\s+[\d.]+\s+miles?\s+(north|south|east|west)\s+of\s+', '', location)
    
    key = clean.lower().strip()
    if key in geocode_cache:
        return geocode_cache[key]
    
    params = urllib.parse.urlencode({
        'address': clean + ', USA',
        'key': GOOGLE_API_KEY
    })
    
    url = f"https://maps.googleapis.com/maps/api/geocode/json?{params}"
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            if data['status'] == 'OK' and data['results']:
                loc = data['results'][0]['geometry']['location']
                result = (round(loc['lat'], 6), round(loc['lng'], 6))
                geocode_cache[key] = result
                return result
            else:
                geocode_cache[key] = None
                return None
    except Exception as e:
        geocode_cache[key] = None
        return None


STATE_FULL = {
    'CT': 'Connecticut', 'ME': 'Maine', 'MA': 'Massachusetts',
    'NH': 'New Hampshire', 'RI': 'Rhode Island', 'VT': 'Vermont',
    'NY': 'New York'
}


def main():
    with open(DATA_FILE) as f:
        data = json.load(f)
    
    trails = data['trails']
    updated = 0
    failed = 0
    no_url = 0
    no_endpoints = 0
    
    total = len(trails)
    
    for i, trail in enumerate(trails):
        url = trail.get('url', '')
        state = STATE_FULL.get(trail.get('state', ''), trail.get('state', ''))
        
        if not url:
            no_url += 1
            continue
        
        # Skip trails that already have real endpoint data (not just center point copied)
        if (trail.get('startLat') and trail.get('endLat') and
            trail.get('startLat') != trail.get('lat') and
            trail.get('startLng') != trail.get('lng')):
            print(f"[{i+1}/{total}] {trail['name']}... ⏭️  already has endpoints")
            continue
        
        sys.stdout.write(f"[{i+1}/{total}] {trail['name']}...")
        sys.stdout.flush()
        
        # Fetch endpoints from TrailLink
        raw_endpoints = fetch_trail_endpoints(url)
        time.sleep(1.2)  # Rate limit TrailLink
        
        if not raw_endpoints or raw_endpoints.startswith('ERROR'):
            print(f" ⚠️  {raw_endpoints or 'No endpoints found'}")
            no_endpoints += 1
            # Keep existing data
            if not trail.get('startLat'):
                trail['startLat'] = trail['lat']
                trail['startLng'] = trail['lng']
                trail['endLat'] = trail['lat']
                trail['endLng'] = trail['lng']
            continue
        
        # Store raw endpoint text
        trail['endpointsRaw'] = raw_endpoints
        
        # Parse into two geocodable strings
        loc_a, loc_b = parse_endpoints(raw_endpoints, state)
        
        if not loc_a or not loc_b:
            print(f" ⚠️  Can't parse: {raw_endpoints[:80]}")
            no_endpoints += 1
            if not trail.get('startLat'):
                trail['startLat'] = trail['lat']
                trail['startLng'] = trail['lng']
                trail['endLat'] = trail['lat']
                trail['endLng'] = trail['lng']
            continue
        
        # Geocode both endpoints
        start = geocode(loc_a)
        end = geocode(loc_b)
        
        if start and end:
            trail['startLat'] = start[0]
            trail['startLng'] = start[1]
            trail['endLat'] = end[0]
            trail['endLng'] = end[1]
            # Update center point to midpoint of start/end
            trail['lat'] = round((start[0] + end[0]) / 2, 6)
            trail['lng'] = round((start[1] + end[1]) / 2, 6)
            updated += 1
            print(f" ✅ ({start[0]:.4f},{start[1]:.4f}) → ({end[0]:.4f},{end[1]:.4f})")
        else:
            failed += 1
            print(f" ❌ Geocode failed: {loc_a} / {loc_b}")
            if not trail.get('startLat'):
                trail['startLat'] = trail['lat']
                trail['startLng'] = trail['lng']
                trail['endLat'] = trail['lat']
                trail['endLng'] = trail['lng']
        
        # Save every 10 trails to avoid losing progress
        if (i + 1) % 10 == 0:
            with open(DATA_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"  💾 Saved progress ({i+1}/{total})")
    
    # Final save
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n{'='*50}")
    print(f"Updated: {updated}")
    print(f"Failed geocode: {failed}")
    print(f"No endpoints found: {no_endpoints}")
    print(f"No URL: {no_url}")
    print(f"Geocode cache: {len(geocode_cache)} unique locations")
    print(f"Total trails: {total}")


if __name__ == '__main__':
    main()
