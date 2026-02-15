# Analytics Demo - Quick Start Guide

Built by Sparky overnight! ⚡

## Test It Right Now

### 1. Open the Dashboard
http://192.168.0.39:5001

You'll see zero stats at first - that's normal!

### 2. Generate Some Traffic
Open the calculator page (in another tab):
http://192.168.0.39:8888/calculator.html

### 3. Click Around
- Change voltage dropdown
- Enter some amp hours  
- Click the preset buttons
- Change speed, motor power, etc.
- Click links in the header

### 4. Watch the Dashboard Update
Switch back to the dashboard tab and hit "Refresh" (or wait 30 seconds for auto-refresh)

You should see:
- ✅ Total events increasing
- ✅ Page views showing calculator.html
- ✅ Clicks showing which elements you clicked
- ✅ Calculator usage events
- ✅ Recent events table populating
- ✅ Timeline showing activity

## What You're Seeing

**Page Views:** Every time you load a page  
**Clicks:** Every button, link, or tracked element you click  
**Calculator Use:** When you change calculator inputs  
**Sessions:** Unique visitor count (using sessionStorage)

## Pro Tips

**Test Multiple Pages:**
- Add tracker.js to index.html, routes.html, etc.
- See which pages get the most traffic

**Session Tracking:**
- Open in incognito = new session
- Same tab = same session
- Close/reopen = same session (for that browser)

**Time Ranges:**
- Try "Last Hour" vs "Last 24 Hours" in the dropdown
- Perfect for seeing real-time vs historical data

**Export Data:**
- Database is at `analytics/analytics.db`
- Use any SQLite browser to export to CSV
- Or add export feature to dashboard (easy to do!)

## Servers Running

- **Analytics:** Port 5001 (Flask backend + dashboard)
- **Staging Site:** Port 8888 (test pages)

## Stop/Start Servers

### Stop Analytics
```bash
pkill -f "analytics.*server.py"
```

### Start Analytics
```bash
cd ~/projects/ne-ebike-staging/analytics
source venv/bin/activate
python3 server.py
```

### Stop Staging Site
```bash
pkill -f "http.server 8888"
```

### Start Staging Site
```bash
cd ~/projects/ne-ebike-staging
python3 -m http.server 8888 &
```

## Next Steps

**If You Like It:**
1. Add tracker to all site pages
2. Deploy to production
3. Add more custom events
4. Build weekly email reports
5. Add data export features

**If You Want Changes:**
- Let me know what to tweak!
- Different metrics to track?
- Dashboard improvements?
- More privacy controls?

---

**Questions?** Wake me up! I'm always listening. ⚡

**Files:**
- Full docs: `README.md`
- This guide: `QUICKSTART.md`
- Backend: `server.py`
- Tracker: `tracker.js`
- Database: `analytics.db`
