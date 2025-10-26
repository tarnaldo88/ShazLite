"""
FastAPI main application module.
Configures the FastAPI app with middleware, error handlers, and routing.
"""

import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog

from backend.api.models import ErrorResponse
from backend.api.middleware import (
    LoggingMiddleware, 
    TimingMiddleware, 
    SecurityHeadersMiddleware,
    RequestSizeLimitMiddleware,
    TimeoutMiddleware,
    PerformanceMonitoringMiddleware
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
    app.state.start_time = time.time()
    logger.info("Starting Audio Fingerprinting API server", start_time=app.state.start_time)
    
    # Initialize database connections, load models, etc.
    # This will be expanded when we implement the database integration
    
    yield
    
    # Shutdown
    uptime = time.time() - app.state.start_time
    logger.info("Shutting down Audio Fingerprinting API server", uptime_seconds=uptime)


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
    
    # Request timeout middleware (must be early in the chain)
    app.add_middleware(
        TimeoutMiddleware,
        timeout_seconds=settings.request_timeout_seconds
    )
    
    # Request size limit middleware
    app.add_middleware(
        RequestSizeLimitMiddleware,
        max_size=settings.max_request_size
    )
    
    # Security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Performance monitoring middleware (should be after timing)
    app.add_middleware(PerformanceMonitoringMiddleware)
    
    # Custom timing middleware
    app.add_middleware(TimingMiddleware)
    
    # Custom logging middleware (should be last for complete request info)
    app.add_middleware(LoggingMiddleware)


def setup_exception_handlers(app: FastAPI) -> None:
    """Configure global exception handlers."""
    
    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
        """Handle validation errors with detailed tracking."""
        error_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        # Extract additional error details
        error_details = {
            "endpoint": request.url.path,
            "method": request.method,
            "query_params": dict(request.query_params),
            "error_type": type(exc).__name__
        }
        
        # Add exception-specific details if available
        if hasattr(exc, 'details') and exc.details:
            error_details.update(exc.details)
        
        logger.error(
            "Validation error with tracking",
            error_id=error_id,
            error_message=str(exc),
            path=request.url.path,
            method=request.method,
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            error_details=error_details
        )
        
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error="validation_error",
                message=str(exc),
                error_id=error_id,
                timestamp=time.time(),
                details=error_details
            ).dict(),
            headers={"X-Request-ID": error_id}
        )
    
    @app.exception_handler(AudioProcessingError)
    async def audio_processing_error_handler(request: Request, exc: AudioProcessingError) -> JSONResponse:
        """Handle audio processing errors with detailed tracking."""
        error_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        # Extract detailed error information
        error_details = {
            "endpoint": request.url.path,
            "method": request.method,
            "error_type": type(exc).__name__,
            "processing_stage": "audio_fingerprinting"
        }
        
        # Add exception-specific details if available
        if hasattr(exc, 'details') and exc.details:
            error_details.update(exc.details)
        
        # Add file information if available in request
        if hasattr(request.state, 'file_info'):
            error_details["file_info"] = request.state.file_info
        
        logger.error(
            "Audio processing error with tracking",
            error_id=error_id,
            error_message=str(exc),
            path=request.url.path,
            method=request.method,
            client_ip=request.client.host if request.client else None,
            content_type=request.headers.get("content-type"),
            content_length=request.headers.get("content-length"),
            error_details=error_details,
            exc_info=True
        )
        
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="audio_processing_error",
                message="Failed to process audio sample. Please check the audio format and try again.",
                error_id=error_id,
                timestamp=time.time(),
                details=error_details
            ).dict(),
            headers={
                "X-Request-ID": error_id,
                "Retry-After": "10"
            }
        )
    
    @app.exception_handler(DatabaseError)
    async def database_error_handler(request: Request, exc: DatabaseError) -> JSONResponse:
        """Handle database errors with detailed tracking."""
        error_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        # Extract detailed error information
        error_details = {
            "endpoint": request.url.path,
            "method": request.method,
            "error_type": type(exc).__name__,
            "service": "database"
        }
        
        # Add exception-specific details if available
        if hasattr(exc, 'details') and exc.details:
            error_details.update(exc.details)
        
        # Determine retry strategy based on error type
        retry_after = "30"
        if "timeout" in str(exc).lower():
            retry_after = "10"
        elif "connection" in str(exc).lower():
            retry_after = "60"
        
        logger.error(
            "Database error with tracking",
            error_id=error_id,
            error_message=str(exc),
            path=request.url.path,
            method=request.method,
            client_ip=request.client.host if request.client else None,
            retry_after_seconds=retry_after,
            error_details=error_details,
            exc_info=True
        )
        
        return JSONResponse(
            status_code=503,
            content=ErrorResponse(
                error="database_error",
                message="Database service temporarily unavailable. Please try again later.",
                error_id=error_id,
                timestamp=time.time(),
                details=error_details
            ).dict(),
            headers={
                "X-Request-ID": error_id,
                "Retry-After": retry_after
            }
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle HTTP exceptions with detailed tracking."""
        error_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        # Extract detailed error information
        error_details = {
            "endpoint": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
            "error_type": "HTTPException"
        }
        
        # Add headers if they exist in the exception
        if hasattr(exc, 'headers') and exc.headers:
            error_details["response_headers"] = exc.headers
        
        # Determine log level based on status code
        if exc.status_code >= 500:
            log_level = "error"
        elif exc.status_code >= 400:
            log_level = "warning"
        else:
            log_level = "info"
        
        getattr(logger, log_level)(
            "HTTP exception with tracking",
            error_id=error_id,
            status_code=exc.status_code,
            detail=exc.detail,
            path=request.url.path,
            method=request.method,
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            error_details=error_details
        )
        
        # Prepare response headers
        response_headers = {"X-Request-ID": error_id}
        if hasattr(exc, 'headers') and exc.headers:
            response_headers.update(exc.headers)
        
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error="http_error",
                message=exc.detail,
                error_id=error_id,
                timestamp=time.time(),
                details=error_details
            ).dict(),
            headers=response_headers
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions with comprehensive tracking."""
        error_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        # Extract comprehensive error information
        error_details = {
            "endpoint": request.url.path,
            "method": request.method,
            "error_type": type(exc).__name__,
            "error_module": getattr(type(exc), '__module__', 'unknown'),
            "query_params": dict(request.query_params),
            "headers": dict(request.headers)
        }
        
        # Add request body info if available (be careful with sensitive data)
        if request.headers.get("content-type"):
            error_details["content_type"] = request.headers.get("content-type")
            error_details["content_length"] = request.headers.get("content-length")
        
        # Add exception-specific details if available
        if hasattr(exc, '__dict__'):
            # Filter out potentially sensitive information
            safe_attrs = {k: v for k, v in exc.__dict__.items() 
                         if not k.startswith('_') and isinstance(v, (str, int, float, bool, list, dict))}
            if safe_attrs:
                error_details["exception_attributes"] = safe_attrs
        
        logger.error(
            "Unexpected error with comprehensive tracking",
            error_id=error_id,
            error_type=type(exc).__name__,
            error_message=str(exc),
            path=request.url.path,
            method=request.method,
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            content_type=request.headers.get("content-type"),
            content_length=request.headers.get("content-length"),
            error_details=error_details,
            exc_info=True
        )
        
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="internal_server_error",
                message="An unexpected error occurred. Please contact support if the problem persists.",
                error_id=error_id,
                timestamp=time.time(),
                details=error_details
            ).dict(),
            headers={
                "X-Request-ID": error_id,
                "X-Error-Type": type(exc).__name__
            }
        )


