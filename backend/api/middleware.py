"""
Custom middleware for the FastAPI application.
"""

import time
import uuid
import asyncio
from typing import Callable, Optional

from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger()


class TimingMiddleware(BaseHTTPMiddleware):
    """Middleware to track request processing time."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and add timing information."""
        start_time = time.time()
        
        # Add request ID for tracking
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Process the request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        process_time_ms = int(process_time * 1000)
        
        # Add timing headers
        response.headers["X-Process-Time"] = str(process_time_ms)
        response.headers["X-Request-ID"] = request_id
        
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request/response logging."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response information."""
        start_time = time.time()
        
        # Get request ID from TimingMiddleware
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        # Log incoming request
        logger.info(
            "Request started",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            content_length=request.headers.get("content-length")
        )
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            process_time_ms = int(process_time * 1000)
            
            # Log response
            logger.info(
                "Request completed",
                request_id=request_id,
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                process_time_ms=process_time_ms,
                response_size=response.headers.get("content-length")
            )
            
            return response
            
        except Exception as exc:
            # Log error
            process_time = time.time() - start_time
            process_time_ms = int(process_time * 1000)
            
            logger.error(
                "Request failed",
                request_id=request_id,
                method=request.method,
                url=str(request.url),
                process_time_ms=process_time_ms,
                error_type=type(exc).__name__,
                error_message=str(exc),
                exc_info=True
            )
            
            # Re-raise the exception
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Add HSTS header for HTTPS
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to limit request body size."""
    
    def __init__(self, app, max_size: int = 10 * 1024 * 1024):  # 10MB default
        super().__init__(app)
        self.max_size = max_size
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check request size before processing."""
        content_length = request.headers.get("content-length")
        
        if content_length:
            content_length = int(content_length)
            if content_length > self.max_size:
                logger.warning(
                    "Request size limit exceeded",
                    content_length=content_length,
                    max_size=self.max_size,
                    url=str(request.url)
                )
                
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=413,
                    detail=f"Request body too large. Maximum size is {self.max_size} bytes."
                )
        
        return await call_next(request)


