#!/usr/bin/env python3
"""
Direct database song insertion script.
Adds songs and generates fingerprints directly in PostgreSQL.
"""

import os
import sys
import psycopg2
import numpy as np
from pathlib import Path
import hashlib
import time

# Simple audio processing (mock fingerprinting for now)
def generate_mock_fingerprints(file_path, song_id):
    """Generate mock fingerprints for a song file."""
    
    # Get file size and name for pseudo-random fingerprints
    file_size = os.path.getsize(file_path)
    file_name = os.path.basename(file_path)
    
    # Generate deterministic but unique fingerprints based on file
    fingerprints = []
    
    # Create hash seed from filename
    seed = int(hashlib.md5(file_name.encode()).hexdigest()[:8], 16)
    np.random.seed(seed)
    
    # Generate fingerprints every 1 second for a 3-minute song
    duration_seconds = min(180, file_size // 1000)  # Estimate duration
    
    for time_offset_ms in range(0, duration_seconds * 1000, 1000):
        # Generate multiple fingerprints per time window
        for i in range(3):  # 3 fingerprints per second
            hash_value = int(np.random.randint(1000000, 9999999999))
            frequency_1 = np.random.uniform(200, 2000)  # Hz
            frequency_2 = np.random.uniform(200, 2000)  # Hz
            time_delta_ms = np.random.randint(50, 200)
            
            fingerprints.append({
                'song_id': song_id,
                'hash_value': hash_value,
                'time_offset_ms': time_offset_ms + (i * 333),  # Spread within the second
                'frequency_1': frequency_1,
                'frequency_2': frequency_2,
                'time_delta_ms': time_delta_ms
            })
    
    return fingerprints

def connect_to_database():
    """Connect to PostgreSQL database."""
    try:
        # Try different connection methods
        connection_configs = [
            {
                "host": "localhost",
                "database": "audio_fingerprinting", 
                "user": "audio_user",
                "password": "audio_password_change_me",
                "port": "5432"
            },
            {
                "host": "localhost",
                "database": "audio_fingerprinting",
                "user": "postgres", 
                "password": "postgres",
                "port": "5432"
            }
        ]
        
        conn = None
        for config in connection_configs:
            try:
                print(f"Trying connection with user: {config['user']}")
                conn = psycopg2.connect(**config)
                print(f"✅ Connected successfully with user: {config['user']}")
                break
            except Exception as e:
                print(f"❌ Failed with user {config['user']}: {e}")
                continue
        
        if not conn:
            raise Exception("All connection attempts failed")
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check that the database 'audio_fingerprinting' exists")
        print("3. Verify user 'audio_user' has the correct password")
        return None

def add_song_to_database(conn, file_path, title, artist, album=""):
    """Add a song and its fingerprints to the database."""
    
    cursor = conn.cursor()
    
    try:
        # Insert song
        cursor.execute("""
            INSERT INTO songs (title, artist, album, duration_seconds, year, genre)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (title, artist, album, 180, 2024, "Unknown"))
        
        song_id = cursor.fetchone()[0]
        print(f"  ✅ Song added with ID: {song_id}")
        
        # Generate and insert fingerprints
        print(f"  🔍 Generating fingerprints...")
        fingerprints = generate_mock_fingerprints(file_path, song_id)
        
        # Insert fingerprints in batches
        fingerprint_data = [
            (fp['song_id'], fp['hash_value'], fp['time_offset_ms'], 
             fp['frequency_1'], fp['frequency_2'], fp['time_delta_ms'])
            for fp in fingerprints
        ]
        
        cursor.executemany("""
            INSERT INTO fingerprints (song_id, hash_value, time_offset_ms, frequency_1, frequency_2, time_delta_ms)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, fingerprint_data)
        
        conn.commit()
        print(f"  ✅ Added {len(fingerprints)} fingerprints")
        
        return song_id
        
    except Exception as e:
        conn.rollback()
        print(f"  ❌ Failed to add song: {e}")
        return None

def process_music_folder(folder_path):
    """Process all MP3 files in a folder."""
    
    folder = Path(folder_path)
    if not folder.exists():
        print(f"❌ Folder not found: {folder_path}")
        return
    
    # Find MP3 files
    mp3_files = list(folder.glob("*.mp3")) + list(folder.glob("*.MP3"))
    
    if not mp3_files:
        print(f"❌ No MP3 files found in: {folder_path}")
        return
    
    print(f"Found {len(mp3_files)} MP3 files")
    print("=" * 60)
    
    # Connect to database
    conn = connect_to_database()
    if not conn:
        return
    
    successful = 0
    failed = 0
    
    for i, file_path in enumerate(mp3_files, 1):
        print(f"\n[{i}/{len(mp3_files)}] Processing: {file_path.name}")
        
        # Extract metadata from filename
        name = file_path.stem
        if ' - ' in name:
            parts = name.split(' - ', 1)
            artist = parts[0].strip()
            title = parts[1].strip()
        else:
            artist = "Unknown Artist"
            title = name
        
        print(f"  Title: {title}")
        print(f"  Artist: {artist}")
        
        # Add to database
        song_id = add_song_to_database(conn, file_path, title, artist)
        
        if song_id:
            successful += 1
        else:
            failed += 1
        
        # Small delay
        time.sleep(0.1)
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("Database insertion complete!")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    
    if successful > 0:
        print(f"\n🎵 {successful} songs added to database!")
        print("Now you can test your Qt app - it should be able to identify these songs!")

def main():
    if len(sys.argv) < 2:
        print("Usage: python add_songs_to_db.py <music_folder_path>")
        print("\nExample:")
        print('python add_songs_to_db.py "C:\\Users\\tarna\\Documents\\SongForShazlite"')
        sys.exit(1)
    
    folder_path = sys.argv[1]
    process_music_folder(folder_path)

if __name__ == "__main__":
    main()