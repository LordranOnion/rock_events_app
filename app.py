from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import requests

app = Flask(__name__)
app.secret_key = 'supersecretkey'
DB_API = 'http://localhost:5001'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/events')
def api_events():
    resp = requests.get(f"{DB_API}/events")
    return jsonify(resp.json())

@app.route('/api/price', methods=['POST'])
def get_price():
    event_id = request.json.get('event_id')
    # SSRF: If event_id looks like a URL, fetch it!
    if isinstance(event_id, str) and (event_id.startswith("http://") or event_id.startswith("https://")):
        try:
            resp = requests.get(event_id)
            # Return contents or status for demo
            return jsonify({
                "ssrf": True,
                "target": event_id,
                "status": resp.status_code,
                "content": resp.text[:200]  # Only first 200 chars for safety
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        # Default: fetch from DB as before
        try:
            # ... DB logic for fetching price by ID (as before)
            resp = requests.get(f"http://localhost:5001/events/{event_id}")
            data = resp.json()
            if 'price' in data:
                return jsonify({'price': data['price']})
            return jsonify({'error': 'Event not found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        r = requests.get(f"{DB_API}/users")
        users = r.json()
        if any(u['username'] == username and u['is_admin'] for u in users):
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

@app.route('/admin/api/users')
def admin_users():
    if request.remote_addr == '127.0.0.1':
        return jsonify(get_users())
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(get_users())

@app.route('/admin/api/events')
def admin_events():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    resp = requests.get(f"{DB_API}/events")
    return jsonify(resp.json())

@app.route('/admin/api/users/add', methods=['POST'])
def admin_add_user():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    resp = requests.post(f"{DB_API}/users", json=data)
    return jsonify(resp.json()), resp.status_code

@app.route('/admin/api/users/remove', methods=['POST'])
def admin_remove_user():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    user_id = request.json.get('user_id')
    resp = requests.delete(f"{DB_API}/users/{user_id}")
    return jsonify(resp.json()), resp.status_code

@app.route('/admin/api/events/add', methods=['POST'])
def admin_add_event():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    resp = requests.post(f"{DB_API}/events", json=data)
    return jsonify(resp.json()), resp.status_code

@app.route('/admin/api/events/remove', methods=['POST'])
def admin_remove_event():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    event_id = request.json.get('event_id')
    resp = requests.delete(f"{DB_API}/events/{event_id}")
    return jsonify(resp.json()), resp.status_code

if __name__ == "__main__":
    app.run(port=5000, debug=True)
