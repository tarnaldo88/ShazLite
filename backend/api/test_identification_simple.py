"""
Simple tests for the audio identification endpoint functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
from backend.api.routes.identification import (
    validate_audio_file, 
    convert_audio_to_numpy,
    AudioSample
)
from backend.api.exceptions import AudioFormatError, AudioSizeError
from backend.api.config import Settings


def test_validate_audio_file_success():
    """Test successful audio file validation."""
    # Mock upload file
    mock_file = MagicMock()
    mock_file.size = 1000000  # 1MB
    mock_file.content_type = "audio/wav"
    mock_file.filename = "test.wav"
    
    # Mock settings
    settings = MagicMock()
    settings.max_request_size = 10000000  # 10MB
    settings.supported_audio_formats = ["wav", "mp3", "flac", "m4a"]
    
    # Should not raise any exception
    validate_audio_file(mock_file, settings)


def test_validate_audio_file_too_large():
    """Test audio file validation with file too large."""
    mock_file = MagicMock()
    mock_file.size = 20000000  # 20MB
    mock_file.content_type = "audio/wav"
    mock_file.filename = "test.wav"
    
    settings = MagicMock()
    settings.max_request_size = 10000000  # 10MB
    settings.supported_audio_formats = ["wav", "mp3", "flac", "m4a"]
    
    with pytest.raises(AudioSizeError):
        validate_audio_file(mock_file, settings)


def test_validate_audio_file_invalid_format():
    """Test audio file validation with invalid format."""
    mock_file = MagicMock()
    mock_file.size = 1000000
    mock_file.content_type = "text/plain"
    mock_file.filename = "test.txt"
    
    settings = MagicMock()
    settings.max_request_size = 10000000
    settings.supported_audio_formats = ["wav", "mp3", "flac", "m4a"]
    
    with pytest.raises(AudioFormatError):
        validate_audio_file(mock_file, settings)


def test_convert_audio_to_numpy():
    """Test audio conversion to numpy array."""
    # Create a simple WAV file structure
    wav_header = b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x02\x00\x44\xac\x00\x00\x10\xb1\x02\x00\x04\x00\x10\x00data\x00\x08\x00\x00'
    audio_data = b'\x00\x00' * 1000  # 1000 samples of silence
    
    audio_sample = AudioSample(
        data=wav_header + audio_data,
        sample_rate=44100,
        channels=2,
        duration_ms=1000,
        format="wav"
    )
    
    result = convert_audio_to_numpy(audio_sample)
    
    # Should return a numpy array
    import numpy as np
    assert isinstance(result, np.ndarray)
    assert result.dtype == np.float32


if __name__ == "__main__":
    pytest.main([__file__])