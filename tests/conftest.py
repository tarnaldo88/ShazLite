"""
Pytest configuration and fixtures for end-to-end testing.
"""

import pytest
import asyncio
import tempfile
import os
import numpy as np
from typing import Generator, Dict, Any
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import application components
from backend.api.main import create_app
from backend.database.connection import get_db_session
from backend.database.models import Base
from backend.database.population_utils import DatabaseSeeder


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_database_url():
    """Create a temporary test database URL."""
    # Use SQLite for testing
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    db_url = f"sqlite:///{temp_db.name}"
    yield db_url
    
    # Cleanup
    try:
        os.unlink(temp_db.name)
    except OSError:
        pass


@pytest.fixture(scope="session")
def test_engine(test_database_url):
    """Create test database engine."""
    engine = create_engine(test_database_url, connect_args={"check_same_thread": False})
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="session")
def test_session_factory(test_engine):
    """Create test database session factory."""
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture
def test_session(test_session_factory):
    """Create a test database session."""
    session = test_session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="session")
def test_app(test_database_url):
    """Create test FastAPI application."""
    # Override database URL for testing
    os.environ["DATABASE_URL"] = test_database_url
    os.environ["TESTING"] = "true"
    
    app = create_app()
    yield app
    
    # Cleanup environment
    os.environ.pop("DATABASE_URL", None)
    os.environ.pop("TESTING", None)


@pytest.fixture(scope="session")
def test_client(test_app):
    """Create test client for API requests."""
    with TestClient(test_app) as client:
        yield client


@pytest.fixture(scope="session")
def sample_audio_data():
    """Generate sample audio data for testing."""
    sample_rate = 44100
    duration = 5.0  # 5 seconds
    frequency = 440.0  # A4 note
    
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio_data = np.sin(2 * np.pi * frequency * t).astype(np.float32)
    
    return {
        "data": audio_data,
        "sample_rate": sample_rate,
        "duration": duration,
        "frequency": frequency
    }


@pytest.fixture(scope="session")
def reference_songs_data():
    """Generate reference songs data for testing."""
    songs = []
    
    # Create different test songs with distinct characteristics
    sample_rate = 44100
    duration = 10.0  # 10 seconds
    
    for i, (title, artist, frequency) in enumerate([
        ("Test Song A", "Test Artist 1", 440.0),  # A4
        ("Test Song B", "Test Artist 2", 523.25),  # C5
        ("Test Song C", "Test Artist 1", 659.25),  # E5
        ("Test Song D", "Test Artist 3", 783.99),  # G5
        ("Test Song E", "Test Artist 2", 880.0),   # A5
    ]):
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # Create more complex waveforms for better fingerprinting
        audio_data = (
            np.sin(2 * np.pi * frequency * t) +
            0.5 * np.sin(2 * np.pi * frequency * 2 * t) +  # Second harmonic
            0.25 * np.sin(2 * np.pi * frequency * 3 * t)   # Third harmonic
        ).astype(np.float32)
        
        songs.append({
            "id": i + 1,
            "title": title,
            "artist": artist,
            "album": f"Test Album {i + 1}",
            "duration_seconds": int(duration),
            "audio_data": audio_data,
            "sample_rate": sample_rate,
            "frequency": frequency
        })
    
    return songs


@pytest.fixture
def populated_database(test_session, reference_songs_data):
    """Populate test database with reference songs."""
    # Override the database session for the seeder
    original_get_session = get_db_session
    
    def mock_get_session():
        return test_session
    
    # Temporarily replace the session getter
    import backend.database.connection
    backend.database.connection.get_db_session = mock_get_session
    
    try:
        seeder = DatabaseSeeder()
        
        # Add reference songs to database
        for song_data in reference_songs_data:
            # This would normally use the seeder to add songs with fingerprints
            # For now, we'll add basic song records
            from backend.database.models import Song
            
            song = Song(
                title=song_data["title"],
                artist=song_data["artist"],
                album=song_data["album"],
                duration_seconds=song_data["duration_seconds"]
            )
            test_session.add(song)
        
        test_session.commit()
        
        yield test_session
        
    finally:
        # Restore original session getter
        backend.database.connection.get_db_session = original_get_session


@pytest.fixture
def test_audio_files(sample_audio_data, tmp_path):
    """Create temporary audio files for testing."""
    files = {}
    
    # Create WAV file
    wav_file = tmp_path / "test_audio.wav"
    
    # Simple WAV file creation (44-byte header + audio data)
    audio_data = sample_audio_data["data"]
    sample_rate = sample_audio_data["sample_rate"]
    
    # Convert float32 to int16
    audio_int16 = (audio_data * 32767).astype(np.int16)
    
    # Create minimal WAV header
    wav_header = bytearray(44)
    wav_header[0:4] = b'RIFF'
    wav_header[8:12] = b'WAVE'
    wav_header[12:16] = b'fmt '
    wav_header[16:20] = (16).to_bytes(4, 'little')  # PCM format chunk size
    wav_header[20:22] = (1).to_bytes(2, 'little')   # PCM format
    wav_header[22:24] = (1).to_bytes(2, 'little')   # Mono
    wav_header[24:28] = sample_rate.to_bytes(4, 'little')  # Sample rate
    wav_header[28:32] = (sample_rate * 2).to_bytes(4, 'little')  # Byte rate
    wav_header[32:34] = (2).to_bytes(2, 'little')   # Block align
    wav_header[34:36] = (16).to_bytes(2, 'little')  # Bits per sample
    wav_header[36:40] = b'data'
    wav_header[40:44] = (len(audio_int16) * 2).to_bytes(4, 'little')  # Data size
    
    # Update RIFF chunk size
    total_size = 36 + len(audio_int16) * 2
    wav_header[4:8] = total_size.to_bytes(4, 'little')
    
    # Write WAV file
    with open(wav_file, 'wb') as f:
        f.write(wav_header)
        f.write(audio_int16.tobytes())
    
    files['wav'] = str(wav_file)
    
    # Create a dummy MP3 file (just for format testing)
    mp3_file = tmp_path / "test_audio.mp3"
    with open(mp3_file, 'wb') as f:
        # Write minimal MP3 header (not a real MP3, just for testing)
        f.write(b'\xff\xfb\x90\x00')  # MP3 sync word and header
        f.write(audio_int16.tobytes())
    
    files['mp3'] = str(mp3_file)
    
    return files


@pytest.fixture
def performance_test_config():
    """Configuration for performance testing."""
    return {
        "concurrent_users": 10,
        "requests_per_user": 5,
        "max_response_time_ms": 10000,  # 10 seconds as per requirements
        "fingerprint_timeout_ms": 5000,  # 5 seconds for fingerprinting
        "database_timeout_ms": 3000,     # 3 seconds for database search
    }