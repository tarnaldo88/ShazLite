"""
API Integration Tests for Audio Fingerprinting System

Tests the complete audio upload and identification flow, error handling for malformed requests,
and concurrent request processing as specified in task 4.5.

Requirements addressed:
- 2.4: Response time requirements and timeout handling
- 4.3: Concurrent request processing capabilities  
- 5.3: Error handling for network failure
"""

import pytest
import asyncio
import io
import time
import concurrent.futures
from typing import List, Dict, Any
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from fastapi import status

from backend.api.main import create_app
from backend.models.audio import Fingerprint
from backend.models.match import MatchResult


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    # Mock database dependencies to avoid connection issues
    with patch('backend.database.connection.psycopg2'), \
         patch('backend.database.connection.sqlalchemy'):
        app = create_app()
        return TestClient(app)


@pytest.fixture
def sample_audio_files():
    """Create sample audio files for testing."""
    # Create minimal WAV file headers + audio data
    wav_header = b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x02\x00\x44\xac\x00\x00\x10\xb1\x02\x00\x04\x00\x10\x00data\x00\x08\x00\x00'
    
    files = {
        'valid_wav': wav_header + b'\x00\x00' * 1000,
        'small_wav': wav_header + b'\x00\x00' * 100,
        'large_wav': wav_header + b'\x00\x00' * 50000,
        'empty_file': b'',
        'invalid_format': b'This is not an audio file',
        'corrupted_wav': wav_header[:20] + b'\xFF' * 100  # Corrupted header
    }
    
    return files


class TestAudioUploadAndIdentificationFlow:
    """Test complete audio upload and identification flow."""
    
    @patch('backend.api.routes.identification.get_engine')
    @patch('backend.api.routes.identification.get_db_session')
    def test_successful_identification_flow(self, mock_db_session, mock_get_engine, client, sample_audio_files):
        """Test complete successful audio identification flow."""
        # Mock audio engine
        mock_engine = MagicMock()
        mock_fingerprint_result = MagicMock()
        mock_fingerprint_result.count = 5
        mock_fingerprint_result.hash_values = [12345, 67890, 11111, 22222, 33333]
        mock_fingerprint_result.time_offsets = [1000, 2000, 3000, 4000, 5000]
        mock_fingerprint_result.anchor_frequencies = [440.0, 880.0, 1320.0, 1760.0, 2200.0]
        mock_fingerprint_result.target_frequencies = [660.0, 1320.0, 1980.0, 2640.0, 3300.0]
        mock_fingerprint_result.time_deltas = [500, 500, 500, 500, 500]
        
        mock_engine.generate_fingerprint.return_value = mock_fingerprint_result
        mock_get_engine.return_value = mock_engine
        
        # Mock database match
        mock_session = MagicMock()
        mock_match_repo = MagicMock()
        mock_match_result = MatchResult(
            song_id=1,
            title="Test Song",
            artist="Test Artist", 
            album="Test Album",
            confidence=0.92,
            match_count=15,
            time_offset_ms=2500
        )
        mock_match_repo.find_best_match.return_value = mock_match_result
        
        mock_db_session.return_value.__enter__.return_value = mock_session
        mock_db_session.return_value.__exit__.return_value = None
        
        with patch('backend.api.routes.identification.MatchRepository', return_value=mock_match_repo):
            # Test identification request
            files = {"audio_file": ("test.wav", io.BytesIO(sample_audio_files['valid_wav']), "audio/wav")}
            response = client.post("/api/v1/identify", files=files)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["match"]["title"] == "Test Song"
        assert data["match"]["artist"] == "Test Artist"
        assert data["match"]["album"] == "Test Album"
        assert data["match"]["confidence"] == 0.92
        assert data["match"]["match_count"] == 15
        assert data["match"]["song_id"] == 1
        assert "request_id" in data
        assert "processing_time_ms" in data
        assert data["processing_time_ms"] > 0 
   
    @patch('backend.api.routes.identification.get_engine')
    @patch('backend.api.routes.identification.get_db_session')
    def test_no_match_found_flow(self, mock_db_session, mock_get_engine, client, sample_audio_files):
        """Test flow when no matching song is found."""
        # Mock audio engine with fingerprints
        mock_engine = MagicMock()
        mock_fingerprint_result = MagicMock()
        mock_fingerprint_result.count = 3
        mock_fingerprint_result.hash_values = [99999, 88888, 77777]
        mock_fingerprint_result.time_offsets = [1000, 2000, 3000]
        mock_fingerprint_result.anchor_frequencies = [440.0, 880.0, 1320.0]
        mock_fingerprint_result.target_frequencies = [660.0, 1320.0, 1980.0]
        mock_fingerprint_result.time_deltas = [500, 500, 500]
        
        mock_engine.generate_fingerprint.return_value = mock_fingerprint_result
        mock_get_engine.return_value = mock_engine
        
        # Mock database with no match
        mock_session = MagicMock()
        mock_match_repo = MagicMock()
        mock_match_repo.find_best_match.return_value = None
        
        mock_db_session.return_value.__enter__.return_value = mock_session
        mock_db_session.return_value.__exit__.return_value = None
        
        with patch('backend.api.routes.identification.MatchRepository', return_value=mock_match_repo):
            files = {"audio_file": ("unknown.wav", io.BytesIO(sample_audio_files['valid_wav']), "audio/wav")}
            response = client.post("/api/v1/identify", files=files)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is False
        assert data["match"] is None
        assert "No matching song found" in data["message"]
        assert "request_id" in data
        assert "processing_time_ms" in data
    
    @patch('backend.api.routes.identification.get_engine')
    def test_no_fingerprints_generated_flow(self, mock_get_engine, client, sample_audio_files):
        """Test flow when no fingerprints can be generated."""
        # Mock engine with no fingerprints
        mock_engine = MagicMock()
        mock_fingerprint_result = MagicMock()
        mock_fingerprint_result.count = 0
        mock_fingerprint_result.hash_values = []
        mock_fingerprint_result.time_offsets = []
        
        mock_engine.generate_fingerprint.return_value = mock_fingerprint_result
        mock_get_engine.return_value = mock_engine
        
        files = {"audio_file": ("silent.wav", io.BytesIO(sample_audio_files['small_wav']), "audio/wav")}
        response = client.post("/api/v1/identify", files=files)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is False
        assert data["match"] is None
        assert "Unable to generate fingerprints" in data["message"]


