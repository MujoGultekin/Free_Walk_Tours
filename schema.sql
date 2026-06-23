-- Database structural configuration definitions for user profiles
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL, -- Supported: 'guide', 'participant', 'admin'
    languages TEXT      -- Comma-separated language attributes for guide roles
);

-- Tour details data structures
CREATE TABLE IF NOT EXISTS tours (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    guide_id INTEGER NOT NULL,
    meeting_point TEXT NOT NULL,
    duration INTEGER NOT NULL, -- Estimated in minutes
    language TEXT NOT NULL,
    max_participants INTEGER NOT NULL,
    description TEXT NOT NULL,
    stops TEXT NOT NULL,       -- Comma-separated landmark destinations
    photo_1 TEXT, photo_2 TEXT, photo_3 TEXT, photo_4 TEXT, photo_5 TEXT,
    FOREIGN KEY (guide_id) REFERENCES users(id)
);

-- Weekly execution schedule configurations
CREATE TABLE IF NOT EXISTS tour_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tour_id INTEGER NOT NULL,
    day_of_week TEXT NOT NULL, -- e.g., 'Monday', 'Tuesday'
    start_time TEXT NOT NULL,  -- e.g., '10:00'
    FOREIGN KEY (tour_id) REFERENCES tours(id)
);

-- Client booking registration storage structures
CREATE TABLE IF NOT EXISTS reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tour_id INTEGER NOT NULL,
    participant_id INTEGER NOT NULL,
    tour_date TEXT NOT NULL,   -- Date string formatting: 'YYYY-MM-DD'
    additional_count INTEGER DEFAULT 0,
    additional_names TEXT,     -- Comma-separated names for supplementary visitors
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tour_id) REFERENCES tours(id),
    FOREIGN KEY (participant_id) REFERENCES users(id)
);

-- Post-tour validation reporting indicators
CREATE TABLE IF NOT EXISTS post_tour_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tour_id INTEGER NOT NULL,
    tour_date TEXT NOT NULL,
    actual_participants INTEGER NOT NULL,
    evidence_photo TEXT NOT NULL,
    FOREIGN KEY (tour_id) REFERENCES tours(id)
);