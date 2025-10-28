#!/usr/bin/env python3
"""Test the matching system with known audio."""

import numpy as np
from audio_engine.fingerprint_api import get_engine
from backend.database.connection import get_db_session
from backend.database.repositories import MatchRepository
from backend.models.audio import Fingerprint

def create_test_audio():
    """Create the same test audio we used for fingerprints."""
    sample_rate = 44100
    duration = 5  # 5 seconds for testing
    frequency = 440  # A4 note
    
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = np.sin(2 * np.pi * frequency * t).astype(np.float32)
    
    return audio_data, sample_rate

def test_matching():
    """Test if we can match the same audio."""
    try:
        print("Creating test audio...")
        audio_data, sample_rate = create_test_audio()
        
        print("Generating fingerprints from test audio...")
        engine = get_engine()
        fingerprint_result = engine.generate_fingerprint(audio_data, sample_rate, 1)
        
        # Convert to Fingerprint objects
        query_fingerprints = []
        max_fingerprints = min(fingerprint_result.count, 1000)  # Limit for testing
        
        for i in range(max_fingerprints):
            fingerprint = Fingerprint(
                hash_value=int(fingerprint_result.hash_values[i]),
                time_offset_ms=int(fingerprint_result.time_offsets[i])
            )
            query_fingerprints.append(fingerprint)
        
        print(f"Generated {len(query_fingerprints)} query fingerprints")
        
        # Test matching
        print("Testing database matching...")
        with get_db_session() as session:
            match_repo = MatchRepository(session)
            match_result = match_repo.find_best_match(query_fingerprints, min_matches=3)
            
            if match_result:
                print(f"✅ MATCH FOUND!")
                print(f"  Song: {match_result.title} by {match_result.artist}")
                print(f"  Confidence: {match_result.confidence:.2%}")
                print(f"  Match count: {match_result.match_count}")
            else:
                print("❌ No match found")
                
                # Debug: Check if we have any matching hashes
                from backend.database.repositories import FingerprintRepository
                fp_repo = FingerprintRepository(session)
                matches = fp_repo.find_matching_fingerprints(query_fingerprints[:100])  # Test first 100
                print(f"Debug: Found {len(matches)} raw hash matches from first 100 fingerprints")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_matching()