# Makefile for Audio Fingerprinting System

.PHONY: help install install-dev build-engine clean test lint format run-backend run-client docker-build docker-up docker-down

# Default target
help:
	@echo "Available targets:"
	@echo "  install      - Install Python dependencies"
	@echo "  install-dev  - Install development dependencies"
	@echo "  build-engine - Build C++ audio engine"
	@echo "  build-client - Build Qt client application"
	@echo "  clean        - Clean build artifacts"
	@echo "  test         - Run tests"
	@echo "  lint         - Run linting checks"
	@echo "  format       - Format code"
	@echo "  run-backend  - Run FastAPI backend server"
	@echo "  run-client   - Run client application"
	@echo "  docker-build - Build Docker containers"
	@echo "  docker-up    - Start Docker services"
	@echo "  docker-down  - Stop Docker services"

# Installation targets
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -e .[dev]

# Build targets
build-engine:
	cd audio_engine && python setup.py build_ext --inplace

build-client:
	cd client && mkdir -p build && cd build && cmake .. && make

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf audio_engine/build/
	cd client && rm -rf build/

# Testing and quality targets
test:
	pytest tests/ -v

test-coverage:
	pytest tests/ --cov=backend --cov=audio_engine --cov-report=html

lint:
	black --check backend/ audio_engine/
	isort --check-only backend/ audio_engine/
	mypy backend/ audio_engine/

format:
	black backend/ audio_engine/
	isort backend/ audio_engine/

# Run targets
run-backend:
	cd backend && uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

run-client:
	cd client/build && ./audio_fingerprinting_client

# Docker targets
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

# Database targets
db-migrate:
	cd backend && alembic upgrade head

db-seed:
	cd backend && python scripts/seed_database.py