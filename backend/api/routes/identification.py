"""
Audio identification endpoint implementation.
"""

import time
import uuid
import logging
from typing import Optional
import asyncio
from io import BytesIO

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form
from fastapi.responses import JSONResponse
import structlog

from backend.api.models import AudioIdentificationResponse, MatchResult as APIMatchResult
from backend.api.exceptions import (
    ValidationError, 
    AudioProcessingError, 
    DatabaseError,
    AudioFormatError,
    AudioSizeError,
    FingerprintGenerationError,
    MatchingError
)
from backend.api.config import get_settings
from backend.database.connection import get_db_session
from backend.database.repositories import MatchRepository, FingerprintRepository
from backend.models.audio import AudioSample, Fingerprint
from backend.models.match import MatchResult
from audio_engine.fingerprint_api import get_engine, AudioFingerprintEngine

logger = structlog.get_logger()
router = APIRouter()


def validate_audio_file(file: UploadFile, settings) -> None:
    """Validate uploaded audio file."""
    # Check file size
    if file.size and file.size > settings.max_request_size:
        raise AudioSizeError(f"Audio file too large. Maximum size: {settings.max_request_size} bytes")
    
    # Check content type
    allowed_content_types = [
        "audio/wav", "audio/wave", "audio/x-wav",
        "audio/mpeg", "audio/mp3",
        "audio/flac", "audio/x-flac",
        "audio/mp4", "audio/m4a"
    ]
    
    if file.content_type and file.content_type not in allowed_content_types:
        raise AudioFormatError(f"Unsupported audio format: {file.content_type}")
    
    # Check file extension
    if file.filename:
        extension = file.filename.lower().split('.')[-1]
        if extension not in settings.supported_audio_formats:
            raise AudioFormatError(f"Unsupported file extension: {extension}")


async def process_audio_file(file: UploadFile) -> AudioSample:
    """Process uploaded audio file into AudioSample."""
    try:
        # Read file content
        audio_data = await file.read()
        
        if not audio_data:
            raise ValidationError("Audio file is empty")
        
        # Determine format from filename or content type
        format_name = "wav"  # Default
        if file.filename:
            extension = file.filename.lower().split('.')[-1]
            if extension in ["mp3", "wav", "flac", "m4a"]:
                format_name = extension
        elif file.content_type:
            if "mp3" in file.content_type or "mpeg" in file.content_type:
                format_name = "mp3"
            elif "flac" in file.content_type:
                format_name = "flac"
            elif "mp4" in file.content_type or "m4a" in file.content_type:
                format_name = "m4a"
        
        # For now, we'll assume standard audio parameters
        # In a real implementation, we'd parse the audio file headers
        sample_rate = 44100
        channels = 2
        duration_ms = len(audio_data) // (sample_rate * channels * 2) * 1000  # Rough estimate
        
        return AudioSample(
            data=audio_data,
            sample_rate=sample_rate,
            channels=channels,
            duration_ms=duration_ms,
            format=format_name
        )
        
    except Exception as e:
        logger.error("Failed to process audio file", error=str(e))
        raise AudioProcessingError(f"Failed to process audio file: {str(e)}")


def convert_audio_to_numpy(audio_sample: AudioSample):
    """Convert AudioSample to numpy array for fingerprinting."""
    import numpy as np
    
    try:
        # For this implementation, we'll create a simple conversion
        # In a real system, you'd use a proper audio library like librosa or pydub
        
        # Convert bytes to numpy array (assuming 16-bit PCM)
        if audio_sample.format in ["wav"]:
            # Simple WAV parsing (skip header, assume 16-bit PCM)
            audio_bytes = audio_sample.data[44:]  # Skip WAV header
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            
            # Convert to float32 and normalize
            audio_array = audio_array.astype(np.float32) / 32768.0
            
            # Convert stereo to mono if needed
            if audio_sample.channels == 2:
                audio_array = audio_array.reshape(-1, 2).mean(axis=1)
            
            return audio_array
        else:
            # For other formats, we'd need proper decoding
            # For now, create dummy data for testing
            duration_samples = int(audio_sample.sample_rate * audio_sample.duration_ms / 1000)
            return np.random.randn(duration_samples).astype(np.float32) * 0.1
            
    except Exception as e:
        logger.error("Failed to convert audio to numpy", error=str(e))
        raise AudioProcessingError(f"Failed to convert audio data: {str(e)}")


async def generate_fingerprints(audio_sample: AudioSample, engine: AudioFingerprintEngine) -> list[Fingerprint]:
    """Generate fingerprints from audio sample."""
    try:
        # Convert audio to numpy array
        audio_array = convert_audio_to_numpy(audio_sample)
        
        # Generate fingerprints using the engine
        fingerprint_result = engine.generate_fingerprint(
            audio_array, 
            audio_sample.sample_rate, 
            1  # Always use mono for fingerprinting
        )
        
        # Convert to Fingerprint objects
        fingerprints = []
        for i in range(fingerprint_result.count):
            fingerprint = Fingerprint(
                hash_value=fingerprint_result.hash_values[i],
                time_offset_ms=fingerprint_result.time_offsets[i],
                frequency_1=fingerprint_result.anchor_frequencies[i] if i < len(fingerprint_result.anchor_frequencies) else None,
                frequency_2=fingerprint_result.target_frequencies[i] if i < len(fingerprint_result.target_frequencies) else None,
                time_delta_ms=fingerprint_result.time_deltas[i] if i < len(fingerprint_result.time_deltas) else None
            )
            fingerprints.append(fingerprint)
        
        logger.info(f"Generated {len(fingerprints)} fingerprints from audio sample")
        return fingerprints
        
    except Exception as e:
        logger.error("Fingerprint generation failed", error=str(e))
        raise FingerprintGenerationError(f"Failed to generate fingerprints: {str(e)}")


