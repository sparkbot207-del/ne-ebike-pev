# Simple Analytics System - Demo

Built overnight by Sparky ⚡

## What It Is

A lightweight, privacy-friendly analytics system that tracks:
- **Page views** - Which pages people visit
- **Clicks** - What links/buttons they click
- **Calculator usage** - How people use the range calculator
- **Time on page** - How long people spend

**Zero cost, zero third-party tracking, full control.**

## URLs

- **Dashboard:** http://192.168.0.39:5001
- **Test Page:** http://192.168.0.39:8888/calculator.html (with tracker enabled)

## How It Works

### 1. JavaScript Tracker (`tracker.js`)
- Tiny script (<2KB) added to pages
- Tracks events using sendBeacon (non-blocking, fast)
- Generates session IDs (sessionStorage, not cookies)
- Sends events to backend API

### 2. Backend API (`server.py`)
- Python Flask server on port 5001
- SQLite database (no database server needed)
- REST API endpoints:
  - `POST /api/track` - receive events
  - `GET /api/stats?hours=24` - get statistics
- CORS enabled for cross-origin tracking

### 3. Database (`analytics.db`)
- SQLite (fast, simple, zero config)
- Events table stores:
  - Timestamp
  - Session ID
  - Event type (pageview, click, calculator_use)
  - Page URL
  - Element clicked
  - Metadata (JSON)
  - User agent, IP

### 4. Dashboard (`templates/dashboard.html`)
- Real-time stats
- Page view breakdown
- Popular clicks heatmap
- Activity timeline
- Recent events table
- Auto-refreshes every 30 seconds

## What Gets Tracked

**Page Views:**
- URL visited
- Page title
- Referrer (where they came from)

**Clicks:**
- Element clicked (ID, class, or tag)
- Link text
- Destination URL

**Calculator Usage:**
- Which fields are changed
- Values entered (for optimization insights)

**Session Data:**
- Session duration
- Pages per session
- Unique visitors

## Privacy

- **No cookies** - uses sessionStorage
- **No personal data** - just aggregate usage
- **No third parties** - all data stays on our server
- **Lightweight** - minimal performance impact
- **Non-blocking** - uses sendBeacon API

## Files

```
analytics/
├── server.py           # Flask backend
├── tracker.js          # Client-side tracker
├── analytics.db        # SQLite database (created on first run)
├── templates/
│   └── dashboard.html  # Analytics dashboard
├── venv/               # Python virtual environment
└── README.md           # This file
```

## Running It

### Start Analytics Server
```bash
cd ~/projects/ne-ebike-staging/analytics
source venv/bin/activate
python3 server.py
```

Server runs on port 5001

### Add Tracker to a Page
```html
<!-- Add before closing </body> tag -->
<script src="analytics/tracker.js"></script>
```

### View Dashboard
Open http://192.168.0.39:5001 in your browser

## Customization

### Change Tracking Endpoint
Edit `tracker.js`:
```javascript
const ANALYTICS_ENDPOINT = 'http://your-server.com/api/track';
```

### Track Custom Events
```javascript
// In your page's JavaScript
trackEvent('custom_event', {
    element: 'my-button',
    metadata: { plan: 'premium' }
});
```

### Add More Metrics
Edit `server.py` to add custom queries and stats.

## Production Deployment

For the live site (when ready):

1. **Security:**
   - Rate limiting (prevent spam)
   - Input validation
   - IP anonymization option

2. **Performance:**
   - Database indexes (already added)
   - Cache stats queries
   - Consider PostgreSQL for high traffic

3. **Privacy:**
   - Add opt-out mechanism
   - GDPR compliance (if needed)
   - Privacy policy update

4. **Hosting:**
   - Run on same server as site
   - Or separate analytics server
   - Could run on the Pi itself

## Cost

**$0/month** - Everything self-hosted, no external services.

## Next Steps (If You Like It)

1. Add to more pages (routes, laws, shops, planner)
2. Track specific user flows (route → calculator → charging stations)
3. A/B testing capabilities
4. Export data to CSV
5. Email reports (daily/weekly summaries)
6. Alerts (if traffic spikes or drops)

---

**Built:** February 9, 2026  
**By:** Sparky ⚡  
**Status:** Demo (fully functional)
