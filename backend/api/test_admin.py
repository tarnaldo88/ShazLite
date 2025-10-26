"""
Tests for administrative endpoints.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from io import BytesIO

# Mock all database imports to avoid dependency issues
with patch.dict('sys.modules', {
    'psycopg2': Mock(),
    'backend.database.connection': Mock(),
    'backend.database.repositories': Mock(),
    'backend.database.population_utils': Mock(),
    'backend.database.models': Mock(),
    'backend.models.song': Mock(),
    'backend.models.audio': Mock(),
    'backend.models.match': Mock(),
    'audio_engine.fingerprint_api': Mock(),
}):
    from backend.api.routes.admin import router
    from backend.api.config import Settings


@pytest.fixture
def test_settings():
    """Create test settings."""
    return Settings(
        debug=True,
        enable_admin_endpoints=True,
        admin_api_key="test-admin-key",
        max_request_size=10 * 1024 * 1024,
        supported_audio_formats=["wav", "mp3", "flac", "m4a"]
    )


@pytest.fixture
def client(test_settings):
    """Create test client with mocked dependencies."""
    app = FastAPI()
    
    # Mock the dependency
    def mock_get_settings():
        return test_settings
    
    # Override the dependency
    from backend.api.routes.admin import get_settings, verify_admin_access
    app.dependency_overrides[get_settings] = mock_get_settings
    
    # Include the admin router
    app.include_router(router, prefix="/api/v1/admin")
    
    return TestClient(app)


@pytest.fixture
def admin_headers():
    """Headers with admin API key."""
    return {"X-API-Key": "test-admin-key"}


@pytest.fixture
def sample_wav_file():
    """Create a minimal WAV file for testing."""
    # Create a minimal WAV file (44 bytes header + some audio data)
    wav_header = b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x08\x00\x00'
    audio_data = b'\x00\x00' * 1000  # 1000 samples of silence
    return wav_header + audio_data


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check_success(self, client):
        """Test successful health check."""
        with patch('backend.database.connection.get_db_session') as mock_db, \
             patch('audio_engine.fingerprint_api.get_engine') as mock_engine:
            
            # Mock database session and repository
            mock_session = Mock()
            mock_db.return_value.__enter__.return_value = mock_session
            
            mock_match_repo = Mock()
            mock_match_repo.get_database_stats.return_value = {
                'total_songs': 100,
                'total_fingerprints': 5000
            }
            
            with patch('backend.database.repositories.MatchRepository', return_value=mock_match_repo):
                # Mock audio engine
                mock_engine_instance = Mock()
                mock_engine_instance.get_engine_info.return_value = {
                    'version': '1.0.0',
                    'engine': 'test'
                }
                mock_engine.return_value = mock_engine_instance
                
                response = client.get("/api/v1/admin/health")
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "healthy"
                assert "timestamp" in data
                assert "version" in data
                assert "components" in data
                assert data["components"]["database"] == "healthy"
                assert data["components"]["audio_engine"] == "healthy"
    
    def test_health_check_database_error(self, client):
        """Test health check with database error."""
        with patch('backend.database.connection.get_db_session') as mock_db:
            # Mock database connection failure
            mock_db.side_effect = Exception("Database connection failed")
            
            with patch('audio_engine.fingerprint_api.get_engine') as mock_engine:
                mock_engine_instance = Mock()
                mock_engine_instance.get_engine_info.return_value = {'version': '1.0.0'}
                mock_engine.return_value = mock_engine_instance
                
                response = client.get("/api/v1/admin/health")
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "unhealthy"
                assert data["components"]["database"] == "unhealthy"
                assert "database_error" in data["components"]


class TestAddSongEndpoint:
    """Test add reference song endpoint."""
    
    def test_add_song_success(self, client, admin_headers, sample_wav_file):
        """Test successful song addition."""
        with patch('backend.database.population_utils.DatabasePopulator') as mock_populator_class, \
             patch('audio_engine.fingerprint_api.get_engine') as mock_engine:
            
            # Mock fingerprint generation
            mock_engine_instance = Mock()
            mock_fingerprint_result = Mock()
            mock_fingerprint_result.count = 100
            mock_fingerprint_result.hash_values = [12345] * 100
            mock_fingerprint_result.time_offsets = list(range(0, 10000, 100))
            mock_fingerprint_result.anchor_frequencies = [440.0] * 100
            mock_fingerprint_result.target_frequencies = [880.0] * 100
            mock_fingerprint_result.time_deltas = [100] * 100
            
            mock_engine_instance.generate_fingerprint.return_value = mock_fingerprint_result
            mock_engine.return_value = mock_engine_instance
            
            # Mock database populator
            mock_populator = Mock()
            mock_populator.add_song_with_fingerprints.return_value = 123  # Song ID
            mock_populator_class.return_value = mock_populator
            
            # Prepare form data
            files = {"audio_file": ("test.wav", BytesIO(sample_wav_file), "audio/wav")}
            data = {
                "title": "Test Song",
                "artist": "Test Artist",
                "album": "Test Album",
                "duration_seconds": 180
            }
            
            response = client.post(
                "/api/v1/admin/add-song",
                files=files,
                data=data,
                headers=admin_headers
            )
            
            assert response.status_code == 200
            result = response.json()
            assert result["success"] is True
            assert result["song_id"] == 123
            assert result["fingerprint_count"] == 100
            assert "processing_time_ms" in result
            assert "request_id" in result
    
    def test_add_song_unauthorized(self, client, sample_wav_file):
        """Test add song without admin key."""
        files = {"audio_file": ("test.wav", BytesIO(sample_wav_file), "audio/wav")}
        data = {"title": "Test Song", "artist": "Test Artist"}
        
        response = client.post("/api/v1/admin/add-song", files=files, data=data)
        
        assert response.status_code == 401
        assert "Invalid or missing admin API key" in response.json()["detail"]
    
    def test_add_song_validation_error(self, client, admin_headers, sample_wav_file):
        """Test add song with validation errors."""
        files = {"audio_file": ("test.wav", BytesIO(sample_wav_file), "audio/wav")}
        data = {"title": "", "artist": "Test Artist"}  # Empty title
        
        response = client.post(
            "/api/v1/admin/add-song",
            files=files,
            data=data,
            headers=admin_headers
        )
        
        assert response.status_code == 400
        assert "Title and artist are required" in response.json()["detail"]
    
    def test_add_song_duplicate(self, client, admin_headers, sample_wav_file):
        """Test adding duplicate song."""
        with patch('backend.database.population_utils.DatabasePopulator') as mock_populator_class, \
             patch('audio_engine.fingerprint_api.get_engine') as mock_engine:
            
            # Mock fingerprint generation
            mock_engine_instance = Mock()
            mock_fingerprint_result = Mock()
            mock_fingerprint_result.count = 50
            mock_fingerprint_result.hash_values = [12345] * 50
            mock_fingerprint_result.time_offsets = list(range(0, 5000, 100))
            mock_fingerprint_result.anchor_frequencies = [440.0] * 50
            mock_fingerprint_result.target_frequencies = [880.0] * 50
            mock_fingerprint_result.time_deltas = [100] * 50
            
            mock_engine_instance.generate_fingerprint.return_value = mock_fingerprint_result
            mock_engine.return_value = mock_engine_instance
            
            # Mock database populator returning None (duplicate)
            mock_populator = Mock()
            mock_populator.add_song_with_fingerprints.return_value = None
            mock_populator_class.return_value = mock_populator
            
            files = {"audio_file": ("test.wav", BytesIO(sample_wav_file), "audio/wav")}
            data = {"title": "Existing Song", "artist": "Existing Artist"}
            
            response = client.post(
                "/api/v1/admin/add-song",
                files=files,
                data=data,
                headers=admin_headers
            )
            
            assert response.status_code == 200
            result = response.json()
            assert result["success"] is False
            assert result["song_id"] is None
            assert "already exists" in result["message"]


class TestBatchProcessEndpoint:
    """Test batch processing endpoint."""
    
    def test_batch_populate_database(self, client, admin_headers):
        """Test database population batch operation."""
        with patch('backend.database.population_utils.DatabaseSeeder') as mock_seeder_class:
            # Mock seeder
            mock_seeder = Mock()
            mock_seeder.seed_sample_songs.return_value = {
                'added_songs': 10,
                'skipped_duplicates': 2,
                'failed_songs': 0,
                'total_fingerprints': 500
            }
            mock_seeder_class.return_value = mock_seeder
            
            request_data = {
                "operation": "populate_database",
                "parameters": {"song_count": 10}
            }
            
            response = client.post(
                "/api/v1/admin/batch-process",
                json=request_data,
                headers=admin_headers
            )
            
            assert response.status_code == 200
            result = response.json()
            assert result["success"] is True
            assert result["operation"] == "populate_database"
            assert result["items_processed"] == 10
            assert "Added 10 songs" in result["message"]
    
    def test_batch_rebuild_index(self, client, admin_headers):
        """Test index rebuild batch operation."""
        request_data = {
            "operation": "rebuild_index",
            "parameters": {}
        }
        
        response = client.post(
            "/api/v1/admin/batch-process",
            json=request_data,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["operation"] == "rebuild_index"
        assert "rebuilt" in result["message"]
    
    def test_batch_cleanup_duplicates(self, client, admin_headers):
        """Test duplicate cleanup batch operation."""
        request_data = {
            "operation": "cleanup_duplicates",
            "parameters": {}
        }
        
        response = client.post(
            "/api/v1/admin/batch-process",
            json=request_data,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["operation"] == "cleanup_duplicates"
        assert "cleanup" in result["message"]
    
    def test_batch_invalid_operation(self, client, admin_headers):
        """Test invalid batch operation."""
        request_data = {
            "operation": "invalid_operation",
            "parameters": {}
        }
        
        response = client.post(
            "/api/v1/admin/batch-process",
            json=request_data,
            headers=admin_headers
        )
        
        assert response.status_code == 400
        assert "Unknown batch operation" in response.json()["detail"]
    
    def test_batch_unauthorized(self, client):
        """Test batch operation without admin key."""
        request_data = {
            "operation": "populate_database",
            "parameters": {"song_count": 5}
        }
        
        response = client.post("/api/v1/admin/batch-process", json=request_data)
        
        assert response.status_code == 401
        assert "Invalid or missing admin API key" in response.json()["detail"]


class TestAdminEndpointsDisabled:
    """Test behavior when admin endpoints are disabled."""
    
    def test_endpoints_disabled(self):
        """Test that admin endpoints return 404 when disabled."""
        disabled_settings = Settings(
            debug=True,
            enable_admin_endpoints=False
        )
        
        with patch('backend.api.config.get_settings', return_value=disabled_settings):
            app = create_app()
            client = TestClient(app)
            
            # Test health endpoint
            response = client.get("/api/v1/admin/health")
            assert response.status_code == 404
            assert "disabled" in response.json()["detail"]
            
            # Test add song endpoint
            response = client.post("/api/v1/admin/add-song")
            assert response.status_code == 404
            assert "disabled" in response.json()["detail"]
            
            # Test batch process endpoint
            response = client.post("/api/v1/admin/batch-process")
            assert response.status_code == 404
            assert "disabled" in response.json()["detail"]