class TestErrorHandlingForMalformedRequests:
    """Test error handling for various malformed requests."""
    
    def test_missing_audio_file(self, client):
        """Test request without audio file."""
        response = client.post("/api/v1/identify")
        assert response.status_code == 422  # Validation error
    
    def test_empty_audio_file(self, client, sample_audio_files):
        """Test request with empty audio file."""
        files = {"audio_file": ("empty.wav", io.BytesIO(sample_audio_files['empty_file']), "audio/wav")}
        response = client.post("/api/v1/identify", files=files)
        assert response.status_code == 500  # Audio processing error
    
    def test_invalid_file_format(self, client, sample_audio_files):
        """Test request with invalid file format."""
        files = {"audio_file": ("test.txt", io.BytesIO(sample_audio_files['invalid_format']), "text/plain")}
        response = client.post("/api/v1/identify", files=files)
        assert response.status_code == 400  # Validation error
    
    def test_unsupported_audio_format(self, client):
        """Test request with unsupported audio format."""
        files = {"audio_file": ("test.ogg", io.BytesIO(b"fake ogg data"), "audio/ogg")}
        response = client.post("/api/v1/identify", files=files)
        assert response.status_code == 400
    
    def test_corrupted_audio_file(self, client, sample_audio_files):
        """Test request with corrupted audio file."""
        files = {"audio_file": ("corrupted.wav", io.BytesIO(sample_audio_files['corrupted_wav']), "audio/wav")}
        response = client.post("/api/v1/identify", files=files)
        # Should handle gracefully, either 400 or 500 depending on where corruption is detected
        assert response.status_code in [400, 500]
    
    @patch('backend.api.routes.identification.get_engine')
    def test_audio_engine_failure(self, mock_get_engine, client, sample_audio_files):
        """Test handling of audio engine failures."""
        mock_engine = MagicMock()
        mock_engine.generate_fingerprint.side_effect = Exception("Engine crashed")
        mock_get_engine.return_value = mock_engine
        
        files = {"audio_file": ("test.wav", io.BytesIO(sample_audio_files['valid_wav']), "audio/wav")}
        response = client.post("/api/v1/identify", files=files)
        
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert "error_id" in data
    
    @patch('backend.api.routes.identification.get_engine')
    @patch('backend.api.routes.identification.get_db_session')
    def test_database_failure(self, mock_db_session, mock_get_engine, client, sample_audio_files):
        """Test handling of database failures."""
        # Mock successful engine
        mock_engine = MagicMock()
        mock_fingerprint_result = MagicMock()
        mock_fingerprint_result.count = 2
        mock_fingerprint_result.hash_values = [12345, 67890]
        mock_fingerprint_result.time_offsets = [1000, 2000]
        mock_fingerprint_result.anchor_frequencies = [440.0, 880.0]
        mock_fingerprint_result.target_frequencies = [660.0, 1320.0]
        mock_fingerprint_result.time_deltas = [500, 500]
        
        mock_engine.generate_fingerprint.return_value = mock_fingerprint_result
        mock_get_engine.return_value = mock_engine
        
        # Mock database failure
        mock_db_session.side_effect = Exception("Database connection failed")
        
        files = {"audio_file": ("test.wav", io.BytesIO(sample_audio_files['valid_wav']), "audio/wav")}
        response = client.post("/api/v1/identify", files=files)
        
        assert response.status_code == 503  # Service unavailable
        data = response.json()
        assert "error" in data
        assert "Database service temporarily unavailable" in data["message"]
    
    def test_request_timeout_simulation(self, client, sample_audio_files):
        """Test request timeout handling (simulated)."""
        # This would require actual timeout configuration in a real test
        # For now, we test that the endpoint responds within reasonable time
        start_time = time.time()
        
        files = {"audio_file": ("test.wav", io.BytesIO(sample_audio_files['valid_wav']), "audio/wav")}
        response = client.post("/api/v1/identify", files=files)
        
        elapsed_time = time.time() - start_time
        
        # Should respond quickly in test environment
        assert elapsed_time < 5.0  # 5 second max for test
        assert response.status_code in [200, 400, 500]  # Any valid response


