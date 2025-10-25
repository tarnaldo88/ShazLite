"""
Audio Fingerprinting Engine

High-performance C++ audio fingerprinting engine with Python bindings
for music identification applications.
"""

from .audio_fingerprint_engine import (
    # Main functions
    generate_fingerprint,
    batch_process_songs,
    preprocess_audio,
    compute_spectrogram,
    
    # Classes
    AudioSample,
    AudioFingerprint,
    SpectralPeak,
    AudioPreprocessor,
    FFTProcessor,
    PeakDetector,
    HashGenerator,
    
    # Version
    __version__
)

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
    'HashGenerator',
    '__version__'
]