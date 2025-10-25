"""
Configuration management for the FastAPI application.
"""

import os
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    api_title: str = Field(default="Audio Fingerprinting API", env="API_TITLE")
    api_version: str = Field(default="1.0.0", env="API_VERSION")
    api_description: str = Field(
        default="API for audio fingerprinting and song identification",
        env="API_DESCRIPTION"
    )
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    debug: bool = Field(default=False, env="DEBUG")
    reload: bool = Field(default=False, env="RELOAD")
    
    # Security Configuration
    allowed_hosts: List[str] = Field(default=["*"], env="ALLOWED_HOSTS")
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    max_request_size: int = Field(default=10 * 1024 * 1024, env="MAX_REQUEST_SIZE")  # 10MB
    
    # Database Configuration
    database_url: str = Field(default="postgresql://localhost/audio_fingerprinting", env="DATABASE_URL")
    database_pool_size: int = Field(default=10, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")
    database_pool_timeout: int = Field(default=30, env="DATABASE_POOL_TIMEOUT")
    
    # Audio Processing Configuration
    max_audio_duration_ms: int = Field(default=30000, env="MAX_AUDIO_DURATION_MS")  # 30 seconds
    supported_audio_formats: List[str] = Field(
        default=["wav", "mp3", "flac", "m4a"],
        env="SUPPORTED_AUDIO_FORMATS"
    )
    audio_sample_rate: int = Field(default=44100, env="AUDIO_SAMPLE_RATE")
    
    # Fingerprinting Configuration
    fingerprint_confidence_threshold: float = Field(
        default=0.1,
        env="FINGERPRINT_CONFIDENCE_THRESHOLD"
    )
    max_fingerprint_matches: int = Field(default=1000, env="MAX_FINGERPRINT_MATCHES")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # Performance Configuration
    request_timeout_seconds: int = Field(default=30, env="REQUEST_TIMEOUT_SECONDS")
    audio_processing_timeout_seconds: int = Field(
        default=10,
        env="AUDIO_PROCESSING_TIMEOUT_SECONDS"
    )
    database_query_timeout_seconds: int = Field(
        default=5,
        env="DATABASE_QUERY_TIMEOUT_SECONDS"
    )
    
    # Admin Configuration
    admin_api_key: Optional[str] = Field(default=None, env="ADMIN_API_KEY")
    enable_admin_endpoints: bool = Field(default=True, env="ENABLE_ADMIN_ENDPOINTS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings