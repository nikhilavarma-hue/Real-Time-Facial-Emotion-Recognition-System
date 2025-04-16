-- Schema for the facial emotion recognition application

-- Drop tables if they exist
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS emotion_records;
DROP TABLE IF EXISTS sessions;
DROP TABLE IF EXISTS settings;

-- Create users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create emotion records table
CREATE TABLE emotion_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    emotions_data TEXT NOT NULL,  -- JSON string of emotion probabilities
    dominant_emotion TEXT NOT NULL DEFAULT 'neutral',
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Create sessions table
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Create settings table
CREATE TABLE settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    theme TEXT DEFAULT 'light',
    notification_enabled BOOLEAN DEFAULT TRUE,
    privacy_mode BOOLEAN DEFAULT FALSE,
    analysis_frequency INTEGER DEFAULT 5,  -- Analyze every N frames
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Create indexes
CREATE INDEX idx_emotion_records_user_id ON emotion_records (user_id);
CREATE INDEX idx_emotion_records_timestamp ON emotion_records (timestamp);
CREATE INDEX idx_sessions_token ON sessions (session_token);
CREATE INDEX idx_users_username ON users (username);