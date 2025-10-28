#!/usr/bin/env python3
"""
Simple database initialization script for testing the Qt app.
This creates a minimal SQLite database for development/testing.
"""

import sqlite3
import os
import sys

def create_simple_database():
    """Create a simple SQLite database for testing."""
    
    db_path = "audio_fingerprinting.db"
    
    # Remove existing database
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database: {db_path}")
    
    # Create new database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Creating database tables...")
    
    # Create songs table
    cursor.execute("""
        CREATE TABLE songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            artist TEXT NOT NULL,
            album TEXT,
            duration_seconds INTEGER,
            year INTEGER,
            genre TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create fingerprints table
    cursor.execute("""
        CREATE TABLE fingerprints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_id INTEGER NOT NULL,
            hash_value INTEGER NOT NULL,
            time_offset_ms INTEGER NOT NULL,
            frequency_1 REAL,
            frequency_2 REAL,
            time_delta_ms INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX idx_fingerprints_hash ON fingerprints(hash_value)")
    cursor.execute("CREATE INDEX idx_fingerprints_song_id ON fingerprints(song_id)")
    cursor.execute("CREATE INDEX idx_songs_artist ON songs(artist)")
    cursor.execute("CREATE INDEX idx_songs_title ON songs(title)")
    
    # Insert a test song for demonstration
    cursor.execute("""
        INSERT INTO songs (title, artist, album, duration_seconds, year, genre)
        VALUES ('Test Song', 'Test Artist', 'Test Album', 180, 2024, 'Test')
    """)
    
    # Insert some dummy fingerprints for the test song
    test_fingerprints = [
        (1, 12345, 1000, 440.0, 880.0, 100),
        (1, 23456, 2000, 523.0, 1046.0, 150),
        (1, 34567, 3000, 659.0, 1318.0, 200),
    ]
    
    cursor.executemany("""
        INSERT INTO fingerprints (song_id, hash_value, time_offset_ms, frequency_1, frequency_2, time_delta_ms)
        VALUES (?, ?, ?, ?, ?, ?)
    """, test_fingerprints)
    
    conn.commit()
    conn.close()
    
    print(f"✅ Database created successfully: {db_path}")
    print("✅ Test song and fingerprints added")
    print("\nDatabase contents:")
    
    # Show what was created
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM songs")
    song_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM fingerprints")
    fingerprint_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT title, artist FROM songs LIMIT 5")
    songs = cursor.fetchall()
    
    print(f"Songs: {song_count}")
    print(f"Fingerprints: {fingerprint_count}")
    print("Sample songs:")
    for song in songs:
        print(f"  - {song[1]} - {song[0]}")
    
    conn.close()
    
    return db_path

def main():
    print("Initializing simple database for audio fingerprinting...")
    print("=" * 60)
    
    try:
        db_path = create_simple_database()
        
        print("\n" + "=" * 60)
        print("✅ Database initialization complete!")
        print(f"Database file: {os.path.abspath(db_path)}")
        print("\nNow you can:")
        print("1. Test your Qt app - it should be able to identify audio")
        print("2. The test song won't match real audio, but the system will work")
        print("3. Add real songs later using the upload functionality")
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()