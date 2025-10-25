"""
Song-related data models for the fingerprinting system.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Song:
    """Represents a song in the database."""
    id: Optional[int]
    title: str
    artist: str
    album: Optional[str] = None
    duration_seconds: Optional[int] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate song parameters."""
        if not self.title.strip():
            raise ValueError("Song title cannot be empty")
        if not self.artist.strip():
            raise ValueError("Artist name cannot be empty")
        if self.duration_seconds is not None and self.duration_seconds <= 0:
            raise ValueError("Duration must be positive")


@dataclass
class SongMetadata:
    """Extended song metadata for display purposes."""
    song: Song
    fingerprint_count: int
    last_matched: Optional[datetime] = None
    match_count: int = 0