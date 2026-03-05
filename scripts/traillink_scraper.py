#!/usr/bin/env python3
"""
TrailLink Selenium Scraper
Logs into TrailLink and extracts real coordinates from trail pages.
Saves progress after each trail so nothing is lost on timeout.
"""

import json
import time
import re
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

TRAILS_FILE = "/home/bhalliday/projects/ne-ebike-staging/data/trails.json"
USERNAME = "sparkbot207@gmail.com"
PASSWORD = "Unlockm3!"

# State centroids for detecting bad coords
CENTROIDS = {
    'MA': (42.23, -71.80), 'CT': (41.60, -72.70), 'ME': (45.25, -69.25),
    'NH': (43.68, -71.58), 'RI': (41.68, -71.51), 'VT': (44.00, -72.70)
}

# State bounding boxes for validation
BOUNDS = {
    'CT': (40.95, 42.05, -73.73, -71.79),
    'MA': (41.19, 42.89, -73.51, -69.93),
    'ME': (43.06, 47.46, -71.08, -66.95),
    'NH': (42.70, 45.31, -72.56, -70.70),
    'RI': (41.15, 42.02, -71.86, -71.12),
    'VT': (42.73, 45.02, -73.44, -71.50),
}


def is_bad_coord(trail):
    """Check if a trail's coordinates are suspicious (near state centroid)."""
    state = trail.get('state', '')
    if state not in CENTROIDS:
        return False
    clat, clng = CENTROIDS[state]
    return abs(trail['lat'] - clat) < 1.0 and abs(trail['lng'] - clng) < 1.0


def is_valid_coord(lat, lng, state):
    """Check if coordinates fall within state bounding box."""
    if state not in BOUNDS:
        return True
    min_lat, max_lat, min_lng, max_lng = BOUNDS[state]
    return min_lat <= lat <= max_lat and min_lng <= lng <= max_lng


def setup_driver():
    """Set up headless Chrome."""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36')
    
    service = Service('/usr/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)
    return driver


def login(driver):
    """Log into TrailLink."""
    print("Logging into TrailLink...")
    driver.get("https://www.traillink.com/login/")
    time.sleep(3)
    
    try:
        # Find and fill email field
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="email"], input[name="email"], #email'))
        )
        email_field.clear()
        email_field.send_keys(USERNAME)
        
        # Find and fill password field
        pwd_field = driver.find_element(By.CSS_SELECTOR, 'input[type="password"], input[name="password"], #password')
        pwd_field.clear()
        pwd_field.send_keys(PASSWORD)
        
        # Submit
        submit = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"], input[type="submit"]')
        submit.click()
        
        time.sleep(5)
        print(f"Login complete. Current URL: {driver.current_url}")
        return True
    except Exception as e:
        print(f"Login failed: {e}")
        # Try to continue anyway — some pages might not need login
        return False


