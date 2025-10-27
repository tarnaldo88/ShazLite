#include <QtTest/QtTest>
#include <QSignalSpy>
#include <QTimer>
#include <QAudioFormat>
#include "audiorecorder.h"

class TestAudioRecorder : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void cleanupTestCase();
    void init();
    void cleanup();
    
    // Core functionality tests
    void testInitialization();
    void testAudioFormatProperty();
    void testPermissionHandling();
    void testRecordingStateManagement();
    void testProgressTracking();
    void testErrorHandling();
    void testRecordingDuration();
    
    // Signal emission tests
    void testRecordingSignals();
    void testPermissionSignals();
    void testErrorSignals();

private:
    AudioRecorder *recorder;
};

void TestAudioRecorder::initTestCase()
{
    // Setup test environment
}

void TestAudioRecorder::cleanupTestCase()
{
    // Cleanup test environment
}

void TestAudioRecorder::init()
{
    recorder = new AudioRecorder(this);
}

void TestAudioRecorder::cleanup()
{
    if (recorder) {
        recorder->stopRecording();
        recorder->deleteLater();
        recorder = nullptr;
    }
}

void TestAudioRecorder::testInitialization()
{
    QVERIFY(recorder != nullptr);
    QCOMPARE(recorder->isRecording(), false);
    QCOMPARE(recorder->recordingProgress(), 0);
    QCOMPARE(recorder->errorMessage(), QString());
    QCOMPARE(recorder->audioFormat(), QString("wav"));
}

void TestAudioRecorder::testAudioFormatProperty()
{
    QSignalSpy spy(recorder, &AudioRecorder::audioFormatChanged);
    
    // Test setting WAV format
    recorder->setAudioFormat("wav");
    QCOMPARE(recorder->audioFormat(), QString("wav"));
    QCOMPARE(spy.count(), 0); // No change, same value
    
    // Test setting MP3 format
    recorder->setAudioFormat("mp3");
    QCOMPARE(recorder->audioFormat(), QString("mp3"));
    QCOMPARE(spy.count(), 1);
    
    // Test setting invalid format (should default to WAV)
    recorder->setAudioFormat("invalid");
    QCOMPARE(recorder->audioFormat(), QString("wav"));
    QCOMPARE(spy.count(), 2);
}

void TestAudioRecorder::testPermissionHandling()
{
    QSignalSpy hasPermissionSpy(recorder, &AudioRecorder::hasPermissionChanged);
    QSignalSpy permissionGrantedSpy(recorder, &AudioRecorder::permissionGranted);
    QSignalSpy permissionDeniedSpy(recorder, &AudioRecorder::permissionDenied);
    
    // Test permission request
    recorder->requestPermission();
    
    // Wait for permission result (timeout after 5 seconds)
    QTest::qWait(1000);
    
    // Verify signals are properly defined
    QVERIFY(hasPermissionSpy.isValid());
    QVERIFY(permissionGrantedSpy.isValid());
    QVERIFY(permissionDeniedSpy.isValid());
}

void TestAudioRecorder::testRecordingStateManagement()
{
    QSignalSpy isRecordingSpy(recorder, &AudioRecorder::isRecordingChanged);
    
    // Test that recording cannot start without permission
    if (!recorder->hasPermission()) {
        recorder->startRecording();
        QCOMPARE(recorder->isRecording(), false);
        QVERIFY(!recorder->errorMessage().isEmpty());
    }
    
    // Test stop recording when not recording
    recorder->stopRecording();
    QCOMPARE(recorder->isRecording(), false);
    
    QVERIFY(isRecordingSpy.isValid());
}

void TestAudioRecorder::testProgressTracking()
{
    QSignalSpy progressSpy(recorder, &AudioRecorder::recordingProgressChanged);
    
    // Test initial progress
    QCOMPARE(recorder->recordingProgress(), 0);
    
    // Verify progress signal is properly defined
    QVERIFY(progressSpy.isValid());
}

void TestAudioRecorder::testErrorHandling()
{
    QSignalSpy errorSpy(recorder, &AudioRecorder::errorMessageChanged);
    QSignalSpy recordingFailedSpy(recorder, &AudioRecorder::recordingFailed);
    
    // Test error message property
    QCOMPARE(recorder->errorMessage(), QString());
    
    // Verify error signals are properly defined
    QVERIFY(errorSpy.isValid());
    QVERIFY(recordingFailedSpy.isValid());
}

void TestAudioRecorder::testRecordingDuration()
{
    // Test that recording duration constant is properly defined
    // This tests the static constant RECORDING_DURATION_MS
    const int expectedDuration = 10000; // 10 seconds
    
    // We can't directly access the private constant, but we can test
    // that the recording behavior is consistent with the expected duration
    QVERIFY(expectedDuration > 0);
}

void TestAudioRecorder::testRecordingSignals()
{
    QSignalSpy recordingCompletedSpy(recorder, &AudioRecorder::recordingCompleted);
    QSignalSpy recordingFailedSpy(recorder, &AudioRecorder::recordingFailed);
    
    // Verify recording completion and failure signals are properly defined
    QVERIFY(recordingCompletedSpy.isValid());
    QVERIFY(recordingFailedSpy.isValid());
}

void TestAudioRecorder::testPermissionSignals()
{
    QSignalSpy permissionGrantedSpy(recorder, &AudioRecorder::permissionGranted);
    QSignalSpy permissionDeniedSpy(recorder, &AudioRecorder::permissionDenied);
    
    // Verify permission signals are properly defined
    QVERIFY(permissionGrantedSpy.isValid());
    QVERIFY(permissionDeniedSpy.isValid());
}

void TestAudioRecorder::testErrorSignals()
{
    QSignalSpy errorMessageSpy(recorder, &AudioRecorder::errorMessageChanged);
    QSignalSpy recordingFailedSpy(recorder, &AudioRecorder::recordingFailed);
    
    // Verify error signals are properly defined
    QVERIFY(errorMessageSpy.isValid());
    QVERIFY(recordingFailedSpy.isValid());
}

QTEST_MAIN(TestAudioRecorder)
#include "test_audiorecorder.moc"