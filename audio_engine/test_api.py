#!/usr/bin/env python3
"""
Test script for the high-level fingerprint API.
"""

import numpy as np
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_high_level_api():
    """Test the high-level fingerprint API"""
    try:
        from fingerprint_api import AudioFingerprintEngine, generate_fingerprint
        
        print("✓ Successfully imported high-level API")
        
        # Create engine instance
        engine = AudioFingerprintEngine()
        print("✓ Created engine instance")
        
        # Generate test audio
        sample_rate = 44100
        duration = 5  # seconds
        frequency = 440  # Hz
        
        t = np.linspace(0, duration, sample_rate * duration, False)
        audio_data = np.sin(2 * np.pi * frequency * t).astype(np.float32)
        
        print(f"✓ Generated test audio: {len(audio_data)} samples")
        
        # Test fingerprint generation
        result = engine.generate_fingerprint(audio_data, sample_rate, 1)
        print(f"✓ Generated fingerprint with {result.count} hashes")
        
        # Test convenience function
        result2 = generate_fingerprint(audio_data, sample_rate, 1)
        print(f"✓ Convenience function generated {result2.count} hashes")
        
        # Test preprocessing
        preprocessed_data, new_rate, new_channels = engine.preprocess_audio(audio_data, sample_rate, 1)
        print(f"✓ Preprocessed audio: {len(preprocessed_data)} samples at {new_rate} Hz")
        
        # Test batch processing
        audio_samples = [
            {'data': audio_data, 'sample_rate': sample_rate, 'channels': 1}
        ]
        song_ids = ['test_song']
        
        batch_results = engine.batch_process_reference_songs(audio_samples, song_ids)
        print(f"✓ Batch processed {len(batch_results)} songs")
        
        for batch_result in batch_results:
            if batch_result.success:
                print(f"  - {batch_result.song_id}: {batch_result.fingerprint_count} fingerprints")
            else:
                print(f"  - {batch_result.song_id}: FAILED - {batch_result.error_message}")
        
        # Test engine info
        info = engine.get_engine_info()
        print(f"✓ Engine info: version {info['version']}")
        
        return True
        
    except Exception as e:
        print(f"✗ High-level API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_handling():
    """Test error handling in the API"""
    try:
        from fingerprint_api import AudioFingerprintEngine
        
        engine = AudioFingerprintEngine()
        
        # Test empty audio
        try:
            engine.generate_fingerprint([], 44100, 1)
            print("✗ Should have failed with empty audio")
            return False
        except (ValueError, RuntimeError):
            print("✓ Correctly handled empty audio")
        
        # Test invalid sample rate
        try:
            engine.generate_fingerprint([1.0, 2.0, 3.0], -1, 1)
            print("✗ Should have failed with negative sample rate")
            return False
        except (ValueError, RuntimeError):
            print("✓ Correctly handled invalid sample rate")
        
        # Test invalid channels
        try:
            engine.generate_fingerprint([1.0, 2.0, 3.0], 44100, 5)
            print("✗ Should have failed with invalid channels")
            return False
        except (ValueError, RuntimeError):
            print("✓ Correctly handled invalid channels")
        
        return True
        
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing High-Level Fingerprint API")
    print("=" * 40)
    
    success = True
    
    print("\n1. Testing high-level API...")
    success &= test_high_level_api()
    
    print("\n2. Testing error handling...")
    success &= test_error_handling()
    
    print("\n" + "=" * 40)
    if success:
        print("✓ All API tests passed!")
        sys.exit(0)
    else:
        print("✗ Some API tests failed!")
        sys.exit(1)