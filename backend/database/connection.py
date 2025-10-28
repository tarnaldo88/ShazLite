"""
Database connection management with connection pooling.
"""
import os
import logging
from typing import Optional
from contextlib import contextmanager
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration settings."""
    
    def __init__(self, settings=None):
        if settings:
            self.host = settings.db_host
            self.port = settings.db_port
            self.database = settings.db_name
            self.username = settings.db_user
            self.password = settings.db_password
            self.min_connections = settings.db_min_connections
            self.max_connections = settings.db_max_connections
            self.pool_timeout = settings.db_pool_timeout
        else:
            # Fallback to environment variables
            self.host = os.getenv('DB_HOST', 'localhost')
            self.port = int(os.getenv('DB_PORT', '5432'))
            self.database = os.getenv('DB_NAME', 'audio_fingerprinting')
            self.username = os.getenv('DB_USER', 'postgres')
            self.password = os.getenv('DB_PASSWORD', 'postgres')
            self.min_connections = int(os.getenv('DB_MIN_CONNECTIONS', '5'))
            self.max_connections = int(os.getenv('DB_MAX_CONNECTIONS', '20'))
            self.pool_timeout = int(os.getenv('DB_POOL_TIMEOUT', '30'))
    
    @property
    def connection_string(self) -> str:
        """Get SQLAlchemy connection string."""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def psycopg2_params(self) -> dict:
        """Get psycopg2 connection parameters."""
        return {
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'user': self.username,
            'password': self.password
        }


class DatabaseConnectionManager:
    """Manages database connections with pooling."""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self._engine: Optional[sqlalchemy.Engine] = None
        self._session_factory: Optional[sessionmaker] = None
        self._connection_pool: Optional[psycopg2.pool.ThreadedConnectionPool] = None
    
    def initialize(self):
        """Initialize database connections and pools."""
        try:
            # Create SQLAlchemy engine with connection pooling
            self._engine = create_engine(
                self.config.connection_string,
                poolclass=QueuePool,
                pool_size=self.config.min_connections,
                max_overflow=self.config.max_connections - self.config.min_connections,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=3600,  # Recycle connections every hour
                echo=False  # Set to True for SQL debugging
            )
            
            # Create session factory
            self._session_factory = sessionmaker(bind=self._engine)
            
            # Create psycopg2 connection pool for raw queries
            self._connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=self.config.min_connections,
                maxconn=self.config.max_connections,
                **self.config.psycopg2_params
            )
            
            logger.info("Database connection pools initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database connections: {e}")
            raise
    
    def close(self):
        """Close all database connections."""
        if self._connection_pool:
            self._connection_pool.closeall()
            self._connection_pool = None
        
        if self._engine:
            self._engine.dispose()
            self._engine = None
        
        self._session_factory = None
        logger.info("Database connections closed")
    
    @contextmanager
    def get_session(self):
        """Get SQLAlchemy session with automatic cleanup."""
        if not self._session_factory:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    @contextmanager
    def get_connection(self):
        """Get raw psycopg2 connection with automatic cleanup."""
        if not self._connection_pool:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        connection = None
        try:
            connection = self._connection_pool.getconn()
            yield connection
        except Exception:
            if connection:
                connection.rollback()
            raise
        finally:
            if connection:
                self._connection_pool.putconn(connection)
    
    def execute_migration(self, migration_file: str):
        """Execute a database migration script."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                with open(migration_file, 'r') as f:
                    migration_sql = f.read()
                
                try:
                    cursor.execute(migration_sql)
                    conn.commit()
                    logger.info(f"Migration {migration_file} executed successfully")
                except Exception as e:
                    conn.rollback()
                    logger.error(f"Migration {migration_file} failed: {e}")
                    raise
    
    def test_connection(self) -> bool:
        """Test database connectivity."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    return result[0] == 1
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False


# Global database manager instance
db_manager = DatabaseConnectionManager()


def initialize_database(config: Optional[DatabaseConfig] = None):
    """Initialize the global database manager."""
    global db_manager
    if config:
        db_manager = DatabaseConnectionManager(config)
    db_manager.initialize()


def close_database():
    """Close the global database manager."""
    global db_manager
    db_manager.close()


@contextmanager
def get_db_session():
    """Get database session from global manager."""
    with db_manager.get_session() as session:
        yield session


@contextmanager
def get_db_connection():
    """Get database connection from global manager."""
    with db_manager.get_connection() as connection:
        yield connection