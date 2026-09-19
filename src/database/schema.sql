CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact TEXT UNIQUE,
    role TEXT NOT NULL CHECK (role IN ('citizen', 'staff', 'admin'))
);

CREATE TABLE IF NOT EXISTS reports (
    report_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    before_photo TEXT,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    created_at TEXT NOT NULL,
    status TEXT DEFAULT 'OPEN',
    priority TEXT DEFAULT 'MEDIUM',
    risk_level TEXT DEFAULT 'NORMAL',

    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS assignments (
    assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    staff_id INTEGER NOT NULL,
    assigned_at TEXT NOT NULL,
    accepted_at TEXT,

    FOREIGN KEY (report_id) REFERENCES reports(report_id),
    FOREIGN KEY (staff_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS cleanup_evidence (
    evidence_id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    after_photo TEXT,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    captured_at TEXT NOT NULL,
    verification_status TEXT DEFAULT 'PENDING',

    FOREIGN KEY (report_id) REFERENCES reports(report_id)
);

CREATE TABLE IF NOT EXISTS status_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    old_status TEXT,
    new_status TEXT NOT NULL,
    changed_at TEXT NOT NULL,
    remarks TEXT,

    FOREIGN KEY (report_id) REFERENCES reports(report_id)
);