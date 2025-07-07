from flask import Flask, render_template, request, jsonify
import sqlite3
import os

app = Flask(__name__)

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/events')
def get_events():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name, date, venue, price FROM events')
    events = [
        {'id': row[0], 'name': row[1], 'date': row[2], 'venue': row[3], 'price': row[4]}
        for row in c.fetchall()
    ]
    conn.close()
    return jsonify(events)

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

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
