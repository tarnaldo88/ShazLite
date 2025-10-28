-- Create the audio_user for the backend to use
-- Run this in pgAdmin as the postgres superuser

-- Create user
CREATE USER audio_user WITH PASSWORD 'torres123';

-- Grant database privileges
GRANT ALL PRIVILEGES ON DATABASE audio_fingerprinting TO audio_user;

-- Connect to the audio_fingerprinting database first, then run:
-- \c audio_fingerprinting;

-- Grant table privileges
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO audio_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO audio_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO audio_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO audio_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO audio_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO audio_user;

-- Verify the user was created
SELECT usename FROM pg_user WHERE usename = 'audio_user';