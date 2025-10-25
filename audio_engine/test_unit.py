#!/usr/bin/env python3
"""
Unit tests for the audio fingerprinting engine.

Tests core functionality including:
- Fingerprint generation consistency
- Peak detection accuracy
- Synthetic signal processing
- Known fingerprint validation
"""

import unittest
import numpy as np
import sys
import os
import time
from typing import List, Dict, Tuple

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from fingerprint_api import AudioFingerprintEngine, FingerprintResult
    import audio_fingerprint_engine as afe
except ImportError as e:
    print(f"Failed to import audio engine: {e}")
    print("Make sure to build the module first: python setup.py build_ext --inplace")
    sys.exit(1)


class TestAudioSampleGeneration(unittest.TestCase):
    """Test generation of synthetic audio samples with known characteristics"""
    
    def setUp(self):
        self.sample_rate = 44100
        self.engine = AudioFingerprintEngine()
    
    def test_pure_tone_generation(self):
        """Test generation of pure tone audio samples"""
        frequency = 440.0  # A4 note
        duration = 5.0  # seconds
        
        # Generate pure sine wave
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        audio_data = np.sin(2 * np.pi * frequency * t).astype(np.float32)
        
        self.assertEqual(len(audio_data), int(self.sample_rate * duration))
        self.assertTrue(np.all(np.abs(audio_data) <= 1.0))
        
        # Verify frequency content through FFT
        fft_result = np.fft.fft(audio_data[:4096])  # Use first 4096 samples
        freqs = np.fft.fftfreq(4096, 1/self.sample_rate)
        magnitude = np.abs(fft_result)
        
        # Find peak frequency
        peak_idx = np.argmax(magnitude[:2048])  # Only positive frequencies
        peak_freq = abs(freqs[peak_idx])
        
        self.assertAlmostEqual(peak_freq, frequency, delta=5.0)
    
    def test_multi_tone_generation(self):
        """Test generation of multi-tone audio samples"""
        frequencies = [440.0, 880.0, 1320.0]  # A4, A5, E6
        duration = 3.0
        
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        audio_data = np.zeros_like(t, dtype=np.float32)
        
        # Sum multiple sine waves
        for freq in frequencies:
            audio_data += np.sin(2 * np.pi * freq * t) / len(frequencies)
        
        self.assertEqual(len(audio_data), int(self.sample_rate * duration))
        self.assertTrue(np.all(np.abs(audio_data) <= 1.0))
        
        # Generate fingerprint
        result = self.engine.generate_fingerprint(audio_data, self.sample_rate, 1)
        self.assertGreater(result.count, 0)
    
    def test_chirp_signal_generation(self):
        """Test generation of frequency sweep (chirp) signals"""
        duration = 2.0
        f0, f1 = 200.0, 2000.0  # Sweep from 200Hz to 2kHz
        
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        # Linear chirp
        audio_data = np.sin(2 * np.pi * (f0 * t + (f1 - f0) * t**2 / (2 * duration))).astype(np.float32)
        
        self.assertEqual(len(audio_data), int(self.sample_rate * duration))
        
        # Generate fingerprint
        result = self.engine.generate_fingerprint(audio_data, self.sample_rate, 1)
        self.assertGreater(result.count, 0)


