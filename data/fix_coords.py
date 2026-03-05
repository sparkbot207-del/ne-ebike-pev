#!/usr/bin/env python3
"""Fix bad trail coordinates by scraping TrailLink pages and falling back to Nominatim."""

import json, re, time, urllib.request, urllib.parse, sys, functools
print = functools.partial(print, flush=True)

HEADERS = {'User-Agent': 'NEEbikeTrailBot/1.0 (trail coordinate lookup)'}

BOUNDS = {
    'CT': (40.95, 42.05, -73.73, -71.79),
    'MA': (41.19, 42.89, -73.51, -69.93),
    'ME': (43.06, 47.46, -71.08, -66.95),
    'NH': (42.70, 45.31, -72.56, -70.70),
    'RI': (41.15, 42.02, -71.86, -71.12),
    'VT': (42.73, 45.02, -73.44, -71.50),
}

def in_bounds(lat, lng, state):
    b = BOUNDS.get(state)
    if not b: return False
    return b[0] <= lat <= b[1] and b[2] <= lng <= b[3]

def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read().decode('utf-8', errors='replace')
    except Exception as e:
        return None

def scrape_traillink(url):
    html = fetch(url)
    if not html: return None, None
    
    # Try various patterns for coordinates
    patterns = [
        # startLat/startLng in JS
        (r'startLat["\s:]+(-?\d+\.?\d*)', r'startLng["\s:]+(-?\d+\.?\d*)'),
        # latitude/longitude in JSON
        (r'"latitude":\s*(-?\d+\.?\d*)', r'"longitude":\s*(-?\d+\.?\d*)'),
        # lat/lng in map URLs
        (r'center=(-?\d+\.?\d*),', r'center=-?\d+\.?\d*,(-?\d+\.?\d*)'),
        # data-lat / data-lng
        (r'data-lat="(-?\d+\.?\d*)"', r'data-lng="(-?\d+\.?\d*)"'),
        # og:latitude
        (r'og:latitude["\s]+content="(-?\d+\.?\d*)"', r'og:longitude["\s]+content="(-?\d+\.?\d*)"'),
        # geo.position
        (r'geo\.position["\s]+content="(-?\d+\.?\d*);', r'geo\.position["\s]+content="-?\d+\.?\d*;(-?\d+\.?\d*)"'),
    ]
    
    for lat_pat, lng_pat in patterns:
        lat_m = re.search(lat_pat, html)
        lng_m = re.search(lng_pat, html)
        if lat_m and lng_m:
            lat, lng = float(lat_m.group(1)), float(lng_m.group(1))
            if 25 < lat < 50 and -80 < lng < -60:
                return lat, lng
    
    # Try finding any coordinate pair that looks like New England
    coords = re.findall(r'(-?\d{2}\.\d{3,})', html)
    lats = [float(c) for c in coords if 40 < float(c) < 48]
    lngs = [float(c) for c in coords if -74 < float(c) < -66]
    if lats and lngs:
        return lats[0], lngs[0]
    
    return None, None

def geocode_nominatim(name, state):
    state_names = {'CT':'Connecticut','MA':'Massachusetts','ME':'Maine','NH':'New Hampshire','RI':'Rhode Island','VT':'Vermont'}
    q = f"{name} trail {state_names.get(state, state)}"
    url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(q)}&format=json&limit=1"
    html = fetch(url)
    if not html: return None, None
    try:
        results = json.loads(html)
        if results:
            return float(results[0]['lat']), float(results[0]['lon'])
    except:
        pass
    return None, None

def main():
    with open('trails.json') as f:
        data = json.load(f)
    
    trails = data['trails']
    bad = [(i, t) for i, t in enumerate(trails) if not t.get('topPick') and not t.get('trailheadLat')]
    
    print(f"Processing {len(bad)} trails...")
    
    stats = {'scraped': 0, 'geocoded': 0, 'failed': 0, 'out_of_bounds': 0}
    state_stats = {}
    failed_trails = []
    
    for idx, (i, trail) in enumerate(bad):
        name = trail['name']
        state = trail['state']
        url = trail.get('websiteUrl', '')
        
        if state not in state_stats:
            state_stats[state] = {'fixed': 0, 'failed': 0}
        
        # Try scraping
        lat, lng = None, None
        if url:
            lat, lng = scrape_traillink(url)
            time.sleep(1.5)
        
        source = 'scrape'
        if lat is None:
            lat, lng = geocode_nominatim(name, state)
            source = 'geocode'
            time.sleep(1.1)
        
        if lat is not None and lng is not None:
            if in_bounds(lat, lng, state):
                trails[i]['lat'] = round(lat, 6)
                trails[i]['lng'] = round(lng, 6)
                stats['scraped' if source == 'scrape' else 'geocoded'] += 1
                state_stats[state]['fixed'] += 1
                print(f"  [{idx+1}/{len(bad)}] ✓ {name} ({state}) -> {lat:.4f}, {lng:.4f} [{source}]")
            else:
                stats['out_of_bounds'] += 1
                state_stats[state]['failed'] += 1
                failed_trails.append(f"{name} ({state}) - out of bounds: {lat:.4f}, {lng:.4f}")
                print(f"  [{idx+1}/{len(bad)}] ⚠ {name} ({state}) - OUT OF BOUNDS {lat:.4f}, {lng:.4f}")
        else:
            stats['failed'] += 1
            state_stats[state]['failed'] += 1
            failed_trails.append(f"{name} ({state}) - no coords found")
            print(f"  [{idx+1}/{len(bad)}] ✗ {name} ({state}) - FAILED")
        
        if (idx + 1) % 20 == 0:
            print(f"  --- Progress: {idx+1}/{len(bad)} ---")
    
    # Write back
    with open('trails.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    # Summary
    print(f"\n{'='*50}")
    print(f"SUMMARY")
    print(f"{'='*50}")
    print(f"Scraped:       {stats['scraped']}")
    print(f"Geocoded:      {stats['geocoded']}")
    print(f"Out of bounds: {stats['out_of_bounds']}")
    print(f"Failed:        {stats['failed']}")
    print(f"Total fixed:   {stats['scraped'] + stats['geocoded']}")
    print(f"\nPer state:")
    for state in sorted(state_stats.keys()):
        s = state_stats[state]
        print(f"  {state}: {s['fixed']} fixed, {s['failed']} failed")
    
    if failed_trails:
        print(f"\nFailed trails:")
        for t in failed_trails:
            print(f"  - {t}")

if __name__ == '__main__':
    main()
