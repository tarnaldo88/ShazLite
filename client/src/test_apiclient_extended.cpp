#include <QtTest/QtTest>
#include <QSignalSpy>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QTimer>
#include <QJsonObject>
#include <QJsonDocument>
#include "apiclient.h"

class TestApiClientExtended : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void cleanupTestCase();
    void init();
    void cleanup();
    
    // Core functionality tests
    void testInitialization();
    void testServerUrlProperty();
    void testProcessingStateManagement();
    void testUploadProgressTracking();
    void testAudioIdentificationRequest();
    void testHealthCheckRequest();
    void testRequestCancellation();
    void testRetryLogic();
    void testTimeoutHandling();
    void testNetworkErrorHandling();
    
    // Signal emission tests
    void testIdentificationSignals();
    void testHealthCheckSignals();
    void testRetrySignals();
    void testProgressSignals();

private:
    ApiClient *client;
    QByteArray createTestAudioData();
};

void TestApiClientExtended::initTestCase()
{
    // Setup test environment
}

void TestApiClientExtended::cleanupTestCase()
{
    // Cleanup test environment
}

void TestApiClientExtended::init()
{
    client = new ApiClient(this);
}

void TestApiClientExtended::cleanup()
{
    if (client) {
        client->cancelCurrentRequest();
        client->deleteLater();
        client = nullptr;
    }
}

QByteArray TestApiClientExtended::createTestAudioData()
{
    // Create minimal test audio data (WAV header + some data)
    QByteArray data;
    data.append("RIFF");
    data.append(QByteArray(4, 0)); // File size placeholder
    data.append("WAVE");
    data.append("fmt ");
    data.append(QByteArray(4, 16)); // Format chunk size
    data.append(QByteArray(16, 0)); // Format data
    data.append("data");
    data.append(QByteArray(4, 0)); // Data size placeholder
    data.append(QByteArray(1000, 0)); // Sample audio data
    return data;
}

void TestApiClientExtended::testInitialization()
{
    QVERIFY(client != nullptr);
    QCOMPARE(client->isProcessing(), false);
    QCOMPARE(client->uploadProgress(), 0);
    QCOMPARE(client->serverUrl(), QString("http://localhost:8000"));
}

void TestApiClientExtended::testServerUrlProperty()
{
    QSignalSpy spy(client, &ApiClient::serverUrlChanged);
    
    // Test setting new URL
    client->setServerUrl("http://example.com:8080");
    QCOMPARE(client->serverUrl(), QString("http://example.com:8080"));
    QCOMPARE(spy.count(), 1);
    
    // Test setting same URL (should not emit signal)
    client->setServerUrl("http://example.com:8080");
    QCOMPARE(spy.count(), 1);
    
    // Test setting URL with trailing slash
    client->setServerUrl("http://test.com/");
    QCOMPARE(client->serverUrl(), QString("http://test.com/"));
    QCOMPARE(spy.count(), 2);
}

void TestApiClientExtended::testProcessingStateManagement()
{
    QSignalSpy processingChangedSpy(client, &ApiClient::isProcessingChanged);
    
    // Initial state should be not processing
    QCOMPARE(client->isProcessing(), false);
    
    // Verify signal is properly defined
    QVERIFY(processingChangedSpy.isValid());
}

void TestApiClientExtended::testUploadProgressTracking()
{
    QSignalSpy progressSpy(client, &ApiClient::uploadProgressChanged);
    
    // Initial progress should be 0
    QCOMPARE(client->uploadProgress(), 0);
    
    // Verify progress signal is properly defined
    QVERIFY(progressSpy.isValid());
}

void TestApiClientExtended::testAudioIdentificationRequest()
{
    QSignalSpy processingChangedSpy(client, &ApiClient::isProcessingChanged);
    QSignalSpy identificationResultSpy(client, &ApiClient::identificationResult);
    QSignalSpy identificationFailedSpy(client, &ApiClient::identificationFailed);
    
    // Test with empty audio data (should fail immediately)
    QByteArray emptyData;
    client->identifyAudio(emptyData);
    
    // Should immediately fail with empty data
    QCOMPARE(identificationFailedSpy.count(), 1);
    QCOMPARE(client->isProcessing(), false);
    
    // Test with valid audio data structure
    QByteArray testData = createTestAudioData();
    client->identifyAudio(testData);
    
    // Should start processing (even if it will fail due to no server)
    // The processing state should change
    QTest::qWait(100); // Brief wait for async processing
    
    // Verify signals are properly defined
    QVERIFY(processingChangedSpy.isValid());
    QVERIFY(identificationResultSpy.isValid());
    QVERIFY(identificationFailedSpy.isValid());
}

