# Audio Fingerprinting Client

Cross-platform Qt6 desktop application for audio fingerprinting and song identification.

## Features

- 10-second audio recording from microphone
- Real-time audio processing and fingerprinting
- Song identification via backend API
- Modern QML/QtQuick user interface
- Cross-platform support (Windows, macOS, Linux)

## Requirements

- Qt 6.5 or later
- CMake 3.21 or later
- C++17 compatible compiler
- Audio input device (microphone)

### Qt6 Components Required

- Qt6::Core
- Qt6::Quick
- Qt6::Multimedia
- Qt6::Network

## Building

### Prerequisites

1. Install Qt6 with the required components
2. Install CMake 3.21+
3. Ensure Qt6 is in your PATH or set CMAKE_PREFIX_PATH

### Build Instructions

#### Windows
```cmd
# Using the build script
build.bat Release

# Or manually
mkdir build
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release
cmake --install . --config Release
```

#### macOS/Linux
```bash
# Using the build script
chmod +x build.sh
./build.sh Release

# Or manually
mkdir build
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --parallel
cmake --install .
```

### Development Build
```bash
./build.sh Debug  # or build.bat Debug on Windows
```

## Configuration

The application connects to the backend API server. Default configuration:
- Server URL: `http://localhost:8000`
- API endpoints: `/api/v1/identify`, `/api/v1/health`

## Usage

1. Launch the application
2. Click the microphone button to start recording
3. Record for 10 seconds (automatic stop)
4. Wait for processing and identification results
5. View song information or try again

## Architecture

- **main.cpp**: Application entry point and QML setup
- **AudioRecorder**: C++ class for microphone audio capture
- **ApiClient**: C++ class for HTTP communication with backend
- **QML Views**: Modern UI components for recording and results
- **CMake**: Cross-platform build system with Qt6 integration

## Deployment

### Windows
```cmd
windeployqt --qmldir qml install/bin/AudioFingerprintingClient.exe
```

### macOS
```bash
macdeployqt install/AudioFingerprintingClient.app
```

### Linux
Ensure Qt6 runtime libraries are available on target systems or use AppImage/Flatpak packaging.

## Troubleshooting

### Audio Recording Issues
- Check microphone permissions
- Verify audio device availability
- Test with different audio formats

### Network Issues
- Verify backend server is running
- Check firewall settings
- Confirm API endpoint URLs

### Build Issues
- Ensure Qt6 is properly installed
- Check CMake version compatibility
- Verify compiler C++17 support