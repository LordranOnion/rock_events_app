from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import requests

app = Flask(__name__)
app.secret_key = 'supersecretkey'
DB_API = 'http://localhost:5001'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/')
def api_events():
    resp = requests.get(f"{DB_API}/")
    return jsonify(resp.json())

@app.route('/api/price', methods=['POST'])
def get_price():
    event_id = request.json.get('event_id')
    resp = requests.get(f"{DB_API}/{event_id}")
    data = resp.json()
    if 'price' in data:
        return jsonify({'price': data['price']})
    return jsonify({'error': 'Event not found'}), 404

### -- Admin panel endpoints similar to before, but now always proxying to DB_API

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
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    resp = requests.get(f"{DB_API}/users")
    return jsonify(resp.json())

@app.route('/admin/api/')
def admin_events():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    resp = requests.get(f"{DB_API}/")
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

@app.route('/admin/api//add', methods=['POST'])
def admin_add_event():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    resp = requests.post(f"{DB_API}/", json=data)
    return jsonify(resp.json()), resp.status_code

@app.route('/admin/api//remove', methods=['POST'])
def admin_remove_event():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    event_id = request.json.get('event_id')
    resp = requests.delete(f"{DB_API}//{event_id}")
    return jsonify(resp.json()), resp.status_code

if __name__ == "__main__":
    app.run(port=5000, debug=True)
