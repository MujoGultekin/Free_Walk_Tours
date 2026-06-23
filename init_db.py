import sqlite3
from werkzeug.security import generate_password_hash

def init_db():
    # Establish connection with the SQLite database file
    conn = sqlite3.connect('database.db')
    
    # Read and execute the SQL database structure from schema.sql
    with open('schema.sql', 'r') as f:
        conn.executescript(f.read())
    
    cursor = conn.cursor()
    
    # Generate secure password hash for testing credentials ('password123')
    hashed_pwd = generate_password_hash('password123')
    
    # 1. Insert Platform Administrator Profile (Required for Prova Finale)
    cursor.execute("""
        INSERT OR IGNORE INTO users (id, first_name, last_name, email, password, role) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (1, 'Alessandro', 'Rossi', 'admin@roma.it', hashed_pwd, 'admin'))
    
    # 2. Insert Professional Tour Guides Data
    cursor.execute("""
        INSERT OR IGNORE INTO users (id, first_name, last_name, email, password, role, languages) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (2, 'Marco', 'Verdi', 'marco@guide.com', hashed_pwd, 'guide', 'Italian,English,Spanish'))
    
    cursor.execute("""
        INSERT OR IGNORE INTO users (id, first_name, last_name, email, password, role, languages) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (3, 'Sofia', 'Bianchi', 'sofia@guide.com', hashed_pwd, 'guide', 'English,German,Portuguese'))
    
    # 3. Insert Registered Participants (Tourists) Data
    cursor.execute("""
        INSERT OR IGNORE INTO users (id, first_name, last_name, email, password, role) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (4, 'John', 'Doe', 'john@part.com', hashed_pwd, 'participant'))
    
    cursor.execute("""
        INSERT OR IGNORE INTO users (id, first_name, last_name, email, password, role) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (5, 'Maria', 'Garcia', 'maria@part.com', hashed_pwd, 'participant'))
    
    cursor.execute("""
        INSERT OR IGNORE INTO users (id, first_name, last_name, email, password, role) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (6, 'Hans', 'Müller', 'hans@part.com', hashed_pwd, 'participant'))
    
    # 4. Insert Sample Roma Walking Tours Data
    cursor.execute("""
        INSERT OR IGNORE INTO tours (id, title, guide_id, meeting_point, duration, language, max_participants, description, stops, photo_1)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (1, 'Colosseum & Ancient Rome Secrets', 2, 'Colosseum Metro Exit', 120, 'English', 20, 
          'Explore the majestic history of Rome, the gladiators, and the Roman Forum with an expert.', 
          'Colosseum,Roman Forum,Palatine Hill', 'colosseum.jpg'))
          
    cursor.execute("""
        INSERT OR IGNORE INTO tours (id, title, guide_id, meeting_point, duration, language, max_participants, description, stops, photo_1)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (2, 'Trastevedere Roman Street Food Tour', 2, 'Piazza Santa Maria in Trastevere', 90, 'Italian', 15, 
          'Discover authentic Roman cuisine and street delicacies in the heart of Trastevere.', 
          'Piazza Santa Maria,Local Bakery,Suppli Shop', 'trastevere.jpg'))

    cursor.execute("""
        INSERT OR IGNORE INTO tours (id, title, guide_id, meeting_point, duration, language, max_participants, description, stops, photo_1)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (3, 'Baroque Rome & Fountains Walk', 3, 'Piazza del Popolo', 150, 'English', 25, 
          'A beautiful walk through the masterworks of Bernini and Borromini across historical squares.', 
          'Piazza del Popolo,Trevi Fountain,Pantheon,Piazza Navona', 'fountains.jpg'))
    
    # 5. Insert Weekly Tour Operational Schedules
    cursor.execute("INSERT OR IGNORE INTO tour_schedules (id, tour_id, day_of_week, start_time) VALUES (?, ?, ?, ?)", (1, 1, 'Monday', '10:00'))
    cursor.execute("INSERT OR IGNORE INTO tour_schedules (id, tour_id, day_of_week, start_time) VALUES (?, ?, ?, ?)", (2, 1, 'Wednesday', '15:00'))
    cursor.execute("INSERT OR IGNORE INTO tour_schedules (id, tour_id, day_of_week, start_time) VALUES (?, ?, ?, ?)", (3, 2, 'Friday', '18:30'))
    cursor.execute("INSERT OR IGNORE INTO tour_schedules (id, tour_id, day_of_week, start_time) VALUES (?, ?, ?, ?)", (4, 3, 'Saturday', '11:00'))
    
    # 6. Insert Mock Booking Reservations to populate Admin Dashboard Statistics
    cursor.execute("""
        INSERT OR IGNORE INTO reservations (id, tour_id, participant_id, tour_date, additional_count, additional_names) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (1, 1, 4, '2026-07-06', 1, 'Jane Doe'))
    
    cursor.execute("""
        INSERT OR IGNORE INTO reservations (id, tour_id, participant_id, tour_date, additional_count, additional_names) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (2, 2, 5, '2026-07-10', 0, None))
    
    cursor.execute("""
        INSERT OR IGNORE INTO reservations (id, tour_id, participant_id, tour_date, additional_count, additional_names) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (3, 3, 6, '2026-07-11', 2, 'Anna Müller, Kurt Müller'))

    conn.commit()
    conn.close()
    print("Database successfully initialized with comprehensive English sample records!")

if __name__ == '__main__':
    init_db()