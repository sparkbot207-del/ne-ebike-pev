#!/usr/bin/env python3
"""
Simple Analytics Server
Tracks page views and clicks for NewEnglandEBike.org
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime, timedelta
import os

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"], "allow_headers": ["Content-Type"]}})

DB_PATH = os.path.join(os.path.dirname(__file__), 'analytics.db')

def init_db():
    """Initialize the database schema"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            session_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            page TEXT NOT NULL,
            element TEXT,
            metadata TEXT,
            user_agent TEXT,
            ip_address TEXT
        )
    ''')
    
    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp)
    ''')
    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_event_type ON events(event_type)
    ''')
    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_page ON events(page)
    ''')
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    """Analytics dashboard"""
    return render_template('dashboard.html')

@app.route('/api/track', methods=['POST'])
def track_event():
    """
    Track an analytics event
    
    POST /api/track
    {
        "session_id": "abc123",
        "event_type": "pageview" | "click" | "calculator_use",
        "page": "/routes.html",
        "element": "route-link-minuteman",
        "metadata": {"key": "value"}
    }
    """
    try:
        data = request.get_json()
        
        session_id = data.get('session_id', 'unknown')
        event_type = data.get('event_type', 'unknown')
        page = data.get('page', '/')
        element = data.get('element')
        metadata = json.dumps(data.get('metadata', {}))
        user_agent = request.headers.get('User-Agent', '')
        ip_address = request.remote_addr
        timestamp = datetime.utcnow().isoformat()
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO events (timestamp, session_id, event_type, page, element, metadata, user_agent, ip_address)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, session_id, event_type, page, element, metadata, user_agent, ip_address))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'ok'}), 200
        
    except Exception as e:
        print(f"Error tracking event: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """
    Get analytics stats
    
    Query params:
    - hours: number of hours to look back (default 24)
    """
    try:
        hours = int(request.args.get('hours', 24))
        since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Page views
        c.execute('''
            SELECT page, COUNT(*) as views
            FROM events
            WHERE event_type = 'pageview' AND timestamp > ?
            GROUP BY page
            ORDER BY views DESC
        ''', (since,))
        page_views = [dict(row) for row in c.fetchall()]
        
        # Click events
        c.execute('''
            SELECT element, COUNT(*) as clicks
            FROM events
            WHERE event_type = 'click' AND timestamp > ?
            GROUP BY element
            ORDER BY clicks DESC
            LIMIT 20
        ''', (since,))
        clicks = [dict(row) for row in c.fetchall()]
        
        # Timeline (hourly buckets)
        c.execute('''
            SELECT 
                strftime('%Y-%m-%d %H:00', timestamp) as hour,
                event_type,
                COUNT(*) as count
            FROM events
            WHERE timestamp > ?
            GROUP BY hour, event_type
            ORDER BY hour
        ''', (since,))
        timeline = [dict(row) for row in c.fetchall()]
        
        # Total stats
        c.execute('''
            SELECT 
                COUNT(*) as total_events,
                COUNT(DISTINCT session_id) as unique_sessions,
                COUNT(DISTINCT page) as unique_pages,
                SUM(CASE WHEN event_type = 'pageview' THEN 1 ELSE 0 END) as pageviews,
                SUM(CASE WHEN event_type = 'click' THEN 1 ELSE 0 END) as clicks
            FROM events
            WHERE timestamp > ?
        ''', (since,))
        totals = dict(c.fetchone())
        
        # Recent events (last 50)
        c.execute('''
            SELECT *
            FROM events
            ORDER BY timestamp DESC
            LIMIT 50
        ''', ())
        recent = [dict(row) for row in c.fetchall()]
        
        conn.close()
        
        return jsonify({
            'hours': hours,
            'totals': totals,
            'page_views': page_views,
            'clicks': clicks,
            'timeline': timeline,
            'recent': recent
        }), 200
        
    except Exception as e:
        print(f"Error fetching stats: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/t')
def track_get():
    """GET-based tracking (no CORS preflight needed)"""
    try:
        from datetime import datetime
        timestamp = datetime.utcnow().isoformat()
        session_id = request.args.get('s', 'unknown')
        event_type = request.args.get('t', 'pageview')
        page = request.args.get('p', '/')
        element = request.args.get('e')
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            INSERT INTO events (timestamp, session_id, event_type, page, element, metadata, user_agent, ip_address)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, session_id, event_type, page, element, '{}', 
              request.headers.get('User-Agent', ''), request.remote_addr))
        conn.commit()
        conn.close()
        
        # Return 1x1 transparent GIF
        gif = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
        return gif, 200, {'Content-Type': 'image/gif', 'Cache-Control': 'no-store'}
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    init_db()
    print("Analytics server starting...")
    print(f"Database: {DB_PATH}")
    app.run(host='0.0.0.0', port=5001, debug=True)
