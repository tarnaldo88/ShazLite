#!/usr/bin/env python3
"""Migrate existing fingerprint data to the new schema."""

import psycopg2
from backend.database.connection import DatabaseConnectionManager, DatabaseConfig
from backend.api.config import get_settings

def migrate_data():
    """Migrate existing data to new schema."""
    try:
        # Connect directly with psycopg2 to check old data
        conn = psycopg2.connect(
            host='localhost', 
            port=5433, 
            database='audio_fingerprinting', 
            user='postgres', 
            password='audio_password_change_me'
        )
        cur = conn.cursor()
        
        # Check what tables exist with data
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name NOT IN ('songs', 'fingerprints')
        """)
        old_tables = cur.fetchall()
        print("Old tables found:", [t[0] for t in old_tables])
        
        # Check if we have any fingerprint-like data
        for table_name in [t[0] for t in old_tables]:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cur.fetchone()[0]
                if count > 0:
                    print(f"Table '{table_name}': {count} rows")
                    
                    # Show sample data
                    cur.execute(f"SELECT * FROM {table_name} LIMIT 3")
                    columns = [desc[0] for desc in cur.description]
                    rows = cur.fetchall()
                    print(f"  Columns: {columns}")
                    for i, row in enumerate(rows):
                        print(f"  Row {i+1}: {row}")
            except Exception as e:
                print(f"Error querying {table_name}: {e}")
        
        # Insert sample songs for testing
        print("\nInserting sample songs...")
        
        songs_data = [
            ("SOFI TUKKER - Swing", "SOFI TUKKER", "Swing", 180),
            ("50 Cent - Many Men", "50 Cent", "Get Rich or Die Tryin'", 240),
            ("Test Song", "Test Artist", "Test Album", 200)
        ]
        
        for title, artist, album, duration in songs_data:
            cur.execute("""
                INSERT INTO songs (title, artist, album, duration_seconds, created_at) 
                VALUES (%s, %s, %s, %s, NOW())
            """, (title, artist, album, duration))
        
        conn.commit()
        print("✅ Sample songs inserted")
        
        # Check songs
        cur.execute("SELECT id, title, artist FROM songs")
        songs = cur.fetchall()
        print("Songs in database:")
        for song_id, title, artist in songs:
            print(f"  {song_id}: {title} by {artist}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    migrate_data()