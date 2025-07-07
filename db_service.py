from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DB_PATH = 'events.db'

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

@app.route('/events', methods=['GET'])
def get_events():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name, date, venue, price FROM events')
    events = [{'id': r[0], 'name': r[1], 'date': r[2], 'venue': r[3], 'price': r[4]} for r in c.fetchall()]
    conn.close()
    return jsonify(events)

@app.route('/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name, date, venue, price FROM events WHERE id=?', (event_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return jsonify({'id': row[0], 'name': row[1], 'date': row[2], 'venue': row[3], 'price': row[4]})
    return jsonify({'error': 'Not found'}), 404

@app.route('/events', methods=['POST'])
def add_event():
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO events (name, date, venue, price) VALUES (?, ?, ?, ?)',
              (data['name'], data['date'], data['venue'], data['price']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/events/<int:event_id>', methods=['DELETE'])
def remove_event(event_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM events WHERE id=?', (event_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/users', methods=['GET'])
def get_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, username, is_admin FROM users')
    users = [{'id': r[0], 'username': r[1], 'is_admin': r[2]} for r in c.fetchall()]
    conn.close()
    return jsonify(users)

@app.route('/users', methods=['POST'])
def add_user():
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, is_admin) VALUES (?, ?)',
                  (data['username'], int(data.get('is_admin', 0))))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Username exists'}), 409
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/users/<int:user_id>', methods=['DELETE'])
def remove_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM users WHERE id=? AND is_admin=0', (user_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

if __name__ == "__main__":
    init_db()
    app.run(port=5001, debug=True)
