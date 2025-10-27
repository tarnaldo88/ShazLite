# API Client Implementation

## Overview

The `ApiClient` class provides a robust HTTP client for communicating with the audio fingerprinting backend server. It includes advanced features like upload progress tracking, automatic retry logic, and proper error handling.

## Features

### 1. QNetworkAccessManager Integration

- Uses Qt's `QNetworkAccessManager` for HTTP communication
- Supports multipart form data uploads for audio files
- Handles WAV file format with proper headers

### 2. Upload Progress Tracking

- Real-time upload progress monitoring via `QProgressBar`
- Progress signals emitted during file upload
- Visual feedback in the UI during upload process

### 3. Retry Logic with Exponential Backoff

- Automatic retry on network failures (up to 3 attempts)
- Exponential backoff delay: 2s, 4s, 8s
- Retry on specific error types:
  - Connection refused
  - Host not found
  - Timeout errors
  - Temporary network failures

### 4. Timeout Handling

- 30-second timeout for requests
- Automatic retry on timeout
- User cancellation support

## API Reference

### Properties

```cpp
Q_PROPERTY(bool isProcessing READ isProcessing NOTIFY isProcessingChanged)
Q_PROPERTY(QString serverUrl READ serverUrl WRITE setServerUrl NOTIFY serverUrlChanged)
Q_PROPERTY(int uploadProgress READ uploadProgress NOTIFY uploadProgressChanged)
```

### Public Methods

```cpp
// Main identification method
void identifyAudio(const QByteArray &audioData);

// Server health check
void checkHealth();

// Cancel current request
void cancelCurrentRequest();

// Server URL management
void setServerUrl(const QString &url);
QString serverUrl() const;
```

### Signals

```cpp
// Processing state
void isProcessingChanged();
void uploadProgressChanged();

// Results
void identificationResult(const QJsonObject &result);
void identificationFailed(const QString &error);

// Health check
void healthCheckResult(bool isHealthy);

// Retry notifications
void retryAttempt(int attempt, int maxRetries);
```

## Usage Example

### Basic Usage

```cpp
ApiClient *client = new ApiClient(this);

// Connect signals
connect(client, &ApiClient::identificationResult, this, [](const QJsonObject &result) {
    qDebug() << "Song identified:" << result["title"].toString();
});

connect(client, &ApiClient::identificationFailed, this, [](const QString &error) {
    qDebug() << "Identification failed:" << error;
});

// Start identification
QByteArray audioData = getRecordedAudio();
client->identifyAudio(audioData);
```

### Progress Tracking

```cpp
connect(client, &ApiClient::uploadProgressChanged, this, [client]() {
    int progress = client->uploadProgress();
    qDebug() << "Upload progress:" << progress << "%";
    // Update progress bar in UI
});
```

### Retry Handling

```cpp
connect(client, &ApiClient::retryAttempt, this, [](int attempt, int maxRetries) {
    qDebug() << "Retrying request... (" << attempt << "/" << maxRetries << ")";
    // Show retry status in UI
});
```

## QML Integration

The API client is exposed to QML and can be used directly:

```qml
// Progress bar with upload tracking
ProgressBar {
    visible: apiClient.isProcessing
    value: apiClient.uploadProgress > 0 ? apiClient.uploadProgress / 100.0 : -1
    indeterminate: apiClient.isProcessing && apiClient.uploadProgress === 0
}

// Status text with retry information
Label {
    text: {
        if (apiClient.uploadProgress > 0 && apiClient.uploadProgress < 100) {
            return `Uploading: ${apiClient.uploadProgress}%`
        } else if (apiClient.isProcessing) {
            return "Identifying song..."
        }
        return ""
    }
}

// Cancel button
Button {
    text: "Cancel"
    visible: apiClient.isProcessing
    onClicked: apiClient.cancelCurrentRequest()
}

// Retry status
Connections {
    target: apiClient
    function onRetryAttempt(attempt, maxRetries) {
        retryLabel.text = `Retrying... (${attempt}/${maxRetries})`
        retryLabel.visible = true
    }
}
```

## Error Handling

The API client handles various error scenarios:

1. **Network Errors**: Automatic retry with exponential backoff
2. **Timeout Errors**: Retry up to maximum attempts
3. **Server Errors**: Parse error messages from JSON responses
4. **Invalid Data**: Validate audio data before sending

## Configuration

### Constants

```cpp
static const int REQUEST_TIMEOUT_MS = 30000;  // 30 seconds
static const int MAX_RETRIES = 3;             // Maximum retry attempts
static const int RETRY_DELAY_MS = 2000;       // Base retry delay (2 seconds)
```

### Retry Strategy

- **Exponential Backoff**: Delay = base_delay \* 2^(attempt - 1)
- **Retryable Errors**: Connection issues, timeouts, temporary failures
- **Non-Retryable Errors**: Authentication, bad request, server errors

## Testing

### Unit Tests

Run the unit tests to verify functionality:

```bash
# Build with tests enabled
cmake -B build -S . -DCMAKE_BUILD_TYPE=Debug
cmake --build build

# Run tests
cd build && ctest
```

### Demo Application

Build and run the demo to see the API client in action:

```bash
# Build with demo enabled
cmake -B build -S . -DCMAKE_BUILD_TYPE=Debug -DBUILD_DEMO=ON
cmake --build build

# Run demo
./build/apiclient_demo
```

## Requirements Compliance

This implementation satisfies the following requirements:

- **Requirement 2.1**: Audio transmission within 2 seconds via HTTP client
- **Requirement 5.3**: Network connectivity handling with retry logic

### Task 5.3 Completion

✅ **Create QNetworkAccessManager for HTTP client communication**

- Implemented with proper multipart form data support
- Handles WAV file uploads with correct headers

✅ **Implement audio file upload with QProgressBar tracking**

- Real-time upload progress monitoring
- Progress signals for UI integration
- Visual feedback during upload process

✅ **Write retry logic for network failures using QTimer**

- Automatic retry on network failures (max 3 attempts)
- Exponential backoff delay strategy
- Retry on appropriate error types only
- User notification of retry attempts
