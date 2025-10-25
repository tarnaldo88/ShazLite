"""
FastAPI main application module.
Configures the FastAPI app with middleware, error handlers, and routing.
"""

import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog

from backend.api.models import ErrorResponse
from backend.api.middleware import (
    LoggingMiddleware, 
    TimingMiddleware, 
    SecurityHeadersMiddleware,
    RequestSizeLimitMiddleware
)
from backend.api.exceptions import AudioProcessingError, DatabaseError, ValidationError
from backend.api.config import get_settings


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting Audio Fingerprinting API server")
    
    # Initialize database connections, load models, etc.
    # This will be expanded when we implement the database integration
    
    yield
    
    # Shutdown
    logger.info("Shutting down Audio Fingerprinting API server")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    settings = get_settings()
    
    app = FastAPI(
        title=settings.api_title,
        description=settings.api_description,
        version=settings.api_version,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan
    )
    
    # Add middleware
    setup_middleware(app)
    
    # Add exception handlers
    setup_exception_handlers(app)
    
    # Add routes (will be implemented in subsequent tasks)
    setup_routes(app)
    
    return app


def setup_middleware(app: FastAPI) -> None:
    """Configure application middleware."""
    
    settings = get_settings()
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
    
    # Trusted host middleware for security
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_hosts
    )
    
    # Request size limit middleware
    app.add_middleware(
        RequestSizeLimitMiddleware,
        max_size=settings.max_request_size
    )
    
    # Security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Custom timing middleware
    app.add_middleware(TimingMiddleware)
    
    # Custom logging middleware
    app.add_middleware(LoggingMiddleware)


def setup_exception_handlers(app: FastAPI) -> None:
    """Configure global exception handlers."""
    
    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
        """Handle validation errors."""
        error_id = str(uuid.uuid4())
        logger.error(
            "Validation error",
            error_id=error_id,
            error_message=str(exc),
            path=request.url.path,
            method=request.method
        )
        
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error="validation_error",
                message=str(exc),
                error_id=error_id,
                timestamp=time.time()
            ).dict()
        )
    
    @app.exception_handler(AudioProcessingError)
    async def audio_processing_error_handler(request: Request, exc: AudioProcessingError) -> JSONResponse:
        """Handle audio processing errors."""
        error_id = str(uuid.uuid4())
        logger.error(
            "Audio processing error",
            error_id=error_id,
            error_message=str(exc),
            path=request.url.path,
            method=request.method
        )
        
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="audio_processing_error",
                message="Failed to process audio sample",
                error_id=error_id,
                timestamp=time.time()
            ).dict()
        )
    
    @app.exception_handler(DatabaseError)
    async def database_error_handler(request: Request, exc: DatabaseError) -> JSONResponse:
        """Handle database errors."""
        error_id = str(uuid.uuid4())
        logger.error(
            "Database error",
            error_id=error_id,
            error_message=str(exc),
            path=request.url.path,
            method=request.method
        )
        
        return JSONResponse(
            status_code=503,
            content=ErrorResponse(
                error="database_error",
                message="Database service temporarily unavailable",
                error_id=error_id,
                timestamp=time.time()
            ).dict(),
            headers={"Retry-After": "30"}
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle HTTP exceptions."""
        error_id = str(uuid.uuid4())
        logger.warning(
            "HTTP exception",
            error_id=error_id,
            status_code=exc.status_code,
            detail=exc.detail,
            path=request.url.path,
            method=request.method
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error="http_error",
                message=exc.detail,
                error_id=error_id,
                timestamp=time.time()
            ).dict()
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions."""
        error_id = str(uuid.uuid4())
        logger.error(
            "Unexpected error",
            error_id=error_id,
            error_type=type(exc).__name__,
            error_message=str(exc),
            path=request.url.path,
            method=request.method,
            exc_info=True
        )
        
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="internal_server_error",
                message="An unexpected error occurred",
                error_id=error_id,
                timestamp=time.time()
            ).dict()
        )


def setup_routes(app: FastAPI) -> None:
    """Configure application routes."""
    from backend.api.routes import identification
    
    # Include identification routes
    app.include_router(
        identification.router,
        prefix="/api/v1",
        tags=["identification"]
    )


# Create the application instance
app = create_app()