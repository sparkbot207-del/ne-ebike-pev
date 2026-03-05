#!/usr/bin/env python3
"""Clean, deduplicate, and merge TrailLink scraped trails into curated trails.json"""

import json
import re
import shutil
from pathlib import Path

DATA_DIR = Path("/home/bhalliday/projects/ne-ebike-staging/data")

# State centroids for flagging suspicious coords
STATE_CENTROIDS = {
    "CT": (41.6032, -73.0877),
    "MA": (42.2302, -71.5301),
    "ME": (45.2538, -69.4455),
    "NH": (43.1939, -71.5724),
    "RI": (41.5801, -71.4774),
    "VT": (44.0459, -72.7107),
}

def slugify(name):
    s = name.lower().strip()
    s = re.sub(r'[^a-z0-9\s-]', '', s)
    s = re.sub(r'[\s-]+', '-', s)
    return s.strip('-')

def extract_surface(raw):
    if not raw or not isinstance(raw, str):
        return "Unknown"
    raw_lower = raw.lower().strip()
    
    # If it's already clean
    clean_surfaces = {
        "paved": "Paved", "asphalt": "Paved", "concrete": "Paved",
        "crushed stone": "Crushed Stone", "crushed gravel": "Crushed Stone",
        "gravel": "Gravel", "dirt": "Dirt", "boardwalk": "Boardwalk",
        "crushed limestone": "Crushed Stone", "sand": "Sand",
        "packed gravel": "Gravel", "cinder": "Cinder",
    }
    
    # Direct match
    for key, val in clean_surfaces.items():
        if raw_lower == key:
            return val
    
    # Look for keywords in longer text
    if "asphalt" in raw_lower or "paved" in raw_lower or "concrete" in raw_lower:
        if "gravel" in raw_lower or "crushed" in raw_lower:
            return "Paved/Gravel"
        return "Paved"
    if "crushed stone" in raw_lower or "crushed limestone" in raw_lower:
        return "Crushed Stone"
    if "crushed" in raw_lower:
        return "Crushed Stone"
    if "hardpack" in raw_lower or "hard-pack" in raw_lower:
        return "Gravel"
    if "gravel" in raw_lower:
        return "Gravel"
    if "cinder" in raw_lower:
        return "Cinder"
    if "dirt" in raw_lower:
        return "Dirt"
    if "boardwalk" in raw_lower:
        return "Boardwalk"
    if "sand" in raw_lower:
        return "Sand"
    
    return "Unknown"

def clean_description(raw, name):
    if not raw:
        return ""
    # Remove boilerplate TrailLink suffix
    desc = re.sub(r'\. View amenities,.*?on TrailLink\.?', '.', raw)
    # Remove "X spans Y from ... to ..."  boilerplate
    desc = re.sub(r'^' + re.escape(name) + r' spans [\d.]+ from .+?\.', '', desc).strip()
    if not desc or desc == '.':
        return ""
    # Clean up whitespace
    desc = re.sub(r'\s+', ' ', desc).strip()
    if desc == '.':
        return ""
    return desc

def clean_cities(raw):
    if not raw or not isinstance(raw, str):
        return None
    raw = raw.strip()
    # Garbage patterns
    garbage = ["october", "march", "here to", "mechanicsville", ""]
    if any(g in raw.lower() for g in garbage) or len(raw) < 3:
        return None
    # If it looks like actual city names (contains commas or short words)
    if re.match(r'^[A-Za-z\s,.-]+$', raw) and len(raw) < 200:
        return raw
    return None

def is_suspicious_coords(lat, lng, state):
    """Check if coords are near state centroid (likely bad data)"""
    if state not in STATE_CENTROIDS:
        return True
    clat, clng = STATE_CENTROIDS[state]
    # Within ~0.5 degrees of centroid = suspicious
    if abs(lat - clat) < 0.5 and abs(lng - clng) < 0.5:
        return True
    return False

def generate_tags(surface, description, name):
    tags = []
    if surface and surface != "Unknown":
        tags.append(surface)
    
    desc_lower = (description or "").lower() + " " + (name or "").lower()
    tag_keywords = {
        "river": "Riverside", "lake": "Lakeside", "ocean": "Coastal",
        "coast": "Coastal", "bay": "Coastal", "scenic": "Scenic",
        "mountain": "Mountain Views", "historic": "Historic",
        "urban": "Urban", "forest": "Forest", "park": "Park",
        "canal": "Canal", "bridge": "Bridges", "waterfront": "Waterfront",
    }
    for kw, tag in tag_keywords.items():
        if kw in desc_lower and tag not in tags:
            tags.append(tag)
    
    return tags if tags else ["Rail Trail"]

