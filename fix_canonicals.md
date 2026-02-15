# SEO Fixes - Canonical Tags & Redirects

## Issue: Missing Canonical Tags
- All 10 pages missing `<link rel="canonical">` tags
- Causes Google to see same page multiple times (www vs non-www, trailing slashes, etc.)
- Results in: redirect warnings, duplicate content, crawl waste

## Solution
Add to each HTML file in <head> section:
```html
<link rel="canonical" href="https://newenglandebike.org/[PAGE_NAME]">
```

## URLs to Fix:
1. index.html → https://newenglandebike.org/
2. routes.html → https://newenglandebike.org/routes.html
3. laws.html → https://newenglandebike.org/laws.html
4. planner.html → https://newenglandebike.org/planner.html
5. shops.html → https://newenglandebike.org/shops.html
6. guides.html → https://newenglandebike.org/guides.html
7. article-ebike-laws-guide.html → https://newenglandebike.org/article-ebike-laws-guide.html
8. article-winter-battery-storage.html → https://newenglandebike.org/article-winter-battery-storage.html
9. article-charging-best-practices.html → https://newenglandebike.org/article-charging-best-practices.html
10. calculator.html → https://newenglandebike.org/calculator.html

## Additional Fix: .htaccess Redirects
Create .htaccess to handle:
- www → non-www redirect
- http → https redirect
- Trailing slashes normalization
