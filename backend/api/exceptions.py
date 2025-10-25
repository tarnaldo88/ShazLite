"""
Custom exception classes for the audio fingerprinting API.
"""


class AudioFingerprintingException(Exception):
    """Base exception class for audio fingerprinting errors."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(AudioFingerprintingException):
    """Exception raised for input validation errors."""
    pass


class AudioProcessingError(AudioFingerprintingException):
    """Exception raised for audio processing errors."""
    pass


class DatabaseError(AudioFingerprintingException):
    """Exception raised for database operation errors."""
    pass


class FingerprintGenerationError(AudioProcessingError):
    """Exception raised when fingerprint generation fails."""
    pass


class AudioFormatError(ValidationError):
    """Exception raised for unsupported audio formats."""
    pass


class AudioSizeError(ValidationError):
    """Exception raised when audio file size is invalid."""
    pass


class EngineError(AudioProcessingError):
    """Exception raised when the C++ audio engine fails."""
    pass


class MatchingError(DatabaseError):
    """Exception raised during fingerprint matching operations."""
    pass


class ConfigurationError(AudioFingerprintingException):
    """Exception raised for configuration-related errors."""
    pass