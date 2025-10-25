"""
High-level Python API for audio fingerprinting engine.

This module provides a clean, error-handled interface to the C++ audio
fingerprinting engine for use by the backend API.
"""

import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass

try:
    from . import audio_fingerprint_engine as afe
except ImportError:
    # Fallback for development/testing
    import audio_fingerprint_engine as afe

logger = logging.getLogger(__name__)


@dataclass
class FingerprintResult:
    """Result of fingerprint generation"""
    hash_values: List[int]
    time_offsets: List[int]
    anchor_frequencies: List[float]
    target_frequencies: List[float]
    time_deltas: List[int]
    count: int
    processing_time_ms: Optional[int] = None


@dataclass
class BatchProcessingResult:
    """Result of batch processing a reference song"""
    song_id: str
    success: bool
    fingerprint_count: int
    processing_time_ms: int
    total_duration_ms: int
    error_message: Optional[str] = None
    hash_values: Optional[List[int]] = None
    time_offsets: Optional[List[int]] = None


class AudioFingerprintEngine:
    """
    High-level interface to the C++ audio fingerprinting engine.
    
    Provides error handling, logging, and a clean API for the backend.
    """
    
    def __init__(self):
        """Initialize the fingerprinting engine"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("Audio fingerprinting engine initialized")
    
    def generate_fingerprint(
        self, 
        audio_data: Union[np.ndarray, List[float]], 
        sample_rate: int, 
        channels: int = 1
    ) -> FingerprintResult:
        """
        Generate audio fingerprint from audio data.
        
        Args:
            audio_data: Audio samples as numpy array or list
            sample_rate: Sample rate in Hz
            channels: Number of audio channels (1 or 2)
            
        Returns:
            FingerprintResult containing hash values and metadata
            
        Raises:
            ValueError: If audio data is invalid
            RuntimeError: If fingerprinting fails
        """
        try:
            # Convert to numpy array if needed
            if not isinstance(audio_data, np.ndarray):
                audio_data = np.array(audio_data, dtype=np.float32)
            elif audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Validate inputs
            if len(audio_data) == 0:
                raise ValueError("Audio data is empty")
            
            if sample_rate <= 0:
                raise ValueError("Sample rate must be positive")
            
            if channels not in [1, 2]:
                raise ValueError("Only mono (1) and stereo (2) audio supported")
            
            self.logger.debug(
                f"Generating fingerprint for {len(audio_data)} samples "
                f"at {sample_rate} Hz, {channels} channel(s)"
            )
            
            # Generate fingerprint using C++ engine
            result = afe.generate_fingerprint(audio_data, sample_rate, channels)
            
            fingerprint_result = FingerprintResult(
                hash_values=result['hash_values'],
                time_offsets=result['time_offsets'],
                anchor_frequencies=result['anchor_frequencies'],
                target_frequencies=result['target_frequencies'],
                time_deltas=result['time_deltas'],
                count=result['count']
            )
            
            self.logger.info(f"Generated {fingerprint_result.count} fingerprints")
            return fingerprint_result
            
        except Exception as e:
            self.logger.error(f"Fingerprint generation failed: {e}")
            raise RuntimeError(f"Fingerprint generation failed: {e}") from e
    
    def preprocess_audio(
        self, 
        audio_data: Union[np.ndarray, List[float]], 
        sample_rate: int, 
        channels: int
    ) -> Tuple[np.ndarray, int, int]:
        """
        Preprocess audio for fingerprinting.
        
        Args:
            audio_data: Raw audio samples
            sample_rate: Original sample rate
            channels: Number of channels
            
        Returns:
            Tuple of (preprocessed_data, new_sample_rate, new_channels)
            
        Raises:
            ValueError: If audio data is invalid
            RuntimeError: If preprocessing fails
        """
        try:
            # Convert to numpy array if needed
            if not isinstance(audio_data, np.ndarray):
                audio_data = np.array(audio_data, dtype=np.float32)
            elif audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            self.logger.debug(f"Preprocessing {len(audio_data)} samples")
            
            # Preprocess using C++ engine
            result = afe.preprocess_audio(audio_data, sample_rate, channels)
            
            return (
                result['data'],
                result['sample_rate'],
                result['channels']
            )
            
        except Exception as e:
            self.logger.error(f"Audio preprocessing failed: {e}")
            raise RuntimeError(f"Audio preprocessing failed: {e}") from e
    
    def batch_process_reference_songs(
        self, 
        audio_samples: List[Dict], 
        song_ids: List[str]
    ) -> List[BatchProcessingResult]:
        """
        Batch process reference songs for database population.
        
        Args:
            audio_samples: List of audio sample dictionaries with keys:
                          'data', 'sample_rate', 'channels'
            song_ids: List of song identifiers
            
        Returns:
            List of BatchProcessingResult objects
            
        Raises:
            ValueError: If inputs are invalid
            RuntimeError: If batch processing fails
        """
        try:
            if len(audio_samples) != len(song_ids):
                raise ValueError("Number of audio samples must match number of song IDs")
            
            if not audio_samples:
                raise ValueError("No audio samples provided")
            
            self.logger.info(f"Batch processing {len(audio_samples)} reference songs")
            
            # Convert audio data to numpy arrays
            processed_samples = []
            for i, sample in enumerate(audio_samples):
                if not isinstance(sample['data'], np.ndarray):
                    sample['data'] = np.array(sample['data'], dtype=np.float32)
                elif sample['data'].dtype != np.float32:
                    sample['data'] = sample['data'].astype(np.float32)
                processed_samples.append(sample)
            
            # Process using C++ engine
            results = afe.batch_process_songs(processed_samples, song_ids)
            
            # Convert to BatchProcessingResult objects
            batch_results = []
            for result in results:
                batch_result = BatchProcessingResult(
                    song_id=result['song_id'],
                    success=result['success'],
                    fingerprint_count=result.get('fingerprint_count', 0),
                    processing_time_ms=result['processing_time_ms'],
                    total_duration_ms=result['total_duration_ms'],
                    error_message=result.get('error_message'),
                    hash_values=result.get('hash_values'),
                    time_offsets=result.get('time_offsets')
                )
                batch_results.append(batch_result)
            
            successful = sum(1 for r in batch_results if r.success)
            self.logger.info(f"Batch processing completed: {successful}/{len(batch_results)} successful")
            
            return batch_results
            
        except Exception as e:
            self.logger.error(f"Batch processing failed: {e}")
            raise RuntimeError(f"Batch processing failed: {e}") from e
    
    def compute_spectrogram(
        self, 
        audio_data: Union[np.ndarray, List[float]], 
        fft_size: int = 2048, 
        hop_size: int = 1024
    ) -> Dict:
        """
        Compute spectrogram from audio data.
        
        Args:
            audio_data: Audio samples
            fft_size: FFT window size
            hop_size: Hop size between windows
            
        Returns:
            Dictionary with spectrogram data and metadata
            
        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If computation fails
        """
        try:
            # Convert to numpy array if needed
            if not isinstance(audio_data, np.ndarray):
                audio_data = np.array(audio_data, dtype=np.float32)
            elif audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            if fft_size <= 0 or (fft_size & (fft_size - 1)) != 0:
                raise ValueError("FFT size must be a positive power of 2")
            
            if hop_size <= 0 or hop_size > fft_size:
                raise ValueError("Hop size must be positive and <= FFT size")
            
            self.logger.debug(f"Computing spectrogram with FFT size {fft_size}, hop size {hop_size}")
            
            # Compute using C++ engine
            result = afe.compute_spectrogram(audio_data, fft_size, hop_size)
            
            self.logger.debug(
                f"Computed spectrogram: {result['time_frames']} x {result['frequency_bins']}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Spectrogram computation failed: {e}")
            raise RuntimeError(f"Spectrogram computation failed: {e}") from e
    
    def get_engine_info(self) -> Dict[str, str]:
        """
        Get information about the audio fingerprinting engine.
        
        Returns:
            Dictionary with engine information
        """
        return {
            'version': afe.__version__,
            'engine': 'C++ with Python bindings',
            'fft_library': 'FFTW3 (if available) or built-in DFT',
            'supported_formats': 'mono/stereo float32 audio'
        }


# Global engine instance for convenience
_engine_instance = None


def get_engine() -> AudioFingerprintEngine:
    """Get global engine instance (singleton pattern)"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = AudioFingerprintEngine()
    return _engine_instance


# Convenience functions that use the global engine instance
def generate_fingerprint(
    audio_data: Union[np.ndarray, List[float]], 
    sample_rate: int, 
    channels: int = 1
) -> FingerprintResult:
    """Generate fingerprint using global engine instance"""
    return get_engine().generate_fingerprint(audio_data, sample_rate, channels)


def preprocess_audio(
    audio_data: Union[np.ndarray, List[float]], 
    sample_rate: int, 
    channels: int
) -> Tuple[np.ndarray, int, int]:
    """Preprocess audio using global engine instance"""
    return get_engine().preprocess_audio(audio_data, sample_rate, channels)


def batch_process_reference_songs(
    audio_samples: List[Dict], 
    song_ids: List[str]
) -> List[BatchProcessingResult]:
    """Batch process songs using global engine instance"""
    return get_engine().batch_process_reference_songs(audio_samples, song_ids)