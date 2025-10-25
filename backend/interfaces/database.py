"""
Database interface definitions for the fingerprinting system.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from backend.models.song import Song
from backend.models.audio import Fingerprint
from backend.models.match import MatchResult


class DatabaseRepositoryInterface(ABC):
    """Interface for database operations."""
    
    @abstractmethod
    async def create_song(self, title: str, artist: str, album: Optional[str] = None, 
                         duration_seconds: Optional[int] = None) -> Song:
        """
        Create a new song record in the database.
        
        Args:
            title: Song title
            artist: Artist name
            album: Album name (optional)
            duration_seconds: Song duration (optional)
            
        Returns:
            Created song object with database ID
            
        Raises:
            DatabaseError: If song creation fails
        """
        pass
    
    @abstractmethod
    async def get_song_by_id(self, song_id: int) -> Optional[Song]:
        """
        Retrieve a song by its database ID.
        
        Args:
            song_id: Database ID of the song
            
        Returns:
            Song object if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def insert_fingerprints(self, song_id: int, fingerprints: List[Fingerprint]) -> bool:
        """
        Insert fingerprints for a song into the database.
        
        Args:
            song_id: Database ID of the associated song
            fingerprints: List of fingerprint objects to insert
            
        Returns:
            True if insertion successful, False otherwise
            
        Raises:
            DatabaseError: If fingerprint insertion fails
        """
        pass
    
    @abstractmethod
    async def search_fingerprints(self, fingerprints: List[Fingerprint]) -> List[MatchResult]:
        """
        Search for matching fingerprints in the database.
        
        Args:
            fingerprints: List of fingerprints to search for
            
        Returns:
            List of match results with confidence scores
            
        Raises:
            DatabaseError: If search operation fails
        """
        pass
    
    @abstractmethod
    async def get_song_count(self) -> int:
        """
        Get the total number of songs in the database.
        
        Returns:
            Number of songs in the database
        """
        pass
    
    @abstractmethod
    async def get_fingerprint_count(self) -> int:
        """
        Get the total number of fingerprints in the database.
        
        Returns:
            Number of fingerprints in the database
        """
        pass


class ConnectionManagerInterface(ABC):
    """Interface for database connection management."""
    
    @abstractmethod
    async def get_connection(self) -> Any:
        """
        Get a database connection from the pool.
        
        Returns:
            Database connection object
            
        Raises:
            ConnectionError: If connection cannot be established
        """
        pass
    
    @abstractmethod
    async def release_connection(self, connection: Any) -> None:
        """
        Release a database connection back to the pool.
        
        Args:
            connection: Database connection to release
        """
        pass
    
    @abstractmethod
    async def close_all_connections(self) -> None:
        """
        Close all database connections in the pool.
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if database is accessible and healthy.
        
        Returns:
            True if database is healthy, False otherwise
        """
        pass