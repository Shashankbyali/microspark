from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
from datetime import datetime, timedelta
import json

app = Flask(__name__)
app.secret_key = 'microspark-secret-key-change-in-production'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'mp4', 'mov', 'avi'}

# Ensure uploads directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    conn = sqlite3.connect('microspark.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Skills table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            skill_name TEXT NOT NULL,
            target_time INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Sessions table (tracking completed practice sessions)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            skill_id INTEGER NOT NULL,
            duration INTEGER NOT NULL,
            proof_file TEXT,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (skill_id) REFERENCES skills (id)
        )
    ''')
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('choose_skill'))
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not username or not email or not password:
            return jsonify({'error': 'All fields are required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            hashed_password = generate_password_hash(password)
            cursor.execute(
                'INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                (username, email, hashed_password)
            )
            conn.commit()
            user_id = cursor.lastrowid
            session['user_id'] = user_id
            session['username'] = username
            conn.close()
            return jsonify({'success': True, 'redirect': url_for('choose_skill')})
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'error': 'Username or email already exists'}), 400
    
    return render_template('index.html')

@app.route('/signin', methods=['POST'])
def signin():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, username))
    user = cursor.fetchone()
    conn.close()
    
    if user and check_password_hash(user['password'], password):
        session['user_id'] = user['id']
        session['username'] = user['username']
        return jsonify({'success': True, 'redirect': url_for('choose_skill')})
    else:
        return jsonify({'error': 'Invalid username or password'}), 401

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/choose-skill')
def choose_skill():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('choose_skill.html')

@app.route('/api/skills', methods=['POST'])
def create_skill():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    skill_name = data.get('skill_name')
    target_time = data.get('target_time')
    
    if not skill_name:
        return jsonify({'error': 'Skill name is required'}), 400
    
    if target_time not in [5, 10, 15, 20]:
        return jsonify({'error': 'Target time must be 5, 10, 15, or 20 minutes'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO skills (user_id, skill_name, target_time) VALUES (?, ?, ?)',
        (session['user_id'], skill_name, target_time)
    )
    skill_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'skill_id': skill_id})

@app.route('/api/sessions', methods=['POST'])
def create_session():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    skill_id = data.get('skill_id')
    duration = data.get('duration')
    proof_file = data.get('proof_file', None)
    
    if not skill_id or not duration:
        return jsonify({'error': 'Skill ID and duration are required'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO sessions (user_id, skill_id, duration, proof_file) VALUES (?, ?, ?, ?)',
        (session['user_id'], skill_id, duration, proof_file)
    )
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'session_id': session_id})

@app.route('/api/upload-proof', methods=['POST'])
def upload_proof():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{session['user_id']}_{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return jsonify({'success': True, 'filename': filename})
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/progress')
def progress():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('progress.html')

@app.route('/api/progress')
def get_progress():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Get daily data
    cursor.execute('''
        SELECT DATE(completed_at) as date, COUNT(*) as count
        FROM sessions
        WHERE user_id = ?
        GROUP BY DATE(completed_at)
        ORDER BY date DESC
        LIMIT 30
    ''', (session['user_id'],))
    
    daily_data = cursor.fetchall()
    
    # Calculate streak (consecutive days including today)
    streak = 0
    today = datetime.now().date()
    dates_with_sessions = set()
    
    for row in daily_data:
        date_str = row['date']
        if isinstance(date_str, str):
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            date_obj = date_str
        dates_with_sessions.add(date_obj)
    
    # Check consecutive days starting from today
    current_date = today
    while current_date in dates_with_sessions:
        streak += 1
        current_date -= timedelta(days=1)
    
    # Also check if yesterday had a session (for ongoing streak)
    if streak == 0 and (today - timedelta(days=1)) in dates_with_sessions:
        # Check backwards from yesterday
        current_date = today - timedelta(days=1)
        while current_date in dates_with_sessions:
            streak += 1
            current_date -= timedelta(days=1)
    
    # Get all sessions with skill names
    cursor.execute('''
        SELECT s.*, sk.skill_name
        FROM sessions s
        JOIN skills sk ON s.skill_id = sk.id
        WHERE s.user_id = ?
        ORDER BY s.completed_at DESC
        LIMIT 50
    ''', (session['user_id'],))
    
    sessions = [dict(row) for row in cursor.fetchall()]
    
    # Get skill statistics
    cursor.execute('''
        SELECT sk.skill_name, COUNT(s.id) as session_count, 
               SUM(s.duration) as total_time
        FROM skills sk
        LEFT JOIN sessions s ON sk.id = s.skill_id
        WHERE sk.user_id = ?
        GROUP BY sk.id, sk.skill_name
    ''', (session['user_id'],))
    
    skill_stats = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify({
        'streak': streak,
        'sessions': sessions,
        'skill_stats': skill_stats,
        'daily_data': [dict(row) for row in daily_data]
    })

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

