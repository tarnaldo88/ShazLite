#include "audiorecorder.h"
#include <QAudioFormat>
#include <QDebug>
#include <QPermissions>
#include <QCoreApplication>
#include <QDataStream>

AudioRecorder::AudioRecorder(QObject *parent)
    : QObject(parent)
    , m_audioInput(nullptr)
    , m_audioDevice(nullptr)
    , m_progressTimer(new QTimer(this))
    , m_isRecording(false)
    , m_recordingProgress(0)
    , m_hasPermission(false)
    , m_audioFormat("wav") // Default to WAV format
{
    // Set up progress timer
    m_progressTimer->setInterval(PROGRESS_UPDATE_INTERVAL_MS);
    connect(m_progressTimer, &QTimer::timeout, this, &AudioRecorder::updateProgress);
    
    // Check initial permission status
    checkPermission();
}

AudioRecorder::~AudioRecorder()
{
    if (m_isRecording) {
        stopRecording();
    }
}

void AudioRecorder::startRecording()
{
    if (m_isRecording) {
        return;
    }

    // Check permission first
    if (!m_hasPermission) {
        setErrorMessage("Microphone permission required");
        emit recordingFailed(m_errorMessage);
        requestPermission();
        return;
    }

    // Clear previous data and errors
    m_audioBuffer.clear();
    setErrorMessage("");
    setRecordingProgress(0);

    // Get default audio input device
    QAudioDevice audioDevice = QMediaDevices::defaultAudioInput();
    if (audioDevice.isNull()) {
        setErrorMessage("No audio input device available");
        emit recordingFailed(m_errorMessage);
        return;
    }

    // Set up audio format
    setupAudioFormat();

    // Check if format is supported
    if (!audioDevice.isFormatSupported(m_currentFormat)) {
        // Try to find a supported format
        m_currentFormat = audioDevice.preferredFormat();
        m_currentFormat.setChannelCount(1); // Force mono
        qDebug() << "Using preferred format:" << m_currentFormat;
    }

    // Create audio input
    m_audioInput = new QAudioSource(audioDevice, m_currentFormat, this);
    
    // Start recording
    m_audioDevice = m_audioInput->start();
    if (!m_audioDevice) {
        setErrorMessage("Failed to start audio recording");
        emit recordingFailed(m_errorMessage);
        delete m_audioInput;
        m_audioInput = nullptr;
        return;
    }

    // Connect to read audio data
    connect(m_audioDevice, &QIODevice::readyRead, this, &AudioRecorder::handleAudioInput);

    setIsRecording(true);
    m_progressTimer->start();

    qDebug() << "Recording started with format:" << m_currentFormat;

    // Auto-stop after 10 seconds
    QTimer::singleShot(RECORDING_DURATION_MS, this, &AudioRecorder::stopRecording);
}

void AudioRecorder::stopRecording()
{
    if (!m_isRecording) {
        return;
    }

    m_progressTimer->stop();
    
    if (m_audioInput) {
        m_audioInput->stop();
        delete m_audioInput;
        m_audioInput = nullptr;
        m_audioDevice = nullptr;
    }

    setIsRecording(false);
    setRecordingProgress(100);

    if (!m_audioBuffer.isEmpty()) {
        // Encode audio data based on selected format
        QByteArray encodedData;
        if (m_audioFormat.toLower() == "mp3") {
            encodedData = encodeToMp3(m_audioBuffer, m_currentFormat);
        } else {
            encodedData = encodeToWav(m_audioBuffer, m_currentFormat);
        }
        
        if (!encodedData.isEmpty()) {
            qDebug() << "Recording completed, encoded" << encodedData.size() << "bytes as" << m_audioFormat;
            emit recordingCompleted(encodedData);
        } else {
            setErrorMessage("Failed to encode audio data");
            emit recordingFailed(m_errorMessage);
        }
    } else {
        setErrorMessage("No audio data recorded");
        emit recordingFailed(m_errorMessage);
    }
}

void AudioRecorder::updateProgress()
{
    if (!m_isRecording) {
        return;
    }

    static int elapsed = 0;
    elapsed += PROGRESS_UPDATE_INTERVAL_MS;
    
    int progress = (elapsed * 100) / RECORDING_DURATION_MS;
    setRecordingProgress(qMin(progress, 100));

    if (elapsed >= RECORDING_DURATION_MS) {
        elapsed = 0;
    }
}

void AudioRecorder::handleAudioInput()
{
    if (m_audioDevice) {
        QByteArray data = m_audioDevice->readAll();
        m_audioBuffer.append(data);
    }
}