class TimeoutMiddleware(BaseHTTPMiddleware):
    """Middleware to handle request timeouts for long-running operations."""
    
    def __init__(self, app, timeout_seconds: int = 30):
        super().__init__(app)
        self.timeout_seconds = timeout_seconds
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with timeout handling."""
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        try:
            # Set timeout for the request processing
            response = await asyncio.wait_for(
                call_next(request),
                timeout=self.timeout_seconds
            )
            return response
            
        except asyncio.TimeoutError:
            logger.error(
                "Request timeout exceeded",
                request_id=request_id,
                timeout_seconds=self.timeout_seconds,
                method=request.method,
                url=str(request.url)
            )
            
            # Return timeout error response with tracking ID
            from fastapi.responses import JSONResponse
            from backend.api.models import ErrorResponse
            
            error_response = ErrorResponse(
                error="request_timeout",
                message=f"Request processing exceeded {self.timeout_seconds} seconds timeout",
                error_id=request_id,
                timestamp=time.time(),
                details={
                    "timeout_seconds": self.timeout_seconds,
                    "endpoint": str(request.url.path)
                }
            )
            
            return JSONResponse(
                status_code=408,
                content=error_response.dict(),
                headers={
                    "X-Request-ID": request_id,
                    "Retry-After": "60"
                }
            )


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Enhanced middleware for detailed performance monitoring and metrics collection."""
    
    def __init__(self, app):
        super().__init__(app)
        self.request_metrics = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Monitor request performance with detailed metrics."""
        start_time = time.time()
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        # Track memory usage before request
        import psutil
        import os
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Log detailed request start information
        logger.info(
            "Request performance monitoring started",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            path=request.url.path,
            query_params=dict(request.query_params),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            content_type=request.headers.get("content-type"),
            content_length=request.headers.get("content-length"),
            memory_before_mb=round(memory_before, 2)
        )
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate detailed performance metrics
            end_time = time.time()
            process_time = end_time - start_time
            process_time_ms = int(process_time * 1000)
            
            # Track memory usage after request
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_delta = memory_after - memory_before
            
            # Add performance headers to response
            response.headers["X-Process-Time-Ms"] = str(process_time_ms)
            response.headers["X-Memory-Delta-MB"] = str(round(memory_delta, 2))
            response.headers["X-Request-ID"] = request_id
            
            # Determine performance category
            if process_time_ms < 100:
                performance_category = "fast"
            elif process_time_ms < 1000:
                performance_category = "normal"
            elif process_time_ms < 5000:
                performance_category = "slow"
            else:
                performance_category = "very_slow"
            
            # Log detailed performance metrics
            logger.info(
                "Request performance monitoring completed",
                request_id=request_id,
                method=request.method,
                url=str(request.url),
                path=request.url.path,
                status_code=response.status_code,
                process_time_ms=process_time_ms,
                process_time_seconds=round(process_time, 3),
                performance_category=performance_category,
                memory_before_mb=round(memory_before, 2),
                memory_after_mb=round(memory_after, 2),
                memory_delta_mb=round(memory_delta, 2),
                response_size_bytes=response.headers.get("content-length"),
                response_content_type=response.headers.get("content-type")
            )
            
            # Store metrics for potential aggregation
            self._store_request_metrics(request, response, process_time_ms, memory_delta)
            
            return response
            
        except Exception as exc:
            # Calculate performance metrics for failed requests
            end_time = time.time()
            process_time = end_time - start_time
            process_time_ms = int(process_time * 1000)
            
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_delta = memory_after - memory_before
            
            # Log detailed error performance information
            logger.error(
                "Request performance monitoring failed",
                request_id=request_id,
                method=request.method,
                url=str(request.url),
                path=request.url.path,
                process_time_ms=process_time_ms,
                process_time_seconds=round(process_time, 3),
                memory_before_mb=round(memory_before, 2),
                memory_after_mb=round(memory_after, 2),
                memory_delta_mb=round(memory_delta, 2),
                error_type=type(exc).__name__,
                error_message=str(exc),
                exc_info=True
            )
            
            # Re-raise the exception
            raise
    
    def _store_request_metrics(self, request: Request, response: Response, 
                             process_time_ms: int, memory_delta: float) -> None:
        """Store request metrics for aggregation and monitoring."""
        endpoint = request.url.path
        method = request.method
        
        # Initialize endpoint metrics if not exists
        key = f"{method}:{endpoint}"
        if key not in self.request_metrics:
            self.request_metrics[key] = {
                "count": 0,
                "total_time_ms": 0,
                "min_time_ms": float('inf'),
                "max_time_ms": 0,
                "total_memory_delta_mb": 0,
                "status_codes": {},
                "last_updated": time.time()
            }
        
        # Update metrics
        metrics = self.request_metrics[key]
        metrics["count"] += 1
        metrics["total_time_ms"] += process_time_ms
        metrics["min_time_ms"] = min(metrics["min_time_ms"], process_time_ms)
        metrics["max_time_ms"] = max(metrics["max_time_ms"], process_time_ms)
        metrics["total_memory_delta_mb"] += memory_delta
        metrics["last_updated"] = time.time()
        
        # Track status codes
        status_code = str(response.status_code)
        metrics["status_codes"][status_code] = metrics["status_codes"].get(status_code, 0) + 1
        
        # Log aggregated metrics periodically (every 100 requests)
        if metrics["count"] % 100 == 0:
            avg_time_ms = metrics["total_time_ms"] / metrics["count"]
            avg_memory_mb = metrics["total_memory_delta_mb"] / metrics["count"]
            
            logger.info(
                "Endpoint performance summary",
                endpoint=key,
                request_count=metrics["count"],
                avg_time_ms=round(avg_time_ms, 2),
                min_time_ms=metrics["min_time_ms"],
                max_time_ms=metrics["max_time_ms"],
                avg_memory_delta_mb=round(avg_memory_mb, 2),
                status_codes=metrics["status_codes"]
            )
    
    def get_metrics_summary(self) -> dict:
        """Get current performance metrics summary."""
        summary = {}
        for endpoint, metrics in self.request_metrics.items():
            if metrics["count"] > 0:
                avg_time_ms = metrics["total_time_ms"] / metrics["count"]
                avg_memory_mb = metrics["total_memory_delta_mb"] / metrics["count"]
                
                summary[endpoint] = {
                    "request_count": metrics["count"],
                    "avg_response_time_ms": round(avg_time_ms, 2),
                    "min_response_time_ms": metrics["min_time_ms"],
                    "max_response_time_ms": metrics["max_time_ms"],
                    "avg_memory_delta_mb": round(avg_memory_mb, 2),
                    "status_codes": metrics["status_codes"],
                    "last_updated": metrics["last_updated"]
                }
        
        return summary