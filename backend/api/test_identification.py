"""
Tests for the audio identification endpoint.
"""

import pytest
import io
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.models.audio import Fingerprint
from backend.models.match import MatchResult


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    # Mock the database connection to avoid psycopg2 dependency
    with patch('backend.database.connection.psycopg2'), \
         patch('backend.database.connection.sqlalchemy'):
        from backend.api.main import create_app
        app = create_app()
        return TestClient(app)


@pytest.fixture
def sample_audio_file():
    """Create a sample WAV file for testing."""
    # Create a minimal WAV file header + some audio data
    wav_header = b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x02\x00\x44\xac\x00\x00\x10\xb1\x02\x00\x04\x00\x10\x00data\x00\x08\x00\x00'
    audio_data = b'\x00\x00' * 1000  # 1000 samples of silence
    return wav_header + audio_data


def test_identify_endpoint_exists(client):
    """Test that the identify endpoint exists and accepts POST requests."""
    # Test without file (should return 422 for missing required field)
    response = client.post("/api/v1/identify")
    assert response.status_code == 422


@patch('backend.api.routes.identification.get_engine')
@patch('backend.api.routes.identification.get_db_session')
def test_identify_audio_success(mock_db_session, mock_get_engine, client, sample_audio_file):
    """Test successful audio identification."""
    # Mock the audio engine
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
    
    # Mock the database session and match repository
    mock_session = MagicMock()
    mock_match_repo = MagicMock()
    mock_match_result = MatchResult(
        song_id=1,
        title="Test Song",
        artist="Test Artist",
        album="Test Album",
        confidence=0.85,
        match_count=10,
        time_offset_ms=5000
    )
    mock_match_repo.find_best_match.return_value = mock_match_result
    
    # Mock the context manager
    mock_db_session.return_value.__enter__.return_value = mock_session
    mock_db_session.return_value.__exit__.return_value = None
    
    with patch('backend.api.routes.identification.MatchRepository', return_value=mock_match_repo):
        # Make request with audio file
        files = {"audio_file": ("test.wav", io.BytesIO(sample_audio_file), "audio/wav")}
        response = client.post("/api/v1/identify", files=files)
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["match"]["title"] == "Test Song"
    assert data["match"]["artist"] == "Test Artist"
    assert data["match"]["confidence"] == 0.85
    assert "request_id" in data
    assert "processing_time_ms" in data


@patch('backend.api.routes.identification.get_engine')
@patch('backend.api.routes.identification.get_db_session')
def test_identify_audio_no_match(mock_db_session, mock_get_engine, client, sample_audio_file):
    """Test audio identification when no match is found."""
    # Mock the audio engine
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
    
    # Mock the database session with no match
    mock_session = MagicMock()
    mock_match_repo = MagicMock()
    mock_match_repo.find_best_match.return_value = None
    
    mock_db_session.return_value.__enter__.return_value = mock_session
    mock_db_session.return_value.__exit__.return_value = None
    
    with patch('backend.api.routes.identification.MatchRepository', return_value=mock_match_repo):
        files = {"audio_file": ("test.wav", io.BytesIO(sample_audio_file), "audio/wav")}
        response = client.post("/api/v1/identify", files=files)
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is False
    assert data["match"] is None
    assert "No matching song found" in data["message"]


def test_identify_audio_invalid_file_type(client):
    """Test audio identification with invalid file type."""
    # Create a text file instead of audio
    text_content = b"This is not an audio file"
    files = {"audio_file": ("test.txt", io.BytesIO(text_content), "text/plain")}
    
    response = client.post("/api/v1/identify", files=files)
    assert response.status_code == 400


def test_identify_audio_empty_file(client):
    """Test audio identification with empty file."""
    files = {"audio_file": ("empty.wav", io.BytesIO(b""), "audio/wav")}
    
    response = client.post("/api/v1/identify", files=files)
    assert response.status_code == 500  # Should be processed as audio processing error


@patch('backend.api.routes.identification.get_engine')
def test_identify_audio_engine_error(mock_get_engine, client, sample_audio_file):
    """Test audio identification when engine fails."""
    # Mock engine to raise an exception
    mock_engine = MagicMock()
    mock_engine.generate_fingerprint.side_effect = Exception("Engine failed")
    mock_get_engine.return_value = mock_engine
    
    files = {"audio_file": ("test.wav", io.BytesIO(sample_audio_file), "audio/wav")}
    response = client.post("/api/v1/identify", files=files)
    
    assert response.status_code == 500


if __name__ == "__main__":
    pytest.main([__file__])