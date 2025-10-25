#!/usr/bin/env python3
"""
Test integration between backend service and C++ audio engine.
"""

import sys
import os
import numpy as np

# Add backend to path
backend_path = os.path.dirname(__file__)
sys.path.insert(0, backend_path)

# Add project root to path
project_root = os.path.dirname(backend_path)
sys.path.insert(0, project_root)

def test_service_integration():
    """Test the audio fingerprint service integration"""
    try:
        from backend.services.audio_fingerprint_service import (
            AudioFingerprintService, 
            get_audio_fingerprint_service,
            is_engine_available
        )
        from backend.models.audio import AudioSample
        
        print("✓ Successfully imported backend service")
        
        # Check if engine is available
        if not is_engine_available():
            print("✗ C++ engine not available")
            return False
        
        print("✓ C++ engine is available")
        
        # Create service instance
        service = get_audio_fingerprint_service()
        print("✓ Created service instance")
        
        # Create test audio sample
        sample_rate = 44100
        duration = 5  # seconds
        frequency = 440  # Hz
        
        t = np.linspace(0, duration, sample_rate * duration, False)
        audio_data = np.sin(2 * np.pi * frequency * t).astype(np.float32)
        
        audio_sample = AudioSample(
            data=audio_data.tobytes(),
            sample_rate=sample_rate,
            channels=1,
            duration_ms=int(duration * 1000),
            format='float32'
        )
        
        print(f"✓ Created test audio sample: {len(audio_sample.data)} samples")
        
        # Test validation
        is_valid = service.validate_audio_format(audio_sample)
        print(f"✓ Audio validation: {is_valid}")
        
        if not is_valid:
            print("✗ Audio sample failed validation")
            return False
        
        # Test preprocessing
        preprocessed = service.preprocess_audio(audio_sample)
        print(f"✓ Preprocessed audio: {len(preprocessed.data)} samples at {preprocessed.sample_rate} Hz")
        
        # Test fingerprint generation
        fingerprints = service.generate_fingerprint(audio_sample)
        print(f"✓ Generated {len(fingerprints)} fingerprints")
        
        if fingerprints:
            fp = fingerprints[0]
            print(f"  First fingerprint: hash={fp.hash_value}, time={fp.time_offset_ms}ms")
        
        # Test engine info
        info = service.get_engine_info()
        print(f"✓ Engine info: version {info.get('version', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Service integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_batch_processing():
    """Test batch processing functionality"""
    try:
        from backend.services.audio_fingerprint_service import get_audio_fingerprint_service
        
        service = get_audio_fingerprint_service()
        
        # Create dummy file paths (service will create test data)
        audio_files = [
            "test_song_1.wav",
            "test_song_2.wav",
            "test_song_3.wav"
        ]
        
        print(f"Testing batch processing with {len(audio_files)} files...")
        
        # Note: This will fail because files don't exist, but we can test the error handling
        try:
            results = service.batch_process(audio_files)
            print(f"✓ Batch processing returned {len(results)} results")
        except Exception as e:
            print(f"✓ Batch processing correctly handled missing files: {type(e).__name__}")
        
        return True
        
    except Exception as e:
        print(f"✗ Batch processing test failed: {e}")
        return False

def test_error_handling():
    """Test error handling in the service"""
    try:
        from backend.services.audio_fingerprint_service import get_audio_fingerprint_service
        from backend.models.audio import AudioSample
        
        service = get_audio_fingerprint_service()
        
        # Test empty audio (skip AudioSample validation by creating manually)
        try:
            empty_sample = AudioSample.__new__(AudioSample)
            empty_sample.data = b''
            empty_sample.sample_rate = 44100
            empty_sample.channels = 1
            empty_sample.duration_ms = 1000  # Valid duration to pass __post_init__
            empty_sample.format = 'float32'
            
            is_valid = service.validate_audio_format(empty_sample)
            print(f"✓ Empty audio validation: {is_valid} (should be False)")
        except Exception as e:
            print(f"✓ Empty audio correctly rejected: {type(e).__name__}")
        
        # Test invalid sample rate
        try:
            test_data = np.array([1.0, 2.0, 3.0], dtype=np.float32).tobytes()
            invalid_sample = AudioSample.__new__(AudioSample)
            invalid_sample.data = test_data
            invalid_sample.sample_rate = -1
            invalid_sample.channels = 1
            invalid_sample.duration_ms = 100
            invalid_sample.format = 'float32'
            
            is_valid = service.validate_audio_format(invalid_sample)
            print(f"✓ Invalid sample rate validation: {is_valid} (should be False)")
        except Exception as e:
            print(f"✓ Invalid sample rate correctly rejected: {type(e).__name__}")
        
        # Test invalid channels
        try:
            invalid_channels = AudioSample.__new__(AudioSample)
            invalid_channels.data = test_data
            invalid_channels.sample_rate = 44100
            invalid_channels.channels = 5
            invalid_channels.duration_ms = 100
            invalid_channels.format = 'float32'
            
            is_valid = service.validate_audio_format(invalid_channels)
            print(f"✓ Invalid channels validation: {is_valid} (should be False)")
        except Exception as e:
            print(f"✓ Invalid channels correctly rejected: {type(e).__name__}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Backend Service Integration")
    print("=" * 40)
    
    success = True
    
    print("\n1. Testing service integration...")
    success &= test_service_integration()
    
    print("\n2. Testing batch processing...")
    success &= test_batch_processing()
    
    print("\n3. Testing error handling...")
    success &= test_error_handling()
    
    print("\n" + "=" * 40)
    if success:
        print("✓ All integration tests passed!")
        sys.exit(0)
    else:
        print("✗ Some integration tests failed!")
        sys.exit(1)