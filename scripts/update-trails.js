#!/usr/bin/env node
/**
 * Rail Trail Database Updater
 * Scrapes TrailLink.com for New England rail trails
 * Run manually or via GitHub Actions
 */

const fs = require('fs');
const path = require('path');

const STATES = ['ct', 'me', 'ma', 'nh', 'ri', 'vt'];
const STATE_NAMES = { ct: 'CT', me: 'ME', ma: 'MA', nh: 'NH', ri: 'RI', vt: 'VT' };
const BASE_URL = 'https://www.traillink.com';
const OUTPUT_FILE = path.join(__dirname, '..', 'data', 'rail_trails.json');

// Rate limiting - be nice to TrailLink
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

async function fetchWithRetry(url, retries = 3) {
    for (let i = 0; i < retries; i++) {
        try {
            const response = await fetch(url, {
                headers: {
                    'User-Agent': 'NEEBikeTrailBot/1.0 (https://sparkbot207-del.github.io/ne-ebike-pev/; trail database updates)',
                    'Accept': 'text/html,application/xhtml+xml',
                }
            });
            if (response.ok) {
                return await response.text();
            }
            console.log(`  Retry ${i + 1}/${retries} for ${url} (status: ${response.status})`);
        } catch (e) {
            console.log(`  Retry ${i + 1}/${retries} for ${url} (error: ${e.message})`);
        }
        await delay(2000);
    }
    return null;
}

// Simple HTML parsing without external dependencies
function extractText(html, startMarker, endMarker) {
    const startIdx = html.indexOf(startMarker);
    if (startIdx === -1) return null;
    const afterStart = startIdx + startMarker.length;
    const endIdx = html.indexOf(endMarker, afterStart);
    if (endIdx === -1) return null;
    return html.substring(afterStart, endIdx).trim();
}

function extractTrailLinks(html) {
    const trails = [];
    const regex = /href="(\/trail\/[^"]+)"/g;
    let match;
    const seen = new Set();
    
    while ((match = regex.exec(html)) !== null) {
        let trailPath = match[1];
        // Strip URL fragments (#section) so /trail/foo/ and /trail/foo/#reviews aren't treated as separate trails
        trailPath = trailPath.split('#')[0];
        // Normalize trailing slash
        if (!trailPath.endsWith('/')) trailPath += '/';
        if (!seen.has(trailPath) && !trailPath.includes('/map') && !trailPath.includes('/photos')) {
            seen.add(trailPath);
            trails.push(BASE_URL + trailPath);
        }
    }
    return trails;
}

