#ifndef AUDIORECORDER_H
#define AUDIORECORDER_H

#include <QObject>
#include <QAudioSource>
#include <QAudioDevice>
#include <QMediaDevices>
#include <QIODevice>
#include <QTimer>
#include <QByteArray>
#include <QPermissions>
#include <QAudioFormat>

class AudioRecorder : public QObject
{
    Q_OBJECT
    Q_PROPERTY(bool isRecording READ isRecording NOTIFY isRecordingChanged)
    Q_PROPERTY(int recordingProgress READ recordingProgress NOTIFY recordingProgressChanged)
    Q_PROPERTY(QString errorMessage READ errorMessage NOTIFY errorMessageChanged)
    Q_PROPERTY(bool hasPermission READ hasPermission NOTIFY hasPermissionChanged)
    Q_PROPERTY(QString audioFormat READ audioFormat WRITE setAudioFormat NOTIFY audioFormatChanged)

public:
    explicit AudioRecorder(QObject *parent = nullptr);
    ~AudioRecorder();

    bool isRecording() const { return m_isRecording; }
    int recordingProgress() const { return m_recordingProgress; }
    QString errorMessage() const { return m_errorMessage; }
    bool hasPermission() const { return m_hasPermission; }
    QString audioFormat() const { return m_audioFormat; }
    void setAudioFormat(const QString &format);

public slots:
    void startRecording();
    void stopRecording();
    void requestPermission();
    void checkPermission();

signals:
    void isRecordingChanged();
    void recordingProgressChanged();
    void errorMessageChanged();
    void hasPermissionChanged();
    void audioFormatChanged();
    void recordingCompleted(const QByteArray &audioData);
    void recordingFailed(const QString &error);
    void permissionGranted();
    void permissionDenied();

private slots:
    void updateProgress();
    void handleAudioInput();
    void handlePermissionResult();

private:
    void setIsRecording(bool recording);
    void setRecordingProgress(int progress);
    void setErrorMessage(const QString &message);
    void setHasPermission(bool hasPermission);
    void setupAudioFormat();
    QByteArray encodeToWav(const QByteArray &rawData, const QAudioFormat &format);
    QByteArray encodeToMp3(const QByteArray &rawData, const QAudioFormat &format);

    QAudioSource *m_audioInput;
    QIODevice *m_audioDevice;
    QTimer *m_progressTimer;
    QByteArray m_audioBuffer;
    QAudioFormat m_currentFormat;
    
    bool m_isRecording;
    int m_recordingProgress;
    QString m_errorMessage;
    bool m_hasPermission;
    QString m_audioFormat; // "wav" or "mp3"
    
    static const int RECORDING_DURATION_MS = 10000; // 10 seconds
    static const int PROGRESS_UPDATE_INTERVAL_MS = 100; // Update every 100ms
};

#endif // AUDIORECORDER_H