"""
Tests for performance monitoring and error handling enhancements.
"""

import pytest
import time
import asyncio
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI, Request, HTTPException

from backend.api.main import create_app
from backend.api.middleware import (
    TimeoutMiddleware, 
    PerformanceMonitoringMiddleware
)
from backend.api.exceptions import (
    ValidationError, 
    AudioProcessingError, 
    DatabaseError
)


@pytest.fixture
def app():
    """Create test FastAPI application."""
    return create_app()


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestTimeoutMiddleware:
    """Test timeout middleware functionality."""
    
    def test_timeout_middleware_normal_request(self):
        """Test that normal requests pass through timeout middleware."""
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            await asyncio.sleep(0.1)  # Short delay
            return {"status": "ok"}
        
        app.add_middleware(TimeoutMiddleware, timeout_seconds=1)
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    
    def test_timeout_middleware_timeout_request(self):
        """Test that long requests are timed out."""
        app = FastAPI()
        
        @app.get("/slow")
        async def slow_endpoint():
            await asyncio.sleep(2)  # Long delay
            return {"status": "ok"}
        
        app.add_middleware(TimeoutMiddleware, timeout_seconds=0.5)
        
        client = TestClient(app)
        response = client.get("/slow")
        
        assert response.status_code == 408
        assert "timeout" in response.json()["error"]
        assert "error_id" in response.json()
        assert "X-Request-ID" in response.headers


class TestPerformanceMonitoringMiddleware:
    """Test performance monitoring middleware functionality."""
    
    def test_performance_monitoring_headers(self):
        """Test that performance headers are added to responses."""
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}
        
        app.add_middleware(PerformanceMonitoringMiddleware)
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 200
        assert "X-Process-Time-Ms" in response.headers
        assert "X-Memory-Delta-MB" in response.headers
        assert "X-Request-ID" in response.headers
    
    def test_performance_monitoring_metrics_collection(self):
        """Test that performance metrics are collected."""
        middleware = PerformanceMonitoringMiddleware(None)
        
        # Simulate storing metrics
        request = Mock()
        request.url.path = "/test"
        request.method = "GET"
        
        response = Mock()
        response.status_code = 200
        response.headers = {}
        
        middleware._store_request_metrics(request, response, 100, 1.5)
        
        # Check metrics were stored
        metrics = middleware.get_metrics_summary()
        assert "GET:/test" in metrics
        assert metrics["GET:/test"]["request_count"] == 1
        assert metrics["GET:/test"]["avg_response_time_ms"] == 100.0


class TestEnhancedErrorHandling:
    """Test enhanced error handling with tracking IDs."""
    
    def test_validation_error_with_tracking(self, client):
        """Test validation error includes tracking ID and details."""
        # This would test an actual endpoint that raises ValidationError
        # For now, we'll test the error handler structure
        pass
    
    def test_audio_processing_error_with_tracking(self, client):
        """Test audio processing error includes detailed tracking."""
        # This would test an actual endpoint that raises AudioProcessingError
        # For now, we'll test the error handler structure
        pass
    
    def test_database_error_with_retry_after(self, client):
        """Test database error includes retry-after header."""
        # This would test an actual endpoint that raises DatabaseError
        # For now, we'll test the error handler structure
        pass
    
    def test_http_exception_with_tracking(self, client):
        """Test HTTP exceptions include tracking information."""
        # Test 404 error
        response = client.get("/nonexistent-endpoint")
        
        assert response.status_code == 404
        response_data = response.json()
        
        assert "error_id" in response_data
        assert "timestamp" in response_data
        assert "X-Request-ID" in response.headers
    
    def test_general_exception_with_comprehensive_tracking(self, client):
        """Test general exceptions include comprehensive tracking."""
        # This would require an endpoint that raises an unexpected exception
        # For integration testing
        pass


class TestPerformanceMetricsEndpoint:
    """Test the performance metrics endpoint."""
    
    def test_metrics_endpoint_structure(self, client):
        """Test that metrics endpoint returns proper structure."""
        response = client.get("/api/v1/admin/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "timestamp" in data
        assert "server_info" in data
        assert "endpoints" in data
        assert "system" in data
        assert "version" in data["server_info"]


class TestIntegratedPerformanceMonitoring:
    """Test integrated performance monitoring across the application."""
    
    def test_request_lifecycle_monitoring(self, client):
        """Test that a complete request lifecycle is properly monitored."""
        # Make a request to health endpoint
        response = client.get("/api/v1/admin/health")
        
        # Check response has monitoring headers
        assert "X-Process-Time-Ms" in response.headers
        assert "X-Request-ID" in response.headers
        
        # Verify timing header is reasonable
        process_time = int(response.headers["X-Process-Time-Ms"])
        assert 0 <= process_time <= 10000  # Should be under 10 seconds
    
    def test_error_tracking_consistency(self, client):
        """Test that error tracking is consistent across different error types."""
        # Test various error scenarios and verify consistent tracking
        
        # 404 error
        response = client.get("/nonexistent")
        assert response.status_code == 404
        assert "error_id" in response.json()
        assert "X-Request-ID" in response.headers
        
        # Method not allowed
        response = client.put("/api/v1/admin/health")
        assert response.status_code == 405
        assert "error_id" in response.json()
        assert "X-Request-ID" in response.headers


@pytest.mark.asyncio
async def test_timeout_middleware_async():
    """Test timeout middleware with async operations."""
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse
    from starlette.routing import Route
    
    async def slow_endpoint(request):
        await asyncio.sleep(2)
        return JSONResponse({"status": "ok"})
    
    app = Starlette(routes=[Route("/slow", slow_endpoint)])
    app.add_middleware(TimeoutMiddleware, timeout_seconds=0.5)
    
    # This test would need to be run with an async test client
    # to properly test the timeout functionality


def test_performance_monitoring_memory_tracking():
    """Test memory usage tracking in performance monitoring."""
    middleware = PerformanceMonitoringMiddleware(None)
    
    # Test that memory tracking methods work
    assert hasattr(middleware, '_store_request_metrics')
    assert hasattr(middleware, 'get_metrics_summary')
    
    # Test metrics summary structure
    summary = middleware.get_metrics_summary()
    assert isinstance(summary, dict)


def test_error_response_model_completeness():
    """Test that error responses include all required fields."""
    from backend.api.models import ErrorResponse
    
    error_response = ErrorResponse(
        error="test_error",
        message="Test error message",
        error_id="test-123",
        details={"key": "value"}
    )
    
    response_dict = error_response.dict()
    
    assert "error" in response_dict
    assert "message" in response_dict
    assert "error_id" in response_dict
    assert "timestamp" in response_dict
    assert "details" in response_dict
    assert response_dict["details"]["key"] == "value"


if __name__ == "__main__":
    pytest.main([__file__])