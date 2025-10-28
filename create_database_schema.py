#!/usr/bin/env python3
"""Create the database schema for audio fingerprinting."""

from backend.database.connection import DatabaseConnectionManager, DatabaseConfig
from backend.database.models import Base
from backend.api.config import get_settings

def create_schema():
    """Create all database tables."""
    try:
        # Load settings
        settings = get_settings()
        
        # Create database config
        db_config = DatabaseConfig(settings)
        
        # Create connection manager
        db_manager = DatabaseConnectionManager(db_config)
        db_manager.initialize()
        
        print("✅ Database connection initialized")
        
        # Create all tables
        Base.metadata.create_all(db_manager._engine)
        
        print("✅ Database schema created successfully")
        print("Tables created:")
        for table_name in Base.metadata.tables.keys():
            print(f"  - {table_name}")
        
        db_manager.close()
        
    except Exception as e:
        print(f"❌ Failed to create database schema: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_schema()