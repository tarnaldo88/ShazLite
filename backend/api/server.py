"""
FastAPI server startup script.
"""

import uvicorn
from backend.api.config import get_settings


def main():
    """Start the FastAPI server."""
    settings = get_settings()
    
    uvicorn.run(
        "backend.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
        access_log=True
    )


if __name__ == "__main__":
    main()