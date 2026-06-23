import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'roma_secret_key_2026'

# Configure upload path for tour evidence photos
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

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
        return User(id=user_data['id'], first_name=user_data['first_name'], last_name=user_data['last_name'], email=user_data['email'], role=user_data['role'], languages=user_data['languages'])
    return None

@app.context_processor
def inject_now():
    return {'current_year': 2026}

# --- ROUTES ---

@app.route('/')
def index():
    conn = get_db_connection()
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

@app.route('/tour/<int:tour_id>')
def tour_details(tour_id):
    conn = get_db_connection()
    tour = conn.execute('SELECT * FROM tours WHERE id = ?', (tour_id,)).fetchone()
    if not tour:
        conn.close()
        flash('Tour not found.', 'danger')
        return redirect(url_for('index'))
        
    schedules = conn.execute('SELECT * FROM tour_schedules WHERE tour_id = ?', (tour_id,)).fetchall()
    conn.close()
    return render_template('tour_details.html', tour=tour, schedules=schedules)

@app.route('/book_tour/<int:tour_id>', methods=['POST'])
@login_required
def book_tour(tour_id):
    if current_user.role != 'participant':
        flash('Only registered tourists can book tours.', 'danger')
        return redirect(url_for('index'))
        
    tour_date = request.form.get('tour_date')
    additional_count = int(request.form.get('additional_count', 0))
    additional_names = request.form.get('additional_names', '')

    if additional_count > 3:
        flash('You can only add a maximum of 3 additional guests.', 'danger')
        return redirect(url_for('tour_details', tour_id=tour_id))

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO reservations (tour_id, participant_id, tour_date, additional_count, additional_names)
        VALUES (?, ?, ?, ?, ?)
    ''', (tour_id, current_user.id, tour_date, additional_count, additional_names))
    conn.commit()
    conn.close()

    flash('Reservation successfully confirmed!', 'success')
    return redirect(url_for('participant_profile'))

@app.route('/cancel_booking/<int:reservation_id>', methods=['POST'])
@login_required
def cancel_booking(reservation_id):
    conn = get_db_connection()
    res = conn.execute('''
        SELECT r.*, s.start_time 
        FROM reservations r 
        JOIN tour_schedules s ON r.tour_id = s.tour_id
        WHERE r.id = ? AND r.participant_id = ?
    ''', (reservation_id, current_user.id)).fetchone()

    if not res:
        conn.close()
        flash('Reservation log not found.', 'danger')
        return redirect(url_for('participant_profile'))

    tour_datetime_str = f"{res['tour_date']} {res['start_time']}"
    tour_datetime = datetime.strptime(tour_datetime_str, '%Y-%m-%d %H:%M')
    
    if tour_datetime - datetime.now() < timedelta(hours=24):
        conn.close()
        flash('Cancellation denied. Bookings can only be altered up to 24 hours prior to departure.', 'danger')
        return redirect(url_for('participant_profile'))

    conn.execute('DELETE FROM reservations WHERE id = ?', (reservation_id,))
    conn.commit()
    conn.close()

    flash('Reservation cancelled successfully.', 'info')
    return redirect(url_for('participant_profile'))

# --- NEW ROUTE: EDIT TOUR (WITH LOCK CONSTRAINT ON EXISTING RESERVATIONS) ---
@app.route('/edit_tour/<int:tour_id>', methods=['GET', 'POST'])
@login_required
def edit_tour(tour_id):
    if current_user.role != 'guide':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))
        
    conn = get_db_connection()
    tour = conn.execute('SELECT * FROM tours WHERE id = ? AND guide_id = ?', (tour_id, current_user.id)).fetchone()
    
    if not tour:
        conn.close()
        flash('Tour profile not found.', 'danger')
        return redirect(url_for('guide_profile'))
        
    # Check if this tour has at least one active reservation log
    has_reservation = conn.execute('SELECT id FROM reservations WHERE tour_id = ?', (tour_id,)).fetchone()
    
    if request.method == 'POST':
        title = request.form.get('title')
        meeting_point = request.form.get('meeting_point')
        duration = int(request.form.get('duration'))
        description = request.form.get('description')
        stops = request.form.get('stops')
        
        # Mandatory fields if modifications are locked due to exam rule
        if has_reservation:
            # Guide can only alter description, title, meeting point, and itinerary stops
            conn.execute('''
                UPDATE tours 
                SET title = ?, meeting_point = ?, description = ?, stops = ?
                WHERE id = ?
            ''', (title, meeting_point, description, stops, tour_id))
            flash('Tour description elements modified. Core attributes remained locked due to active bookings.', 'warning')
        else:
            # Guide can alter everything if no bookings exist
            language = request.form.get('language')
            max_participants = int(request.form.get('max_participants'))
            conn.execute('''
                UPDATE tours 
                SET title = ?, meeting_point = ?, duration = ?, description = ?, stops = ?, language = ?, max_participants = ?
                WHERE id = ?
            ''', (title, meeting_point, duration, description, stops, language, max_participants, tour_id))
            flash('Tour profile completely updated successfully.', 'success')
            
        conn.commit()
        conn.close()
        return redirect(url_for('guide_profile'))
        
    conn.close()
    return render_template('edit_tour.html', tour=tour, has_reservation=has_reservation)

# --- NEW ROUTE: POST-TOUR SUMMARY REPORTING ---
@app.route('/report_tour/<int:tour_id>', methods=['GET', 'POST'])
@login_required
def report_tour(tour_id):
    if current_user.role != 'guide':
        flash('Unauthorized access privileges.', 'danger')
        return redirect(url_for('index'))
        
    conn = get_db_connection()
    tour = conn.execute('SELECT * FROM tours WHERE id = ? AND guide_id = ?', (tour_id, current_user.id)).fetchone()
    
    if not tour:
        conn.close()
        flash('Tour data missing.', 'danger')
        return redirect(url_for('guide_profile'))
        
    if request.method == 'POST':
        tour_date = request.form.get('tour_date')
        actual_participants = int(request.form.get('actual_participants'))
        
        # Process files collection (Accept between 1 and 5 files as required)
        uploaded_files = request.files.getlist('evidence_photos')
        valid_files = [f for f in uploaded_files if f.filename != '']
        
        if len(valid_files) < 1 or len(valid_files) > 5:
            flash('You must upload between 1 and 5 dynamic evidence photos from the event.', 'danger')
            conn.close()
            return redirect(url_for('report_tour', tour_id=tour_id))
            
        # Save primary evidence filename reference
        primary_photo = secure_filename(valid_files[0].filename)
        for f in valid_files:
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            
        conn.execute('''
            INSERT INTO post_tour_reports (tour_id, tour_date, actual_participants, evidence_photo)
            VALUES (?, ?, ?, ?)
        ''', (tour_id, tour_date, actual_participants, primary_photo))
        conn.commit()
        conn.close()
        
        flash('Post-tour verification report submitted successfully to the platform metrics.', 'success')
        return redirect(url_for('guide_profile'))
        
    conn.close()
    return render_template('report_tour.html', tour=tour)

# --- AUTHENTICATION & BASE ROUTES ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        selected_langs = request.form.getlist('languages')
        languages_str = ",".join(selected_langs) if selected_langs else None

        if not first_name or not last_name or not email or not password or not role:
            flash('All mandatory fields must be completed.', 'danger')
            return redirect(url_for('register'))

        conn = get_db_connection()
        existing_user = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
        if existing_user:
            flash('Email address already registered.', 'danger')
            conn.close()
            return redirect(url_for('register'))
            
        hashed_password = generate_password_hash(password)
        conn.execute('INSERT INTO users (first_name, last_name, email, password, role, languages) VALUES (?, ?, ?, ?, ?, ?)',
                     (first_name, last_name, email, hashed_password, role, languages_str))
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
            user_obj = User(id=user_data['id'], first_name=user_data['first_name'], last_name=user_data['last_name'], email=user_data['email'], role=user_data['role'], languages=user_data['languages'])
            login_user(user_obj)
            flash(f'Welcome back, {user_obj.first_name}!', 'success')
            if user_obj.role == 'admin': return redirect(url_for('admin_dashboard'))
            elif user_obj.role == 'guide': return redirect(url_for('guide_profile'))
            else: return redirect(url_for('participant_profile'))
        else:
            flash('Invalid email or password credentials.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Successfully logged out.', 'info')
    return redirect(url_for('index'))

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
    total_guides = conn.execute("SELECT COUNT(*) FROM users WHERE role='guide'").fetchone()[0]
    total_parts = conn.execute("SELECT COUNT(*) FROM users WHERE role='participant'").fetchone()[0]
    total_tours = conn.execute("SELECT COUNT(*) FROM tours").fetchone()[0]
    total_res = conn.execute("SELECT COUNT(*) FROM reservations").fetchone()[0]
    lang_stats = conn.execute('SELECT t.language, COUNT(r.id) as count FROM reservations r JOIN tours t ON r.tour_id = t.id GROUP BY t.language').fetchall()
    guides = conn.execute("SELECT id, first_name, last_name, email, languages FROM users WHERE role='guide'").fetchall()
    guides_with_tours = []
    for g in guides:
        tours = conn.execute("SELECT title FROM tours WHERE guide_id = ?", (g['id'],)).fetchall()
        guides_with_tours.append({'info': g, 'tours': tours})
    conn.close()
    return render_template('admin.html', total_guides=total_guides, total_parts=total_parts, total_tours=total_tours, total_res=total_res, lang_stats=lang_stats, guides_with_tours=guides_with_tours)

if __name__ == '__main__':
    app.run(debug=True)