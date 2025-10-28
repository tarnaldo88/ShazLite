-- Update the audio_user password to match the .env file
ALTER USER audio_user WITH PASSWORD 'audio_password_change_me';

-- Verify the user exists and has correct privileges
SELECT usename, usecreatedb, usesuper FROM pg_user WHERE usename = 'audio_user';

-- Test connection (you can run this after updating the password)
SELECT 'Password updated successfully for audio_user' as result;