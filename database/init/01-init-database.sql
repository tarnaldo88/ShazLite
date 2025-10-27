-- Initialize Audio Fingerprinting Database
-- This script sets up the initial database structure and configuration

-- Create database if it doesn't exist (handled by Docker environment)
-- CREATE DATABASE audio_fingerprinting;

-- Connect to the database
\c audio_fingerprinting;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create custom types
DO $$ BEGIN
    CREATE TYPE audio_format AS ENUM ('wav', 'mp3', 'flac', 'm4a', 'ogg');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create songs table
CREATE TABLE IF NOT EXISTS songs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    artist VARCHAR(255) NOT NULL,
    album VARCHAR(255),
    duration_seconds INTEGER,
    year INTEGER,
    genre VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT songs_title_check CHECK (LENGTH(title) > 0),
    CONSTRAINT songs_artist_check CHECK (LENGTH(artist) > 0),
    CONSTRAINT songs_duration_check CHECK (duration_seconds > 0),
    CONSTRAINT songs_year_check CHECK (year > 1800 AND year <= EXTRACT(YEAR FROM NOW()) + 1)
);

-- Create fingerprints table
CREATE TABLE IF NOT EXISTS fingerprints (
    id BIGSERIAL PRIMARY KEY,
    song_id INTEGER NOT NULL REFERENCES songs(id) ON DELETE CASCADE,
    hash_value BIGINT NOT NULL,
    time_offset_ms INTEGER NOT NULL,
    frequency_1 REAL,
    frequency_2 REAL,
    time_delta_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT fingerprints_time_offset_check CHECK (time_offset_ms >= 0),
    CONSTRAINT fingerprints_frequency_check CHECK (frequency_1 >= 0 AND frequency_2 >= 0),
    CONSTRAINT fingerprints_time_delta_check CHECK (time_delta_ms >= 0)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_songs_artist ON songs(artist);
CREATE INDEX IF NOT EXISTS idx_songs_title ON songs(title);
CREATE INDEX IF NOT EXISTS idx_songs_album ON songs(album);
CREATE INDEX IF NOT EXISTS idx_songs_created_at ON songs(created_at);

-- Critical indexes for fingerprint matching
CREATE INDEX IF NOT EXISTS idx_fingerprints_hash ON fingerprints(hash_value);
CREATE INDEX IF NOT EXISTS idx_fingerprints_song_id ON fingerprints(song_id);
CREATE INDEX IF NOT EXISTS idx_fingerprints_song_time ON fingerprints(song_id, time_offset_ms);
CREATE INDEX IF NOT EXISTS idx_fingerprints_hash_time ON fingerprints(hash_value, time_offset_ms);

-- Composite index for efficient matching queries
CREATE INDEX IF NOT EXISTS idx_fingerprints_hash_song_time ON fingerprints(hash_value, song_id, time_offset_ms);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for songs table
DROP TRIGGER IF EXISTS update_songs_updated_at ON songs;
CREATE TRIGGER update_songs_updated_at
    BEFORE UPDATE ON songs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create function to get database statistics
CREATE OR REPLACE FUNCTION get_database_stats()
RETURNS TABLE(
    total_songs BIGINT,
    total_fingerprints BIGINT,
    avg_fingerprints_per_song NUMERIC,
    database_size TEXT,
    songs_table_size TEXT,
    fingerprints_table_size TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*) FROM songs)::BIGINT as total_songs,
        (SELECT COUNT(*) FROM fingerprints)::BIGINT as total_fingerprints,
        CASE 
            WHEN (SELECT COUNT(*) FROM songs) > 0 
            THEN (SELECT COUNT(*) FROM fingerprints)::NUMERIC / (SELECT COUNT(*) FROM songs)::NUMERIC
            ELSE 0::NUMERIC
        END as avg_fingerprints_per_song,
        pg_size_pretty(pg_database_size(current_database())) as database_size,
        pg_size_pretty(pg_total_relation_size('songs')) as songs_table_size,
        pg_size_pretty(pg_total_relation_size('fingerprints')) as fingerprints_table_size;
END;
$$ LANGUAGE plpgsql;

-- Create function to find matching fingerprints
CREATE OR REPLACE FUNCTION find_matching_fingerprints(
    input_hashes BIGINT[],
    min_matches INTEGER DEFAULT 5,
    max_results INTEGER DEFAULT 10
)
RETURNS TABLE(
    song_id INTEGER,
    title VARCHAR(255),
    artist VARCHAR(255),
    album VARCHAR(255),
    match_count BIGINT,
    confidence NUMERIC,
    time_offset_ms INTEGER
) AS $$
BEGIN
    RETURN QUERY
    WITH fingerprint_matches AS (
        SELECT 
            f.song_id,
            f.time_offset_ms,
            COUNT(*) as match_count
        FROM fingerprints f
        WHERE f.hash_value = ANY(input_hashes)
        GROUP BY f.song_id, f.time_offset_ms
        HAVING COUNT(*) >= min_matches
    ),
    song_matches AS (
        SELECT 
            fm.song_id,
            SUM(fm.match_count) as total_matches,
            MAX(fm.match_count) as best_match_count,
            (array_agg(fm.time_offset_ms ORDER BY fm.match_count DESC))[1] as best_time_offset
        FROM fingerprint_matches fm
        GROUP BY fm.song_id
        ORDER BY total_matches DESC, best_match_count DESC
        LIMIT max_results
    )
    SELECT 
        s.id as song_id,
        s.title,
        s.artist,
        s.album,
        sm.total_matches as match_count,
        LEAST(sm.total_matches::NUMERIC / array_length(input_hashes, 1)::NUMERIC, 1.0) as confidence,
        sm.best_time_offset as time_offset_ms
    FROM song_matches sm
    JOIN songs s ON s.id = sm.song_id
    ORDER BY sm.total_matches DESC, sm.best_match_count DESC;
END;
$$ LANGUAGE plpgsql;

-- Create function to clean up duplicate fingerprints
CREATE OR REPLACE FUNCTION cleanup_duplicate_fingerprints()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    WITH duplicates AS (
        SELECT id,
               ROW_NUMBER() OVER (
                   PARTITION BY song_id, hash_value, time_offset_ms 
                   ORDER BY created_at
               ) as rn
        FROM fingerprints
    )
    DELETE FROM fingerprints 
    WHERE id IN (
        SELECT id FROM duplicates WHERE rn > 1
    );
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions to the application user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO audio_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO audio_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO audio_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO audio_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO audio_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO audio_user;

-- Create sample data (optional, for development)
-- This will be populated by the application's seeding functionality

-- Log initialization completion
DO $$
BEGIN
    RAISE NOTICE 'Audio Fingerprinting Database initialized successfully';
    RAISE NOTICE 'Database: %', current_database();
    RAISE NOTICE 'User: %', current_user;
    RAISE NOTICE 'Timestamp: %', NOW();
END $$;