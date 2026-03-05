# Changelog

## [1.1.8] - 2026-03-05

### Trail Search & Data Improvements
- **Deduplicated trail data** — Reduced rail_trails.json from 458 entries to 229 unique trails
  - Removed exact duplicate entries (e.g., Cape Cod Rail Trail appeared twice with identical data)
  - Removed garbage `cities` field values like "Boston to New York", "Maine to Florida when"
  - All city/location fields now properly empty and cleaned for future population
- **Added zip code search support** — Trail search now accepts 5-digit zip codes (e.g., `04240` for Lewiston, ME)
  - Enhanced `looksLikeAddress()` function to detect zip pattern `^\d{5}(-\d{4})?$`
  - Geocodes zip codes via Nominatim, finds trails within 25-mile radius
  - Updated search placeholder: "Search by trail name, city, zip, or address..."
- **Geocoded all 233 trails** with accurate lat/lng from TrailLink metadata
  - No login required — coordinates extracted from public `<meta>` tags
  - 100% success rate for all New England trails (CT, MA, ME, NH, RI, VT)
- **Fixed state filtering** — State dropdown appends state name to geocode queries for clarity
  - Example: "springfield" + MA dropdown → geocodes as "springfield, Massachusetts"
- **Sync status** — Both `trails.json` (curated) and `rail_trails.json` (live) now in sync with correct coordinates

### Technical
- Routes page placeholder updated
- Commits: `d23fcdf` (dedupe), `8e339e3` (zip search), `abcff92` (version tag)
- No breaking changes to map rendering or filtering logic

## [1.1.7] - 2026-03-04

### SEO Fixes - Redirect Issue Resolution
- **Fixed sitemap redirect errors** — Removed `.html` extensions from all sitemap URLs
  - Google Search Console was reporting "Redirect error" and "Page with redirect" for routes like `/guides.html`
  - GitHub Pages serves HTML files without extension and redirects `.html` requests with 308 status
  - Sitemap now points to clean URLs: `/guides`, `/routes`, `/laws`, etc.
- **Fixed canonical tags** — Updated canonical links in all 10 HTML pages to point to clean URLs
  - Previously: `<link rel="canonical" href="https://newenglandebike.org/guides.html">`
  - Now: `<link rel="canonical" href="https://newenglandebike.org/guides">`
  - Eliminates redirect chain confusion for search engine crawlers
- **Fixed internal navigation links** — Converted all internal href attributes from relative `.html` links to clean URLs
  - Removes unnecessary 308 redirects and preserves link equity
  - Example: `href="index.html"` → `href="/"`
- **Resubmitted sitemap to Google Search Console** — API request to force immediate indexing crawl
- **Expected outcome** — Redirect errors should clear within days; proper indexing should follow within 1-2 weeks

### Technical
- Modified: `sitemap.xml`, all `*.html` files
- Commit: `3503dba` - Fix redirect issues: remove .html from sitemap, canonicals, and internal links
- No database/functional changes; purely SEO configuration

## [1.1.6] - 2026-02-26

### Trail Data Improvements
- **Scraped TrailLink endpoints** — Re-scraped all 318 rail trails from TrailLink pages to extract true start/end coordinates
- **Fixed bad endpoint data** — 214 trails had copied center points as endpoints; now 290/318 have real endpoint coordinates
- **Improved route mapping** — Better route visualization with accurate trail endpoints for "Add to Route" feature
- **Added incremental saves** — Rescrape script now saves progress every 10 trails to prevent loss on timeout

### Technical
- Modified `scripts/rescrape_traillink.py` to skip trails with already-good endpoint data
- Added checkpoint saving during geocoding to protect against session kills
- Total completion time: ~13 minutes for 318 trails (average 2.5 sec/trail including rate limiting)

## [1.1.5] - 2026-02-25

### Security
- **Removed exposed API keys** — Replaced old Google Maps API key (public in git history) with new domain-restricted key
- **Fixed referrer restrictions** — Updated API key website restrictions to use wildcards (`https://newenglandebike.org/*`, `https://www.newenglandebike.org/*`) instead of specific URLs
- **Removed third-party keys** — Eliminated OpenRouteService API key entirely

### Routing Improvements
- **Switched to Google Directions API** with BICYCLING mode (prefers bike lanes, avoids highways)
- **Added geometry library** for polyline encoding/decoding
- **Fixed route visualization** — Routes now draw on map with proper turn-by-turn instructions

