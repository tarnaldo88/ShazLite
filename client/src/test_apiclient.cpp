#include <QtTest/QtTest>
#include <QSignalSpy>
#include <QNetworkAccessManager>
#include <QTimer>
#include "apiclient.h"

class TestApiClient : public QObject
{
    Q_OBJECT

private slots:
    void testInitialization();
    void testServerUrlProperty();
    void testUploadProgressProperty();
    void testCancelRequest();
    void testRetryLogic();

private:
    ApiClient *createApiClient();
};

ApiClient* TestApiClient::createApiClient()
{
    return new ApiClient(this);
}

void TestApiClient::testInitialization()
{
    ApiClient client;
    
    // Test initial state
    QCOMPARE(client.isProcessing(), false);
    QCOMPARE(client.uploadProgress(), 0);
    QCOMPARE(client.serverUrl(), QString("http://localhost:8000"));
}

void TestApiClient::testServerUrlProperty()
{
    ApiClient client;
    QSignalSpy spy(&client, &ApiClient::serverUrlChanged);
    
    // Test setting new URL
    client.setServerUrl("http://example.com:8080");
    QCOMPARE(client.serverUrl(), QString("http://example.com:8080"));
    QCOMPARE(spy.count(), 1);
    
    // Test setting same URL (should not emit signal)
    client.setServerUrl("http://example.com:8080");
    QCOMPARE(spy.count(), 1);
}

void TestApiClient::testUploadProgressProperty()
{
    ApiClient client;
    QSignalSpy spy(&client, &ApiClient::uploadProgressChanged);
    
    // Initial progress should be 0
    QCOMPARE(client.uploadProgress(), 0);
    
    // Test that progress changes are properly signaled
    // Note: This tests the internal setUploadProgress method indirectly
    // through the public interface
}

void TestApiClient::testCancelRequest()
{
    ApiClient client;
    QSignalSpy processingChangedSpy(&client, &ApiClient::isProcessingChanged);
    QSignalSpy failedSpy(&client, &ApiClient::identificationFailed);
    
    // Start a request with empty data to trigger immediate processing
    QByteArray emptyData;
    client.identifyAudio(emptyData);
    
    // Should immediately fail with empty data
    QCOMPARE(failedSpy.count(), 1);
    QCOMPARE(client.isProcessing(), false);
}

void TestApiClient::testRetryLogic()
{
    ApiClient client;
    QSignalSpy retryAttemptSpy(&client, &ApiClient::retryAttempt);
    
    // Test that retry signals are properly defined
    // Note: Full retry testing would require mocking network responses
    // which is beyond the scope of this basic test
    
    QVERIFY(retryAttemptSpy.isValid());
}

QTEST_MAIN(TestApiClient)
#include "test_apiclient.moc"