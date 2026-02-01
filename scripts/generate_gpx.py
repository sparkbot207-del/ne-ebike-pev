#!/usr/bin/env python3
"""
Generate GPX files for trails from our trail data.
Creates simple waypoint GPX files that can be loaded into any GPS app.
"""

import json
import os
from datetime import datetime

GPX_TEMPLATE = '''<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="NE E-Bike and PEV Community"
     xmlns="http://www.topografix.com/GPX/1/1"
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">
  <metadata>
    <name>{name}</name>
    <desc>{description}</desc>
    <author>
      <name>NE E-Bike and PEV Community</name>
      <link href="https://sparkbot207-del.github.io/ne-ebike-pev/">
        <text>NE E-Bike and PEV</text>
      </link>
    </author>
    <time>{timestamp}</time>
  </metadata>
  <wpt lat="{trailhead_lat}" lon="{trailhead_lng}">
    <name>{name} - Trailhead</name>
    <desc>Start point for {name}</desc>
    <sym>Trailhead</sym>
  </wpt>
  <wpt lat="{center_lat}" lon="{center_lng}">
    <name>{name} - Center</name>
    <desc>{description}</desc>
    <sym>Trail</sym>
  </wpt>
</gpx>
'''

def load_trails():
    """Load trail data from JSON."""
    with open('data/trails.json', 'r') as f:
        data = json.load(f)
    return data['trails']

def generate_gpx(trail):
    """Generate GPX content for a trail."""
    return GPX_TEMPLATE.format(
        name=trail['name'],
        description=trail.get('description', ''),
        timestamp=datetime.now().isoformat(),
        trailhead_lat=trail.get('trailheadLat', trail['lat']),
        trailhead_lng=trail.get('trailheadLng', trail['lng']),
        center_lat=trail['lat'],
        center_lng=trail['lng']
    )

def save_gpx_files(trails, output_dir='gpx'):
    """Save GPX files for all trails."""
    os.makedirs(output_dir, exist_ok=True)
    
    generated = []
    for trail in trails:
        # Create safe filename
        filename = trail['id'] + '.gpx'
        filepath = os.path.join(output_dir, filename)
        
        gpx_content = generate_gpx(trail)
        
        with open(filepath, 'w') as f:
            f.write(gpx_content)
        
        generated.append({
            'id': trail['id'],
            'name': trail['name'],
            'file': filename
        })
        print(f"Generated: {filename}")
    
    return generated

def update_trails_json(trails, gpx_files):
    """Update trails.json with GPX file references."""
    gpx_map = {g['id']: g['file'] for g in gpx_files}
    
    for trail in trails:
        if trail['id'] in gpx_map:
            trail['gpxFile'] = 'gpx/' + gpx_map[trail['id']]
    
    with open('data/trails.json', 'w') as f:
        json.dump({'trails': trails, 'metadata': {
            'lastUpdated': datetime.now().isoformat(),
            'gpxGenerated': True
        }}, f, indent=2)
    
    print(f"\nUpdated trails.json with GPX references")

def main():
    print("=" * 50)
    print("GPX File Generator for NE E-Bike Trails")
    print("=" * 50)
    print()
    
    trails = load_trails()
    print(f"Loaded {len(trails)} trails")
    print()
    
    gpx_files = save_gpx_files(trails)
    print(f"\nGenerated {len(gpx_files)} GPX files")
    
    update_trails_json(trails, gpx_files)

if __name__ == "__main__":
    main()
