#include "audiorecorder.h"
#include <QAudioFormat>
#include <QDebug>

AudioRecorder::AudioRecorder(QObject *parent)
    : QObject(parent)
    , m_audioInput(nullptr)
    , m_audioDevice(nullptr)
    , m_progressTimer(new QTimer(this))
    , m_isRecording(false)
    , m_recordingProgress(0)
{
    // Set up progress timer
    m_progressTimer->setInterval(PROGRESS_UPDATE_INTERVAL_MS);
    connect(m_progressTimer, &QTimer::timeout, this, &AudioRecorder::updateProgress);
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
    QAudioFormat format;
    format.setSampleRate(44100);
    format.setChannelCount(1); // Mono
    format.setSampleFormat(QAudioFormat::Int16);

    // Check if format is supported
    if (!audioDevice.isFormatSupported(format)) {
        // Try to find a supported format
        format = audioDevice.preferredFormat();
        format.setChannelCount(1); // Force mono
    }

    // Create audio input
    m_audioInput = new QAudioInput(audioDevice, format, this);
    
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
        emit recordingCompleted(m_audioBuffer);
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