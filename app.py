from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
from datetime import datetime, timedelta
import google.generativeai as genai

app = Flask(__name__)
app.secret_key = 'microspark-secret-key-change-in-production'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# ----------------------------------------
# GOOGLE GEMINI API SETUP + ERROR HANDLING
# ----------------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'mp4', 'mov', 'avi'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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

    # Sessions table
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
            hashed = generate_password_hash(password)
            cursor.execute(
                'INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                (username, email, hashed))
            conn.commit()

            session['user_id'] = cursor.lastrowid
            session['username'] = username
            return jsonify({'success': True, 'redirect': url_for('choose_skill')})
        except sqlite3.IntegrityError:
            return jsonify({'error': 'Username/email already exists'}), 400

    return render_template('index.html')


@app.route('/signin', methods=['POST'])
def signin():
    username = request.form.get('username')
    password = request.form.get('password')

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, username))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user['password'], password):
        session['user_id'] = user['id']
        session['username'] = user['username']
        return jsonify({'success': True, 'redirect': url_for('choose_skill')})

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


# ---------------------------------------------------
# UPDATED CHALLENGES API WITH GEMINI + FALLBACK LIST
# ---------------------------------------------------
@app.route('/api/challenges', methods=['POST'])
def get_challenges():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.json
    skill_type = data.get('skill_type')

    fallback = {
        "Coding": [
            "Build a function to reverse a string.",
            "Create a simple To-Do CLI app storing tasks in memory.",
            "Write a program that checks if a number is prime."
        ],
        "Writing": [
            "Write a 150-word story that starts with 'I woke up and everything changed.'",
            "Describe your happiest memory in a poetic tone.",
            "Write a letter to your future self."
        ],
        "Painting": [
            "Draw any object around you in 10 minutes using shading.",
            "Paint a simple landscape with sky + ground + one object.",
            "Sketch a self-portrait without lifting the pencil."
        ]
    }

    if skill_type not in fallback:
        return jsonify({'error': 'Invalid skill type'}), 400

    # Try calling Gemini
    if GEMINI_API_KEY:
        try:
            model = genai.GenerativeModel("gemini-pro")
            response = model.generate_content(
                f"Generate 3 creative short {skill_type} practice challenges for 5-20 min learners.")
            text = response.text.split("\n")
            suggestions = [line.strip() for line in text if line.strip()][:3]
            return jsonify({'success': True, 'challenges': suggestions})

        except Exception as e:
            print("Gemini error:", str(e))

    # If Gemini fails -> use fallback
    return jsonify({'success': True, 'challenges': fallback[skill_type]})


@app.route('/api/skills', methods=['POST'])
def create_skill():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.json
    skill_name = data.get('skill_name')
    target_time = data.get('target_time')

    if not skill_name:
        return jsonify({'error': 'Skill name required'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO skills (user_id, skill_name, target_time) VALUES (?, ?, ?)',
        (session['user_id'], skill_name, target_time))
    conn.commit()
    return jsonify({'success': True, 'skill_id': cursor.lastrowid})


@app.route('/api/sessions', methods=['POST'])
def create_session():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.json
    skill_id = data.get('skill_id')
    duration = data.get('duration')
    proof_file = data.get('proof_file')

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO sessions (user_id, skill_id, duration, proof_file) VALUES (?, ?, ?, ?)',
        (session['user_id'], skill_id, duration, proof_file))
    conn.commit()

    return jsonify({'success': True})


@app.route('/api/upload-proof', methods=['POST'])
def upload_proof():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'No file provided'}), 400

    filename = f"{session['user_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return jsonify({'success': True, 'filename': filename})


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ------------------------------
# PROGRESS STATISTICS ENDPOINT
# ------------------------------
@app.route('/progress')
def progress():
    return render_template('progress.html')


@app.route('/api/progress')
def get_progress():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT s.*, sk.skill_name
        FROM sessions s
        JOIN skills sk ON s.skill_id = sk.id
        WHERE s.user_id = ?
        ORDER BY s.completed_at DESC
    ''', (session['user_id'],))
    sessions = [dict(row) for row in cursor.fetchall()]

    return jsonify({'sessions': sessions})


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
