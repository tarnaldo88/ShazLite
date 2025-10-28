#!/usr/bin/env python3
"""Create sample fingerprints for testing."""

import psycopg2
import random

def create_sample_fingerprints():
    """Create sample fingerprints for each song."""
    try:
        conn = psycopg2.connect(
            host='localhost', 
            port=5433, 
            database='audio_fingerprinting', 
            user='postgres', 
            password='audio_password_change_me'
        )
        cur = conn.cursor()
        
        # Get all songs
        cur.execute("SELECT id, title, artist FROM songs")
        songs = cur.fetchall()
        
        print("Creating sample fingerprints for songs...")
        
        for song_id, title, artist in songs:
            print(f"Creating fingerprints for: {title} by {artist}")
            
            # Create 1000 sample fingerprints per song
            fingerprints = []
            for i in range(1000):
                hash_value = random.randint(1000000000, 9999999999)  # Random hash
                time_offset = i * 100  # Every 100ms
                fingerprints.append((song_id, hash_value, time_offset))
            
            # Insert fingerprints in batches
            cur.executemany("""
                INSERT INTO fingerprints (song_id, hash_value, time_offset_ms, created_at)
                VALUES (%s, %s, %s, NOW())
            """, fingerprints)
            
            print(f"  ✅ Created {len(fingerprints)} fingerprints")
        
        conn.commit()
        
        # Check total fingerprints
        cur.execute("SELECT COUNT(*) FROM fingerprints")
        total_fingerprints = cur.fetchone()[0]
        print(f"\n✅ Total fingerprints in database: {total_fingerprints}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Failed to create sample fingerprints: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_sample_fingerprints()