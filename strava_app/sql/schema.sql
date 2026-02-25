-- Schema for Strava Activities
-- Optimized for AI Personal Trainer access

DROP TABLE IF EXISTS strava_activities CASCADE;

CREATE TABLE IF NOT EXISTS strava_activities (
    strava_id BIGINT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    sport_type TEXT,
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    start_date_local TIMESTAMP WITHOUT TIME ZONE,
    distance FLOAT NOT NULL, -- in meters (AI should divide by 1000 for km)
    moving_time INTEGER NOT NULL, -- in seconds (AI should divide by 60 for minutes)
    elapsed_time INTEGER NOT NULL, -- in seconds
    total_elevation_gain FLOAT, -- in meters
    average_heartrate FLOAT,
    max_heartrate FLOAT,
    average_speed FLOAT, -- in meters per second (m/s)
    max_speed FLOAT, -- in meters per second (m/s)
    suffer_score INTEGER,
    kudos_count INTEGER DEFAULT 0,
    achievement_count INTEGER DEFAULT 0,
    timezone TEXT,
    metadata JSONB, -- Optional extra data (e.g., gear, description)
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for date-based queries (common for trainers)
CREATE INDEX IF NOT EXISTS idx_activities_start_date ON strava_activities (start_date);
-- Index for type-based queries
CREATE INDEX IF NOT EXISTS idx_activities_type ON strava_activities (type);