### Bug Fixes
- Fixed missing `</script>` tag blocking Leaflet load
- Fixed Nominatim CORS error (removed forbidden User-Agent header)
- Fixed route rendering by adding instructions array for Leaflet Routing Machine

### Commits
- eda6d99: Replace exposed API keys with domain-restricted key
- c6a6b8c: Fix missing </script> tag
- 6be092a: Revert to OSRM routing, fix Nominatim CORS (temporary)
- 0ce5620: Switch to Google Directions API with BICYCLING mode
- 6d41fcb: Fix route drawing - add instructions array

## [1.1.4] - 2026-02-24

### Fixed
- **Sitemap .html redirect errors** — Removed `.html` extensions from all sitemap URLs. Server 308-redirects `.html` → clean URLs, which Google Search Console flagged as 9 redirect errors.
- **Footer nav links** — Removed `.html` extensions from footer links (laws, routes, home) to match clean URL pattern.

### Added
- **Last updated timestamp** in homepage footer.

### Commits
- 2e1c3dc: sitemap.xml fix
- This commit: footer timestamp + nav link cleanup

## [1.1.3] - 2026-02-15

### Bug Fixes (Calculator Page)
- **Fixed missing navigation bar** - Calculator had custom nav that didn't display
  - Replaced with site-standard .nav structure
  - Now matches other pages (brand logo + nav links + mobile toggle)
- **Fixed unreadable text** - Calculator labels too dark (#aaa)
  - Changed labels from #aaa → #cbd5e1 (readable on dark background)
  - Updated hints from #666 → #94a3b8 (better contrast)
  - Updated buttons to match (#cbd5e1)
  - Added font-weight: 500 to labels
- **Added mobile nav toggle** - Calculator now has responsive menu
- **Browser permission notification** - Expected Chrome behavior (Web Bluetooth/WebUSB)
  - Users can safely click "Block" - doesn't affect calculator

## [1.1.2] - 2026-02-15

### UI/UX Improvements
- **Fixed crowded navbar** - Reduced spacing and font sizes for cleaner layout
  - Gap between nav items: 30px → 12px
  - Nav links font-size: 1rem → 0.95rem
  - Logo font-size: 1rem → 0.9rem
- **Fixed button text alignment** - "Join Facebook" button now properly centered
  - Used flexbox (display: flex, align-items/justify-content: center)
  - Added white-space: nowrap to prevent text wrapping
- **Streamlined navigation labels** for compactness:
  - Removed redundant "Home" link
  - Shortened: "Ride Planner" → "Planner", "E-Bike & PEV Shops" → "Shops", etc.
  - Applied consistently across all 9 pages

## [1.1.1] - 2026-02-15

### Fixed (Continued)
- **Discovered missing calculator.html in sitemap** - Page existed but wasn't indexed
  - Added calculator.html to sitemap.xml with priority 0.8
  - Added "Range Calculator" link to main navigation across all pages
  - Now fully discoverable by Google

## [1.1.0] - 2026-02-15

### Fixed
- **SEO: Added canonical tags to all 10 pages** - Fixes duplicate content warnings in Google Search Console
  - Each page now has `<link rel="canonical">` pointing to its canonical URL on newenglandebike.org
  - Resolves: "Page with redirect" (4 pages), "Redirect error" (1 page), "Duplicate without canonical" (1 page)
- **Removed duplicate meta tags** on laws.html and routes.html (each had 2x og:type, og:url, og:title, og:description, og:image, twitter:card tags)
- **Created .htaccess redirect rules** - Handles www→non-www, http→https, trailing slashes
  - Includes gzip compression and cache control headers for performance
  - Adds security headers (X-Frame-Options, X-Content-Type-Options, etc.)
  - Note: GitHub Pages automatically handles redirects; .htaccess is for future Apache-based hosting

### Pages Updated
- article-charging-best-practices.html
- article-ebike-laws-guide.html
- article-winter-battery-storage.html
- calculator.html
- guides.html
- index.html
- laws.html
- planner.html
- routes.html
- shops.html

### Impact
- ✅ Eliminates duplicate content warnings in Google Search Console
- ✅ Improves SEO crawl efficiency
- ✅ Stabilizes indexing for all pages
- ✅ Fixes redirect warnings

## [1.0.0] - 2026-02-08

### Initial Release
- Static website launch
- Responsive design for all devices
- Navigation to community resources
