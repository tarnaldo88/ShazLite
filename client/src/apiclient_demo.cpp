#include <QCoreApplication>
#include <QTimer>
#include <QDebug>
#include "apiclient.h"

class ApiClientDemo : public QObject
{
    Q_OBJECT

public:
    ApiClientDemo(QObject *parent = nullptr) : QObject(parent)
    {
        m_apiClient = new ApiClient(this);
        
        // Connect signals to show functionality
        connect(m_apiClient, &ApiClient::isProcessingChanged, this, [this]() {
            qDebug() << "Processing state changed:" << m_apiClient->isProcessing();
        });
        
        connect(m_apiClient, &ApiClient::uploadProgressChanged, this, [this]() {
            qDebug() << "Upload progress:" << m_apiClient->uploadProgress() << "%";
        });
        
        connect(m_apiClient, &ApiClient::retryAttempt, this, [this](int attempt, int maxRetries) {
            qDebug() << "Retry attempt" << attempt << "of" << maxRetries;
        });
        
        connect(m_apiClient, &ApiClient::identificationResult, this, [this](const QJsonObject &result) {
            qDebug() << "Identification successful:" << result;
            QCoreApplication::quit();
        });
        
        connect(m_apiClient, &ApiClient::identificationFailed, this, [this](const QString &error) {
            qDebug() << "Identification failed:" << error;
            QCoreApplication::quit();
        });
        
        connect(m_apiClient, &ApiClient::healthCheckResult, this, [this](bool isHealthy) {
            qDebug() << "Health check result:" << (isHealthy ? "Healthy" : "Unhealthy");
        });
    }

public slots:
    void runDemo()
    {
        qDebug() << "Starting API Client Demo";
        qDebug() << "Server URL:" << m_apiClient->serverUrl();
        
        // First, check server health
        qDebug() << "Checking server health...";
        m_apiClient->checkHealth();
        
        // Simulate audio data (this would normally come from the audio recorder)
        QByteArray dummyAudioData(44100 * 2 * 10, 0); // 10 seconds of silence
        
        // Start identification after a short delay
        QTimer::singleShot(2000, this, [this, dummyAudioData]() {
            qDebug() << "Starting audio identification...";
            m_apiClient->identifyAudio(dummyAudioData);
        });
    }

private:
    ApiClient *m_apiClient;
};

int main(int argc, char *argv[])
{
    QCoreApplication app(argc, argv);
    
    ApiClientDemo demo;
    
    // Start demo after event loop begins
    QTimer::singleShot(0, &demo, &ApiClientDemo::runDemo);
    
    return app.exec();
}

#include "apiclient_demo.moc"