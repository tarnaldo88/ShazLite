"""
Audio-related data models for the fingerprinting system.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class AudioSample:
    """Represents an audio sample for processing."""
    data: bytes
    sample_rate: int
    channels: int
    duration_ms: int
    format: str
    
    def __post_init__(self):
        """Validate audio sample parameters."""
        if self.sample_rate <= 0:
            raise ValueError("Sample rate must be positive")
        if self.channels <= 0:
            raise ValueError("Channels must be positive")
        if self.duration_ms <= 0:
            raise ValueError("Duration must be positive")
        if not self.data:
            raise ValueError("Audio data cannot be empty")


@dataclass
class Fingerprint:
    """Represents an audio fingerprint with hash and timing information."""
    hash_value: int
    time_offset_ms: int
    frequency_1: Optional[float] = None
    frequency_2: Optional[float] = None
    time_delta_ms: Optional[int] = None
    
    def __post_init__(self):
        """Validate fingerprint parameters."""
        if self.time_offset_ms < 0:
            raise ValueError("Time offset cannot be negative")
        if self.time_delta_ms is not None and self.time_delta_ms < 0:
            raise ValueError("Time delta cannot be negative")


class AudioProcessingError(Exception):
    """Exception raised when audio processing fails."""
    pass


class InvalidAudioFormatError(AudioProcessingError):
    """Exception raised when audio format is invalid."""
    pass