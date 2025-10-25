"""
Basic tests for the core API structure.
"""

import pytest
from fastapi.testclient import TestClient
from backend.api.main import create_app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    app = create_app()
    return TestClient(app)


def test_app_creation():
    """Test that the FastAPI app can be created successfully."""
    app = create_app()
    assert app is not None
    assert app.title == "Audio Fingerprinting API"
    assert app.version == "1.0.0"


def test_middleware_configuration(client):
    """Test that middleware is properly configured."""
    # Make a request to trigger middleware
    response = client.get("/docs")
    
    # Check that timing headers are added
    assert "X-Process-Time" in response.headers
    assert "X-Request-ID" in response.headers
    
    # Check security headers
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"


def test_error_handling(client):
    """Test that error handling works correctly."""
    # Test 404 error
    response = client.get("/nonexistent-endpoint")
    assert response.status_code == 404
    
    # Check error response format
    error_data = response.json()
    assert "error" in error_data
    assert "message" in error_data
    assert "error_id" in error_data
    assert "timestamp" in error_data


def test_cors_headers(client):
    """Test that CORS headers are properly set."""
    response = client.options("/")
    
    # CORS headers should be present
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-methods" in response.headers


if __name__ == "__main__":
    pytest.main([__file__])