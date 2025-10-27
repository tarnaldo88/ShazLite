# Audio Fingerprinting System

A high-performance audio fingerprinting system for music identification, similar to Shazam. The system consists of a cross-platform client application, FastAPI backend server, and C++ audio processing engine.

## Project Structure

```
├── backend/                    # FastAPI backend server
│   ├── api/                   # API endpoints and routing
│   ├── models/                # Data models and schemas
│   ├── services/              # Business logic services
│   ├── database/              # Database operations and models
│   └── interfaces/            # Abstract interfaces
├── audio_engine/              # C++ audio fingerprinting engine
│   ├── src/                   # C++ source files
│   ├── include/               # C++ header files
│   ├── setup.py               # Python extension build script
│   └── CMakeLists.txt         # CMake build configuration
├── client/                    # Cross-platform Qt client application
│   ├── src/                   # C++ source files
│   ├── qml/                   # QML UI files
│   ├── resources/             # Static assets and resources
│   └── CMakeLists.txt         # CMake build configuration
├── database/                  # Database scripts and migrations
│   ├── migrations/            # Database migration files
│   └── seeds/                 # Database seed data
├── requirements.txt           # Python dependencies
├── pyproject.toml            # Python project configuration
├── Makefile                  # Build and development commands
└── .env.example              # Environment configuration template
```

## Quick Start

### Prerequisites

- Python 3.8+
- Qt6 (6.2+) with Qt Multimedia
- PostgreSQL 12+
- FFTW3 library
- C++ compiler with C++17 support
- CMake 3.16+

### Installation

1. Clone the repository
2. Copy `.env.example` to `.env` and configure your settings
3. Install Python dependencies: `make install`
4. Install Qt6 development libraries and Qt Multimedia module
5. Build the C++ audio engine: `make build-engine`
6. Build the Qt client application: `make build-client`

### Development

- Run backend server: `make run-backend`
- Run Qt client application: `make run-client`
- Run tests: `make test`
- Format code: `make format`

## Architecture

The system uses a client-server architecture with the following components:

- **Client Application**: Cross-platform Qt6/QML desktop app for audio recording
- **FastAPI Backend**: Python web server handling API requests and coordination
- **C++ Audio Engine**: High-performance fingerprinting using FFTW3 and spectral analysis
- **PostgreSQL Database**: Stores song metadata and fingerprint hashes with optimized indexes

## Features

- 10-second audio recording and identification
- Real-time spectral analysis and fingerprinting
- Fast database search with confidence scoring
- Cross-platform Qt desktop client (Windows, macOS, Linux)
- Modern QML-based user interface with animations
- Scalable backend architecture for concurrent users
- Administrative endpoints for database management

## License

MIT License - see LICENSE file for details.