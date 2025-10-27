# Multi-stage Dockerfile for Audio Fingerprinting System
FROM python:3.12-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    pkg-config \
    libfftw3-dev \
    libfftw3-3 \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Build the C++ audio engine
WORKDIR /app/audio_engine
RUN python setup.py build_ext --inplace

# Set working directory back to app root
WORKDIR /app

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/admin/health || exit 1

# Default command
CMD ["python", "-m", "uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]


# Development stage
FROM base as development

USER root

# Install development dependencies
RUN pip install --no-cache-dir pytest pytest-cov pytest-xdist black flake8 mypy

# Install additional development tools
RUN apt-get update && apt-get install -y \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

USER appuser

# Override command for development
CMD ["python", "-m", "uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


# Production stage
FROM base as production

# Copy only necessary files for production
COPY --from=base /app /app

# Set production environment
ENV ENVIRONMENT=production \
    DEBUG=false \
    LOG_LEVEL=INFO

# Use gunicorn for production
RUN pip install --no-cache-dir gunicorn[gthread]

# Production command
CMD ["gunicorn", "backend.api.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-"]