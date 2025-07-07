from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # for sessions, use a better key in production!

DB_PATH = 'events.db'

def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # Users table
        c.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                is_admin INTEGER NOT NULL
            )
        ''')
        # Events table
        c.execute('''
            CREATE TABLE events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                date TEXT NOT NULL,
                venue TEXT NOT NULL,
                price REAL NOT NULL
            )
        ''')
        # Insert users
        c.executemany('INSERT INTO users (username, is_admin) VALUES (?, ?)',
            [('admin', 1), ('metalhead123', 0), ('rockfan2024', 0)]
        )
        # Insert sample events (fill with real upcoming events if you want)
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/events')
def api_events():
    return jsonify(get_events())

@app.route('/api/price', methods=['POST'])
def get_price():
    event_id = request.json.get('event_id')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT price FROM events WHERE id=?', (event_id,))
    result = c.fetchone()
    conn.close()
    if result:
        return jsonify({'price': result[0]})
    return jsonify({'error': 'Event not found'}), 404

### --- ADMIN PANEL ROUTES --- ###

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        # check if admin
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id FROM users WHERE username=? AND is_admin=1', (username,))
        admin = c.fetchone()
        conn.close()
        if admin:
            session['admin'] = username
            return redirect(url_for('admin_panel'))
        else:
            return render_template('admin_login.html', error='Invalid admin username')
    return render_template('admin_login.html')

@app.route('/admin/panel')
def admin_panel():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    return render_template('admin_panel.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

# --- ADMIN APIs ---

@app.route('/admin/api/users')
def admin_users():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(get_users())

@app.route('/admin/api/events')
def admin_events():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(get_events())

@app.route('/admin/api/users/add', methods=['POST'])
def admin_add_user():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
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

@app.route('/admin/api/users/remove', methods=['POST'])
def admin_remove_user():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    user_id = request.json.get('user_id')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM users WHERE id=? AND is_admin=0', (user_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/admin/api/events/add', methods=['POST'])
def admin_add_event():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO events (name, date, venue, price) VALUES (?, ?, ?, ?)',
              (data['name'], data['date'], data['venue'], data['price']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/admin/api/events/remove', methods=['POST'])
def admin_remove_event():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
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
