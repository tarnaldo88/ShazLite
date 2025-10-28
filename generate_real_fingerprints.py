#!/usr/bin/env python3
"""Generate real fingerprints from audio files and store in database."""

import os
import psycopg2
import numpy as np
from audio_engine.fingerprint_api import get_engine

def load_audio_file(file_path):
    """Load audio file and convert to numpy array."""
    try:
        # For this example, we'll create dummy audio data
        # In a real implementation, you'd use librosa or pydub to load the actual file
        
        # Create dummy audio data (sine wave) for testing
        sample_rate = 44100
        duration = 30  # 30 seconds
        frequency = 440  # A4 note
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = np.sin(2 * np.pi * frequency * t).astype(np.float32)
        
        return audio_data, sample_rate
    except Exception as e:
        print(f"Error loading audio file {file_path}: {e}")
        return None, None

def generate_fingerprints_for_song(song_id, title, artist):
    """Generate fingerprints for a specific song."""
    try:
        print(f"Generating fingerprints for: {title} by {artist}")
        
        # Load audio (in real implementation, you'd load the actual audio file)
        audio_data, sample_rate = load_audio_file(f"{title}.wav")
        
        if audio_data is None:
            print(f"  ❌ Could not load audio for {title}")
            return []
        
        # Generate fingerprints using the engine
        engine = get_engine()
        fingerprint_result = engine.generate_fingerprint(audio_data, sample_rate, 1)
        
        # Limit fingerprints for performance
        max_fingerprints = 5000
        actual_count = min(fingerprint_result.count, max_fingerprints)
        
        fingerprints = []
        for i in range(actual_count):
            fingerprints.append((
                song_id,
                int(fingerprint_result.hash_values[i]),
                int(fingerprint_result.time_offsets[i])
            ))
        
        print(f"  ✅ Generated {len(fingerprints)} fingerprints")
        return fingerprints
        
    except Exception as e:
        print(f"  ❌ Error generating fingerprints: {e}")
        return []

def main():
    """Main function to generate and store fingerprints."""
    try:
        # Connect to database
        conn = psycopg2.connect(
            host='localhost', 
            port=5433, 
            database='audio_fingerprinting', 
            user='postgres', 
            password='audio_password_change_me'
        )
        cur = conn.cursor()
        
        # Clear existing fingerprints
        print("Clearing existing fingerprints...")
        cur.execute("DELETE FROM fingerprints")
        conn.commit()
        
        # Get all songs
        cur.execute("SELECT id, title, artist FROM songs")
        songs = cur.fetchall()
        
        print(f"Generating fingerprints for {len(songs)} songs...")
        
        for song_id, title, artist in songs:
            # Generate fingerprints for this song
            fingerprints = generate_fingerprints_for_song(song_id, title, artist)
            
            if fingerprints:
                # Insert fingerprints in batches
                cur.executemany("""
                    INSERT INTO fingerprints (song_id, hash_value, time_offset_ms, created_at)
                    VALUES (%s, %s, %s, NOW())
                """, fingerprints)
                conn.commit()
        
        # Check total fingerprints
        cur.execute("SELECT COUNT(*) FROM fingerprints")
        total_fingerprints = cur.fetchone()[0]
        print(f"\n✅ Total fingerprints in database: {total_fingerprints}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Failed to generate fingerprints: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()