#!/usr/bin/env python3
"""
NE E-Bike Admin Panel
A simple Flask-based CMS for managing the New England E-Bike website.
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data'

def load_json(filename):
    """Load a JSON data file."""
    filepath = DATA_DIR / filename
    if filepath.exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return {}

def save_json(filename, data):
    """Save data to a JSON file."""
    filepath = DATA_DIR / filename
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def generate_id(name):
    """Generate a URL-safe ID from a name."""
    return name.lower().replace(' ', '-').replace("'", '').replace('"', '')[:50]

# ============================================
# ROUTES - Dashboard
# ============================================

@app.route('/')
def dashboard():
    """Main dashboard showing overview stats."""
    shops = load_json('shops.json').get('shops', [])
    articles = load_json('articles.json').get('articles', [])
    events = load_json('events.json').get('events', [])
    
    stats = {
        'shops': len([s for s in shops if s.get('active', True)]),
        'articles': len([a for a in articles if a.get('active', True)]),
        'events': len([e for e in events if e.get('active', True)]),
    }
    
    return render_template('dashboard.html', stats=stats)

# ============================================
# ROUTES - Shops
# ============================================

@app.route('/shops')
def shops_list():
    """List all shops."""
    data = load_json('shops.json')
    shops = data.get('shops', [])
    return render_template('shops.html', shops=shops)

@app.route('/shops/add', methods=['GET', 'POST'])
def shops_add():
    """Add a new shop."""
    if request.method == 'POST':
        data = load_json('shops.json')
        shops = data.get('shops', [])
        
        new_shop = {
            'id': generate_id(request.form['name']),
            'name': request.form['name'],
            'address': request.form['address'],
            'city': request.form['city'],
            'state': request.form['state'],
            'zip': request.form['zip'],
            'phone': request.form.get('phone', ''),
            'website': request.form.get('website', ''),
            'services': [s.strip() for s in request.form.get('services', '').split(',') if s.strip()],
            'brands': [b.strip() for b in request.form.get('brands', '').split(',') if b.strip()],
            'featured': 'featured' in request.form,
            'active': True,
            'addedDate': datetime.now().strftime('%Y-%m-%d')
        }
        
        shops.append(new_shop)
        save_json('shops.json', {'shops': shops})
        
        return redirect(url_for('shops_list'))
    
    return render_template('shop_form.html', shop=None, states=NE_STATES)

@app.route('/shops/edit/<shop_id>', methods=['GET', 'POST'])
def shops_edit(shop_id):
    """Edit an existing shop."""
    data = load_json('shops.json')
    shops = data.get('shops', [])
    shop = next((s for s in shops if s['id'] == shop_id), None)
    
    if not shop:
        return redirect(url_for('shops_list'))
    
    if request.method == 'POST':
        shop['name'] = request.form['name']
        shop['address'] = request.form['address']
        shop['city'] = request.form['city']
        shop['state'] = request.form['state']
        shop['zip'] = request.form['zip']
        shop['phone'] = request.form.get('phone', '')
        shop['website'] = request.form.get('website', '')
        shop['services'] = [s.strip() for s in request.form.get('services', '').split(',') if s.strip()]
        shop['brands'] = [b.strip() for b in request.form.get('brands', '').split(',') if b.strip()]
        shop['featured'] = 'featured' in request.form
        shop['active'] = 'active' in request.form
        
        save_json('shops.json', {'shops': shops})
        return redirect(url_for('shops_list'))
    
    return render_template('shop_form.html', shop=shop, states=NE_STATES)

@app.route('/shops/delete/<shop_id>', methods=['POST'])
def shops_delete(shop_id):
    """Delete a shop."""
    data = load_json('shops.json')
    shops = data.get('shops', [])
    shops = [s for s in shops if s['id'] != shop_id]
    save_json('shops.json', {'shops': shops})
    return redirect(url_for('shops_list'))

# ============================================
# ROUTES - Articles
# ============================================

@app.route('/articles')
def articles_list():
    """List all articles."""
    data = load_json('articles.json')
    articles = data.get('articles', [])
    return render_template('articles.html', articles=articles)

@app.route('/articles/add', methods=['GET', 'POST'])
def articles_add():
    """Add a new article."""
    if request.method == 'POST':
        data = load_json('articles.json')
        articles = data.get('articles', [])
        
        new_article = {
            'id': generate_id(request.form['title']),
            'title': request.form['title'],
            'slug': request.form.get('slug', generate_id(request.form['title'])),
            'description': request.form['description'],
            'author': request.form.get('author', 'New England E-Bike Community'),
            'publishDate': request.form.get('publishDate', datetime.now().strftime('%Y-%m-%d')),
            'category': request.form.get('category', 'news'),
            'featured': 'featured' in request.form,
            'active': True
        }
        
        articles.append(new_article)
        save_json('articles.json', {'articles': articles})
        
        return redirect(url_for('articles_list'))
    
    return render_template('article_form.html', article=None)

@app.route('/articles/edit/<article_id>', methods=['GET', 'POST'])
def articles_edit(article_id):
    """Edit an existing article."""
    data = load_json('articles.json')
    articles = data.get('articles', [])
    article = next((a for a in articles if a['id'] == article_id), None)
    
    if not article:
        return redirect(url_for('articles_list'))
    
    if request.method == 'POST':
        article['title'] = request.form['title']
        article['slug'] = request.form.get('slug', article['slug'])
        article['description'] = request.form['description']
        article['author'] = request.form.get('author', article.get('author', ''))
        article['publishDate'] = request.form.get('publishDate', article.get('publishDate', ''))
        article['category'] = request.form.get('category', 'news')
        article['featured'] = 'featured' in request.form
        article['active'] = 'active' in request.form
        
        save_json('articles.json', {'articles': articles})
        return redirect(url_for('articles_list'))
    
    return render_template('article_form.html', article=article)

# ============================================
# ROUTES - Events
# ============================================

@app.route('/events')
def events_list():
    """List all events."""
    data = load_json('events.json')
    events = data.get('events', [])
    return render_template('events.html', events=events)

@app.route('/events/add', methods=['GET', 'POST'])
def events_add():
    """Add a new event."""
    if request.method == 'POST':
        data = load_json('events.json')
        events = data.get('events', [])
        
        new_event = {
            'id': generate_id(request.form['title']),
            'title': request.form['title'],
            'description': request.form['description'],
            'date': request.form['date'],
            'time': request.form.get('time', ''),
            'location': request.form['location'],
            'distance': request.form.get('distance', ''),
            'difficulty': request.form.get('difficulty', 'moderate'),
            'contact': request.form.get('contact', ''),
            'facebookEvent': request.form.get('facebookEvent', ''),
            'active': True
        }
        
        events.append(new_event)
        save_json('events.json', {'events': events})
        
        return redirect(url_for('events_list'))
    
    return render_template('event_form.html', event=None)

@app.route('/events/edit/<event_id>', methods=['GET', 'POST'])
def events_edit(event_id):
    """Edit an existing event."""
    data = load_json('events.json')
    events = data.get('events', [])
    event = next((e for e in events if e['id'] == event_id), None)
    
    if not event:
        return redirect(url_for('events_list'))
    
    if request.method == 'POST':
        event['title'] = request.form['title']
        event['description'] = request.form['description']
        event['date'] = request.form['date']
        event['time'] = request.form.get('time', '')
        event['location'] = request.form['location']
        event['distance'] = request.form.get('distance', '')
        event['difficulty'] = request.form.get('difficulty', 'moderate')
        event['contact'] = request.form.get('contact', '')
        event['facebookEvent'] = request.form.get('facebookEvent', '')
        event['active'] = 'active' in request.form
        
        save_json('events.json', {'events': events})
        return redirect(url_for('events_list'))
    
    return render_template('event_form.html', event=event)

# ============================================
# ROUTES - Git Operations
# ============================================

@app.route('/publish', methods=['POST'])
def publish():
    """Commit and push changes to GitHub."""
    try:
        message = request.form.get('message', 'Update from admin panel')
        
        # Git operations
        os.chdir(BASE_DIR)
        subprocess.run(['git', 'add', '-A'], check=True)
        subprocess.run(['git', 'commit', '-m', message], check=True)
        subprocess.run(['git', 'push'], check=True)
        
        return jsonify({'success': True, 'message': 'Changes published successfully!'})
    except subprocess.CalledProcessError as e:
        return jsonify({'success': False, 'message': f'Git error: {str(e)}'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/git-status')
def git_status():
    """Get current git status."""
    try:
        os.chdir(BASE_DIR)
        result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
        changes = [line for line in result.stdout.strip().split('\n') if line]
        return jsonify({'changes': changes, 'count': len(changes)})
    except Exception as e:
        return jsonify({'error': str(e)})

# ============================================
# Constants
# ============================================

NE_STATES = [
    ('CT', 'Connecticut'),
    ('ME', 'Maine'),
    ('MA', 'Massachusetts'),
    ('NH', 'New Hampshire'),
    ('RI', 'Rhode Island'),
    ('VT', 'Vermont'),
]

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=False)
