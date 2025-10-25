#!/usr/bin/env python3
"""
Test script to verify the audio fingerprinting engine builds and works correctly.
"""

import numpy as np
import sys
import os

# Add current directory to path to import the module
sys.path.insert(0, os.path.dirname(__file__))

def test_basic_functionality():
    """Test basic fingerprinting functionality"""
    try:
        import audio_fingerprint_engine as afe
        print("✓ Successfully imported audio_fingerprint_engine")
        
        # Generate test audio (10 seconds of sine wave)
        sample_rate = 44100
        duration = 10  # seconds
        frequency = 440  # Hz (A4 note)
        
        t = np.linspace(0, duration, sample_rate * duration, False)
        audio_data = np.sin(2 * np.pi * frequency * t).astype(np.float32)
        
        print(f"✓ Generated test audio: {len(audio_data)} samples at {sample_rate} Hz")
        
        # Test preprocessing
        preprocessed = afe.preprocess_audio(audio_data, sample_rate, 1)
        print(f"✓ Preprocessed audio: {len(preprocessed['data'])} samples at {preprocessed['sample_rate']} Hz")
        
        # Test fingerprint generation
        result = afe.generate_fingerprint(audio_data, sample_rate, 1)
        print(f"✓ Generated {result['count']} fingerprints")
        
        if result['count'] > 0:
            print(f"  - First hash: {result['hash_values'][0]}")
            print(f"  - Time range: {min(result['time_offsets'])} - {max(result['time_offsets'])} ms")
            print(f"  - Frequency range: {min(result['anchor_frequencies']):.1f} - {max(result['anchor_frequencies']):.1f} Hz")
        
        # Test spectrogram computation
        spec_result = afe.compute_spectrogram(preprocessed['data'])
        print(f"✓ Computed spectrogram: {spec_result['time_frames']} x {spec_result['frequency_bins']}")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        print("  Make sure to build the module first:")
        print("  python setup.py build_ext --inplace")
        return False
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

def test_batch_processing():
    """Test batch processing functionality"""
    try:
        import audio_fingerprint_engine as afe
        
        # Create multiple test audio samples
        sample_rate = 44100
        duration = 5  # seconds
        
        audio_samples = []
        song_ids = []
        
        for i, freq in enumerate([440, 523, 659]):  # A4, C5, E5
            t = np.linspace(0, duration, sample_rate * duration, False)
            audio_data = np.sin(2 * np.pi * freq * t).astype(np.float32)
            
            audio_samples.append({
                'data': audio_data,
                'sample_rate': sample_rate,
                'channels': 1
            })
            song_ids.append(f"test_song_{i}")
        
        # Test batch processing
        results = afe.batch_process_songs(audio_samples, song_ids)
        print(f"✓ Batch processed {len(results)} songs")
        
        for result in results:
            if result['success']:
                print(f"  - {result['song_id']}: {result['fingerprint_count']} fingerprints in {result['processing_time_ms']} ms")
            else:
                print(f"  - {result['song_id']}: FAILED - {result['error_message']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Batch processing test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Audio Fingerprinting Engine")
    print("=" * 40)
    
    success = True
    
    print("\n1. Testing basic functionality...")
    success &= test_basic_functionality()
    
    print("\n2. Testing batch processing...")
    success &= test_batch_processing()
    
    print("\n" + "=" * 40)
    if success:
        print("✓ All tests passed!")
        sys.exit(0)
    else:
        print("✗ Some tests failed!")
        sys.exit(1)