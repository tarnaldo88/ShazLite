"""
Audio processing interface definitions for the fingerprinting system.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from backend.models.audio import AudioSample, Fingerprint


class AudioProcessorInterface(ABC):
    """Interface for audio fingerprinting operations."""
    
    @abstractmethod
    def generate_fingerprint(self, audio_sample: AudioSample) -> List[Fingerprint]:
        """
        Generate fingerprints from an audio sample.
        
        Args:
            audio_sample: Audio data to process
            
        Returns:
            List of fingerprint objects with hash values and time offsets
            
        Raises:
            AudioProcessingError: If fingerprint generation fails
        """
        pass
    
    @abstractmethod
    def batch_process(self, audio_files: List[str]) -> List[List[Fingerprint]]:
        """
        Process multiple audio files for database population.
        
        Args:
            audio_files: List of file paths to process
            
        Returns:
            List of fingerprint lists, one per input file
            
        Raises:
            AudioProcessingError: If batch processing fails
        """
        pass
    
    @abstractmethod
    def validate_audio_format(self, audio_sample: AudioSample) -> bool:
        """
        Validate that audio sample meets processing requirements.
        
        Args:
            audio_sample: Audio data to validate
            
        Returns:
            True if audio format is valid, False otherwise
        """
        pass


class AudioEngineInterface(ABC):
    """Low-level interface for C++ audio engine operations."""
    
    @abstractmethod
    def compute_stft(self, audio_data: bytes, sample_rate: int) -> List[List[float]]:
        """
        Compute Short-Time Fourier Transform of audio data.
        
        Args:
            audio_data: Raw audio bytes
            sample_rate: Audio sample rate in Hz
            
        Returns:
            2D array of spectral data [time][frequency]
        """
        pass
    
    @abstractmethod
    def detect_peaks(self, spectrogram: List[List[float]]) -> List[tuple]:
        """
        Detect spectral peaks from STFT data.
        
        Args:
            spectrogram: 2D spectral data
            
        Returns:
            List of (time_bin, frequency_bin, magnitude) tuples
        """
        pass
    
    @abstractmethod
    def generate_hashes(self, peaks: List[tuple]) -> List[Fingerprint]:
        """
        Generate hash values from spectral peaks.
        
        Args:
            peaks: List of detected peaks
            
        Returns:
            List of fingerprint objects with hash values
        """
        pass