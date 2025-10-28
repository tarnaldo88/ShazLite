#ifndef APICLIENT_H
#define APICLIENT_H

#include <QObject>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QTimer>
#include <QJsonObject>

class ApiClient : public QObject
{
    Q_OBJECT
    Q_PROPERTY(bool isProcessing READ isProcessing NOTIFY isProcessingChanged)
    Q_PROPERTY(QString serverUrl READ serverUrl WRITE setServerUrl NOTIFY serverUrlChanged)
    Q_PROPERTY(int uploadProgress READ uploadProgress NOTIFY uploadProgressChanged)

public:
    explicit ApiClient(QObject *parent = nullptr);

    bool isProcessing() const { return m_isProcessing; }
    QString serverUrl() const { return m_serverUrl; }
    int uploadProgress() const { return m_uploadProgress; }
    void setServerUrl(const QString &url);

public slots:
    void identifyAudio(const QByteArray &audioData);
    void checkHealth();
    void cancelCurrentRequest();

signals:
    void isProcessingChanged();
    void serverUrlChanged();
    void uploadProgressChanged();
    void identificationResult(const QJsonObject &result);
    void identificationFailed(const QString &error);
    void healthCheckResult(bool isHealthy);
    void retryAttempt(int attempt, int maxRetries);

private slots:
    void handleIdentifyResponse();
    void handleHealthResponse();
    void handleNetworkError(QNetworkReply::NetworkError error);
    void handleTimeout();
    void handleUploadProgress(qint64 bytesSent, qint64 bytesTotal);
    void retryRequest();

private:
    void setIsProcessing(bool processing);
    void setUploadProgress(int progress);
    QByteArray createWavHeader(const QByteArray &audioData, int sampleRate = 44100, int channels = 1);
    QByteArray convertMonoToStereo(const QByteArray &monoData);
    void performIdentifyRequest(const QByteArray &audioData);
    void cleanupCurrentRequest();
    bool shouldRetry(QNetworkReply::NetworkError error) const;

    QNetworkAccessManager *m_networkManager;
    QNetworkReply *m_currentReply;
    QTimer *m_timeoutTimer;
    QTimer *m_retryTimer;
    
    bool m_isProcessing;
    QString m_serverUrl;
    int m_uploadProgress;
    
    // Retry logic
    QByteArray m_pendingAudioData;
    int m_retryCount;
    
    static const int REQUEST_TIMEOUT_MS = 30000; // 30 seconds
    static const int MAX_RETRIES = 3;
    static const int RETRY_DELAY_MS = 2000; // 2 seconds base delay
};

#endif // APICLIENT_H