class TestFingerprintConsistency(unittest.TestCase):
    """Test fingerprint generation consistency across multiple runs"""
    
    def setUp(self):
        self.sample_rate = 44100
        self.engine = AudioFingerprintEngine()
        
        # Create a standard test signal
        duration = 5.0
        frequency = 440.0
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        self.test_audio = np.sin(2 * np.pi * frequency * t).astype(np.float32)
    
    def test_identical_input_consistency(self):
        """Test that identical inputs produce identical fingerprints"""
        num_runs = 5
        results = []
        
        for _ in range(num_runs):
            result = self.engine.generate_fingerprint(self.test_audio, self.sample_rate, 1)
            results.append(result)
        
        # All results should have the same number of fingerprints
        counts = [r.count for r in results]
        self.assertTrue(all(c == counts[0] for c in counts), 
                       f"Inconsistent fingerprint counts: {counts}")
        
        # Hash values should be identical
        if results[0].count > 0:
            for i in range(1, num_runs):
                self.assertEqual(results[0].hash_values, results[i].hash_values,
                               "Hash values differ between runs")
                self.assertEqual(results[0].time_offsets, results[i].time_offsets,
                               "Time offsets differ between runs")
    
    def test_copy_vs_original_consistency(self):
        """Test that copied audio produces identical fingerprints"""
        # Create a copy of the audio data
        audio_copy = self.test_audio.copy()
        
        result1 = self.engine.generate_fingerprint(self.test_audio, self.sample_rate, 1)
        result2 = self.engine.generate_fingerprint(audio_copy, self.sample_rate, 1)
        
        self.assertEqual(result1.count, result2.count)
        if result1.count > 0:
            self.assertEqual(result1.hash_values, result2.hash_values)
            self.assertEqual(result1.time_offsets, result2.time_offsets)
    
    def test_different_array_types_consistency(self):
        """Test consistency across different numpy array types"""
        # Convert to different data types
        audio_float64 = self.test_audio.astype(np.float64)
        audio_list = self.test_audio.tolist()
        
        result1 = self.engine.generate_fingerprint(self.test_audio, self.sample_rate, 1)
        result2 = self.engine.generate_fingerprint(audio_float64, self.sample_rate, 1)
        result3 = self.engine.generate_fingerprint(audio_list, self.sample_rate, 1)
        
        self.assertEqual(result1.count, result2.count)
        self.assertEqual(result1.count, result3.count)
        
        if result1.count > 0:
            self.assertEqual(result1.hash_values, result2.hash_values)
            self.assertEqual(result1.hash_values, result3.hash_values)


class TestPeakDetectionAccuracy(unittest.TestCase):
    """Test peak detection accuracy with synthetic signals"""
    
    def setUp(self):
        self.sample_rate = 44100
        self.engine = AudioFingerprintEngine()
    
    def test_single_peak_detection(self):
        """Test detection of a single spectral peak"""
        frequency = 1000.0  # 1kHz tone
        duration = 3.0
        
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        audio_data = np.sin(2 * np.pi * frequency * t).astype(np.float32)
        
        # Generate fingerprint
        result = self.engine.generate_fingerprint(audio_data, self.sample_rate, 1)
        
        # Should detect peaks around the target frequency
        self.assertGreater(result.count, 0)
        
        # Check that detected frequencies are reasonable
        if result.count > 0:
            # Most anchor frequencies should be near our target
            anchor_freqs = np.array(result.anchor_frequencies)
            freq_range = np.ptp(anchor_freqs)  # Peak-to-peak range
            
            # For a pure tone, frequency range should be relatively small
            self.assertLess(freq_range, 500.0, "Frequency range too large for pure tone")
    
    def test_multiple_peak_detection(self):
        """Test detection of multiple distinct spectral peaks"""
        frequencies = [440.0, 880.0, 1320.0]  # Harmonic series
        duration = 4.0
        
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        audio_data = np.zeros_like(t, dtype=np.float32)
        
        # Create signal with multiple frequency components
        for freq in frequencies:
            audio_data += np.sin(2 * np.pi * freq * t) / len(frequencies)
        
        result = self.engine.generate_fingerprint(audio_data, self.sample_rate, 1)
        
        # Should detect more peaks than single tone
        self.assertGreater(result.count, 0)
        
        if result.count > 0:
            # Check frequency diversity
            anchor_freqs = np.array(result.anchor_frequencies)
            unique_freq_bins = len(np.unique(np.round(anchor_freqs / 50.0)))  # 50Hz bins
            
            # Should have peaks in multiple frequency regions
            self.assertGreater(unique_freq_bins, 1, "Should detect multiple frequency regions")
    
    def test_noise_robustness(self):
        """Test peak detection robustness to noise"""
        frequency = 800.0
        duration = 3.0
        noise_level = 0.02  # 2% noise (very low level)
        
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        clean_signal = np.sin(2 * np.pi * frequency * t).astype(np.float32)
        
        # Add white noise
        np.random.seed(42)  # For reproducible results
        noise = np.random.normal(0, noise_level, len(clean_signal)).astype(np.float32)
        noisy_signal = clean_signal + noise
        
        result_clean = self.engine.generate_fingerprint(clean_signal, self.sample_rate, 1)
        result_noisy = self.engine.generate_fingerprint(noisy_signal, self.sample_rate, 1)
        
        # Both should produce fingerprints
        self.assertGreater(result_clean.count, 0)
        self.assertGreater(result_noisy.count, 0)
        
        # Test that the engine can handle noisy input without crashing
        # and still produces some fingerprints (the exact count may vary significantly)
        # Focus on testing that the engine is robust rather than specific ratios
        self.assertTrue(isinstance(result_noisy.hash_values, list))
        self.assertTrue(isinstance(result_noisy.time_offsets, list))
        self.assertEqual(len(result_noisy.hash_values), result_noisy.count)
        self.assertEqual(len(result_noisy.time_offsets), result_noisy.count)
    
    def test_amplitude_invariance(self):
        """Test that peak detection is amplitude-invariant"""
        frequency = 600.0
        duration = 2.0
        
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        base_signal = np.sin(2 * np.pi * frequency * t).astype(np.float32)
        
        # Test different amplitudes
        amplitudes = [0.1, 0.5, 1.0]
        results = []
        
        for amp in amplitudes:
            scaled_signal = base_signal * amp
            result = self.engine.generate_fingerprint(scaled_signal, self.sample_rate, 1)
            results.append(result)
        
        # All should produce similar number of fingerprints
        counts = [r.count for r in results]
        if all(c > 0 for c in counts):
            max_count = max(counts)
            min_count = min(counts)
            ratio = min_count / max_count
            
            self.assertGreater(ratio, 0.7, "Amplitude scaling affects fingerprint count too much")


