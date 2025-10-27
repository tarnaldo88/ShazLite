#!/bin/bash

echo "Building and running Qt application tests..."
echo

cd "$(dirname "$0")"

if [ ! -d "build" ]; then
    echo "Creating build directory..."
    mkdir build
fi

cd build

echo "Configuring CMake..."
cmake .. -DCMAKE_BUILD_TYPE=Debug
if [ $? -ne 0 ]; then
    echo "CMake configuration failed!"
    exit 1
fi

echo "Building project..."
cmake --build . --config Debug
if [ $? -ne 0 ]; then
    echo "Build failed!"
    exit 1
fi

echo
echo "Running tests..."
echo "================"

echo
echo "Running API Client Test..."
./test_apiclient
echo "API Client Test completed with exit code: $?"

echo
echo "Running Extended API Client Test..."
./test_apiclient_extended
echo "Extended API Client Test completed with exit code: $?"

echo
echo "Running Audio Recorder Test..."
./test_audiorecorder
echo "Audio Recorder Test completed with exit code: $?"

if [ -f "./test_qml_components" ]; then
    echo
    echo "Running QML Components Test..."
    ./test_qml_components
    echo "QML Components Test completed with exit code: $?"
else
    echo "QML Components Test not available (Qt6Qml/Qt6Quick not found)"
fi

echo
echo "Running CTest..."
ctest --verbose
echo "CTest completed with exit code: $?"

echo
echo "All tests completed!"