def setup_routes(app: FastAPI) -> None:
    """Configure application routes."""
    from backend.api.routes import identification, admin
    
    # Include identification routes
    app.include_router(
        identification.router,
        prefix="/api/v1",
        tags=["identification"]
    )
    
    # Include admin routes
    app.include_router(
        admin.router,
        prefix="/api/v1/admin",
        tags=["administration"]
    )
    
    # Add performance metrics endpoint
    @app.get("/api/v1/admin/metrics", tags=["administration"])
    async def get_performance_metrics(
        _: None = Depends(lambda: None)  # Would use admin verification in production
    ):
        """
        Get current performance metrics and monitoring data.
        
        Returns detailed performance statistics for all endpoints including
        response times, memory usage, and request counts.
        """
        # Find the performance monitoring middleware instance
        performance_middleware = None
        for middleware in app.user_middleware:
            if hasattr(middleware, 'cls') and middleware.cls.__name__ == 'PerformanceMonitoringMiddleware':
                # Get the actual middleware instance from the stack
                # This is a simplified approach - in production you'd want a cleaner way to access this
                break
        
        # For now, return a basic metrics structure
        # In a real implementation, you'd access the actual middleware instance
        metrics_summary = {
            "timestamp": time.time(),
            "server_info": {
                "uptime_seconds": time.time() - app.state.start_time if hasattr(app.state, 'start_time') else None,
                "version": get_settings().api_version
            },
            "endpoints": {
                "note": "Detailed endpoint metrics would be available from PerformanceMonitoringMiddleware instance"
            },
            "system": {
                "memory_usage_mb": "Available via psutil in middleware",
                "cpu_usage_percent": "Available via psutil monitoring"
            }
        }
        
        return metrics_summary


# Create the application instance
app = create_app()