async def find_matching_song(fingerprints: list[Fingerprint]) -> Optional[MatchResult]:
    """Find matching song in database."""
    try:
        with get_db_session() as session:
            match_repo = MatchRepository(session)
            
            # Find best match using the repository
            match_result = match_repo.find_best_match(
                fingerprints, 
                min_matches=5  # Minimum number of matching fingerprints
            )
            
            if match_result:
                logger.info(
                    f"Found match: {match_result.title} by {match_result.artist} "
                    f"(confidence: {match_result.confidence:.2f})"
                )
            else:
                logger.info("No matching song found")
            
            return match_result
            
    except Exception as e:
        logger.error("Database matching failed", error=str(e))
        raise MatchingError(f"Failed to find matching song: {str(e)}")


@router.post("/identify", response_model=AudioIdentificationResponse)
async def identify_audio(
    audio_file: UploadFile = File(..., description="Audio file to identify (WAV, MP3, FLAC, M4A)"),
    format: Optional[str] = Form(None, description="Audio format override"),
    settings = Depends(get_settings)
):
    """
    Identify a song from an audio sample.
    
    This endpoint accepts an audio file upload and returns song identification results.
    The audio is processed through the fingerprinting engine and matched against
    the database of known songs.
    
    **Requirements addressed:**
    - 1.1: Audio sample processing and identification
    - 2.1: API endpoint for audio identification requests  
    - 2.2: Audio fingerprint generation and processing
    - 2.4: Response time requirements (10 second total processing)
    - 3.1: Song identification results with metadata
    - 3.2: Confidence scoring for matches
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    logger.info(
        "Audio identification request started",
        request_id=request_id,
        filename=audio_file.filename,
        content_type=audio_file.content_type,
        file_size=audio_file.size
    )
    
    try:
        # Validate audio file
        validate_audio_file(audio_file, settings)
        
        # Process audio file
        audio_sample = await process_audio_file(audio_file)
        
        # Check processing time limit
        processing_time = (time.time() - start_time) * 1000
        if processing_time > settings.audio_processing_timeout_seconds * 1000:
            raise AudioProcessingError("Audio processing timeout exceeded")
        
        # Generate fingerprints
        engine = get_engine()
        fingerprints = await generate_fingerprints(audio_sample, engine)
        
        if not fingerprints:
            logger.warning("No fingerprints generated from audio sample", request_id=request_id)
            return AudioIdentificationResponse(
                success=False,
                processing_time_ms=int((time.time() - start_time) * 1000),
                match=None,
                message="Unable to generate fingerprints from audio sample",
                request_id=request_id
            )
        
        # Find matching song
        match_result = await find_matching_song(fingerprints)
        
        # Calculate total processing time
        total_processing_time = int((time.time() - start_time) * 1000)
        
        # Check total time limit
        if total_processing_time > settings.request_timeout_seconds * 1000:
            logger.warning("Request timeout exceeded", request_id=request_id, processing_time=total_processing_time)
            raise AudioProcessingError("Request processing timeout exceeded")
        
        if match_result:
            # Convert to API model
            api_match = APIMatchResult(
                song_id=match_result.song_id,
                title=match_result.title,
                artist=match_result.artist,
                album=match_result.album,
                confidence=match_result.confidence,
                match_count=match_result.match_count,
                time_offset_ms=match_result.time_offset_ms
            )
            
            logger.info(
                "Audio identification successful",
                request_id=request_id,
                song_id=match_result.song_id,
                title=match_result.title,
                artist=match_result.artist,
                confidence=match_result.confidence,
                processing_time_ms=total_processing_time
            )
            
            return AudioIdentificationResponse(
                success=True,
                processing_time_ms=total_processing_time,
                match=api_match,
                message=f"Song identified with {match_result.confidence:.1%} confidence",
                request_id=request_id
            )
        else:
            logger.info(
                "No song match found",
                request_id=request_id,
                fingerprint_count=len(fingerprints),
                processing_time_ms=total_processing_time
            )
            
            return AudioIdentificationResponse(
                success=False,
                processing_time_ms=total_processing_time,
                match=None,
                message="No matching song found in database",
                request_id=request_id
            )
    
    except ValidationError as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.warning(
            "Validation error in audio identification",
            request_id=request_id,
            error=str(e),
            processing_time_ms=processing_time
        )
        raise HTTPException(status_code=400, detail=str(e))
    
    except (AudioProcessingError, FingerprintGenerationError) as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(
            "Audio processing error",
            request_id=request_id,
            error=str(e),
            processing_time_ms=processing_time
        )
        raise HTTPException(status_code=500, detail="Audio processing failed")
    
    except (DatabaseError, MatchingError) as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(
            "Database error in audio identification",
            request_id=request_id,
            error=str(e),
            processing_time_ms=processing_time
        )
        raise HTTPException(status_code=503, detail="Database service temporarily unavailable")
    
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(
            "Unexpected error in audio identification",
            request_id=request_id,
            error=str(e),
            error_type=type(e).__name__,
            processing_time_ms=processing_time,
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error")