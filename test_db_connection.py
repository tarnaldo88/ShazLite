#!/usr/bin/env python3
"""Test database connection with different credentials."""

import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection(host, port, database, user, password):
    """Test database connection with given credentials."""
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        print(f"✅ SUCCESS: Connected to {database} as {user}")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ FAILED: {user}@{host}:{port}/{database} - {e}")
        return False

if __name__ == "__main__":
    print("Testing database connections...")
    print("=" * 50)
    
    # Test with environment variables
    host = os.getenv('DB_HOST', '127.0.0.1')
    port = int(os.getenv('DB_PORT', '5432'))
    database = os.getenv('DB_NAME', 'audio_fingerprinting')
    user = os.getenv('DB_USER', 'postgres')
    password = os.getenv('DB_PASSWORD', 'audio_password_change_me')
    
    print(f"From .env file:")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Database: {database}")
    print(f"User: {user}")
    print(f"Password: {password}")
    print()
    
    # Test connection to audio_fingerprinting database
    print("1. Testing connection to audio_fingerprinting database:")
    test_connection(host, port, database, user, password)
    
    # Test connection to default postgres database
    print("2. Testing connection to postgres database:")
    test_connection(host, port, 'postgres', user, password)
    
    # Try with different passwords
    print("3. Testing with different passwords:")
    passwords_to_try = ['torres123', 'audio_password_change_me', 'postgres', '']
    
    for pwd in passwords_to_try:
        print(f"   Trying password: '{pwd}'")
        if test_connection(host, port, 'postgres', user, pwd):
            print(f"   ✅ Found working password: '{pwd}'")
            break
    
    print("=" * 50)
    print("Test completed.")