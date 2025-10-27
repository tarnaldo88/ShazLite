# Qt Application Testing Guide

This document describes the comprehensive test suite for the Audio Fingerprinting Qt client application.

## Test Overview

The test suite covers three main areas as specified in task 5.5:

1. **Audio Recording Functionality** - Tests the AudioRecorder class with QTest framework
2. **API Communication and Error Handling** - Tests the ApiClient class for network operations
3. **QML UI Components and User Interactions** - Tests QML components and user interface behavior

## Test Files

### 1. Audio Recorder Tests (`test_audiorecorder.cpp`)

Tests the core audio recording functionality:

- **Initialization**: Verifies proper initial state of AudioRecorder
- **Audio Format Property**: Tests WAV/MP3 format selection and validation
- **Permission Handling**: Tests microphone permission request and response
- **Recording State Management**: Tests start/stop recording functionality
- **Progress Tracking**: Tests recording progress updates during 10-second recording
- **Error Handling**: Tests error message handling and error signal emission
- **Signal Emission**: Verifies all signals are properly defined and emitted

**Key Requirements Tested**: 1.4 (microphone permission), 5.3 (error handling)

### 2. Extended API Client Tests (`test_apiclient_extended.cpp`)

Comprehensive tests for API communication:

- **Initialization**: Tests initial state and default server URL
- **Server URL Property**: Tests URL validation and change notifications
- **Processing State Management**: Tests isProcessing state during requests
- **Upload Progress Tracking**: Tests progress reporting during file uploads
- **Audio Identification Request**: Tests POST /api/v1/identify endpoint calls
- **Health Check Request**: Tests GET /api/v1/health endpoint calls
- **Request Cancellation**: Tests ability to cancel ongoing requests
- **Retry Logic**: Tests automatic retry on network failures (up to 3 attempts)
- **Timeout Handling**: Tests 30-second timeout behavior
- **Network Error Handling**: Tests various network error scenarios
- **Signal Emission**: Verifies all API-related signals work correctly

**Key Requirements Tested**: 5.3 (network error handling, retry logic)

### 3. QML Components Tests (`test_qml_components.cpp`)

Tests QML user interface components:

- **Main Window Loading**: Tests QML engine initialization and window creation
- **Record Button Component**: Tests button properties, states, and interactions
- **Loading Indicator Component**: Tests animation control and visual feedback
- **Confidence Indicator Component**: Tests confidence score display (0-100%)
- **Processing Animation Component**: Tests multi-stage processing animation
- **Recording View Component**: Tests recording page signals and state management
- **Results View Component**: Tests results display and navigation signals
- **User Interactions**: Tests mouse clicks and button interactions
- **Navigation Between Views**: Tests StackView navigation (recording ↔ results)
- **Error Display Handling**: Tests error message display and clearing
- **Progress Indicators**: Tests ProgressBar updates during operations

**Key Requirements Tested**: 1.4 (UI interactions), 5.3 (error display)

## Running Tests

### Prerequisites

- Qt6 with Test, Qml, and Quick modules
- CMake 3.21 or higher
- C++17 compatible compiler

### Build and Run Tests

#### Windows:
```batch
cd client
run_tests.bat
```

#### Linux/macOS:
```bash
cd client
./run_tests.sh
```

#### Manual Build:
```bash
cd client/build
cmake .. -DCMAKE_BUILD_TYPE=Debug
cmake --build . --config Debug
ctest --verbose
```

### Individual Test Execution

Run specific test executables:

```bash
# Audio recorder tests
./test_audiorecorder

# API client tests (original)
./test_apiclient

# API client tests (extended)
./test_apiclient_extended

# QML components tests (if Qt6Qml available)
./test_qml_components
```

## Test Architecture

### QTest Framework Integration

All tests use Qt's QTest framework with:

- **Test Fixtures**: `initTestCase()`, `cleanupTestCase()`, `init()`, `cleanup()`
- **Signal Spies**: `QSignalSpy` for testing signal emissions
- **Assertions**: `QVERIFY()`, `QCOMPARE()`, `QTEST_MAIN()`
- **Async Testing**: `QTest::qWait()` for network operations

### QML Testing Strategy

QML components are tested by:

1. **Loading QML in Test Engine**: Using `QQmlApplicationEngine` with test data
2. **Property Testing**: Verifying initial states and property changes
3. **Signal Testing**: Using `QSignalSpy` to verify signal emissions
4. **Method Invocation**: Testing QML methods via `QMetaObject::invokeMethod()`
5. **Component Interaction**: Simulating user interactions programmatically

### Mock Data and Test Scenarios

Tests use realistic mock data:

- **Audio Data**: Minimal WAV file structure for upload testing
- **API Responses**: JSON objects matching expected server responses
- **Error Scenarios**: Network timeouts, invalid URLs, permission denials
- **UI States**: Loading, error, success, and progress states

## Test Coverage

### Core Functionality Coverage

- ✅ Audio recording initialization and cleanup
- ✅ Microphone permission handling
- ✅ 10-second recording duration enforcement
- ✅ Audio format selection (WAV/MP3)
- ✅ Progress tracking during recording
- ✅ API request/response handling
- ✅ Network error handling and retries
- ✅ Request timeout management
- ✅ QML component property binding
- ✅ User interface state management
- ✅ Navigation between views
- ✅ Error message display

### Signal and Slot Coverage

All Qt signals and slots are tested:

- AudioRecorder: 8 signals tested
- ApiClient: 6 signals tested  
- QML Components: Custom signals for each component

### Error Handling Coverage

Comprehensive error scenario testing:

- Network connectivity issues
- Server unavailability
- Invalid audio data
- Permission denials
- Request timeouts
- Malformed responses

## Continuous Integration

Tests are designed to run in CI environments:

- **Headless Mode**: QML tests can run without display
- **Mock Dependencies**: No external server dependencies required
- **Fast Execution**: Tests complete in under 30 seconds
- **Cross-Platform**: Compatible with Windows, Linux, and macOS

## Test Maintenance

### Adding New Tests

1. Create test methods following naming convention: `test[ComponentName][Functionality]()`
2. Use appropriate test fixtures for setup/cleanup
3. Add comprehensive signal testing for new Qt objects
4. Update CMakeLists.txt to include new test files
5. Document test coverage in this file

### Test Data Management

- Keep test data minimal and focused
- Use realistic but simplified mock data
- Avoid external dependencies in tests
- Clean up test resources in cleanup methods

## Troubleshooting

### Common Issues

1. **Qt6Test not found**: Install Qt6 development packages
2. **QML tests fail**: Ensure Qt6Qml and Qt6Quick are available
3. **Audio tests fail**: Check audio system availability in test environment
4. **Network tests timeout**: Verify test environment network configuration

### Debug Mode

Run tests with debug output:

```bash
export QT_LOGGING_RULES="*.debug=true"
./test_audiorecorder
```

This comprehensive test suite ensures the Qt application meets all requirements for audio recording functionality, API communication, and user interface interactions as specified in task 5.5.