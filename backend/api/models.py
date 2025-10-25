"""
Pydantic models for request/response validation and serialization.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
import time


class AudioSampleRequest(BaseModel):
    """Request model for audio identification."""
    
    # Audio data will be uploaded as multipart/form-data
    # This model validates other request parameters
    format: str = Field(..., description="Audio format (wav, mp3)")
    duration_ms: Optional[int] = Field(None, description="Audio duration in milliseconds")
    sample_rate: Optional[int] = Field(None, description="Audio sample rate")
    
    @validator('format')
    def validate_format(cls, v):
        """Validate audio format."""
        allowed_formats = ['wav', 'mp3', 'flac', 'm4a']
        if v.lower() not in allowed_formats:
            raise ValueError(f'Audio format must be one of: {", ".join(allowed_formats)}')
        return v.lower()
    
    @validator('duration_ms')
    def validate_duration(cls, v):
        """Validate audio duration."""
        if v is not None and (v < 1000 or v > 30000):  # 1-30 seconds
            raise ValueError('Audio duration must be between 1 and 30 seconds')
        return v
    
    @validator('sample_rate')
    def validate_sample_rate(cls, v):
        """Validate sample rate."""
        if v is not None and v < 8000:
            raise ValueError('Sample rate must be at least 8000 Hz')
        return v


class MatchResult(BaseModel):
    """Model for song match results."""
    
    song_id: int = Field(..., description="Database song identifier")
    title: str = Field(..., description="Song title")
    artist: str = Field(..., description="Artist name")
    album: Optional[str] = Field(None, description="Album name")
    confidence: float = Field(..., description="Match confidence score (0.0-1.0)")
    match_count: int = Field(..., description="Number of matching fingerprints")
    time_offset_ms: Optional[int] = Field(None, description="Estimated position in original song")
    
    @validator('confidence')
    def validate_confidence(cls, v):
        """Validate confidence score."""
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v


class AudioIdentificationResponse(BaseModel):
    """Response model for audio identification."""
    
    success: bool = Field(..., description="Whether identification was successful")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    match: Optional[MatchResult] = Field(None, description="Song match result if found")
    message: Optional[str] = Field(None, description="Additional information or error message")
    request_id: str = Field(..., description="Unique request identifier")


class SongMetadata(BaseModel):
    """Model for song metadata."""
    
    title: str = Field(..., min_length=1, max_length=255, description="Song title")
    artist: str = Field(..., min_length=1, max_length=255, description="Artist name")
    album: Optional[str] = Field(None, max_length=255, description="Album name")
    duration_seconds: Optional[int] = Field(None, description="Song duration in seconds")
    genre: Optional[str] = Field(None, max_length=100, description="Music genre")
    year: Optional[int] = Field(None, description="Release year")
    
    @validator('duration_seconds')
    def validate_duration(cls, v):
        """Validate song duration."""
        if v is not None and (v < 1 or v > 7200):  # 1 second to 2 hours
            raise ValueError('Duration must be between 1 and 7200 seconds')
        return v
    
    @validator('year')
    def validate_year(cls, v):
        """Validate release year."""
        if v is not None and (v < 1900 or v > 2030):
            raise ValueError('Year must be between 1900 and 2030')
        return v


class AddSongRequest(BaseModel):
    """Request model for adding reference songs."""
    
    metadata: SongMetadata = Field(..., description="Song metadata")
    # Audio file will be uploaded as multipart/form-data


class AddSongResponse(BaseModel):
    """Response model for adding reference songs."""
    
    success: bool = Field(..., description="Whether song was added successfully")
    song_id: Optional[int] = Field(None, description="Database song identifier")
    fingerprint_count: Optional[int] = Field(None, description="Number of fingerprints generated")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    message: Optional[str] = Field(None, description="Additional information or error message")
    request_id: str = Field(..., description="Unique request identifier")


class HealthCheckResponse(BaseModel):
    """Response model for health check endpoint."""
    
    status: str = Field(..., description="Service status")
    timestamp: float = Field(default_factory=time.time, description="Response timestamp")
    version: str = Field(..., description="API version")
    components: Dict[str, str] = Field(..., description="Component health status")
    uptime_seconds: Optional[float] = Field(None, description="Service uptime in seconds")


class ErrorResponse(BaseModel):
    """Standard error response model."""
    
    error: str = Field(..., description="Error type identifier")
    message: str = Field(..., description="Human-readable error message")
    error_id: str = Field(..., description="Unique error identifier for tracking")
    timestamp: float = Field(default_factory=time.time, description="Error timestamp")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class BatchProcessRequest(BaseModel):
    """Request model for batch processing operations."""
    
    operation: str = Field(..., description="Batch operation type")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Operation parameters")
    
    @validator('operation')
    def validate_operation(cls, v):
        """Validate batch operation type."""
        allowed_operations = ['populate_database', 'rebuild_index', 'cleanup_duplicates']
        if v not in allowed_operations:
            raise ValueError(f'Operation must be one of: {", ".join(allowed_operations)}')
        return v


class BatchProcessResponse(BaseModel):
    """Response model for batch processing operations."""
    
    success: bool = Field(..., description="Whether operation was successful")
    operation: str = Field(..., description="Batch operation type")
    items_processed: int = Field(..., description="Number of items processed")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    message: Optional[str] = Field(None, description="Additional information")
    request_id: str = Field(..., description="Unique request identifier")


class FingerprintData(BaseModel):
    """Model for fingerprint data."""
    
    hash_value: int = Field(..., description="32-bit hash of landmark pair")
    time_offset_ms: int = Field(..., description="Time position in original audio")
    frequency_1: Optional[float] = Field(None, description="First landmark frequency (Hz)")
    frequency_2: Optional[float] = Field(None, description="Second landmark frequency (Hz)")
    time_delta_ms: Optional[int] = Field(None, description="Time difference between landmarks")
    
    @validator('time_offset_ms')
    def validate_time_offset(cls, v):
        """Validate time offset."""
        if v < 0:
            raise ValueError('Time offset must be non-negative')
        return v