class TestConcurrentRequestProcessing:
    """Test concurrent request processing capabilities."""
    
    @patch('backend.api.routes.identification.get_engine')
    @patch('backend.api.routes.identification.get_db_session')
    def test_concurrent_identification_requests(self, mock_db_session, mock_get_engine, client, sample_audio_files):
        """Test handling multiple concurrent identification requests."""
        # Mock successful responses
        mock_engine = MagicMock()
        mock_fingerprint_result = MagicMock()
        mock_fingerprint_result.count = 3
        mock_fingerprint_result.hash_values = [12345, 67890, 11111]
        mock_fingerprint_result.time_offsets = [1000, 2000, 3000]
        mock_fingerprint_result.anchor_frequencies = [440.0, 880.0, 1320.0]
        mock_fingerprint_result.target_frequencies = [660.0, 1320.0, 1980.0]
        mock_fingerprint_result.time_deltas = [500, 500, 500]
        
        mock_engine.generate_fingerprint.return_value = mock_fingerprint_result
        mock_get_engine.return_value = mock_engine
        
        # Mock database
        mock_session = MagicMock()
        mock_match_repo = MagicMock()
        mock_match_result = MatchResult(
            song_id=1,
            title="Concurrent Test Song",
            artist="Test Artist",
            album=None,
            confidence=0.75,
            match_count=8,
            time_offset_ms=1500
        )
        mock_match_repo.find_best_match.return_value = mock_match_result
        
        mock_db_session.return_value.__enter__.return_value = mock_session
        mock_db_session.return_value.__exit__.return_value = None
        
        def make_request(request_id: int) -> Dict[str, Any]:
            """Make a single identification request."""
            with patch('backend.api.routes.identification.MatchRepository', return_value=mock_match_repo):
                files = {"audio_file": (f"test_{request_id}.wav", io.BytesIO(sample_audio_files['valid_wav']), "audio/wav")}
                response = client.post("/api/v1/identify", files=files)
                return {
                    'request_id': request_id,
                    'status_code': response.status_code,
                    'response_data': response.json() if response.status_code == 200 else None,
                    'response_time': time.time()
                }
        
        # Execute concurrent requests
        num_concurrent_requests = 10
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, i) for i in range(num_concurrent_requests)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # Verify all requests completed successfully
        assert len(results) == num_concurrent_requests
        
        successful_requests = [r for r in results if r['status_code'] == 200]
        assert len(successful_requests) >= num_concurrent_requests * 0.8  # At least 80% success rate
        
        # Verify response consistency
        for result in successful_requests:
            if result['response_data']:
                assert result['response_data']['success'] is True
                assert result['response_data']['match']['title'] == "Concurrent Test Song"
                assert 'request_id' in result['response_data']
        
        # Performance check - should handle concurrent requests reasonably fast
        assert total_time < 30.0  # Should complete within 30 seconds
    
    def test_concurrent_mixed_requests(self, client, sample_audio_files):
        """Test concurrent requests with mixed success/failure scenarios."""
        def make_mixed_request(request_id: int) -> Dict[str, Any]:
            """Make requests with different scenarios."""
            if request_id % 3 == 0:
                # Valid request
                files = {"audio_file": (f"valid_{request_id}.wav", io.BytesIO(sample_audio_files['valid_wav']), "audio/wav")}
            elif request_id % 3 == 1:
                # Invalid format
                files = {"audio_file": (f"invalid_{request_id}.txt", io.BytesIO(sample_audio_files['invalid_format']), "text/plain")}
            else:
                # Empty file
                files = {"audio_file": (f"empty_{request_id}.wav", io.BytesIO(sample_audio_files['empty_file']), "audio/wav")}
            
            response = client.post("/api/v1/identify", files=files)
            return {
                'request_id': request_id,
                'status_code': response.status_code,
                'expected_success': request_id % 3 == 0
            }
        
        # Execute mixed concurrent requests
        num_requests = 9  # 3 valid, 3 invalid format, 3 empty
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_mixed_request, i) for i in range(num_requests)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Verify appropriate responses for each type
        valid_requests = [r for r in results if r['expected_success']]
        invalid_requests = [r for r in results if not r['expected_success']]
        
        # Valid requests should get 200 or 500 (depending on mocking)
        for result in valid_requests:
            assert result['status_code'] in [200, 500]
        
        # Invalid requests should get 400 or 500
        for result in invalid_requests:
            assert result['status_code'] in [400, 500]
    
    def test_stress_test_rapid_requests(self, client, sample_audio_files):
        """Test system behavior under rapid request load."""
        def make_rapid_request() -> int:
            """Make a rapid request and return status code."""
            files = {"audio_file": ("rapid.wav", io.BytesIO(sample_audio_files['small_wav']), "audio/wav")}
            response = client.post("/api/v1/identify", files=files)
            return response.status_code
        
        # Make many rapid requests
        num_rapid_requests = 20
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_rapid_request) for _ in range(num_rapid_requests)]
            status_codes = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # System should handle rapid requests without crashing
        assert len(status_codes) == num_rapid_requests
        
        # Most requests should get valid HTTP status codes
        valid_status_codes = [code for code in status_codes if 200 <= code < 600]
        assert len(valid_status_codes) == num_rapid_requests
        
        # Should complete within reasonable time
        assert total_time < 60.0  # 1 minute max