void AudioRecorder::setIsRecording(bool recording)
{
    if (m_isRecording != recording) {
        m_isRecording = recording;
        emit isRecordingChanged();
    }
}

void AudioRecorder::setRecordingProgress(int progress)
{
    if (m_recordingProgress != progress) {
        m_recordingProgress = progress;
        emit recordingProgressChanged();
    }
}

void AudioRecorder::setErrorMessage(const QString &message)
{
    if (m_errorMessage != message) {
        m_errorMessage = message;
        emit errorMessageChanged();
    }
}

void AudioRecorder::setHasPermission(bool hasPermission)
{
    if (m_hasPermission != hasPermission) {
        m_hasPermission = hasPermission;
        emit hasPermissionChanged();
    }
}

void AudioRecorder::setAudioFormat(const QString &format)
{
    QString lowerFormat = format.toLower();
    if (lowerFormat != "wav" && lowerFormat != "mp3") {
        qWarning() << "Unsupported audio format:" << format << "- using WAV";
        lowerFormat = "wav";
    }
    
    if (m_audioFormat != lowerFormat) {
        m_audioFormat = lowerFormat;
        emit audioFormatChanged();
    }
}

void AudioRecorder::requestPermission()
{
#if QT_VERSION >= QT_VERSION_CHECK(6, 5, 0)
    QMicrophonePermission permission;
    switch (qApp->checkPermission(permission)) {
    case Qt::PermissionStatus::Undetermined:
        qApp->requestPermission(permission, this, &AudioRecorder::handlePermissionResult);
        break;
    case Qt::PermissionStatus::Denied:
        setHasPermission(false);
        setErrorMessage("Microphone permission denied. Please enable it in system settings.");
        emit permissionDenied();
        break;
    case Qt::PermissionStatus::Granted:
        setHasPermission(true);
        setErrorMessage("");
        emit permissionGranted();
        break;
    }
#else
    // For older Qt versions, assume permission is granted
    setHasPermission(true);
    emit permissionGranted();
#endif
}

void AudioRecorder::checkPermission()
{
#if QT_VERSION >= QT_VERSION_CHECK(6, 5, 0)
    QMicrophonePermission permission;
    Qt::PermissionStatus status = qApp->checkPermission(permission);
    setHasPermission(status == Qt::PermissionStatus::Granted);
#else
    // For older Qt versions, assume permission is granted
    setHasPermission(true);
#endif
}

void AudioRecorder::handlePermissionResult()
{
#if QT_VERSION >= QT_VERSION_CHECK(6, 5, 0)
    QMicrophonePermission permission;
    Qt::PermissionStatus status = qApp->checkPermission(permission);
    
    if (status == Qt::PermissionStatus::Granted) {
        setHasPermission(true);
        setErrorMessage("");
        emit permissionGranted();
    } else {
        setHasPermission(false);
        setErrorMessage("Microphone permission denied. Please enable it in system settings.");
        emit permissionDenied();
    }
#endif
}

void AudioRecorder::setupAudioFormat()
{
    m_currentFormat.setSampleRate(44100);
    m_currentFormat.setChannelCount(1); // Mono
    m_currentFormat.setSampleFormat(QAudioFormat::Int16);
}

QByteArray AudioRecorder::encodeToWav(const QByteArray &rawData, const QAudioFormat &format)
{
    QByteArray header;
    QDataStream stream(&header, QIODevice::WriteOnly);
    stream.setByteOrder(QDataStream::LittleEndian);

    // WAV header
    stream.writeRawData("RIFF", 4);
    stream << quint32(36 + rawData.size()); // File size - 8
    stream.writeRawData("WAVE", 4);
    
    // Format chunk
    stream.writeRawData("fmt ", 4);
    stream << quint32(16); // Chunk size
    stream << quint16(1);  // Audio format (PCM)
    stream << quint16(format.channelCount());
    stream << quint32(format.sampleRate());
    stream << quint32(format.sampleRate() * format.channelCount() * (format.bytesPerSample())); // Byte rate
    stream << quint16(format.channelCount() * format.bytesPerSample()); // Block align
    stream << quint16(format.bytesPerSample() * 8); // Bits per sample
    
    // Data chunk
    stream.writeRawData("data", 4);
    stream << quint32(rawData.size());
    
    return header + rawData;
}

QByteArray AudioRecorder::encodeToMp3(const QByteArray &rawData, const QAudioFormat &format)
{
    // For now, we'll fall back to WAV encoding since MP3 encoding requires additional libraries
    // In a production environment, you would use libraries like LAME or integrate with Qt's codec system
    qWarning() << "MP3 encoding not fully implemented, falling back to WAV";
    return encodeToWav(rawData, format);
}