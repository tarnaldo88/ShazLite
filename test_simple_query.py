#!/usr/bin/env python3
"""Simple test to verify database connection and basic queries work."""

import os
from dotenv import load_dotenv
from backend.database.connection import DatabaseConnectionManager, DatabaseConfig
from backend.api.config import get_settings

def test_simple_query():
    """Test a simple database query."""
    try:
        # Load settings
        settings = get_settings()
        
        # Create database config
        db_config = DatabaseConfig(settings)
        
        # Create connection manager
        db_manager = DatabaseConnectionManager(db_config)
        db_manager.initialize()
        
        print("✅ Database connection initialized")
        
        # Test simple query
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM songs")
                song_count = cursor.fetchone()[0]
                print(f"✅ Found {song_count} songs in database")
                
                cursor.execute("SELECT COUNT(*) FROM fingerprints LIMIT 1")
                fingerprint_count = cursor.fetchone()[0]
                print(f"✅ Found {fingerprint_count} fingerprints in database")
        
        db_manager.close()
        print("✅ Database connection closed successfully")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_query()