function parseTrailPage(html, url, state) {
    const trail = {
        name: '',
        state: STATE_NAMES[state] || state.toUpperCase(),
        length: 0,
        surface: '',
        description: '',
        lat: null,
        lng: null,
        cities: '',
        url: url,
        rating: null
    };
    
    // Extract name from title
    const titleMatch = html.match(/<h1[^>]*>([^<]+)</);
    if (titleMatch) {
        trail.name = titleMatch[1].trim().replace(/\s+Trail$/i, ' Trail');
    }
    
    // Extract length - prefer the meta description "spans X.X" or explicit Length field
    // Avoid matching promo text like "40,000 miles of trail maps"
    const descForLength = html.match(/meta name="description" content="[^"]*?spans\s+(\d+\.?\d*)/i);
    const lengthField = html.match(/Length[:\s]+(\d+\.?\d*)/i);
    const lengthMatch = descForLength || lengthField || 
                        html.match(/(?<![,\d])(\d+\.?\d*)\s*mi(?:les?)?/i);
    if (lengthMatch && parseFloat(lengthMatch[1]) > 0) {
        trail.length = parseFloat(lengthMatch[1]);
    }
    
    // Extract surface type
    const surfaceMatch = html.match(/Surface[:\s]+([^<\n]+)/i) ||
                         html.match(/(Asphalt|Crushed Stone|Gravel|Dirt|Ballast|Concrete|Boardwalk)(?:[,\s]|<)/i);
    if (surfaceMatch) {
        trail.surface = surfaceMatch[1].trim().replace(/<[^>]+>/g, '');
    }
    
    // Extract description from meta or first paragraph
    const descMatch = html.match(/meta name="description" content="([^"]+)"/) ||
                      html.match(/<p[^>]*class="[^"]*description[^"]*"[^>]*>([^<]+)</);
    if (descMatch) {
        trail.description = descMatch[1].trim().substring(0, 300);
    }
    
    // Extract coordinates - try multiple patterns TrailLink uses
    // Schema.org GeoCoordinates (most reliable)
    const schemaLatMatch = html.match(/"latitude"\s*:\s*"?(-?\d+\.\d+)"?/i);
    const schemaLngMatch = html.match(/"longitude"\s*:\s*"?(-?\d+\.\d+)"?/i);
    // Google Maps embed or data attributes
    const gmapMatch = html.match(/maps\.google[^"]*[?&]q=(-?\d+\.\d+),(-?\d+\.\d+)/) ||
                      html.match(/center=(-?\d+\.\d+),(-?\d+\.\d+)/);
    // Leaflet / JS map init
    const leafletMatch = html.match(/setView\(\[(-?\d+\.\d+),\s*(-?\d+\.\d+)/);
    // Generic lat/lng data attrs
    const dataLatMatch = html.match(/data-lat["\s=]+["']?(-?\d+\.\d+)/i);
    const dataLngMatch = html.match(/data-l(?:ng|on)["\s=]+["']?(-?\d+\.\d+)/i);

    if (schemaLatMatch && schemaLngMatch) {
        trail.lat = parseFloat(schemaLatMatch[1]);
        trail.lng = parseFloat(schemaLngMatch[1]);
    } else if (gmapMatch) {
        trail.lat = parseFloat(gmapMatch[1]);
        trail.lng = parseFloat(gmapMatch[2]);
    } else if (leafletMatch) {
        trail.lat = parseFloat(leafletMatch[1]);
        trail.lng = parseFloat(leafletMatch[2]);
    } else if (dataLatMatch && dataLngMatch) {
        trail.lat = parseFloat(dataLatMatch[1]);
        trail.lng = parseFloat(dataLngMatch[1]);
    }

    // Sanity-check coordinates — must be within continental US bounds
    if (trail.lat !== null && (trail.lat < 24 || trail.lat > 50 || trail.lng > -60 || trail.lng < -130)) {
        trail.lat = null;
        trail.lng = null;
    }

    // Extract rating — TrailLink uses itemprop="ratingValue" and aggregate patterns
    const ratingMatch = html.match(/itemprop="ratingValue"[^>]*>([\d.]+)/) ||
                        html.match(/ratingValue["\s:]+"?([\d.]+)"?/i) ||
                        html.match(/([\d.]+)\s*(?:out of 5|\/5)/i) ||
                        html.match(/averageRating["\s:]+"?([\d.]+)"?/i);
    if (ratingMatch) {
        const r = parseFloat(ratingMatch[1]);
        // Sanity check: rating must be 0-5
        if (r >= 0 && r <= 5) trail.rating = r;
    }
    
    // Extract cities/endpoints
    const citiesMatch = html.match(/(?:from|between)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:to|and)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)/i);
    if (citiesMatch) {
        trail.cities = `${citiesMatch[1]} to ${citiesMatch[2]}`;
    }
    
    return trail;
}

async function scrapeState(state) {
    console.log(`\nScraping ${state.toUpperCase()}...`);
    const trails = [];
    
    // Get the state trail listing page
    const listUrl = `${BASE_URL}/stateactivity/${state}-bike-trails/`;
    const listHtml = await fetchWithRetry(listUrl);
    
    if (!listHtml) {
        console.log(`  Failed to fetch listing for ${state}`);
        return trails;
    }
    
    // Extract trail URLs
    const trailUrls = extractTrailLinks(listHtml);
    console.log(`  Found ${trailUrls.length} trail links`);
    
    // Fetch each trail page
    for (const url of trailUrls) {
        await delay(500); // Be nice to the server
        
        const trailHtml = await fetchWithRetry(url);
        if (!trailHtml) continue;
        
        const trail = parseTrailPage(trailHtml, url, state);
        
        // Validate - need at least name and some length
        if (trail.name && trail.length > 0) {
            trails.push(trail);
            console.log(`  ✓ ${trail.name} (${trail.length} mi)`);
        }
    }
    
    return trails;
}

// Fallback: estimate coordinates from state if not found
function estimateCoordinates(trail) {
    if (trail.lat && trail.lng) return;
    
    // State center coordinates as fallback
    const stateCenters = {
        'CT': { lat: 41.6032, lng: -73.0877 },
        'ME': { lat: 45.2538, lng: -69.4455 },
        'MA': { lat: 42.4072, lng: -71.3824 },
        'NH': { lat: 43.1939, lng: -71.5724 },
        'RI': { lat: 41.5801, lng: -71.4774 },
        'VT': { lat: 44.5588, lng: -72.5778 }
    };
    
    const center = stateCenters[trail.state];
    if (center) {
        // Add small random offset so markers don't stack
        trail.lat = center.lat + (Math.random() - 0.5) * 0.5;
        trail.lng = center.lng + (Math.random() - 0.5) * 0.5;
    }
}

async function main() {
    console.log('='.repeat(50));
    console.log('Rail Trail Database Updater');
    console.log('='.repeat(50));
    
    // Load existing data to preserve good coordinates
    let existingCoords = {};
    if (fs.existsSync(OUTPUT_FILE)) {
        try {
            const existing = JSON.parse(fs.readFileSync(OUTPUT_FILE, 'utf8'));
            const existingTrails = existing.trails || [];
            for (const t of existingTrails) {
                if (t.url && t.lat && t.lng) {
                    existingCoords[t.url] = { lat: t.lat, lng: t.lng };
                }
            }
            console.log(`Loaded ${Object.keys(existingCoords).length} existing coordinates to preserve`);
        } catch (e) {
            console.log('Could not load existing data:', e.message);
        }
    }
    
    const allTrails = [];
    
    for (const state of STATES) {
        const stateTrails = await scrapeState(state);
        
        // Preserve existing good coordinates before falling back to state centers
        for (const trail of stateTrails) {
            if (!trail.lat || !trail.lng) {
                const existing = existingCoords[trail.url];
                if (existing) {
                    trail.lat = existing.lat;
                    trail.lng = existing.lng;
                    continue; // Skip centroid fallback
                }
            }
            estimateCoordinates(trail);
        }
        
        allTrails.push(...stateTrails);
        await delay(1000); // Pause between states
    }
    
    // Report coordinate quality
    const withReal = allTrails.filter(t => t.lat && t.lng).length;
    const total = allTrails.length;
    console.log(`\nCoordinate quality: ${withReal}/${total} trails have coordinates`);
    
    // Deduplicate by URL (TrailLink sometimes returns same trail from multiple pages)
    const seen = new Map();
    for (const trail of allTrails) {
        const key = trail.url || trail.name;
        if (!seen.has(key)) {
            seen.set(key, trail);
        }
    }
    const dedupedTrails = Array.from(seen.values());
    if (dedupedTrails.length < allTrails.length) {
        console.log(`Deduplication: ${allTrails.length} → ${dedupedTrails.length} trails`);
    }
    
    // Calculate totals
    const totalMiles = dedupedTrails.reduce((sum, t) => sum + (t.length || 0), 0);
    
    // Build output
    const output = {
        metadata: {
            generated: new Date().toISOString().split('T')[0],
            source: 'TrailLink.com',
            region: 'New England',
            states: ['CT', 'ME', 'MA', 'NH', 'RI', 'VT'],
            total_trails: dedupedTrails.length,
            total_miles: Math.round(totalMiles * 10) / 10,
            note: 'Auto-updated weekly via GitHub Actions'
        },
        trails: dedupedTrails.sort((a, b) => a.name.localeCompare(b.name))
    };
    
    // Write output
    fs.writeFileSync(OUTPUT_FILE, JSON.stringify(output, null, 2));
    
    console.log('\n' + '='.repeat(50));
    console.log(`Done! ${dedupedTrails.length} trails (${totalMiles.toFixed(1)} miles)`);
    console.log(`Output: ${OUTPUT_FILE}`);
    console.log('='.repeat(50));
    
    // Exit with error if we got very few trails or suspiciously many (something probably broke)
    if (dedupedTrails.length < 50) {
        console.error('\n⚠️  Warning: Very few trails found. Scraping may have failed.');
        process.exit(1);
    }
    // Load existing data to check for unexpected bloat (duplication guard)
    if (fs.existsSync(OUTPUT_FILE)) {
        try {
            const existing = JSON.parse(fs.readFileSync(OUTPUT_FILE, 'utf8'));
            if (dedupedTrails.length > existing.trails.length * 1.5) {
                console.error(`\n⚠️  Refusing to write: new count (${dedupedTrails.length}) is 50%+ more than existing (${existing.trails.length}). Possible duplication bug.`);
                process.exit(1);
            }
        } catch (e) { /* first run, no existing file */ }
    }
}

main().catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
});
