"""
Database population utilities for batch fingerprint insertion and management.
"""
import os
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import hashlib
from datetime import datetime

from backend.database.connection import get_db_session
from backend.database.repositories import SongRepository, FingerprintRepository
from backend.models.song import Song
from backend.models.audio import Fingerprint

logger = logging.getLogger(__name__)


class DuplicateDetector:
    """Handles duplicate detection and prevention for songs and fingerprints."""
    
    def __init__(self, song_repo: SongRepository):
        self.song_repo = song_repo
    
    def is_duplicate_song(self, title: str, artist: str) -> bool:
        """Check if a song already exists in the database."""
        existing_song = self.song_repo.find_song_by_title_artist(title, artist)
        return existing_song is not None
    
    def generate_audio_hash(self, audio_data: bytes) -> str:
        """Generate a hash for audio data to detect duplicates."""
        return hashlib.sha256(audio_data).hexdigest()
    
    def normalize_song_info(self, title: str, artist: str) -> Tuple[str, str]:
        """Normalize song title and artist for consistent comparison."""
        # Remove extra whitespace and convert to lowercase for comparison
        normalized_title = ' '.join(title.strip().split()).lower()
        normalized_artist = ' '.join(artist.strip().split()).lower()
        return normalized_title, normalized_artist


class BatchFingerprintInserter:
    """Handles batch insertion of fingerprints with performance optimization."""
    
    def __init__(self, fingerprint_repo: FingerprintRepository):
        self.fingerprint_repo = fingerprint_repo
        self.batch_size = 1000  # Configurable batch size
    
    def insert_fingerprints_batch(self, song_id: int, fingerprints: List[Fingerprint]) -> int:
        """Insert fingerprints in batches for better performance."""
        total_inserted = 0
        
        try:
            # Process fingerprints in batches
            for i in range(0, len(fingerprints), self.batch_size):
                batch = fingerprints[i:i + self.batch_size]
                
                inserted_count = self.fingerprint_repo.create_fingerprints(song_id, batch)
                total_inserted += inserted_count
                
                logger.debug(f"Inserted batch of {inserted_count} fingerprints for song {song_id}")
            
            logger.info(f"Successfully inserted {total_inserted} fingerprints for song {song_id}")
            return total_inserted
        
        except Exception as e:
            logger.error(f"Failed to insert fingerprints for song {song_id}: {e}")
            raise
    
    def validate_fingerprints(self, fingerprints: List[Fingerprint]) -> List[Fingerprint]:
        """Validate and filter fingerprints before insertion."""
        valid_fingerprints = []
        
        for fp in fingerprints:
            try:
                # Basic validation
                if fp.hash_value is None or fp.time_offset_ms < 0:
                    logger.warning(f"Invalid fingerprint: hash={fp.hash_value}, time={fp.time_offset_ms}")
                    continue
                
                # Check for reasonable hash values (not zero or negative)
                if fp.hash_value <= 0:
                    logger.warning(f"Suspicious hash value: {fp.hash_value}")
                    continue
                
                valid_fingerprints.append(fp)
            
            except Exception as e:
                logger.warning(f"Error validating fingerprint: {e}")
                continue
        
        logger.info(f"Validated {len(valid_fingerprints)} out of {len(fingerprints)} fingerprints")
        return valid_fingerprints


