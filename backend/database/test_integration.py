"""
Integration tests for database operations and performance.
"""
import pytest
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

from backend.database.connection import DatabaseConnectionManager, DatabaseConfig
from backend.database.repositories import SongRepository, FingerprintRepository, MatchRepository
from backend.database.population_utils import DatabasePopulator, DatabaseSeeder
from backend.models.song import Song
from backend.models.audio import Fingerprint


class TestDatabaseIntegration:
    """Integration tests for database operations."""
    
    @pytest.fixture(scope="class")
    def db_manager(self):
        """Create a test database manager."""
        # Use test database configuration
        config = DatabaseConfig()
        config.database = "audio_fingerprinting_test"
        config.min_connections = 2
        config.max_connections = 10
        
        manager = DatabaseConnectionManager(config)
        manager.initialize()
        
        yield manager
        
        manager.close()
    
    @pytest.fixture
    def repositories(self, db_manager):
        """Create repository instances for testing."""
        with db_manager.get_session() as session:
            song_repo = SongRepository(session)
            fingerprint_repo = FingerprintRepository(session)
            match_repo = MatchRepository(session)
            
            yield song_repo, fingerprint_repo, match_repo
    
    def test_fingerprint_insertion_performance(self, repositories):
        """Test fingerprint insertion performance with large datasets."""
        song_repo, fingerprint_repo, match_repo = repositories
        
        # Create a test song
        test_song = Song(
            id=None,
            title="Performance Test Song",
            artist="Test Artist",
            duration_seconds=300
        )
        
        created_song = song_repo.create_song(test_song)
        song_repo.commit()
        
        # Generate large number of fingerprints
        fingerprint_count = 1000
        fingerprints = []
        
        for i in range(fingerprint_count):
            fingerprints.append(Fingerprint(
                hash_value=hash(f"perf_test_{i}") & 0x7FFFFFFF,
                time_offset_ms=i * 100
            ))
        
        # Measure insertion time
        start_time = time.time()
        inserted_count = fingerprint_repo.create_fingerprints(created_song.id, fingerprints)
        fingerprint_repo.commit()
        insertion_time = time.time() - start_time
        
        # Verify results
        assert inserted_count == fingerprint_count
        assert insertion_time < 5.0  # Should complete within 5 seconds
        
        # Test retrieval performance
        start_time = time.time()
        retrieved_fingerprints = fingerprint_repo.get_fingerprints_for_song(created_song.id)
        retrieval_time = time.time() - start_time
        
        assert len(retrieved_fingerprints) == fingerprint_count
        assert retrieval_time < 2.0  # Should retrieve within 2 seconds
        
        print(f"Insertion time for {fingerprint_count} fingerprints: {insertion_time:.3f}s")
        print(f"Retrieval time for {fingerprint_count} fingerprints: {retrieval_time:.3f}s")
    
    def test_query_optimization_large_dataset(self, repositories):
        """Test query optimization with large datasets."""
        song_repo, fingerprint_repo, match_repo = repositories
        
        # Create multiple songs with fingerprints
        songs_count = 10
        fingerprints_per_song = 500
        
        created_songs = []
        all_query_fingerprints = []
        
        for i in range(songs_count):
            # Create song
            song = Song(
                id=None,
                title=f"Query Test Song {i}",
                artist=f"Query Test Artist {i}",
                duration_seconds=250
            )
            
            created_song = song_repo.create_song(song)
            created_songs.append(created_song)
            
            # Create fingerprints
            fingerprints = []
            for j in range(fingerprints_per_song):
                hash_value = hash(f"query_test_{i}_{j}") & 0x7FFFFFFF
                fingerprint = Fingerprint(
                    hash_value=hash_value,
                    time_offset_ms=j * 100
                )
                fingerprints.append(fingerprint)
                
                # Add some fingerprints to query set
                if j % 10 == 0:  # Every 10th fingerprint
                    all_query_fingerprints.append(fingerprint)
            
            fingerprint_repo.create_fingerprints(created_song.id, fingerprints)
        
        song_repo.commit()
        
        # Test query performance with large dataset
        query_fingerprints = all_query_fingerprints[:50]  # Use 50 query fingerprints
        
        start_time = time.time()
        matches = fingerprint_repo.find_matching_fingerprints(query_fingerprints)
        query_time = time.time() - start_time
        
        # Verify results
        assert len(matches) > 0  # Should find matches
        assert query_time < 3.0  # Should complete within 3 seconds
        
        # Test match finding performance
        start_time = time.time()
        best_match = match_repo.find_best_match(query_fingerprints, min_matches=3)
        match_time = time.time() - start_time
        
        assert best_match is not None
        assert match_time < 2.0  # Should complete within 2 seconds
        
        print(f"Query time for {len(query_fingerprints)} fingerprints: {query_time:.3f}s")
        print(f"Match finding time: {match_time:.3f}s")
        print(f"Found {len(matches)} raw matches, best match: {best_match.title}")
    
    def test_concurrent_access_scenarios(self, db_manager):
        """Test concurrent database access scenarios."""
        
        def worker_insert_song(worker_id: int) -> Dict[str, Any]:
            """Worker function to insert a song with fingerprints."""
            try:
                with db_manager.get_session() as session:
                    song_repo = SongRepository(session)
                    fingerprint_repo = FingerprintRepository(session)
                    
                    # Create song
                    song = Song(
                        id=None,
                        title=f"Concurrent Song {worker_id}",
                        artist=f"Concurrent Artist {worker_id}",
                        duration_seconds=180
                    )
                    
                    created_song = song_repo.create_song(song)
                    
                    # Create fingerprints
                    fingerprints = []
                    for i in range(100):  # 100 fingerprints per song
                        fingerprints.append(Fingerprint(
                            hash_value=hash(f"concurrent_{worker_id}_{i}") & 0x7FFFFFFF,
                            time_offset_ms=i * 100
                        ))
                    
                    fingerprint_count = fingerprint_repo.create_fingerprints(
                        created_song.id, fingerprints
                    )
                    
                    return {
                        'worker_id': worker_id,
                        'song_id': created_song.id,
                        'fingerprint_count': fingerprint_count,
                        'success': True
                    }
            
            except Exception as e:
                return {
                    'worker_id': worker_id,
                    'error': str(e),
                    'success': False
                }
        
        def worker_query_fingerprints(worker_id: int) -> Dict[str, Any]:
            """Worker function to query fingerprints."""
            try:
                with db_manager.get_session() as session:
                    fingerprint_repo = FingerprintRepository(session)
                    match_repo = MatchRepository(session)
                    
                    # Create query fingerprints
                    query_fingerprints = []
                    for i in range(20):
                        query_fingerprints.append(Fingerprint(
                            hash_value=hash(f"query_{worker_id}_{i}") & 0x7FFFFFFF,
                            time_offset_ms=i * 100
                        ))
                    
                    # Perform query
                    matches = fingerprint_repo.find_matching_fingerprints(query_fingerprints)
                    
                    return {
                        'worker_id': worker_id,
                        'query_count': len(query_fingerprints),
                        'match_count': len(matches),
                        'success': True
                    }
            
            except Exception as e:
                return {
                    'worker_id': worker_id,
                    'error': str(e),
                    'success': False
                }
        
        # Test concurrent insertions
        insert_workers = 5
        query_workers = 3
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=insert_workers + query_workers) as executor:
            # Submit insert tasks
            insert_futures = [
                executor.submit(worker_insert_song, i) 
                for i in range(insert_workers)
            ]
            
            # Submit query tasks
            query_futures = [
                executor.submit(worker_query_fingerprints, i) 
                for i in range(query_workers)
            ]
            
            # Collect results
            insert_results = []
            query_results = []
            
            for future in as_completed(insert_futures):
                result = future.result()
                insert_results.append(result)
            
            for future in as_completed(query_futures):
                result = future.result()
                query_results.append(result)
        
        total_time = time.time() - start_time
        
        # Verify results
        successful_inserts = [r for r in insert_results if r['success']]
        successful_queries = [r for r in query_results if r['success']]
        
        assert len(successful_inserts) == insert_workers
        assert len(successful_queries) == query_workers
        assert total_time < 10.0  # Should complete within 10 seconds
        
        # Verify no errors occurred
        insert_errors = [r for r in insert_results if not r['success']]
        query_errors = [r for r in query_results if not r['success']]
        
        assert len(insert_errors) == 0, f"Insert errors: {insert_errors}"
        assert len(query_errors) == 0, f"Query errors: {query_errors}"
        
        print(f"Concurrent test completed in {total_time:.3f}s")
        print(f"Successful inserts: {len(successful_inserts)}")
        print(f"Successful queries: {len(successful_queries)}")
    
    def test_database_population_utilities(self, db_manager):
        """Test database population utilities."""
        # Test seeder functionality
        seeder = DatabaseSeeder()
        
        # Create sample songs
        start_time = time.time()
        result = seeder.seed_sample_songs(count=5)
        seeding_time = time.time() - start_time
        
        # Verify seeding results
        assert result['added_songs'] > 0
        assert result['total_fingerprints'] > 0
        assert seeding_time < 5.0  # Should complete within 5 seconds
        
        # Test populator functionality
        populator = DatabasePopulator()
        
        # Test adding individual song
        test_fingerprints = [
            Fingerprint(hash_value=12345, time_offset_ms=1000),
            Fingerprint(hash_value=67890, time_offset_ms=2000),
        ]
        
        song_id = populator.add_song_with_fingerprints(
            title="Population Test Song",
            artist="Population Test Artist",
            fingerprints=test_fingerprints,
            album="Test Album",
            duration_seconds=120
        )
        
        assert song_id is not None
        
        # Test duplicate detection
        duplicate_id = populator.add_song_with_fingerprints(
            title="Population Test Song",
            artist="Population Test Artist",
            fingerprints=test_fingerprints,
            skip_duplicates=True
        )
        
        assert duplicate_id is None  # Should be skipped as duplicate
        
        # Test statistics
        stats = populator.get_population_stats()
        assert 'total_songs' in stats
        assert 'total_fingerprints' in stats
        assert stats['total_songs'] > 0
        assert stats['total_fingerprints'] > 0
        
        print(f"Seeding time for 5 songs: {seeding_time:.3f}s")
        print(f"Database stats: {stats}")


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "-s"])