def extract_coords_from_page(driver, url):
    """Extract lat/lng from a TrailLink trail page."""
    try:
        driver.get(url)
        time.sleep(2)
        
        page_source = driver.page_source
        
        # Method 1: Look for coordinates in map data / JavaScript
        # TrailLink often has lat/lng in their map initialization
        patterns = [
            r'"latitude"\s*:\s*(-?\d+\.?\d*)',
            r'"longitude"\s*:\s*(-?\d+\.?\d*)',
            r'lat["\s:=]+(-?\d{2}\.\d{3,})',
            r'lng["\s:=]+(-?\d{2,3}\.\d{3,})',
            r'center\s*:\s*\[?\s*(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)',
            r'LatLng\((-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)\)',
            r'position.*?(-?\d{2}\.\d{4,}).*?(-?\d{2,3}\.\d{4,})',
        ]
        
        lat, lng = None, None
        
        # Try paired patterns first
        for pattern in patterns[4:]:
            matches = re.findall(pattern, page_source)
            if matches:
                for match in matches:
                    try:
                        t_lat, t_lng = float(match[0]), float(match[1])
                        if 25 < t_lat < 50 and -80 < t_lng < -65:
                            lat, lng = t_lat, t_lng
                            break
                    except (ValueError, IndexError):
                        continue
                if lat:
                    break
        
        # Try individual lat/lng patterns
        if not lat:
            lat_matches = re.findall(patterns[0], page_source)
            lng_matches = re.findall(patterns[1], page_source)
            if lat_matches and lng_matches:
                for lm in lat_matches:
                    t_lat = float(lm)
                    if 25 < t_lat < 50:
                        lat = t_lat
                        break
                for lm in lng_matches:
                    t_lng = float(lm)
                    if -80 < t_lng < -65:
                        lng = t_lng
                        break
        
        # Method 2: Check meta tags
        if not lat:
            metas = driver.find_elements(By.CSS_SELECTOR, 'meta[property], meta[name]')
            for meta in metas:
                prop = meta.get_attribute('property') or meta.get_attribute('name') or ''
                content = meta.get_attribute('content') or ''
                if 'latitude' in prop.lower():
                    try: lat = float(content)
                    except: pass
                if 'longitude' in prop.lower():
                    try: lng = float(content)
                    except: pass
        
        # Method 3: Look for geo coordinates in structured data
        if not lat:
            scripts = driver.find_elements(By.CSS_SELECTOR, 'script[type="application/ld+json"]')
            for script in scripts:
                try:
                    data = json.loads(script.get_attribute('innerHTML'))
                    if isinstance(data, dict):
                        geo = data.get('geo', {})
                        if geo:
                            lat = float(geo.get('latitude', 0))
                            lng = float(geo.get('longitude', 0))
                            if lat and lng:
                                break
                except:
                    continue
        
        if lat and lng and 25 < lat < 50 and -80 < lng < -65:
            return lat, lng
        
        return None, None
        
    except Exception as e:
        print(f"  Error: {e}")
        return None, None


def main():
    # Load trails
    with open(TRAILS_FILE) as f:
        data = json.load(f)
    trails = data['trails']
    
    # Find trails with bad coords and TrailLink URLs
    bad_trails = []
    for i, t in enumerate(trails):
        if t.get('topPick') or t.get('trailheadLat'):
            continue
        if is_bad_coord(t) and t.get('websiteUrl', '').startswith('https://www.traillink.com'):
            bad_trails.append((i, t))
    
    print(f"Found {len(bad_trails)} trails with bad coordinates and TrailLink URLs")
    
    if not bad_trails:
        print("Nothing to do!")
        return
    
    # Filter to specific state if provided
    target_state = sys.argv[1] if len(sys.argv) > 1 else None
    if target_state:
        bad_trails = [(i, t) for i, t in bad_trails if t['state'] == target_state.upper()]
        print(f"Filtering to {target_state.upper()}: {len(bad_trails)} trails")
    
    driver = setup_driver()
    
    try:
        logged_in = login(driver)
        
        fixed = 0
        failed = 0
        
        for idx, (trail_idx, trail) in enumerate(bad_trails):
            url = trail['websiteUrl']
            print(f"[{idx+1}/{len(bad_trails)}] {trail['name']} ({trail['state']})...")
            
            lat, lng = extract_coords_from_page(driver, url)
            
            if lat and lng and is_valid_coord(lat, lng, trail['state']):
                trails[trail_idx]['lat'] = round(lat, 6)
                trails[trail_idx]['lng'] = round(lng, 6)
                print(f"  ✅ {lat}, {lng}")
                fixed += 1
            else:
                print(f"  ❌ Could not extract coordinates")
                failed += 1
            
            # Save after every 5 trails
            if (idx + 1) % 5 == 0:
                with open(TRAILS_FILE, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"  [Saved progress: {fixed} fixed, {failed} failed]")
            
            time.sleep(2)  # Be polite
        
        # Final save
        with open(TRAILS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n{'='*50}")
        print(f"DONE: {fixed} fixed, {failed} failed out of {len(bad_trails)}")
        
        # Summary by state
        state_results = {}
        for _, t in bad_trails:
            s = t['state']
            if s not in state_results:
                state_results[s] = {'fixed': 0, 'failed': 0}
        
        # Recount
        for trail_idx, trail in bad_trails:
            s = trail['state']
            if is_bad_coord(trails[trail_idx]):
                state_results[s]['failed'] += 1
            else:
                state_results[s]['fixed'] += 1
        
        for s in sorted(state_results):
            r = state_results[s]
            print(f"  {s}: {r['fixed']} fixed, {r['failed']} failed")
    
    finally:
        driver.quit()


if __name__ == '__main__':
    main()
