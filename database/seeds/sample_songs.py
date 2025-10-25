"""
Sample song data for database seeding and testing.
"""
import sys
import os
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from backend.database.population_utils import DatabaseSeeder, get_db_stats
from backend.database.connection import initialize_database, close_database
from backend.models.audio import Fingerprint


def create_realistic_sample_songs():
    """Create more realistic sample song data."""
    songs_data = [
        {
            'title': 'Bohemian Rhapsody',
            'artist': 'Queen',
            'album': 'A Night at the Opera',
            'duration_seconds': 355,
        },
        {
            'title': 'Hotel California',
            'artist': 'Eagles',
            'album': 'Hotel California',
            'duration_seconds': 391,
        },
        {
            'title': 'Stairway to Heaven',
            'artist': 'Led Zeppelin',
            'album': 'Led Zeppelin IV',
            'duration_seconds': 482,
        },
        {
            'title': 'Imagine',
            'artist': 'John Lennon',
            'album': 'Imagine',
            'duration_seconds': 183,
        },
        {
            'title': 'Billie Jean',
            'artist': 'Michael Jackson',
            'album': 'Thriller',
            'duration_seconds': 294,
        },
        {
            'title': 'Sweet Child O\' Mine',
            'artist': 'Guns N\' Roses',
            'album': 'Appetite for Destruction',
            'duration_seconds': 356,
        },
        {
            'title': 'Smells Like Teen Spirit',
            'artist': 'Nirvana',
            'album': 'Nevermind',
            'duration_seconds': 301,
        },
        {
            'title': 'Like a Rolling Stone',
            'artist': 'Bob Dylan',
            'album': 'Highway 61 Revisited',
            'duration_seconds': 369,
        },
        {
            'title': 'Purple Haze',
            'artist': 'Jimi Hendrix',
            'album': 'Are You Experienced',
            'duration_seconds': 167,
        },
        {
            'title': 'Good Vibrations',
            'artist': 'The Beach Boys',
            'album': 'Pet Sounds',
            'duration_seconds': 219,
        }
    ]
    
    # Generate fingerprints for each song
    for i, song in enumerate(songs_data):
        # Create more realistic fingerprint patterns
        fingerprint_count = song['duration_seconds'] // 3  # Roughly one fingerprint per 3 seconds
        fingerprints = []
        
        for j in range(fingerprint_count):
            # Generate more realistic hash values based on song characteristics
            base_hash = hash(f"{song['title']}_{song['artist']}_{j}")
            
            # Add some variation to make fingerprints more realistic
            variation = hash(f"variation_{i}_{j}") % 10000
            hash_value = abs(base_hash + variation)
            
            # Time offset with some jitter
            base_time = j * 3000  # 3 second intervals
            time_jitter = (hash(f"time_{i}_{j}") % 1000) - 500  # ±500ms jitter
            time_offset = max(0, base_time + time_jitter)
            
            fingerprints.append(Fingerprint(
                hash_value=hash_value,
                time_offset_ms=time_offset
            ))
        
        song['fingerprints'] = fingerprints
    
    return songs_data


def seed_sample_database():
    """Seed the database with sample songs."""
    try:
        # Initialize database connection
        initialize_database()
        
        # Create seeder
        seeder = DatabaseSeeder()
        
        # Get current stats
        print("Current database stats:")
        current_stats = get_db_stats()
        for key, value in current_stats.items():
            print(f"  {key}: {value}")
        
        # Create and add realistic sample songs
        print("\nCreating realistic sample songs...")
        sample_songs = create_realistic_sample_songs()
        
        # Use the populator to add songs
        from backend.database.population_utils import DatabasePopulator
        populator = DatabasePopulator()
        
        result = populator.bulk_add_songs(sample_songs)
        
        print(f"\nSeeding results:")
        for key, value in result.items():
            print(f"  {key}: {value}")
        
        if result['errors']:
            print("\nErrors encountered:")
            for error in result['errors']:
                print(f"  - {error}")
        
        # Get updated stats
        print("\nUpdated database stats:")
        updated_stats = get_db_stats()
        for key, value in updated_stats.items():
            print(f"  {key}: {value}")
        
        return result
    
    except Exception as e:
        print(f"Error seeding database: {e}")
        raise
    
    finally:
        close_database()


def clear_sample_database():
    """Clear all sample data from the database."""
    try:
        initialize_database()
        
        seeder = DatabaseSeeder()
        result = seeder.clear_all_data()
        
        print(f"Cleared database:")
        for key, value in result.items():
            print(f"  {key}: {value}")
        
        return result
    
    except Exception as e:
        print(f"Error clearing database: {e}")
        raise
    
    finally:
        close_database()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database seeding utility")
    parser.add_argument('--clear', action='store_true', help='Clear all data instead of seeding')
    parser.add_argument('--stats', action='store_true', help='Show database statistics only')
    
    args = parser.parse_args()
    
    if args.stats:
        try:
            initialize_database()
            stats = get_db_stats()
            print("Database statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        finally:
            close_database()
    
    elif args.clear:
        clear_sample_database()
    
    else:
        seed_sample_database()