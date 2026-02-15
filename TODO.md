# TODO - New England E-Bike PEV Site

## High Priority (SEO/Performance)

- [x] **Remove duplicate meta tags** - laws.html, routes.html cleaned (2026-02-15)
- [x] **Create .htaccess redirects** - Rules for www→non-www, http→https, trailing slashes (2026-02-15)
  - ⚠️ **Note**: GitHub Pages doesn't use .htaccess (already handles https + www redirect automatically)
  - This .htaccess is for future migration to Apache-based host
- [ ] **Verify all pages indexing** - Check Google Search Console after 1-2 weeks for successful re-indexing
- [ ] **Monitor redirect errors** - Ensure "redirect error" (1 page) is resolved

## Medium Priority (Content/Features)

- [ ] **Add structured data (Schema.org)** - Some pages have JSON-LD, others don't (improve rich snippets)
- [ ] **Optimize OG images** - Consider page-specific og:image instead of generic hero-banner.jpg
- [ ] **Add lastmod to sitemap** - Update modification dates to trigger re-crawl
- [ ] **Mobile testing** - Verify responsive design on various devices

## Low Priority (Future)

- [ ] **Add analytics dashboard** - Track page views, search impressions, click-through rates
- [ ] **Implement lazy loading** - Optimize performance for images/JS
- [ ] **Add breadcrumb navigation** - Improve UX and SEO
- [ ] **Consider blog section** - Expand content with regular updates

## Done ✅

- [x] Add canonical tags to all pages (2026-02-15)
- [x] Remove duplicate meta tags from laws.html, routes.html (2026-02-15)
- [x] Create .htaccess with redirect rules (2026-02-15)
- [x] Discover and add calculator.html to sitemap (2026-02-15)
- [x] Add calculator link to main navigation (2026-02-15)
- [x] Fix sitemap URLs (added .html extensions)
- [x] Add guides landing page
- [x] Create charging best practices article
- [x] Create winter battery storage guide
