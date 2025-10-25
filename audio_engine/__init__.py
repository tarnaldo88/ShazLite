"""
Audio Fingerprinting Engine

A high-performance C++ audio fingerprinting library with Python bindings
for music identification applications similar to Shazam.

Main Functions:
- generate_fingerprint: Generate fingerprints from audio data
- batch_process_songs: Process multiple reference songs for database
- preprocess_audio: Preprocess audio for fingerprinting
- compute_spectrogram: Compute spectrogram from audio data

Example Usage:
    import numpy as np
    import audio_fingerprint_engine as afe
    
    # Generate fingerprint from audio
    audio_data = np.random.randn(44100 * 10).astype(np.float32)  # 10 seconds
    result = afe.generate_fingerprint(audio_data, sample_rate=44100, channels=1)
    
    print(f"Generated {result['count']} fingerprints")
    print(f"Hash values: {result['hash_values'][:5]}...")  # First 5 hashes
"""

try:
    from .audio_fingerprint_engine import *
    __all__ = [
        'generate_fingerprint',
        'batch_process_songs', 
        'preprocess_audio',
        'compute_spectrogram',
        'AudioSample',
        'AudioFingerprint',
        'SpectralPeak',
        'AudioPreprocessor',
        'FFTProcessor',
        'PeakDetector',
        'HashGenerator'
    ]
except ImportError as e:
    import warnings
    warnings.warn(f"Could not import C++ audio fingerprinting engine: {e}")
    warnings.warn("Make sure the module is compiled. Run: python setup.py build_ext --inplace")
    
    # Provide stub functions for development
    def generate_fingerprint(*args, **kwargs):
        raise RuntimeError("Audio fingerprinting engine not compiled")
    
    def batch_process_songs(*args, **kwargs):
        raise RuntimeError("Audio fingerprinting engine not compiled")
    
    def preprocess_audio(*args, **kwargs):
        raise RuntimeError("Audio fingerprinting engine not compiled")
    
    def compute_spectrogram(*args, **kwargs):
        raise RuntimeError("Audio fingerprinting engine not compiled")

__version__ = "0.1.0"