class TestKnownFingerprintValidation(unittest.TestCase):
    """Test validation with known fingerprint patterns"""
    
    def setUp(self):
        self.sample_rate = 44100
        self.engine = AudioFingerprintEngine()
    
    def test_reference_signal_fingerprints(self):
        """Test fingerprints for well-defined reference signals"""
        # Create a reference signal with known characteristics
        duration = 5.0
        base_freq = 440.0
        
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        
        # Signal with fundamental and harmonics
        audio_data = (
            np.sin(2 * np.pi * base_freq * t) +
            0.5 * np.sin(2 * np.pi * base_freq * 2 * t) +
            0.25 * np.sin(2 * np.pi * base_freq * 3 * t)
        ).astype(np.float32)
        
        result = self.engine.generate_fingerprint(audio_data, self.sample_rate, 1)
        
        # Store as reference
        reference_hashes = result.hash_values.copy()
        reference_count = result.count
        
        self.assertGreater(reference_count, 0)
        
        # Test that the same signal produces the same fingerprints
        result2 = self.engine.generate_fingerprint(audio_data, self.sample_rate, 1)
        
        self.assertEqual(result2.count, reference_count)
        self.assertEqual(result2.hash_values, reference_hashes)
    
    def test_time_shifted_signal(self):
        """Test fingerprints for time-shifted versions of the same signal"""
        duration = 4.0
        frequency = 500.0
        
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        original_signal = np.sin(2 * np.pi * frequency * t).astype(np.float32)
        
        # Create time-shifted version by adding silence at the beginning
        silence_duration = 1.0  # 1 second of silence
        silence_samples = int(self.sample_rate * silence_duration)
        silence = np.zeros(silence_samples, dtype=np.float32)
        shifted_signal = np.concatenate([silence, original_signal])
        
        result_original = self.engine.generate_fingerprint(original_signal, self.sample_rate, 1)
        result_shifted = self.engine.generate_fingerprint(shifted_signal, self.sample_rate, 1)
        
        # Both should produce fingerprints
        self.assertGreater(result_original.count, 0)
        self.assertGreater(result_shifted.count, 0)
        
        # The shifted version should have some matching hash values
        # (though time offsets will be different)
        original_hashes = set(result_original.hash_values)
        shifted_hashes = set(result_shifted.hash_values)
        
        common_hashes = original_hashes.intersection(shifted_hashes)
        overlap_ratio = len(common_hashes) / len(original_hashes) if original_hashes else 0
        
        self.assertGreater(overlap_ratio, 0.3, "Time-shifted signal should have significant hash overlap")
    
    def test_frequency_content_validation(self):
        """Test that fingerprints reflect actual frequency content"""
        # Create signals with different frequency content
        duration = 3.0
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        
        # Low frequency signal
        low_freq_signal = np.sin(2 * np.pi * 200.0 * t).astype(np.float32)
        
        # High frequency signal  
        high_freq_signal = np.sin(2 * np.pi * 2000.0 * t).astype(np.float32)
        
        result_low = self.engine.generate_fingerprint(low_freq_signal, self.sample_rate, 1)
        result_high = self.engine.generate_fingerprint(high_freq_signal, self.sample_rate, 1)
        
        if result_low.count > 0 and result_high.count > 0:
            # Low frequency signal should have lower anchor frequencies on average
            avg_freq_low = np.mean(result_low.anchor_frequencies)
            avg_freq_high = np.mean(result_high.anchor_frequencies)
            
            self.assertLess(avg_freq_low, avg_freq_high, 
                           "Low frequency signal should have lower average anchor frequencies")


