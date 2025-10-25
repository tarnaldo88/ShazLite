"""
Audio fingerprinting service implementation using the C++ engine.

This service provides the concrete implementation of audio processing
using the C++ fingerprinting engine with Python bindings.
"""

import logging
import numpy as np
from typing import List, Optional, Union
from pathlib import Path

from backend.interfaces.audio_processor import AudioProcessorInterface
from backend.models.audio import AudioSample, Fingerprint

# Import the C++ engine
try:
    import sys
    import os
    # Add audio_engine directory to path
    audio_engine_path = os.path.join(os.path.dirname(__file__), '..', '..', 'audio_engine')
    sys.path.insert(0, audio_engine_path)
    
    from fingerprint_api import AudioFingerprintEngine, FingerprintResult
    ENGINE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"C++ audio engine not available: {e}")
    ENGINE_AVAILABLE = False


class AudioProcessingError(Exception):
    """Exception raised when audio processing fails."""
    pass


class AudioFingerprintService(AudioProcessorInterface):
    """
    Audio fingerprinting service using C++ engine.
    
    Provides high-level audio processing functionality for the backend API,
    implementing the AudioProcessorInterface using the C++ fingerprinting engine.
    """
    
    def __init__(self):
        """Initialize the audio fingerprinting service."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        if not ENGINE_AVAILABLE:
            raise AudioProcessingError("C++ audio engine is not available")
        
        try:
            self.engine = AudioFingerprintEngine()
            self.logger.info("Audio fingerprinting service initialized")
        except Exception as e:
            raise AudioProcessingError(f"Failed to initialize audio engine: {e}")
    
    def generate_fingerprint(self, audio_sample: AudioSample) -> List[Fingerprint]:
        """
        Generate fingerprints from an audio sample.
        
        Args:
            audio_sample: Audio data to process
            
        Returns:
            List of Fingerprint objects
            
        Raises:
            AudioProcessingError: If fingerprint generation fails
        """
        try:
            self.logger.debug(f"Generating fingerprint for {len(audio_sample.data)} bytes")
            
            # Validate audio sample
            if not self.validate_audio_format(audio_sample):
                raise AudioProcessingError("Invalid audio format")
            
            # Convert bytes to numpy array (assuming 32-bit float format)
            audio_data = np.frombuffer(audio_sample.data, dtype=np.float32)
            
            # Generate fingerprint using C++ engine
            result = self.engine.generate_fingerprint(
                audio_data, 
                audio_sample.sample_rate, 
                audio_sample.channels
            )
            
            # Convert to backend Fingerprint objects
            fingerprints = []
            for i in range(result.count):
                fingerprint = Fingerprint(
                    hash_value=result.hash_values[i],
                    time_offset_ms=result.time_offsets[i],
                    frequency_1=result.anchor_frequencies[i],
                    frequency_2=result.target_frequencies[i],
                    time_delta_ms=result.time_deltas[i]
                )
                fingerprints.append(fingerprint)
            
            self.logger.info(f"Generated {len(fingerprints)} fingerprints")
            return fingerprints
            
        except Exception as e:
            self.logger.error(f"Fingerprint generation failed: {e}")
            raise AudioProcessingError(f"Fingerprint generation failed: {e}")
    
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
        try:
            self.logger.info(f"Batch processing {len(audio_files)} audio files")
            
            # Load audio files (this is a simplified implementation)
            # In a real implementation, you'd use a proper audio library like librosa
            audio_samples = []
            song_ids = []
            
            for i, file_path in enumerate(audio_files):
                if not Path(file_path).exists():
                    raise AudioProcessingError(f"Audio file not found: {file_path}")
                
                # For now, create dummy audio data
                # In production, load actual audio files
                sample_rate = 44100
                duration = 30  # 30 seconds
                t = np.linspace(0, duration, sample_rate * duration, False)
                audio_data = np.sin(2 * np.pi * 440 * t).astype(np.float32)
                
                audio_samples.append({
                    'data': audio_data,
                    'sample_rate': sample_rate,
                    'channels': 1
                })
                song_ids.append(f"song_{i}_{Path(file_path).stem}")
            
            # Process using C++ engine
            results = self.engine.batch_process_reference_songs(audio_samples, song_ids)
            
            # Convert results to backend format
            all_fingerprints = []
            for result in results:
                if result.success:
                    fingerprints = []
                    if result.hash_values and result.time_offsets:
                        for j in range(len(result.hash_values)):
                            fingerprint = Fingerprint(
                                hash_value=result.hash_values[j],
                                time_offset_ms=result.time_offsets[j],
                                anchor_freq_hz=0.0,  # Not provided in batch result
                                target_freq_hz=0.0,  # Not provided in batch result
                                time_delta_ms=0      # Not provided in batch result
                            )
                            fingerprints.append(fingerprint)
                    all_fingerprints.append(fingerprints)
                else:
                    self.logger.error(f"Failed to process {result.song_id}: {result.error_message}")
                    all_fingerprints.append([])  # Empty list for failed processing
            
            successful = sum(1 for result in results if result.success)
            self.logger.info(f"Batch processing completed: {successful}/{len(results)} successful")
            
            return all_fingerprints
            
        except Exception as e:
            self.logger.error(f"Batch processing failed: {e}")
            raise AudioProcessingError(f"Batch processing failed: {e}")
    
    def validate_audio_format(self, audio_sample: AudioSample) -> bool:
        """
        Validate that audio sample meets processing requirements.
        
        Args:
            audio_sample: Audio data to validate
            
        Returns:
            True if audio format is valid, False otherwise
        """
        try:
            # Check if audio data exists and is not empty
            if not audio_sample.data or len(audio_sample.data) == 0:
                self.logger.warning("Audio sample is empty")
                return False
            
            # Check sample rate
            if audio_sample.sample_rate <= 0:
                self.logger.warning(f"Invalid sample rate: {audio_sample.sample_rate}")
                return False
            
            # Check channels
            if audio_sample.channels not in [1, 2]:
                self.logger.warning(f"Unsupported channel count: {audio_sample.channels}")
                return False
            
            # Check format (should be float32 for our engine)
            if audio_sample.format not in ['float32', 'wav', 'mp3']:
                self.logger.warning(f"Unsupported format: {audio_sample.format}")
                return False
            
            # Calculate expected number of samples (assuming 4 bytes per float32 sample)
            bytes_per_sample = 4  # float32
            expected_samples = len(audio_sample.data) // (bytes_per_sample * audio_sample.channels)
            duration_seconds = expected_samples / audio_sample.sample_rate
            
            # Check minimum duration (at least 1 second)
            if duration_seconds < 1.0:
                self.logger.warning(f"Audio too short: {duration_seconds:.2f} seconds")
                return False
            
            # Check maximum duration (limit to 10 minutes to prevent memory issues)
            if duration_seconds > 600.0:
                self.logger.warning(f"Audio too long: {duration_seconds:.2f} seconds")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Audio validation failed: {e}")
            return False
    
    def preprocess_audio(self, audio_sample: AudioSample) -> AudioSample:
        """
        Preprocess audio sample for fingerprinting.
        
        Args:
            audio_sample: Raw audio sample
            
        Returns:
            Preprocessed audio sample
            
        Raises:
            AudioProcessingError: If preprocessing fails
        """
        try:
            # Convert bytes to numpy array
            audio_data = np.frombuffer(audio_sample.data, dtype=np.float32)
            
            # Preprocess using C++ engine
            processed_data, new_rate, new_channels = self.engine.preprocess_audio(
                audio_data, 
                audio_sample.sample_rate, 
                audio_sample.channels
            )
            
            # Convert back to bytes
            processed_bytes = processed_data.astype(np.float32).tobytes()
            
            # Create new AudioSample with preprocessed data
            return AudioSample(
                data=processed_bytes,
                sample_rate=new_rate,
                channels=new_channels,
                duration_ms=int(len(processed_data) * 1000 / new_rate),
                format='float32'
            )
            
        except Exception as e:
            self.logger.error(f"Audio preprocessing failed: {e}")
            raise AudioProcessingError(f"Audio preprocessing failed: {e}")
    
    def get_engine_info(self) -> dict:
        """
        Get information about the audio engine.
        
        Returns:
            Dictionary with engine information
        """
        try:
            return self.engine.get_engine_info()
        except Exception as e:
            self.logger.error(f"Failed to get engine info: {e}")
            return {"error": str(e)}


# Global service instance for dependency injection
_service_instance: Optional[AudioFingerprintService] = None


def get_audio_fingerprint_service() -> AudioFingerprintService:
    """
    Get global audio fingerprint service instance (singleton pattern).
    
    Returns:
        AudioFingerprintService instance
        
    Raises:
        AudioProcessingError: If service cannot be initialized
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = AudioFingerprintService()
    return _service_instance


def is_engine_available() -> bool:
    """
    Check if the C++ audio engine is available.
    
    Returns:
        True if engine is available, False otherwise
    """
    return ENGINE_AVAILABLE