from flask import Flask, render_template, request, jsonify
import requests
import sqlite3
import os

app = Flask(__name__)
DB_PATH = 'events.db'

# ========== DATABASE INIT ==========
def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            is_admin INTEGER NOT NULL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            date TEXT NOT NULL,
            venue TEXT NOT NULL,
            price REAL NOT NULL)''')
        c.executemany('INSERT INTO users (username, is_admin) VALUES (?, ?)', [
            ('admin', 1), ('metalhead123', 0), ('rockfan2024', 0)
        ])
        events = [
            ("Metallica Live", "2025-07-20", "OAKA Stadium", 75.0),
            ("Rockwave Festival", "2025-07-28", "TerraVibe Park", 60.0),
            ("Slipknot Night", "2025-08-10", "Technopolis", 55.0),
            ("Judas Priest Reunion", "2025-08-15", "Gazi Music Hall", 70.0),
            ("Sabaton & Guests", "2025-08-25", "Faliro Indoor Hall", 50.0),
        ]
        c.executemany('INSERT INTO events (name, date, venue, price) VALUES (?, ?, ?, ?)', events)
        conn.commit()
        conn.close()

def get_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, username, is_admin FROM users')
    users = [{'id': r[0], 'username': r[1], 'is_admin': r[2]} for r in c.fetchall()]
    conn.close()
    return users

def get_events():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name, date, venue, price FROM events')
    events = [{'id': r[0], 'name': r[1], 'date': r[2], 'venue': r[3], 'price': r[4]} for r in c.fetchall()]
    conn.close()
    return events

# ========== ROUTES ==========

@app.route('/')
def index():
    return render_template('index.html')

# --- Public JSON Endpoints ---
@app.route('/users')
def users():
    return jsonify(get_users())

@app.route('/events')
def events():
    return jsonify(get_events())

@app.route('/price', methods=['POST'])
def get_price():
    event_id = request.json.get('event_id')
    # SSRF for pentest lab: if input looks like a URL, fetch it
    if isinstance(event_id, str) and (event_id.startswith("http://") or event_id.startswith("https://")):
        try:
            resp = requests.get(event_id)
            return jsonify({
                "ssrf": True,
                "target": event_id,
                "status": resp.status_code,
                "content": resp.text[:200]
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    # Normal: fetch event price by ID from DB
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT price FROM events WHERE id=?', (event_id,))
        row = c.fetchone()
        conn.close()
        if row:
            return jsonify({'price': row[0]})
        return jsonify({'error': 'Event not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ======== ADMIN PANEL (NO AUTH) =========

@app.route('/admin')
def admin_panel():
    return render_template('admin_panel.html')

# ----- ADMIN JSON ENDPOINTS -----
@app.route('/admin/users/add', methods=['POST'])
def admin_add_user():
    username = request.json.get('username')
    is_admin = 1 if request.json.get('is_admin') else 0
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, is_admin) VALUES (?, ?)', (username, is_admin))
        conn.commit()
        return jsonify({'status': 'ok'})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already exists'}), 409
    finally:
        conn.close()

@app.route('/admin/users/remove', methods=['POST'])
def admin_remove_user():
    user_id = request.json.get('user_id')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM users WHERE id=? AND is_admin=0', (user_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/admin/events/add', methods=['POST'])
def admin_add_event():
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO events (name, date, venue, price) VALUES (?, ?, ?, ?)',
              (data['name'], data['date'], data['venue'], data['price']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/admin/events/remove', methods=['POST'])
def admin_remove_event():
    event_id = request.json.get('event_id')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM events WHERE id=?', (event_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