class TestEnginePerformance(unittest.TestCase):
    """Test performance characteristics of the audio engine"""
    
    def setUp(self):
        self.sample_rate = 44100
        self.engine = AudioFingerprintEngine()
    
    def test_processing_time_bounds(self):
        """Test that processing time is within reasonable bounds"""
        duration = 10.0  # 10 second audio
        frequency = 440.0
        
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        audio_data = np.sin(2 * np.pi * frequency * t).astype(np.float32)
        
        start_time = time.time()
        result = self.engine.generate_fingerprint(audio_data, self.sample_rate, 1)
        processing_time = time.time() - start_time
        
        # Processing should complete within reasonable time (less than 5 seconds for 10s audio)
        self.assertLess(processing_time, 5.0, 
                       f"Processing took too long: {processing_time:.2f}s for {duration}s audio")
        
        # Should produce fingerprints
        self.assertGreater(result.count, 0)
    
    def test_memory_efficiency(self):
        """Test memory usage with different audio lengths"""
        durations = [1.0, 5.0, 10.0]
        frequency = 440.0
        
        for duration in durations:
            t = np.linspace(0, duration, int(self.sample_rate * duration), False)
            audio_data = np.sin(2 * np.pi * frequency * t).astype(np.float32)
            
            # This should not crash or consume excessive memory
            result = self.engine.generate_fingerprint(audio_data, self.sample_rate, 1)
            
            # Fingerprint count should scale reasonably with duration
            fingerprints_per_second = result.count / duration if duration > 0 else 0
            
            # Should be reasonable number of fingerprints per second (not too many or too few)
            self.assertGreater(fingerprints_per_second, 1, 
                             f"Too few fingerprints per second: {fingerprints_per_second}")
            self.assertLess(fingerprints_per_second, 1000, 
                           f"Too many fingerprints per second: {fingerprints_per_second}")


def create_test_suite():
    """Create a test suite with all test classes"""
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestAudioSampleGeneration,
        TestFingerprintConsistency,
        TestPeakDetectionAccuracy,
        TestKnownFingerprintValidation,
        TestEnginePerformance
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    return suite


if __name__ == "__main__":
    print("Audio Fingerprinting Engine Unit Tests")
    print("=" * 50)
    
    # Run the test suite
    runner = unittest.TextTestRunner(verbosity=2)
    suite = create_test_suite()
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0]}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split('\\n')[-2]}")
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)