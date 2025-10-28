#!/usr/bin/env python3
"""Debug the fingerprint matching to see why songs are misidentified."""

import os
import numpy as np
import librosa
from audio_engine.fingerprint_api import get_engine
from backend.database.connection import initialize_database, DatabaseConfig, get_db_session
from backend.database.repositories import MatchRepository, FingerprintRepository
from backend.models.audio import Fingerprint
from backend.api.config import get_settings

SONGS_DIR = r"C:\Users\tarna\Documents\SongForShazlite"

def load_and_fingerprint_song(file_path, duration_limit=30):
    """Load a song and generate fingerprints from it."""
    try:
        print(f"Loading: {os.path.basename(file_path)}")
        
        # Load only first 30 seconds for testing with consistent sample rate
        target_sr = 44100  # Same as used in database generation
        audio_data, sample_rate = librosa.load(file_path, sr=target_sr, mono=True, duration=duration_limit)
        audio_data = audio_data.astype(np.float32)
        
        print(f"  Sample rate: {sample_rate} Hz")
        print(f"  Duration: {len(audio_data) / sample_rate:.1f} seconds")
        
        # Generate fingerprints
        engine = get_engine()
        fingerprint_result = engine.generate_fingerprint(audio_data, sample_rate, 1)
        
        # Convert to Fingerprint objects (limit to 2000 for testing)
        fingerprints = []
        max_fingerprints = min(fingerprint_result.count, 2000)
        
        for i in range(max_fingerprints):
            fingerprint = Fingerprint(
                hash_value=int(fingerprint_result.hash_values[i]),
                time_offset_ms=int(fingerprint_result.time_offsets[i])
            )
            fingerprints.append(fingerprint)
        
        print(f"  Generated {len(fingerprints)} fingerprints")
        return fingerprints
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return []

def test_song_matching(song_file):
    """Test matching for a specific song."""
    try:
        # Initialize database
        settings = get_settings()
        db_config = DatabaseConfig(settings)
        initialize_database(db_config)
        
        file_path = os.path.join(SONGS_DIR, song_file)
        
        print(f"\n{'='*60}")
        print(f"TESTING: {song_file}")
        print(f"{'='*60}")
        
        # Generate fingerprints from the song
        query_fingerprints = load_and_fingerprint_song(file_path)
        
        if not query_fingerprints:
            print("❌ No fingerprints generated")
            return
        
        # Test matching
        with get_db_session() as session:
            match_repo = MatchRepository(session)
            fp_repo = FingerprintRepository(session)
            
            # Get raw matches first
            print(f"\nTesting raw fingerprint matches...")
            raw_matches = fp_repo.find_matching_fingerprints(query_fingerprints[:500])  # Test first 500
            print(f"Found {len(raw_matches)} raw hash matches")
            
            # Group by song
            song_match_counts = {}
            for song_id, query_time, db_time in raw_matches:
                if song_id not in song_match_counts:
                    song_match_counts[song_id] = 0
                song_match_counts[song_id] += 1
            
            print("Raw matches by song:")
            for song_id, count in sorted(song_match_counts.items(), key=lambda x: x[1], reverse=True):
                # Get song name
                song_repo = match_repo.song_repo
                song = song_repo.get_song_by_id(song_id)
                if song:
                    print(f"  Song {song_id} ({song.title} by {song.artist}): {count} matches")
            
            # Test full matching algorithm
            print(f"\nTesting full matching algorithm...")
            match_result = match_repo.find_best_match(query_fingerprints, min_matches=3)
            
            if match_result:
                print(f"✅ MATCH FOUND:")
                print(f"  Song: {match_result.title} by {match_result.artist}")
                print(f"  Confidence: {match_result.confidence:.2%}")
                print(f"  Match count: {match_result.match_count}")
                print(f"  Time offset: {match_result.time_offset_ms}ms")
            else:
                print("❌ No match found by algorithm")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Test matching for all songs."""
    songs_to_test = [
        "SOFI-TUKKER-Swing.mp3",
        "50 Cent - Many Men (1960's Motown Soul Almost Real AI Cover).mp3",
        "Malaa - Notorious.mp3"
    ]
    
    for song in songs_to_test:
        test_song_matching(song)
        print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()