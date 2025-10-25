#!/usr/bin/env python3
"""
Example usage of the audio fingerprinting engine Python bindings.

This script demonstrates how to use the audio fingerprinting engine
for generating fingerprints from audio data.
"""

import numpy as np
import sys
import os

# Add current directory to path for local imports
sys.path.insert(0, os.path.dirname(__file__))

def example_basic_fingerprinting():
    """Basic fingerprinting example"""
    print("=== Basic Fingerprinting Example ===")
    
    try:
        # Import the high-level API
        from fingerprint_api import generate_fingerprint, AudioFingerprintEngine
        
        # Create a test audio signal (5 seconds of a 440 Hz sine wave)
        sample_rate = 44100
        duration = 5.0
        frequency = 440.0  # A4 note
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio_data = np.sin(2 * np.pi * frequency * t).astype(np.float32)
        
        print(f"Generated test audio: {len(audio_data)} samples at {sample_rate} Hz")
        
        # Generate fingerprint
        result = generate_fingerprint(audio_data, sample_rate, channels=1)
        
        print(f"Generated {result.count} fingerprints")
        print(f"Time range: {min(result.time_offsets)} - {max(result.time_offsets)} ms")
        print(f"Frequency range: {min(result.anchor_frequencies):.1f} - {max(result.anchor_frequencies):.1f} Hz")
        
        # Show first few fingerprints
        print("\nFirst 5 fingerprints:")
        for i in range(min(5, result.count)):
            print(f"  Hash: {result.hash_values[i]:10d}, "
                  f"Time: {result.time_offsets[i]:4d} ms, "
                  f"Freq: {result.anchor_frequencies[i]:6.1f} -> {result.target_frequencies[i]:6.1f} Hz")
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True

def example_batch_processing():
    """Batch processing example for reference songs"""
    print("\n=== Batch Processing Example ===")
    
    try:
        from fingerprint_api import AudioFingerprintEngine
        
        engine = AudioFingerprintEngine()
        
        # Create multiple test songs with different frequencies
        sample_rate = 44100
        duration = 3.0
        frequencies = [440, 523, 659, 784]  # A4, C5, E5, G5
        note_names = ["A4", "C5", "E5", "G5"]
        
        audio_samples = []
        song_ids = []
        
        for i, (freq, note) in enumerate(zip(frequencies, note_names)):
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            # Add some harmonics to make it more interesting
            audio_data = (np.sin(2 * np.pi * freq * t) + 
                         0.3 * np.sin(2 * np.pi * freq * 2 * t) +
                         0.1 * np.sin(2 * np.pi * freq * 3 * t)).astype(np.float32)
            
            audio_samples.append({
                'data': audio_data,
                'sample_rate': sample_rate,
                'channels': 1
            })
            song_ids.append(f"song_{i:02d}_{note}")
        
        print(f"Processing {len(audio_samples)} reference songs...")
        
        # Batch process the songs
        results = engine.batch_process_reference_songs(audio_samples, song_ids)
        
        print(f"\nBatch processing results:")
        total_fingerprints = 0
        total_time = 0
        
        for result in results:
            if result.success:
                print(f"  ✓ {result.song_id}: {result.fingerprint_count} fingerprints "
                      f"({result.processing_time_ms} ms)")
                total_fingerprints += result.fingerprint_count
                total_time += result.processing_time_ms
            else:
                print(f"  ✗ {result.song_id}: FAILED - {result.error_message}")
        
        print(f"\nTotal: {total_fingerprints} fingerprints in {total_time} ms")
        print(f"Average: {total_fingerprints / len(results):.1f} fingerprints per song")
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True

def example_preprocessing():
    """Audio preprocessing example"""
    print("\n=== Audio Preprocessing Example ===")
    
    try:
        from fingerprint_api import AudioFingerprintEngine
        
        engine = AudioFingerprintEngine()
        
        # Create stereo audio at high sample rate
        original_rate = 48000
        duration = 2.0
        frequency = 1000.0
        
        t = np.linspace(0, duration, int(original_rate * duration), False)
        
        # Create stereo signal (left channel has fundamental, right has harmonic)
        left_channel = np.sin(2 * np.pi * frequency * t)
        right_channel = np.sin(2 * np.pi * frequency * 2 * t) * 0.5
        
        # Interleave stereo channels
        stereo_data = np.zeros(len(left_channel) * 2, dtype=np.float32)
        stereo_data[0::2] = left_channel  # Left channel
        stereo_data[1::2] = right_channel  # Right channel
        
        print(f"Original audio: {len(stereo_data)} samples at {original_rate} Hz (stereo)")
        
        # Preprocess the audio
        processed_data, new_rate, new_channels = engine.preprocess_audio(
            stereo_data, original_rate, 2
        )
        
        print(f"Preprocessed audio: {len(processed_data)} samples at {new_rate} Hz "
              f"({new_channels} channel)")
        
        # Show the effect of preprocessing
        print(f"Sample rate change: {original_rate} Hz -> {new_rate} Hz "
              f"({new_rate/original_rate:.3f}x)")
        print(f"Channel reduction: 2 -> {new_channels}")
        print(f"Length change: {len(stereo_data)} -> {len(processed_data)} samples "
              f"({len(processed_data)/len(stereo_data)*2:.3f}x)")
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True

def example_engine_info():
    """Display engine information"""
    print("\n=== Engine Information ===")
    
    try:
        from fingerprint_api import AudioFingerprintEngine
        
        engine = AudioFingerprintEngine()
        info = engine.get_engine_info()
        
        print("Audio Fingerprinting Engine Information:")
        for key, value in info.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True

def main():
    """Run all examples"""
    print("Audio Fingerprinting Engine - Usage Examples")
    print("=" * 50)
    
    success = True
    
    # Run all examples
    success &= example_basic_fingerprinting()
    success &= example_batch_processing()
    success &= example_preprocessing()
    success &= example_engine_info()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ All examples completed successfully!")
        return 0
    else:
        print("✗ Some examples failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())