"""
SQLAlchemy ORM models for the audio fingerprinting database.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class SongModel(Base):
    """SQLAlchemy model for songs table."""
    
    __tablename__ = 'songs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    artist = Column(String(255), nullable=False)
    album = Column(String(255), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationship to fingerprints
    fingerprints = relationship("FingerprintModel", back_populates="song", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Song(id={self.id}, title='{self.title}', artist='{self.artist}')>"
    
    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            'id': self.id,
            'title': self.title,
            'artist': self.artist,
            'album': self.album,
            'duration_seconds': self.duration_seconds,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class FingerprintModel(Base):
    """SQLAlchemy model for fingerprints table."""
    
    __tablename__ = 'fingerprints'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    song_id = Column(Integer, ForeignKey('songs.id', ondelete='CASCADE'), nullable=False)
    hash_value = Column(BigInteger, nullable=False)
    time_offset_ms = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationship to song
    song = relationship("SongModel", back_populates="fingerprints")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_fingerprints_hash', 'hash_value'),
        Index('idx_fingerprints_song_time', 'song_id', 'time_offset_ms'),
        Index('idx_fingerprints_hash_time', 'hash_value', 'time_offset_ms'),
        Index('idx_fingerprints_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Fingerprint(id={self.id}, song_id={self.song_id}, hash={self.hash_value})>"
    
    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            'id': self.id,
            'song_id': self.song_id,
            'hash_value': self.hash_value,
            'time_offset_ms': self.time_offset_ms,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# Additional indexes on songs table
Index('idx_songs_artist_title', SongModel.artist, SongModel.title)
Index('idx_songs_created_at', SongModel.created_at)