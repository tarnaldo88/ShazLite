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

public:
    explicit ApiClient(QObject *parent = nullptr);

    bool isProcessing() const { return m_isProcessing; }
    QString serverUrl() const { return m_serverUrl; }
    void setServerUrl(const QString &url);

public slots:
    void identifyAudio(const QByteArray &audioData);
    void checkHealth();

signals:
    void isProcessingChanged();
    void serverUrlChanged();
    void identificationResult(const QJsonObject &result);
    void identificationFailed(const QString &error);
    void healthCheckResult(bool isHealthy);

private slots:
    void handleIdentifyResponse();
    void handleHealthResponse();
    void handleNetworkError(QNetworkReply::NetworkError error);
    void handleTimeout();

private:
    void setIsProcessing(bool processing);
    QByteArray createWavHeader(const QByteArray &audioData, int sampleRate = 44100, int channels = 1);

    QNetworkAccessManager *m_networkManager;
    QNetworkReply *m_currentReply;
    QTimer *m_timeoutTimer;
    
    bool m_isProcessing;
    QString m_serverUrl;
    
    static const int REQUEST_TIMEOUT_MS = 30000; // 30 seconds
    static const int MAX_RETRIES = 3;
    int m_retryCount;
};

#endif // APICLIENT_H