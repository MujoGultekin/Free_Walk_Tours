import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'roma_secret_key_2026'

# Configure Flask-Login settings
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# Helper function to establish connection with SQLite database
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# User class model for session management
class User(UserMixin):
    def __init__(self, id, first_name, last_name, email, role, languages=None):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.role = role
        self.languages = languages

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user_data = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user_data:
        return User(
            id=user_data['id'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            email=user_data['email'],
            role=user_data['role'],
            languages=user_data['languages']
        )
    return None

# Context processor to inject the modern year into templates dynamically
@app.context_processor
def inject_now():
    return {'current_year': 2026}

# --- ROUTES ---

@app.route('/')
def index():
    conn = get_db_connection()
    
    # Process search filters from requests
    lang_filter = request.args.get('language', '')
    duration_filter = request.args.get('duration', '')
    
    query = 'SELECT * FROM tours WHERE 1=1'
    params = []
    
    if lang_filter:
        query += ' AND language = ?'
        params.append(lang_filter)
    if duration_filter:
        query += ' AND duration <= ?'
        params.append(int(duration_filter))
        
    tours = conn.execute(query, params).fetchall()
    conn.close()
    return render_template('index.html', tours=tours)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        
        # Process language checkboxes for guide profiles
        selected_langs = request.form.getlist('languages')
        languages_str = ",".join(selected_langs) if selected_langs else None

        # Backend mandatory fields verification
        if not first_name or not last_name or not email or not password or not role:
            flash('All mandatory fields must be completed.', 'danger')
            return redirect(url_for('register'))

        conn = get_db_connection()
        # Verify email uniqueness
        existing_user = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
        
        if existing_user:
            flash('Email address already registered.', 'danger')
            conn.close()
            return redirect(url_for('register'))
            
        hashed_password = generate_password_hash(password)
        conn.execute('''
            INSERT INTO users (first_name, last_name, email, password, role, languages)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (first_name, last_name, email, hashed_password, role, languages_str))
        conn.commit()
        conn.close()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        user_data = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if user_data and check_password_hash(user_data['password'], password):
            user_obj = User(
                id=user_data['id'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                email=user_data['email'],
                role=user_data['role'],
                languages=user_data['languages']
            )
            login_user(user_obj)
            flash(f'Welcome back, {user_obj.first_name}!', 'success')
            
            # Dynamic redirection rules based on authorization roles
            if user_obj.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user_obj.role == 'guide':
                return redirect(url_for('guide_profile'))
            else:
                return redirect(url_for('participant_profile'))
        else:
            flash('Invalid email or password credentials.', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Successfully logged out.', 'info')
    return redirect(url_for('index'))

# --- ROLES AND DASHBOARDS ---

@app.route('/profile/guide')
@login_required
def guide_profile():
    if current_user.role != 'guide':
        flash('Unauthorized access area.', 'danger')
        return redirect(url_for('index'))
        
    conn = get_db_connection()
    tours = conn.execute('SELECT * FROM tours WHERE guide_id = ?', (current_user.id,)).fetchall()
    conn.close()
    return render_template('profile_guide.html', tours=tours)

@app.route('/profile/participant')
@login_required
def participant_profile():
    if current_user.role != 'participant':
        flash('Unauthorized access area.', 'danger')
        return redirect(url_for('index'))
        
    conn = get_db_connection()
    reservations = conn.execute('''
        SELECT r.*, t.title, t.meeting_point 
        FROM reservations r
        JOIN tours t ON r.tour_id = t.id
        WHERE r.participant_id = ?
    ''', (current_user.id,)).fetchall()
    conn.close()
    return render_template('profile_participant.html', reservations=reservations)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied. Administrator privileges required.', 'danger')
        return redirect(url_for('index'))
        
    conn = get_db_connection()
    
    # Extract global platform metrics required for Prova Finale graduation tier
    total_guides = conn.execute("SELECT COUNT(*) FROM users WHERE role='guide'").fetchone()[0]
    total_parts = conn.execute("SELECT COUNT(*) FROM users WHERE role='participant'").fetchone()[0]
    total_tours = conn.execute("SELECT COUNT(*) FROM tours").fetchone()[0]
    total_res = conn.execute("SELECT COUNT(*) FROM reservations").fetchone()[0]
    
    # Calculate reservation frequencies per active language
    lang_stats = conn.execute('''
        SELECT t.language, COUNT(r.id) as count 
        FROM reservations r
        JOIN tours t ON r.tour_id = t.id
        GROUP BY t.language
    ''').fetchall()
    
    # Extract structural overview for registered guides accounts
    guides = conn.execute("SELECT id, first_name, last_name, email, languages FROM users WHERE role='guide'").fetchall()
    
    guides_with_tours = []
    for g in guides:
        tours = conn.execute("SELECT title FROM tours WHERE guide_id = ?", (g['id'],)).fetchall()
        guides_with_tours.append({'info': g, 'tours': tours})
        
    conn.close()
    return render_template('admin.html', 
                           total_guides=total_guides, total_parts=total_parts,
                           total_tours=total_tours, total_res=total_res,
                           lang_stats=lang_stats, guides_with_tours=guides_with_tours)

if __name__ == '__main__':
    app.run(debug=True)