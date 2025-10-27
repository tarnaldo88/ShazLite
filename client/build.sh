#!/bin/bash

# Cross-platform build script for Qt6 Audio Fingerprinting Client

set -e

# Configuration
BUILD_TYPE=${1:-Release}
BUILD_DIR="build"
INSTALL_DIR="install"

echo "Building Audio Fingerprinting Client..."
echo "Build type: $BUILD_TYPE"

# Create build directory
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Configure with CMake
cmake .. \
    -DCMAKE_BUILD_TYPE="$BUILD_TYPE" \
    -DCMAKE_INSTALL_PREFIX="../$INSTALL_DIR"

# Build
cmake --build . --config "$BUILD_TYPE" --parallel

# Install
cmake --install . --config "$BUILD_TYPE"

echo "Build completed successfully!"
echo "Executable location: $INSTALL_DIR/bin/"

# Platform-specific post-build steps
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "macOS: Creating app bundle..."
    # macdeployqt will be run by CMake install
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Linux: Build completed"
    echo "You may need to install Qt6 runtime libraries on target systems"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "Windows: Build completed"
    echo "You may need to run windeployqt for distribution"
fi