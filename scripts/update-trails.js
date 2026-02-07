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
        const trailPath = match[1];
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
    
    // Extract length - look for patterns like "12.5 mi" or "Length: 12.5"
    const lengthMatch = html.match(/(\d+\.?\d*)\s*mi(?:les?)?/i) || 
                        html.match(/Length[:\s]+(\d+\.?\d*)/i);
    if (lengthMatch) {
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
    
    // Extract coordinates from map data or schema
    const latMatch = html.match(/latitude["\s:]+(-?\d+\.?\d*)/i) ||
                     html.match(/lat["\s:]+(-?\d+\.?\d*)/i);
    const lngMatch = html.match(/longitude["\s:]+(-?\d+\.?\d*)/i) ||
                     html.match(/lng["\s:]+(-?\d+\.?\d*)/i) ||
                     html.match(/lon["\s:]+(-?\d+\.?\d*)/i);
    
    if (latMatch && lngMatch) {
        trail.lat = parseFloat(latMatch[1]);
        trail.lng = parseFloat(lngMatch[1]);
    }
    
    // Extract rating
    const ratingMatch = html.match(/(\d\.?\d?)\s*(?:out of 5|\/5|stars)/i) ||
                        html.match(/rating["\s:]+(\d\.?\d*)/i);
    if (ratingMatch) {
        trail.rating = parseFloat(ratingMatch[1]);
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
    
    const allTrails = [];
    
    for (const state of STATES) {
        const stateTrails = await scrapeState(state);
        
        // Add coordinate fallbacks
        for (const trail of stateTrails) {
            estimateCoordinates(trail);
        }
        
        allTrails.push(...stateTrails);
        await delay(1000); // Pause between states
    }
    
    // Calculate totals
    const totalMiles = allTrails.reduce((sum, t) => sum + (t.length || 0), 0);
    
    // Build output
    const output = {
        metadata: {
            generated: new Date().toISOString().split('T')[0],
            source: 'TrailLink.com',
            region: 'New England',
            states: ['CT', 'ME', 'MA', 'NH', 'RI', 'VT'],
            total_trails: allTrails.length,
            total_miles: Math.round(totalMiles * 10) / 10,
            note: 'Auto-updated weekly via GitHub Actions'
        },
        trails: allTrails.sort((a, b) => a.name.localeCompare(b.name))
    };
    
    // Write output
    fs.writeFileSync(OUTPUT_FILE, JSON.stringify(output, null, 2));
    
    console.log('\n' + '='.repeat(50));
    console.log(`Done! ${allTrails.length} trails (${totalMiles.toFixed(1)} miles)`);
    console.log(`Output: ${OUTPUT_FILE}`);
    console.log('='.repeat(50));
    
    // Exit with error if we got very few trails (something probably broke)
    if (allTrails.length < 50) {
        console.error('\n⚠️  Warning: Very few trails found. Scraping may have failed.');
        process.exit(1);
    }
}

main().catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
});
