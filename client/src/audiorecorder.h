#ifndef AUDIORECORDER_H
#define AUDIORECORDER_H

#include <QObject>
#include <QAudioInput>
#include <QAudioDevice>
#include <QMediaDevices>
#include <QIODevice>
#include <QTimer>
#include <QByteArray>

class AudioRecorder : public QObject
{
    Q_OBJECT
    Q_PROPERTY(bool isRecording READ isRecording NOTIFY isRecordingChanged)
    Q_PROPERTY(int recordingProgress READ recordingProgress NOTIFY recordingProgressChanged)
    Q_PROPERTY(QString errorMessage READ errorMessage NOTIFY errorMessageChanged)

public:
    explicit AudioRecorder(QObject *parent = nullptr);
    ~AudioRecorder();

    bool isRecording() const { return m_isRecording; }
    int recordingProgress() const { return m_recordingProgress; }
    QString errorMessage() const { return m_errorMessage; }

public slots:
    void startRecording();
    void stopRecording();

signals:
    void isRecordingChanged();
    void recordingProgressChanged();
    void errorMessageChanged();
    void recordingCompleted(const QByteArray &audioData);
    void recordingFailed(const QString &error);

private slots:
    void updateProgress();
    void handleAudioInput();

private:
    void setIsRecording(bool recording);
    void setRecordingProgress(int progress);
    void setErrorMessage(const QString &message);
    void setupAudioFormat();

    QAudioInput *m_audioInput;
    QIODevice *m_audioDevice;
    QTimer *m_progressTimer;
    QByteArray m_audioBuffer;
    
    bool m_isRecording;
    int m_recordingProgress;
    QString m_errorMessage;
    
    static const int RECORDING_DURATION_MS = 10000; // 10 seconds
    static const int PROGRESS_UPDATE_INTERVAL_MS = 100; // Update every 100ms
};

#endif // AUDIORECORDER_H