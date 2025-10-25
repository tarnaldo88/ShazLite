"""
Database package for the audio fingerprinting system.
"""
from .connection import (
    DatabaseConfig,
    DatabaseConnectionManager,
    initialize_database,
    close_database,
    get_db_session,
    get_db_connection
)
from .models import SongModel, FingerprintModel, Base
from .repositories import (
    SongRepository,
    FingerprintRepository,
    MatchRepository
)
from .population_utils import (
    DatabasePopulator,
    DatabaseSeeder,
    add_song,
    seed_database,
    get_db_stats
)

__all__ = [
    # Connection management
    'DatabaseConfig',
    'DatabaseConnectionManager',
    'initialize_database',
    'close_database',
    'get_db_session',
    'get_db_connection',
    
    # ORM Models
    'SongModel',
    'FingerprintModel',
    'Base',
    
    # Repositories
    'SongRepository',
    'FingerprintRepository',
    'MatchRepository',
    
    # Population utilities
    'DatabasePopulator',
    'DatabaseSeeder',
    'add_song',
    'seed_database',
    'get_db_stats'
]