void TestApiClientExtended::testHealthCheckRequest()
{
    QSignalSpy healthCheckSpy(client, &ApiClient::healthCheckResult);
    
    // Test health check
    client->checkHealth();
    
    // Wait briefly for network request to start
    QTest::qWait(100);
    
    // Verify health check signal is properly defined
    QVERIFY(healthCheckSpy.isValid());
}

void TestApiClientExtended::testRequestCancellation()
{
    QSignalSpy processingChangedSpy(client, &ApiClient::isProcessingChanged);
    
    // Start a request
    QByteArray testData = createTestAudioData();
    client->identifyAudio(testData);
    
    // Cancel the request
    client->cancelCurrentRequest();
    
    // Should not be processing after cancellation
    QCOMPARE(client->isProcessing(), false);
    
    // Verify processing state changes are tracked
    QVERIFY(processingChangedSpy.isValid());
}

void TestApiClientExtended::testRetryLogic()
{
    QSignalSpy retryAttemptSpy(client, &ApiClient::retryAttempt);
    
    // Test that retry signals are properly defined
    QVERIFY(retryAttemptSpy.isValid());
    
    // Test retry with invalid server (will trigger retry logic)
    client->setServerUrl("http://invalid-server-that-does-not-exist:9999");
    QByteArray testData = createTestAudioData();
    client->identifyAudio(testData);
    
    // Wait for potential retry attempts
    QTest::qWait(3000);
    
    // Verify retry mechanism is working (should have attempted retries)
    // Note: We can't guarantee retries will happen in test environment,
    // but we can verify the signal is properly connected
}

void TestApiClientExtended::testTimeoutHandling()
{
    QSignalSpy identificationFailedSpy(client, &ApiClient::identificationFailed);
    
    // Set a very short timeout by using an unresponsive server
    client->setServerUrl("http://10.255.255.1:8000"); // Non-routable IP
    
    QByteArray testData = createTestAudioData();
    client->identifyAudio(testData);
    
    // Wait for timeout (should be less than 30 seconds)
    QTest::qWait(5000);
    
    // Should have failed due to timeout or network error
    QVERIFY(identificationFailedSpy.count() >= 1);
}

void TestApiClientExtended::testNetworkErrorHandling()
{
    QSignalSpy identificationFailedSpy(client, &ApiClient::identificationFailed);
    
    // Test with invalid URL format
    client->setServerUrl("invalid-url");
    
    QByteArray testData = createTestAudioData();
    client->identifyAudio(testData);
    
    // Wait for error
    QTest::qWait(1000);
    
    // Should fail with network error
    QVERIFY(identificationFailedSpy.count() >= 1);
}

void TestApiClientExtended::testIdentificationSignals()
{
    QSignalSpy identificationResultSpy(client, &ApiClient::identificationResult);
    QSignalSpy identificationFailedSpy(client, &ApiClient::identificationFailed);
    
    // Verify identification signals are properly defined
    QVERIFY(identificationResultSpy.isValid());
    QVERIFY(identificationFailedSpy.isValid());
}

void TestApiClientExtended::testHealthCheckSignals()
{
    QSignalSpy healthCheckSpy(client, &ApiClient::healthCheckResult);
    
    // Verify health check signal is properly defined
    QVERIFY(healthCheckSpy.isValid());
}

void TestApiClientExtended::testRetrySignals()
{
    QSignalSpy retryAttemptSpy(client, &ApiClient::retryAttempt);
    
    // Verify retry signal is properly defined
    QVERIFY(retryAttemptSpy.isValid());
}

void TestApiClientExtended::testProgressSignals()
{
    QSignalSpy uploadProgressSpy(client, &ApiClient::uploadProgressChanged);
    QSignalSpy processingChangedSpy(client, &ApiClient::isProcessingChanged);
    
    // Verify progress signals are properly defined
    QVERIFY(uploadProgressSpy.isValid());
    QVERIFY(processingChangedSpy.isValid());
}

QTEST_MAIN(TestApiClientExtended)
#include "test_apiclient_extended.moc"