def main():
    # Backup
    trails_path = DATA_DIR / "trails.json"
    backup_path = DATA_DIR / "trails.json.bak"
    shutil.copy2(trails_path, backup_path)
    print(f"✓ Backup created: {backup_path}")

    # Load files
    with open(trails_path) as f:
        curated_data = json.load(f)
    with open(DATA_DIR / "rail_trails.json") as f:
        scraped_data = json.load(f)

    curated_trails = curated_data["trails"]
    scraped_trails = scraped_data["trails"]

    # Build curated lookup by id and name
    curated_by_id = {t["id"]: t for t in curated_trails}
    curated_by_name = {t["name"].lower(): t for t in curated_trails}

    # Deduplicate scraped trails - keep first non-review URL version
    seen = {}
    for t in scraped_trails:
        key = t["name"].lower() + "|" + t["state"]
        if key not in seen:
            seen[key] = t
        else:
            existing = seen[key]
            # Prefer the one without #trail-detail-reviews in URL
            if "#trail-detail-reviews" in (existing.get("url") or ""):
                seen[key] = t
            # Prefer one with rating
            elif t.get("rating") and not existing.get("rating"):
                seen[key] = t

    unique_scraped = list(seen.values())
    print(f"✓ Deduplicated: {len(scraped_trails)} → {len(unique_scraped)} unique trails")

    # Process scraped trails
    suspicious = []
    new_trails = []
    merged_count = 0

    for st in unique_scraped:
        name = st["name"]
        state = st["state"]
        slug = slugify(name)
        
        surface = extract_surface(st.get("surface"))
        desc = clean_description(st.get("description"), name)
        cities = clean_cities(st.get("cities"))
        lat = st.get("lat", 0)
        lng = st.get("lng", 0)
        length = st.get("length", 0)
        
        coord_suspicious = is_suspicious_coords(lat, lng, state)
        if coord_suspicious:
            suspicious.append(f"  ⚠ {name} ({state}) - coords ({lat:.4f}, {lng:.4f}) near state centroid")

        # Build transformed trail
        trail = {
            "id": slug,
            "name": name,
            "state": state,
            "distance": f"{length} miles" if length else "Unknown",
            "description": desc,
            "lat": round(lat, 4),
            "lng": round(lng, 4),
            "surface": surface,
            "tags": generate_tags(surface, desc, name),
            "websiteUrl": st.get("url", ""),
            "topPick": False,
        }
        if cities:
            trail["cities"] = cities

        # Check if this overlaps with curated
        curated_match = curated_by_name.get(name.lower()) or curated_by_id.get(slug)
        
        if curated_match:
            # Merge: curated wins, supplement missing fields
            merged = dict(curated_match)
            # Add websiteUrl from scraped if curated doesn't have TrailLink
            if "traillink.com" not in (merged.get("websiteUrl") or ""):
                merged["traillinkUrl"] = trail["websiteUrl"]
            # Add rating if available
            if st.get("rating"):
                merged["traillinkRating"] = st["rating"]
            merged_count += 1
            # Update in curated list
            for i, ct in enumerate(curated_trails):
                if ct.get("id") == curated_match.get("id"):
                    curated_trails[i] = merged
                    break
        else:
            new_trails.append(trail)

    # Final merge
    final_trails = curated_trails + new_trails
    
    # Sort by state then name
    final_trails.sort(key=lambda t: (t["state"], t["name"]))

    # State counts
    state_counts = {}
    for t in final_trails:
        s = t["state"]
        state_counts[s] = state_counts.get(s, 0) + 1

    # Write output
    output = {
        "trails": final_trails,
        "metadata": {
            "lastUpdated": "2026-03-05T09:13:00",
            "source": "Curated + TrailLink import",
            "totalTrails": len(final_trails),
        }
    }
    
    with open(trails_path, 'w') as f:
        json.dump(output, f, indent=2)

    # Summary
    print(f"\n{'='*50}")
    print(f"IMPORT SUMMARY")
    print(f"{'='*50}")
    print(f"Original curated trails: {len(curated_data['trails'])}")
    print(f"Scraped trails (raw): {len(scraped_trails)}")
    print(f"Scraped trails (deduplicated): {len(unique_scraped)}")
    print(f"Merged/overlapping: {merged_count}")
    print(f"New trails added: {len(new_trails)}")
    print(f"TOTAL trails: {len(final_trails)}")
    print(f"\nBy state:")
    for s in sorted(state_counts):
        print(f"  {s}: {state_counts[s]}")
    
    print(f"\nSuspicious coordinates ({len(suspicious)} trails):")
    for s in suspicious[:30]:
        print(s)
    if len(suspicious) > 30:
        print(f"  ... and {len(suspicious)-30} more")
    
    # Count surface types
    surface_counts = {}
    for t in final_trails:
        s = t.get("surface", "Unknown")
        surface_counts[s] = surface_counts.get(s, 0) + 1
    print(f"\nSurface types:")
    for s, c in sorted(surface_counts.items(), key=lambda x: -x[1]):
        print(f"  {s}: {c}")

    print(f"\n✓ Written to {trails_path}")

if __name__ == "__main__":
    main()
