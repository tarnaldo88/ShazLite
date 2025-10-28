#!/usr/bin/env python3
"""Load real MP3 files and generate proper fingerprints."""

import os
import psycopg2
import numpy as np
import librosa
from audio_engine.fingerprint_api import get_engine

# Directory containing your MP3 files
SONGS_DIR = r"C:\Users\tarna\Documents\SongForShazlite"

def load_mp3_file(file_path):
    """Load MP3 file and convert to numpy array."""
    try:
        print(f"Loading: {os.path.basename(file_path)}")
        
        # Load MP3 file using librosa with fixed sample rate for consistency
        target_sr = 44100  # Standardize on 44.1kHz
        audio_data, sample_rate = librosa.load(file_path, sr=target_sr, mono=True)
        
        # Convert to float32 if needed
        audio_data = audio_data.astype(np.float32)
        
        print(f"  Sample rate: {sample_rate} Hz (resampled to {target_sr})")
        print(f"  Duration: {len(audio_data) / sample_rate:.1f} seconds")
        print(f"  Samples: {len(audio_data)}")
        
        return audio_data, sample_rate
        
    except Exception as e:
        print(f"  ❌ Error loading {file_path}: {e}")
        return None, None

def extract_song_info(filename):
    """Extract song title and artist from filename."""
    # Remove .mp3 extension
    name = os.path.splitext(filename)[0]
    
    # Try to parse different formats
    if " - " in name:
        parts = name.split(" - ", 1)
        artist = parts[0].strip()
        title = parts[1].strip()
    else:
        # If no separator, use filename as title
        artist = "Unknown Artist"
        title = name
    
    return title, artist

def generate_fingerprints_for_file(file_path):
    """Generate fingerprints for a single MP3 file."""
    try:
        # Load audio file
        audio_data, sample_rate = load_mp3_file(file_path)
        
        if audio_data is None:
            return None, []
        
        # Extract song info from filename
        filename = os.path.basename(file_path)
        title, artist = extract_song_info(filename)
        
        print(f"  Generating fingerprints for: {title} by {artist}")
        
        # Generate fingerprints using the engine
        engine = get_engine()
        fingerprint_result = engine.generate_fingerprint(audio_data, sample_rate, 1)
        
        # Limit fingerprints for performance (take every 10th fingerprint)
        max_fingerprints = 5000
        step = max(1, fingerprint_result.count // max_fingerprints)
        
        fingerprints = []
        for i in range(0, fingerprint_result.count, step):
            if len(fingerprints) >= max_fingerprints:
                break
            fingerprints.append((
                int(fingerprint_result.hash_values[i]),
                int(fingerprint_result.time_offsets[i])
            ))
        
        print(f"  ✅ Generated {len(fingerprints)} fingerprints")
        
        return (title, artist), fingerprints
        
    except Exception as e:
        print(f"  ❌ Error generating fingerprints: {e}")
        return None, []

def main():
    """Main function to process all MP3 files."""
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
        
        # Clear existing data
        print("Clearing existing songs and fingerprints...")
        cur.execute("DELETE FROM fingerprints")
        cur.execute("DELETE FROM songs")
        conn.commit()
        
        # Get all MP3 files
        mp3_files = [f for f in os.listdir(SONGS_DIR) if f.lower().endswith('.mp3')]
        print(f"Found {len(mp3_files)} MP3 files:")
        for f in mp3_files:
            print(f"  - {f}")
        
        print("\nProcessing files...")
        
        for mp3_file in mp3_files:
            file_path = os.path.join(SONGS_DIR, mp3_file)
            
            # Generate fingerprints
            song_info, fingerprints = generate_fingerprints_for_file(file_path)
            
            if song_info and fingerprints:
                title, artist = song_info
                
                # Insert song into database
                cur.execute("""
                    INSERT INTO songs (title, artist, album, duration_seconds, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                    RETURNING id
                """, (title, artist, "Unknown Album", 180))  # Default duration
                
                song_id = cur.fetchone()[0]
                print(f"  Inserted song with ID: {song_id}")
                
                # Insert fingerprints
                fingerprint_data = [(song_id, hash_val, time_offset) for hash_val, time_offset in fingerprints]
                cur.executemany("""
                    INSERT INTO fingerprints (song_id, hash_value, time_offset_ms, created_at)
                    VALUES (%s, %s, %s, NOW())
                """, fingerprint_data)
                
                conn.commit()
                print(f"  ✅ Inserted {len(fingerprints)} fingerprints")
            
            print()  # Empty line for readability
        
        # Show final statistics
        cur.execute("SELECT COUNT(*) FROM songs")
        song_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM fingerprints")
        fingerprint_count = cur.fetchone()[0]
        
        print(f"✅ Processing complete!")
        print(f"  Total songs: {song_count}")
        print(f"  Total fingerprints: {fingerprint_count}")
        
        # Show songs in database
        cur.execute("SELECT id, title, artist FROM songs")
        songs = cur.fetchall()
        print("\nSongs in database:")
        for song_id, title, artist in songs:
            print(f"  {song_id}: {title} by {artist}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Failed to process MP3 files: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()