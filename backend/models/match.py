"""
Match result data models for the fingerprinting system.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class MatchResult:
    """Represents a song identification match result."""
    song_id: int
    title: str
    artist: str
    album: Optional[str]
    confidence: float
    match_count: int
    time_offset_ms: int
    
    def __post_init__(self):
        """Validate match result parameters."""
        if self.confidence < 0.0 or self.confidence > 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        if self.match_count < 0:
            raise ValueError("Match count cannot be negative")
        if self.time_offset_ms < 0:
            raise ValueError("Time offset cannot be negative")


@dataclass
class IdentificationRequest:
    """Represents a request for audio identification."""
    audio_data: bytes
    format: str
    client_id: Optional[str] = None
    
    def __post_init__(self):
        """Validate identification request parameters."""
        if not self.audio_data:
            raise ValueError("Audio data cannot be empty")
        if not self.format.strip():
            raise ValueError("Audio format cannot be empty")


@dataclass
class IdentificationResponse:
    """Represents the response from audio identification."""
    success: bool
    match_result: Optional[MatchResult] = None
    error_message: Optional[str] = None
    processing_time_ms: Optional[int] = None
    
    def __post_init__(self):
        """Validate identification response."""
        if self.success and self.match_result is None:
            raise ValueError("Successful response must include match result")
        if not self.success and self.error_message is None:
            raise ValueError("Failed response must include error message")