class DatabasePopulator:
    """Main class for populating the database with songs and fingerprints."""
    
    def __init__(self):
        self.duplicate_detector = None
        self.batch_inserter = None
        self.song_repo = None
        self.fingerprint_repo = None
    
    def _initialize_repositories(self, session):
        """Initialize repository instances with the current session."""
        self.song_repo = SongRepository(session)
        self.fingerprint_repo = FingerprintRepository(session)
        self.duplicate_detector = DuplicateDetector(self.song_repo)
        self.batch_inserter = BatchFingerprintInserter(self.fingerprint_repo)
    
    def add_song_with_fingerprints(
        self,
        title: str,
        artist: str,
        fingerprints: List[Fingerprint],
        album: Optional[str] = None,
        duration_seconds: Optional[int] = None,
        skip_duplicates: bool = True
    ) -> Optional[int]:
        """
        Add a song with its fingerprints to the database.
        Returns the song ID if successful, None if skipped due to duplicates.
        """
        with get_db_session() as session:
            self._initialize_repositories(session)
            
            try:
                # Check for duplicates if requested
                if skip_duplicates and self.duplicate_detector.is_duplicate_song(title, artist):
                    logger.info(f"Skipping duplicate song: '{title}' by '{artist}'")
                    return None
                
                # Validate fingerprints
                valid_fingerprints = self.batch_inserter.validate_fingerprints(fingerprints)
                if not valid_fingerprints:
                    logger.error(f"No valid fingerprints for song '{title}' by '{artist}'")
                    return None
                
                # Create song
                song = Song(
                    id=None,
                    title=title,
                    artist=artist,
                    album=album,
                    duration_seconds=duration_seconds
                )
                
                created_song = self.song_repo.create_song(song)
                logger.info(f"Created song: '{created_song.title}' by '{created_song.artist}' (ID: {created_song.id})")
                
                # Insert fingerprints
                fingerprint_count = self.batch_inserter.insert_fingerprints_batch(
                    created_song.id, valid_fingerprints
                )
                
                # Commit the transaction
                self.song_repo.commit()
                
                logger.info(f"Successfully added song '{title}' with {fingerprint_count} fingerprints")
                return created_song.id
            
            except Exception as e:
                logger.error(f"Failed to add song '{title}' by '{artist}': {e}")
                self.song_repo.rollback()
                raise
    
    def bulk_add_songs(self, songs_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Bulk add multiple songs with their fingerprints.
        
        Args:
            songs_data: List of dictionaries containing song info and fingerprints
                       Each dict should have: title, artist, fingerprints, album (optional), duration_seconds (optional)
        
        Returns:
            Dictionary with statistics about the operation
        """
        stats = {
            'total_songs': len(songs_data),
            'added_songs': 0,
            'skipped_duplicates': 0,
            'failed_songs': 0,
            'total_fingerprints': 0,
            'errors': []
        }
        
        for song_data in songs_data:
            try:
                title = song_data['title']
                artist = song_data['artist']
                fingerprints = song_data['fingerprints']
                album = song_data.get('album')
                duration_seconds = song_data.get('duration_seconds')
                
                song_id = self.add_song_with_fingerprints(
                    title=title,
                    artist=artist,
                    fingerprints=fingerprints,
                    album=album,
                    duration_seconds=duration_seconds,
                    skip_duplicates=True
                )
                
                if song_id:
                    stats['added_songs'] += 1
                    stats['total_fingerprints'] += len(fingerprints)
                else:
                    stats['skipped_duplicates'] += 1
            
            except Exception as e:
                stats['failed_songs'] += 1
                error_msg = f"Failed to add '{song_data.get('title', 'Unknown')}': {str(e)}"
                stats['errors'].append(error_msg)
                logger.error(error_msg)
        
        logger.info(f"Bulk operation completed: {stats}")
        return stats
    
    def remove_song_and_fingerprints(self, song_id: int) -> bool:
        """Remove a song and all its fingerprints from the database."""
        with get_db_session() as session:
            self._initialize_repositories(session)
            
            try:
                # Get song info for logging
                song = self.song_repo.get_song_by_id(song_id)
                if not song:
                    logger.warning(f"Song with ID {song_id} not found")
                    return False
                
                # Delete fingerprints first (though CASCADE should handle this)
                fingerprint_count = self.fingerprint_repo.delete_fingerprints_for_song(song_id)
                
                # Delete song
                deleted = self.song_repo.delete_song(song_id)
                
                if deleted:
                    self.song_repo.commit()
                    logger.info(f"Removed song '{song.title}' by '{song.artist}' and {fingerprint_count} fingerprints")
                    return True
                else:
                    logger.warning(f"Failed to delete song with ID {song_id}")
                    return False
            
            except Exception as e:
                logger.error(f"Failed to remove song {song_id}: {e}")
                self.song_repo.rollback()
                raise
    
    def get_population_stats(self) -> Dict[str, Any]:
        """Get statistics about the current database population."""
        with get_db_session() as session:
            self._initialize_repositories(session)
            
            try:
                from backend.database.repositories import MatchRepository
                match_repo = MatchRepository(session)
                return match_repo.get_database_stats()
            
            except Exception as e:
                logger.error(f"Failed to get population stats: {e}")
                raise


class DatabaseSeeder:
    """Handles database seeding with sample songs for testing and development."""
    
    def __init__(self):
        self.populator = DatabasePopulator()
    
    def create_sample_fingerprints(self, count: int = 100, base_time: int = 0) -> List[Fingerprint]:
        """Create sample fingerprints for testing purposes."""
        fingerprints = []
        
        for i in range(count):
            # Generate pseudo-random but deterministic hash values
            hash_value = hash(f"sample_fingerprint_{i}_{base_time}") & 0x7FFFFFFF  # Ensure positive
            time_offset = base_time + (i * 100)  # 100ms intervals
            
            fingerprints.append(Fingerprint(
                hash_value=hash_value,
                time_offset_ms=time_offset
            ))
        
        return fingerprints
    
    def seed_sample_songs(self, count: int = 10) -> Dict[str, Any]:
        """Seed the database with sample songs for testing."""
        sample_songs = []
        
        # Create sample song data
        for i in range(count):
            fingerprints = self.create_sample_fingerprints(
                count=50 + (i * 10),  # Varying fingerprint counts
                base_time=i * 1000
            )
            
            song_data = {
                'title': f'Sample Song {i + 1}',
                'artist': f'Sample Artist {(i % 5) + 1}',  # Some artists have multiple songs
                'album': f'Sample Album {(i % 3) + 1}' if i % 2 == 0 else None,
                'duration_seconds': 180 + (i * 30),  # 3-8 minute songs
                'fingerprints': fingerprints
            }
            
            sample_songs.append(song_data)
        
        logger.info(f"Seeding database with {count} sample songs")
        return self.populator.bulk_add_songs(sample_songs)
    
    def clear_all_data(self) -> Dict[str, int]:
        """Clear all songs and fingerprints from the database (use with caution!)."""
        with get_db_session() as session:
            try:
                from backend.database.models import SongModel, FingerprintModel
                
                # Delete all fingerprints first
                fingerprint_count = session.query(FingerprintModel).count()
                session.query(FingerprintModel).delete()
                
                # Delete all songs
                song_count = session.query(SongModel).count()
                session.query(SongModel).delete()
                
                session.commit()
                
                logger.warning(f"Cleared all data: {song_count} songs, {fingerprint_count} fingerprints")
                return {'songs_deleted': song_count, 'fingerprints_deleted': fingerprint_count}
            
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to clear database: {e}")
                raise


# Convenience functions for common operations
def add_song(title: str, artist: str, fingerprints: List[Fingerprint], **kwargs) -> Optional[int]:
    """Convenience function to add a single song."""
    populator = DatabasePopulator()
    return populator.add_song_with_fingerprints(title, artist, fingerprints, **kwargs)


def seed_database(song_count: int = 10) -> Dict[str, Any]:
    """Convenience function to seed the database with sample data."""
    seeder = DatabaseSeeder()
    return seeder.seed_sample_songs(song_count)


def get_db_stats() -> Dict[str, Any]:
    """Convenience function to get database statistics."""
    populator = DatabasePopulator()
    return populator.get_population_stats()