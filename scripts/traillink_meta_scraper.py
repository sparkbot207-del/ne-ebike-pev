#!/usr/bin/env python3
"""
TrailLink Meta Tag Scraper — lightweight, no Selenium needed.
Extracts lat/lng from meta tags on TrailLink trail pages.
"""

import json
import time
import re
import sys
import urllib.request
import urllib.error

TRAILS_FILE = "/home/bhalliday/projects/ne-ebike-staging/data/trails.json"

CENTROIDS = {
    'MA': (42.23, -71.80), 'CT': (41.60, -72.70), 'ME': (45.25, -69.25),
    'NH': (43.68, -71.58), 'RI': (41.68, -71.51), 'VT': (44.00, -72.70)
}

BOUNDS = {
    'CT': (40.95, 42.05, -73.73, -71.79),
    'MA': (41.19, 42.89, -73.51, -69.93),
    'ME': (43.06, 47.46, -71.08, -66.95),
    'NH': (42.70, 45.31, -72.56, -70.70),
    'RI': (41.15, 42.02, -71.86, -71.12),
    'VT': (42.73, 45.02, -73.44, -71.50),
}


def is_bad_coord(trail):
    state = trail.get('state', '')
    if state not in CENTROIDS:
        return False
    clat, clng = CENTROIDS[state]
    return abs(trail['lat'] - clat) < 1.0 and abs(trail['lng'] - clng) < 1.0


def is_valid_coord(lat, lng, state):
    if state not in BOUNDS:
        return True
    min_lat, max_lat, min_lng, max_lng = BOUNDS[state]
    return min_lat <= lat <= max_lat and min_lng <= lng <= max_lng


def fetch_coords(url):
    """Fetch a TrailLink page and extract lat/lng from meta tags."""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            # Handle redirects
            html = resp.read().decode('utf-8', errors='replace')

        # Extract from meta tags
        lat_match = re.search(r'latitude["\s]+content="(-?\d+\.?\d*)"', html)
        lng_match = re.search(r'longitude["\s]+content="(-?\d+\.?\d*)"', html)

        if lat_match and lng_match:
            return float(lat_match.group(1)), float(lng_match.group(1))

        return None, None
    except Exception as e:
        print(f"  Fetch error: {e}")
        return None, None


def main():
    with open(TRAILS_FILE) as f:
        data = json.load(f)
    trails = data['trails']

    # Find bad trails
    bad_trails = []
    for i, t in enumerate(trails):
        if t.get('topPick') or t.get('trailheadLat'):
            continue
        if is_bad_coord(t) and t.get('websiteUrl', '').startswith('https://www.traillink.com'):
            bad_trails.append((i, t))

    # Filter by state if specified
    target_state = sys.argv[1].upper() if len(sys.argv) > 1 else None
    if target_state:
        bad_trails = [(i, t) for i, t in bad_trails if t['state'] == target_state]
        print(f"State: {target_state} — {len(bad_trails)} trails to fix")
    else:
        print(f"All states — {len(bad_trails)} trails to fix")

    fixed = 0
    failed = 0
    failed_names = []

    for idx, (trail_idx, trail) in enumerate(bad_trails):
        url = trail['websiteUrl']
        print(f"[{idx+1}/{len(bad_trails)}] {trail['name']} ({trail['state']})...", end=" ")

        lat, lng = fetch_coords(url)

        if lat and lng and is_valid_coord(lat, lng, trail['state']):
            trails[trail_idx]['lat'] = round(lat, 6)
            trails[trail_idx]['lng'] = round(lng, 6)
            print(f"✅ {lat}, {lng}")
            fixed += 1
        else:
            print(f"❌ no coords found")
            failed += 1
            failed_names.append(trail['name'])

        # Save every 10
        if (idx + 1) % 10 == 0:
            with open(TRAILS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"  [Saved: {fixed} fixed, {failed} failed]")

        time.sleep(1.5)

    # Final save
    with open(TRAILS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\n{'='*50}")
    print(f"DONE: {fixed} fixed, {failed} failed out of {len(bad_trails)}")

    if failed_names:
        print(f"\nFailed trails:")
        for name in failed_names:
            print(f"  - {name}")


if __name__ == '__main__':
    main()
