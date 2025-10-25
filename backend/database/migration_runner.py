"""
Database migration runner for managing schema changes.
"""
import os
import logging
from pathlib import Path
from typing import List, Tuple
from backend.database.connection import DatabaseConnectionManager, DatabaseConfig

logger = logging.getLogger(__name__)


class MigrationRunner:
    """Handles database migration execution and tracking."""
    
    def __init__(self, db_manager: DatabaseConnectionManager):
        self.db_manager = db_manager
        self.migrations_dir = Path(__file__).parent / "migrations"
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of already applied migrations."""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Check if migrations table exists
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = 'schema_migrations'
                        )
                    """)
                    
                    if not cursor.fetchone()[0]:
                        return []
                    
                    # Get applied migrations
                    cursor.execute("SELECT version FROM schema_migrations ORDER BY version")
                    return [row[0] for row in cursor.fetchall()]
        
        except Exception as e:
            logger.error(f"Failed to get applied migrations: {e}")
            return []
    
    def get_pending_migrations(self) -> List[Tuple[str, Path]]:
        """Get list of pending migrations to apply."""
        applied = set(self.get_applied_migrations())
        pending = []
        
        if not self.migrations_dir.exists():
            logger.warning(f"Migrations directory not found: {self.migrations_dir}")
            return pending
        
        for migration_file in sorted(self.migrations_dir.glob("*.sql")):
            migration_name = migration_file.stem
            if migration_name not in applied:
                pending.append((migration_name, migration_file))
        
        return pending
    
    def apply_migration(self, migration_name: str, migration_file: Path):
        """Apply a single migration."""
        logger.info(f"Applying migration: {migration_name}")
        
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Read and execute migration
                    migration_sql = migration_file.read_text()
                    cursor.execute(migration_sql)
                    conn.commit()
                    
                    logger.info(f"Migration {migration_name} applied successfully")
        
        except Exception as e:
            logger.error(f"Failed to apply migration {migration_name}: {e}")
            raise
    
    def run_migrations(self) -> int:
        """Run all pending migrations."""
        pending = self.get_pending_migrations()
        
        if not pending:
            logger.info("No pending migrations to apply")
            return 0
        
        logger.info(f"Found {len(pending)} pending migrations")
        
        applied_count = 0
        for migration_name, migration_file in pending:
            try:
                self.apply_migration(migration_name, migration_file)
                applied_count += 1
            except Exception as e:
                logger.error(f"Migration failed, stopping at {migration_name}: {e}")
                break
        
        logger.info(f"Applied {applied_count} migrations successfully")
        return applied_count
    
    def create_migration_table(self):
        """Create the schema_migrations table if it doesn't exist."""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS schema_migrations (
                            version VARCHAR(50) PRIMARY KEY,
                            applied_at TIMESTAMP DEFAULT NOW()
                        )
                    """)
                    conn.commit()
                    logger.info("Migration tracking table created")
        
        except Exception as e:
            logger.error(f"Failed to create migration table: {e}")
            raise


def run_database_migrations(config: DatabaseConfig = None) -> int:
    """Convenience function to run all pending migrations."""
    db_manager = DatabaseConnectionManager(config)
    
    try:
        db_manager.initialize()
        
        runner = MigrationRunner(db_manager)
        runner.create_migration_table()
        
        return runner.run_migrations()
    
    finally:
        db_manager.close()


if __name__ == "__main__":
    # Run migrations when script is executed directly
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    try:
        applied = run_database_migrations()
        print(f"Successfully applied {applied} migrations")
        sys.exit(0)
    except Exception as e:
        print(f"Migration failed: {e}")
        sys.exit(1)