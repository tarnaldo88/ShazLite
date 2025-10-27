#include "apiclient.h"
#include <QNetworkRequest>
#include <QHttpMultiPart>
#include <QJsonDocument>
#include <QJsonObject>
#include <QDebug>

ApiClient::ApiClient(QObject *parent)
    : QObject(parent)
    , m_networkManager(new QNetworkAccessManager(this))
    , m_currentReply(nullptr)
    , m_timeoutTimer(new QTimer(this))
    , m_isProcessing(false)
    , m_serverUrl("http://localhost:8000")
    , m_retryCount(0)
{
    m_timeoutTimer->setSingleShot(true);
    m_timeoutTimer->setInterval(REQUEST_TIMEOUT_MS);
    connect(m_timeoutTimer, &QTimer::timeout, this, &ApiClient::handleTimeout);
}

void ApiClient::setServerUrl(const QString &url)
{
    if (m_serverUrl != url) {
        m_serverUrl = url;
        emit serverUrlChanged();
    }
}

void ApiClient::identifyAudio(const QByteArray &audioData)
{
    if (m_isProcessing) {
        return;
    }

    if (audioData.isEmpty()) {
        emit identificationFailed("No audio data provided");
        return;
    }

    setIsProcessing(true);
    m_retryCount = 0;

    // Create WAV file with proper header
    QByteArray wavData = createWavHeader(audioData);

    // Create multipart form data
    QHttpMultiPart *multiPart = new QHttpMultiPart(QHttpMultiPart::FormDataType);

    QHttpPart audioPart;
    audioPart.setHeader(QNetworkRequest::ContentTypeHeader, QVariant("audio/wav"));
    audioPart.setHeader(QNetworkRequest::ContentDispositionHeader, 
                       QVariant("form-data; name=\"audio\"; filename=\"recording.wav\""));
    audioPart.setBody(wavData);
    multiPart->append(audioPart);

    // Create request
    QNetworkRequest request;
    request.setUrl(QUrl(m_serverUrl + "/api/v1/identify"));
    request.setRawHeader("User-Agent", "AudioFingerprintingClient/1.0");

    // Send request
    m_currentReply = m_networkManager->post(request, multiPart);
    multiPart->setParent(m_currentReply); // Delete multiPart with reply

    connect(m_currentReply, &QNetworkReply::finished, this, &ApiClient::handleIdentifyResponse);
    connect(m_currentReply, QOverload<QNetworkReply::NetworkError>::of(&QNetworkReply::errorOccurred),
            this, &ApiClient::handleNetworkError);

    m_timeoutTimer->start();
}

void ApiClient::checkHealth()
{
    QNetworkRequest request;
    request.setUrl(QUrl(m_serverUrl + "/api/v1/health"));
    request.setRawHeader("User-Agent", "AudioFingerprintingClient/1.0");

    QNetworkReply *reply = m_networkManager->get(request);
    connect(reply, &QNetworkReply::finished, this, &ApiClient::handleHealthResponse);
}

void ApiClient::handleIdentifyResponse()
{
    m_timeoutTimer->stop();
    
    if (!m_currentReply) {
        return;
    }

    QNetworkReply::NetworkError error = m_currentReply->error();
    QByteArray responseData = m_currentReply->readAll();
    int statusCode = m_currentReply->attribute(QNetworkRequest::HttpStatusCodeAttribute).toInt();

    m_currentReply->deleteLater();
    m_currentReply = nullptr;

    setIsProcessing(false);

    if (error == QNetworkReply::NoError && statusCode == 200) {
        // Parse JSON response
        QJsonParseError parseError;
        QJsonDocument doc = QJsonDocument::fromJson(responseData, &parseError);
        
        if (parseError.error == QJsonParseError::NoError) {
            QJsonObject result = doc.object();
            emit identificationResult(result);
        } else {
            emit identificationFailed("Invalid response format");
        }
    } else {
        QString errorMessage = QString("Request failed with status %1").arg(statusCode);
        if (!responseData.isEmpty()) {
            QJsonDocument errorDoc = QJsonDocument::fromJson(responseData);
            if (!errorDoc.isNull()) {
                QJsonObject errorObj = errorDoc.object();
                if (errorObj.contains("detail")) {
                    errorMessage = errorObj["detail"].toString();
                }
            }
        }
        emit identificationFailed(errorMessage);
    }
}

void ApiClient::handleHealthResponse()
{
    QNetworkReply *reply = qobject_cast<QNetworkReply*>(sender());
    if (!reply) {
        return;
    }

    bool isHealthy = (reply->error() == QNetworkReply::NoError && 
                     reply->attribute(QNetworkRequest::HttpStatusCodeAttribute).toInt() == 200);
    
    emit healthCheckResult(isHealthy);
    reply->deleteLater();
}

void ApiClient::handleNetworkError(QNetworkReply::NetworkError error)
{
    Q_UNUSED(error)
    
    m_timeoutTimer->stop();
    setIsProcessing(false);

    if (m_currentReply) {
        QString errorString = m_currentReply->errorString();
        m_currentReply->deleteLater();
        m_currentReply = nullptr;
        
        emit identificationFailed(QString("Network error: %1").arg(errorString));
    }
}

void ApiClient::handleTimeout()
{
    if (m_currentReply) {
        m_currentReply->abort();
        m_currentReply->deleteLater();
        m_currentReply = nullptr;
    }
    
    setIsProcessing(false);
    emit identificationFailed("Request timeout");
}

void ApiClient::setIsProcessing(bool processing)
{
    if (m_isProcessing != processing) {
        m_isProcessing = processing;
        emit isProcessingChanged();
    }
}

QByteArray ApiClient::createWavHeader(const QByteArray &audioData, int sampleRate, int channels)
{
    QByteArray header;
    QDataStream stream(&header, QIODevice::WriteOnly);
    stream.setByteOrder(QDataStream::LittleEndian);

    // WAV header
    stream.writeRawData("RIFF", 4);
    stream << quint32(36 + audioData.size()); // File size - 8
    stream.writeRawData("WAVE", 4);
    
    // Format chunk
    stream.writeRawData("fmt ", 4);
    stream << quint32(16); // Chunk size
    stream << quint16(1);  // Audio format (PCM)
    stream << quint16(channels);
    stream << quint32(sampleRate);
    stream << quint32(sampleRate * channels * 2); // Byte rate
    stream << quint16(channels * 2); // Block align
    stream << quint16(16); // Bits per sample
    
    // Data chunk
    stream.writeRawData("data", 4);
    stream << quint32(audioData.size());
    
    return header + audioData;
}