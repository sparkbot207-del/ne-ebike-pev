# Changelog

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
