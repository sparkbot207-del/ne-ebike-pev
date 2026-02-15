# Changelog

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
