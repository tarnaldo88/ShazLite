-- Audio Fingerprinting Database Schema
-- Creates tables for songs and fingerprints with proper indexes

-- Song metadata table
CREATE TABLE IF NOT EXISTS songs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    artist VARCHAR(255) NOT NULL,
    album VARCHAR(255),
    duration_seconds INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT songs_title_not_empty CHECK (LENGTH(TRIM(title)) > 0),
    CONSTRAINT songs_artist_not_empty CHECK (LENGTH(TRIM(artist)) > 0),
    CONSTRAINT songs_duration_positive CHECK (duration_seconds IS NULL OR duration_seconds > 0)
);

-- Fingerprint hash table
CREATE TABLE IF NOT EXISTS fingerprints (
    id BIGSERIAL PRIMARY KEY,
    song_id INTEGER NOT NULL REFERENCES songs(id) ON DELETE CASCADE,
    hash_value BIGINT NOT NULL,
    time_offset_ms INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT fingerprints_time_offset_non_negative CHECK (time_offset_ms >= 0)
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_fingerprints_hash ON fingerprints(hash_value);
CREATE INDEX IF NOT EXISTS idx_fingerprints_song_time ON fingerprints(song_id, time_offset_ms);
CREATE INDEX IF NOT EXISTS idx_songs_artist_title ON songs(artist, title);
CREATE INDEX IF NOT EXISTS idx_fingerprints_hash_time ON fingerprints(hash_value, time_offset_ms);

-- Additional performance indexes
CREATE INDEX IF NOT EXISTS idx_songs_created_at ON songs(created_at);
CREATE INDEX IF NOT EXISTS idx_fingerprints_created_at ON fingerprints(created_at);

-- Statistics for query optimization
ANALYZE songs;
ANALYZE fingerprints;