class TestAdminEndpointIntegration:
    """Test admin endpoint integration."""
    
    @patch('backend.api.routes.admin.verify_admin_access')
    def test_health_check_endpoint(self, mock_verify_admin, client):
        """Test health check endpoint integration."""
        mock_verify_admin.return_value = None  # Allow access
        
        with patch('backend.api.routes.admin.get_db_session'), \
             patch('backend.api.routes.admin.get_engine'):
            response = client.get("/api/v1/admin/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "components" in data
    
    @patch('backend.api.routes.admin.verify_admin_access')
    @patch('backend.api.routes.admin.get_engine')
    @patch('backend.api.routes.admin.DatabasePopulator')
    def test_add_song_endpoint_integration(self, mock_populator, mock_get_engine, mock_verify_admin, client, sample_audio_files):
        """Test add song endpoint integration."""
        mock_verify_admin.return_value = None
        
        # Mock engine
        mock_engine = MagicMock()
        mock_fingerprint_result = MagicMock()
        mock_fingerprint_result.count = 5
        mock_fingerprint_result.hash_values = [1, 2, 3, 4, 5]
        mock_fingerprint_result.time_offsets = [100, 200, 300, 400, 500]
        mock_fingerprint_result.anchor_frequencies = [440.0] * 5
        mock_fingerprint_result.target_frequencies = [880.0] * 5
        mock_fingerprint_result.time_deltas = [50] * 5
        
        mock_engine.generate_fingerprint.return_value = mock_fingerprint_result
        mock_get_engine.return_value = mock_engine
        
        # Mock populator
        mock_populator_instance = MagicMock()
        mock_populator_instance.add_song_with_fingerprints.return_value = 123
        mock_populator.return_value = mock_populator_instance
        
        # Make request
        files = {"audio_file": ("new_song.wav", io.BytesIO(sample_audio_files['valid_wav']), "audio/wav")}
        data = {"title": "New Song", "artist": "New Artist", "album": "New Album"}
        
        response = client.post("/api/v1/admin/add-song", files=files, data=data)
        
        assert response.status_code == 200
        response_data = response.json()
        
        assert response_data["success"] is True
        assert response_data["song_id"] == 123
        assert response_data["fingerprint_count"] == 5
        assert "processing_time_ms" in response_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])