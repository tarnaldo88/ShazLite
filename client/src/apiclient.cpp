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
    , m_retryTimer(new QTimer(this))
    , m_isProcessing(false)
    , m_serverUrl("http://localhost:8000")
    , m_uploadProgress(0)
    , m_retryCount(0)
{
    m_timeoutTimer->setSingleShot(true);
    m_timeoutTimer->setInterval(REQUEST_TIMEOUT_MS);
    connect(m_timeoutTimer, &QTimer::timeout, this, &ApiClient::handleTimeout);
    
    m_retryTimer->setSingleShot(true);
    connect(m_retryTimer, &QTimer::timeout, this, &ApiClient::retryRequest);
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
    setUploadProgress(0);
    m_retryCount = 0;
    m_pendingAudioData = audioData;

    performIdentifyRequest(audioData);
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

    cleanupCurrentRequest();

    if (error == QNetworkReply::NoError && statusCode == 200) {
        // Success - clear retry data and process response
        m_pendingAudioData.clear();
        setIsProcessing(false);
        setUploadProgress(100);
        
        // Parse JSON response
        QJsonParseError parseError;
        QJsonDocument doc = QJsonDocument::fromJson(responseData, &parseError);
        
        if (parseError.error == QJsonParseError::NoError) {
            QJsonObject result = doc.object();
            emit identificationResult(result);
        } else {
            emit identificationFailed("Invalid response format");
        }
    } else if (shouldRetry(error) && m_retryCount < MAX_RETRIES) {
        // Retry the request
        m_retryCount++;
        emit retryAttempt(m_retryCount, MAX_RETRIES);
        
        // Exponential backoff: base delay * 2^(retry_count - 1)
        int delay = RETRY_DELAY_MS * (1 << (m_retryCount - 1));
        m_retryTimer->start(delay);
    } else {
        // Final failure
        m_pendingAudioData.clear();
        setIsProcessing(false);
        setUploadProgress(0);
        
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
        
        if (m_retryCount >= MAX_RETRIES) {
            errorMessage = QString("Request failed after %1 attempts: %2").arg(MAX_RETRIES).arg(errorMessage);
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
    m_timeoutTimer->stop();
    
    if (!m_currentReply) {
        return;
    }
    
    QString errorString = m_currentReply->errorString();
    cleanupCurrentRequest();
    
    if (shouldRetry(error) && m_retryCount < MAX_RETRIES) {
        // Retry the request
        m_retryCount++;
        emit retryAttempt(m_retryCount, MAX_RETRIES);
        
        // Exponential backoff: base delay * 2^(retry_count - 1)
        int delay = RETRY_DELAY_MS * (1 << (m_retryCount - 1));
        m_retryTimer->start(delay);
    } else {
        // Final failure
        m_pendingAudioData.clear();
        setIsProcessing(false);
        setUploadProgress(0);
        
        QString finalError = QString("Network error: %1").arg(errorString);
        if (m_retryCount >= MAX_RETRIES) {
            finalError = QString("Network error after %1 attempts: %2").arg(MAX_RETRIES).arg(errorString);
        }
        
        emit identificationFailed(finalError);
    }
}

void ApiClient::handleTimeout()
{
    if (m_currentReply) {
        m_currentReply->abort();
    }
    
    cleanupCurrentRequest();
    
    if (m_retryCount < MAX_RETRIES) {
        // Retry on timeout
        m_retryCount++;
        emit retryAttempt(m_retryCount, MAX_RETRIES);
        
        // Exponential backoff: base delay * 2^(retry_count - 1)
        int delay = RETRY_DELAY_MS * (1 << (m_retryCount - 1));
        m_retryTimer->start(delay);
    } else {
        // Final timeout failure
        m_pendingAudioData.clear();
        setIsProcessing(false);
        setUploadProgress(0);
        
        emit identificationFailed(QString("Request timeout after %1 attempts").arg(MAX_RETRIES));
    }
}

void ApiClient::cancelCurrentRequest()
{
    if (m_currentReply) {
        m_currentReply->abort();
    }
    
    m_retryTimer->stop();
    m_timeoutTimer->stop();
    cleanupCurrentRequest();
    
    m_pendingAudioData.clear();
    setIsProcessing(false);
    setUploadProgress(0);
    
    emit identificationFailed("Request cancelled by user");
}

void ApiClient::handleUploadProgress(qint64 bytesSent, qint64 bytesTotal)
{
    if (bytesTotal > 0) {
        int progress = static_cast<int>((bytesSent * 100) / bytesTotal);
        setUploadProgress(progress);
    }
}

void ApiClient::retryRequest()
{
    if (!m_pendingAudioData.isEmpty()) {
        qDebug() << "Retrying request, attempt" << m_retryCount << "of" << MAX_RETRIES;
        performIdentifyRequest(m_pendingAudioData);
    }
}

void ApiClient::setIsProcessing(bool processing)
{
    if (m_isProcessing != processing) {
        m_isProcessing = processing;
        emit isProcessingChanged();
    }
}

void ApiClient::setUploadProgress(int progress)
{
    if (m_uploadProgress != progress) {
        m_uploadProgress = progress;
        emit uploadProgressChanged();
    }
}

void ApiClient::performIdentifyRequest(const QByteArray &audioData)
{
    // Convert mono audio to stereo for server compatibility
    QByteArray stereoAudioData = convertMonoToStereo(audioData);
    QByteArray wavData = createWavHeader(stereoAudioData, 44100, 2);

    // Create multipart form data
    QHttpMultiPart *multiPart = new QHttpMultiPart(QHttpMultiPart::FormDataType);

    QHttpPart audioPart;
    audioPart.setHeader(QNetworkRequest::ContentTypeHeader, QVariant("audio/wav"));
    audioPart.setHeader(QNetworkRequest::ContentDispositionHeader, 
                       QVariant("form-data; name=\"audio_file\"; filename=\"recording.wav\""));
    audioPart.setBody(wavData);
    multiPart->append(audioPart);

    // Create request
    QNetworkRequest request;
    request.setUrl(QUrl(m_serverUrl + "/api/v1/identify"));
    request.setRawHeader("User-Agent", "AudioFingerprintingClient/1.0");

    // Send request
    m_currentReply = m_networkManager->post(request, multiPart);
    multiPart->setParent(m_currentReply); // Delete multiPart with reply

    // Connect signals
    connect(m_currentReply, &QNetworkReply::finished, this, &ApiClient::handleIdentifyResponse);
    connect(m_currentReply, QOverload<QNetworkReply::NetworkError>::of(&QNetworkReply::errorOccurred),
            this, &ApiClient::handleNetworkError);
    connect(m_currentReply, &QNetworkReply::uploadProgress, this, &ApiClient::handleUploadProgress);

    // Start timeout timer
    m_timeoutTimer->start();
    
    // Reset upload progress
    setUploadProgress(0);
}

void ApiClient::cleanupCurrentRequest()
{
    if (m_currentReply) {
        m_currentReply->deleteLater();
        m_currentReply = nullptr;
    }
}

bool ApiClient::shouldRetry(QNetworkReply::NetworkError error) const
{
    // Retry on network errors that might be temporary
    switch (error) {
        case QNetworkReply::ConnectionRefusedError:
        case QNetworkReply::RemoteHostClosedError:
        case QNetworkReply::HostNotFoundError:
        case QNetworkReply::TimeoutError:
        case QNetworkReply::OperationCanceledError:
        case QNetworkReply::TemporaryNetworkFailureError:
        case QNetworkReply::NetworkSessionFailedError:
        case QNetworkReply::BackgroundRequestNotAllowedError:
        case QNetworkReply::UnknownNetworkError:
            return true;
        default:
            return false;
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

QByteArray ApiClient::convertMonoToStereo(const QByteArray &monoData)
{
    // Convert mono 16-bit PCM to stereo by duplicating each sample
    QByteArray stereoData;
    stereoData.reserve(monoData.size() * 2);
    
    // Process 16-bit samples (2 bytes each)
    for (int i = 0; i < monoData.size(); i += 2) {
        if (i + 1 < monoData.size()) {
            // Copy the mono sample to both left and right channels
            stereoData.append(monoData.mid(i, 2)); // Left channel
            stereoData.append(monoData.mid(i, 2)); // Right channel (same as left)
        }
    }
    
    return stereoData;
}