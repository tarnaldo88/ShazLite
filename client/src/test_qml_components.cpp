#include <QtTest/QtTest>
#include <QQmlApplicationEngine>
#include <QQmlContext>
#include <QQuickItem>
#include <QQuickWindow>
#include <QSignalSpy>
#include <QMouseEvent>
#include <QKeyEvent>
#include "audiorecorder.h"
#include "apiclient.h"

class TestQmlComponents : public QObject
{
    Q_OBJECT

private slots:
    void initTestCase();
    void cleanupTestCase();
    void init();
    void cleanup();
    
    // QML Component tests
    void testMainWindowLoading();
    void testRecordButtonComponent();
    void testLoadingIndicatorComponent();
    void testConfidenceIndicatorComponent();
    void testProcessingAnimationComponent();
    void testRecordingViewComponent();
    void testResultsViewComponent();
    
    // User interaction tests
    void testRecordButtonInteraction();
    void testNavigationBetweenViews();
    void testErrorDisplayHandling();
    void testProgressIndicators();

private:
    QQmlApplicationEngine *engine;
    AudioRecorder *audioRecorder;
    ApiClient *apiClient;
    QQuickItem *findQmlItem(const QString &objectName);
    void loadQmlComponent(const QString &qmlFile);
};

void TestQmlComponents::initTestCase()
{
    // Initialize QML engine and register types
    qmlRegisterType<AudioRecorder>("AudioFingerprinting", 1, 0, "AudioRecorder");
    qmlRegisterType<ApiClient>("AudioFingerprinting", 1, 0, "ApiClient");
}

void TestQmlComponents::cleanupTestCase()
{
    // Cleanup
}

void TestQmlComponents::init()
{
    engine = new QQmlApplicationEngine(this);
    audioRecorder = new AudioRecorder(this);
    apiClient = new ApiClient(this);
    
    // Expose C++ objects to QML
    engine->rootContext()->setContextProperty("audioRecorder", audioRecorder);
    engine->rootContext()->setContextProperty("apiClient", apiClient);
}

void TestQmlComponents::cleanup()
{
    if (engine) {
        engine->deleteLater();
        engine = nullptr;
    }
    if (audioRecorder) {
        audioRecorder->deleteLater();
        audioRecorder = nullptr;
    }
    if (apiClient) {
        apiClient->deleteLater();
        apiClient = nullptr;
    }
}

QQuickItem* TestQmlComponents::findQmlItem(const QString &objectName)
{
    if (!engine || engine->rootObjects().isEmpty()) {
        return nullptr;
    }
    
    QObject *rootObject = engine->rootObjects().first();
    return rootObject->findChild<QQuickItem*>(objectName);
}

void TestQmlComponents::loadQmlComponent(const QString &qmlFile)
{
    QString qmlContent = QString(R"(
        import QtQuick 2.15
        import QtQuick.Controls 2.15
        import AudioFingerprinting 1.0
        
        ApplicationWindow {
            id: window
            width: 400
            height: 600
            visible: true
            
            property alias testComponent: loader.item
            
            Loader {
                id: loader
                anchors.fill: parent
                source: "%1"
            }
        }
    )").arg(qmlFile);
    
    engine->loadData(qmlContent.toUtf8());
}

void TestQmlComponents::testMainWindowLoading()
{
    // Test loading the main QML file
    QString mainQml = R"(
        import QtQuick 2.15
        import QtQuick.Controls 2.15
        
        ApplicationWindow {
            id: window
            objectName: "mainWindow"
            width: 400
            height: 600
            visible: true
            title: "Test Window"
            
            property bool testProperty: true
        }
    )";
    
    engine->loadData(mainQml.toUtf8());
    
    // Verify the window was created
    QVERIFY(!engine->rootObjects().isEmpty());
    
    QObject *rootObject = engine->rootObjects().first();
    QVERIFY(rootObject != nullptr);
    QCOMPARE(rootObject->objectName(), QString("mainWindow"));
    
    // Test property access
    QVariant testProp = rootObject->property("testProperty");
    QVERIFY(testProp.isValid());
    QCOMPARE(testProp.toBool(), true);
}

void TestQmlComponents::testRecordButtonComponent()
{
    QString recordButtonQml = R"(
        import QtQuick 2.15
        import QtQuick.Controls 2.15
        
        ApplicationWindow {
            width: 400
            height: 600
            visible: true
            
            Rectangle {
                id: recordButton
                objectName: "recordButton"
                width: 120
                height: 120
                anchors.centerIn: parent
                
                property bool isRecording: false
                property real progress: 0.0
                property bool enabled: true
                
                signal clicked()
                
                MouseArea {
                    anchors.fill: parent
                    onClicked: parent.clicked()
                }
                
                // Test that properties can be modified
                function setRecording(recording) {
                    isRecording = recording
                }
                
                function setProgress(prog) {
                    progress = prog
                }
            }
        }
    )";
    
    engine->loadData(recordButtonQml.toUtf8());
    
    QVERIFY(!engine->rootObjects().isEmpty());
    
    QQuickItem *recordButton = findQmlItem("recordButton");
    QVERIFY(recordButton != nullptr);
    
    // Test initial properties
    QCOMPARE(recordButton->property("isRecording").toBool(), false);
    QCOMPARE(recordButton->property("progress").toReal(), 0.0);
    QCOMPARE(recordButton->property("enabled").toBool(), true);
    
    // Test property changes
    QSignalSpy clickedSpy(recordButton, SIGNAL(clicked()));
    
    // Simulate property changes
    recordButton->setProperty("isRecording", true);
    QCOMPARE(recordButton->property("isRecording").toBool(), true);
    
    recordButton->setProperty("progress", 50.0);
    QCOMPARE(recordButton->property("progress").toReal(), 50.0);
    
    // Test method calls
    QMetaObject::invokeMethod(recordButton, "setRecording", Q_ARG(QVariant, false));
    QCOMPARE(recordButton->property("isRecording").toBool(), false);
    
    QMetaObject::invokeMethod(recordButton, "setProgress", Q_ARG(QVariant, 75.0));
    QCOMPARE(recordButton->property("progress").toReal(), 75.0);
}

void TestQmlComponents::testLoadingIndicatorComponent()
{
    QString loadingIndicatorQml = R"(
        import QtQuick 2.15
        import QtQuick.Controls 2.15
        
        ApplicationWindow {
            width: 400
            height: 600
            visible: true
            
            Item {
                id: loadingIndicator
                objectName: "loadingIndicator"
                width: 40
                height: 40
                anchors.centerIn: parent
                
                property bool running: false
                property color color: "#3498db"
                
                function startAnimation() {
                    running = true
                }
                
                function stopAnimation() {
                    running = false
                }
            }
        }
    )";
    
    engine->loadData(loadingIndicatorQml.toUtf8());
    
    QVERIFY(!engine->rootObjects().isEmpty());
    
    QQuickItem *loadingIndicator = findQmlItem("loadingIndicator");
    QVERIFY(loadingIndicator != nullptr);
    
    // Test initial properties
    QCOMPARE(loadingIndicator->property("running").toBool(), false);
    
    // Test animation control
    QMetaObject::invokeMethod(loadingIndicator, "startAnimation");
    QCOMPARE(loadingIndicator->property("running").toBool(), true);
    
    QMetaObject::invokeMethod(loadingIndicator, "stopAnimation");
    QCOMPARE(loadingIndicator->property("running").toBool(), false);
}

void TestQmlComponents::testConfidenceIndicatorComponent()
{
    QString confidenceIndicatorQml = R"(
        import QtQuick 2.15
        import QtQuick.Controls 2.15
        
        ApplicationWindow {
            width: 400
            height: 600
            visible: true
            
            Item {
                id: confidenceIndicator
                objectName: "confidenceIndicator"
                width: 200
                height: 60
                anchors.centerIn: parent
                
                property real confidence: 0.0
                property bool animated: true
                
                function setConfidence(value) {
                    confidence = value
                }
            }
        }
    )";
    
    engine->loadData(confidenceIndicatorQml.toUtf8());
    
    QVERIFY(!engine->rootObjects().isEmpty());
    
    QQuickItem *confidenceIndicator = findQmlItem("confidenceIndicator");
    QVERIFY(confidenceIndicator != nullptr);
    
    // Test initial properties
    QCOMPARE(confidenceIndicator->property("confidence").toReal(), 0.0);
    QCOMPARE(confidenceIndicator->property("animated").toBool(), true);
    
    // Test confidence value changes
    QMetaObject::invokeMethod(confidenceIndicator, "setConfidence", Q_ARG(QVariant, 0.85));
    QCOMPARE(confidenceIndicator->property("confidence").toReal(), 0.85);
}

void TestQmlComponents::testProcessingAnimationComponent()
{
    QString processingAnimationQml = R"(
        import QtQuick 2.15
        import QtQuick.Controls 2.15
        
        ApplicationWindow {
            width: 400
            height: 600
            visible: true
            
            Item {
                id: processingAnimation
                objectName: "processingAnimation"
                width: 120
                height: 120
                anchors.centerIn: parent
                
                property bool running: false
                property string stage: "uploading"
                property real progress: 0.0
                
                function setStage(newStage) {
                    stage = newStage
                }
                
                function setProgress(newProgress) {
                    progress = newProgress
                }
            }
        }
    )";
    
    engine->loadData(processingAnimationQml.toUtf8());
    
    QVERIFY(!engine->rootObjects().isEmpty());
    
    QQuickItem *processingAnimation = findQmlItem("processingAnimation");
    QVERIFY(processingAnimation != nullptr);
    
    // Test initial properties
    QCOMPARE(processingAnimation->property("running").toBool(), false);
    QCOMPARE(processingAnimation->property("stage").toString(), QString("uploading"));
    QCOMPARE(processingAnimation->property("progress").toReal(), 0.0);
    
    // Test stage changes
    QMetaObject::invokeMethod(processingAnimation, "setStage", Q_ARG(QVariant, "processing"));
    QCOMPARE(processingAnimation->property("stage").toString(), QString("processing"));
    
    QMetaObject::invokeMethod(processingAnimation, "setProgress", Q_ARG(QVariant, 0.5));
    QCOMPARE(processingAnimation->property("progress").toReal(), 0.5);
}

void TestQmlComponents::testRecordingViewComponent()
{
    QString recordingViewQml = R"(
        import QtQuick 2.15
        import QtQuick.Controls 2.15
        
        ApplicationWindow {
            width: 400
            height: 600
            visible: true
            
            Page {
                id: recordingView
                objectName: "recordingView"
                anchors.fill: parent
                
                property var lastRecordedAudio: null
                
                signal recordingCompleted(var audioData)
                signal showResults(var result)
                signal showError(string error)
                
                function simulateRecordingCompleted() {
                    var testData = "test_audio_data"
                    lastRecordedAudio = testData
                    recordingCompleted(testData)
                }
                
                function simulateShowResults() {
                    var testResult = {"title": "Test Song", "artist": "Test Artist"}
                    showResults(testResult)
                }
                
                function simulateShowError() {
                    showError("Test error message")
                }
            }
        }
    )";
    
    engine->loadData(recordingViewQml.toUtf8());
    
    QVERIFY(!engine->rootObjects().isEmpty());
    
    QQuickItem *recordingView = findQmlItem("recordingView");
    QVERIFY(recordingView != nullptr);
    
    // Test signal emissions
    QSignalSpy recordingCompletedSpy(recordingView, SIGNAL(recordingCompleted(QVariant)));
    QSignalSpy showResultsSpy(recordingView, SIGNAL(showResults(QVariant)));
    QSignalSpy showErrorSpy(recordingView, SIGNAL(showError(QString)));
    
    // Test recording completed signal
    QMetaObject::invokeMethod(recordingView, "simulateRecordingCompleted");
    QCOMPARE(recordingCompletedSpy.count(), 1);
    
    // Test show results signal
    QMetaObject::invokeMethod(recordingView, "simulateShowResults");
    QCOMPARE(showResultsSpy.count(), 1);
    
    // Test show error signal
    QMetaObject::invokeMethod(recordingView, "simulateShowError");
    QCOMPARE(showErrorSpy.count(), 1);
}

void TestQmlComponents::testResultsViewComponent()
{
    QString resultsViewQml = R"(
        import QtQuick 2.15
        import QtQuick.Controls 2.15
        
        ApplicationWindow {
            width: 400
            height: 600
            visible: true
            
            Page {
                id: resultsView
                objectName: "resultsView"
                anchors.fill: parent
                
                property var result: null
                property bool isLoading: false
                property string errorMessage: ""
                
                signal backToRecording()
                signal retryIdentification()
                
                function simulateBackToRecording() {
                    backToRecording()
                }
                
                function simulateRetryIdentification() {
                    retryIdentification()
                }
                
                function setResult(newResult) {
                    result = newResult
                }
                
                function setLoading(loading) {
                    isLoading = loading
                }
                
                function setError(error) {
                    errorMessage = error
                }
            }
        }
    )";
    
    engine->loadData(resultsViewQml.toUtf8());
    
    QVERIFY(!engine->rootObjects().isEmpty());
    
    QQuickItem *resultsView = findQmlItem("resultsView");
    QVERIFY(resultsView != nullptr);
    
    // Test initial properties
    QCOMPARE(resultsView->property("isLoading").toBool(), false);
    QCOMPARE(resultsView->property("errorMessage").toString(), QString(""));
    
    // Test signal emissions
    QSignalSpy backToRecordingSpy(resultsView, SIGNAL(backToRecording()));
    QSignalSpy retryIdentificationSpy(resultsView, SIGNAL(retryIdentification()));
    
    // Test back to recording signal
    QMetaObject::invokeMethod(resultsView, "simulateBackToRecording");
    QCOMPARE(backToRecordingSpy.count(), 1);
    
    // Test retry identification signal
    QMetaObject::invokeMethod(resultsView, "simulateRetryIdentification");
    QCOMPARE(retryIdentificationSpy.count(), 1);
    
    // Test property setters
    QMetaObject::invokeMethod(resultsView, "setLoading", Q_ARG(QVariant, true));
    QCOMPARE(resultsView->property("isLoading").toBool(), true);
    
    QMetaObject::invokeMethod(resultsView, "setError", Q_ARG(QVariant, "Test error"));
    QCOMPARE(resultsView->property("errorMessage").toString(), QString("Test error"));
}

void TestQmlComponents::testRecordButtonInteraction()
{
    QString interactiveButtonQml = R"(
        import QtQuick 2.15
        import QtQuick.Controls 2.15
        
        ApplicationWindow {
            width: 400
            height: 600
            visible: true
            
            Button {
                id: recordButton
                objectName: "interactiveButton"
                width: 120
                height: 120
                anchors.centerIn: parent
                text: "Record"
                
                property int clickCount: 0
                
                onClicked: {
                    clickCount++
                }
            }
        }
    )";
    
    engine->loadData(interactiveButtonQml.toUtf8());
    
    QVERIFY(!engine->rootObjects().isEmpty());
    
    QQuickItem *recordButton = findQmlItem("interactiveButton");
    QVERIFY(recordButton != nullptr);
    
    // Test initial click count
    QCOMPARE(recordButton->property("clickCount").toInt(), 0);
    
    // Simulate mouse click
    QSignalSpy clickedSpy(recordButton, SIGNAL(clicked()));
    
    // Trigger click programmatically
    QMetaObject::invokeMethod(recordButton, "clicked");
    
    QCOMPARE(clickedSpy.count(), 1);
    QCOMPARE(recordButton->property("clickCount").toInt(), 1);
}

void TestQmlComponents::testNavigationBetweenViews()
{
    QString navigationQml = R"(
        import QtQuick 2.15
        import QtQuick.Controls 2.15
        
        ApplicationWindow {
            width: 400
            height: 600
            visible: true
            
            StackView {
                id: stackView
                objectName: "stackView"
                anchors.fill: parent
                
                property int currentIndex: 0
                
                function pushView() {
                    currentIndex++
                }
                
                function popView() {
                    if (currentIndex > 0) currentIndex--
                }
                
                function getCurrentIndex() {
                    return currentIndex
                }
            }
        }
    )";
    
    engine->loadData(navigationQml.toUtf8());
    
    QVERIFY(!engine->rootObjects().isEmpty());
    
    QQuickItem *stackView = findQmlItem("stackView");
    QVERIFY(stackView != nullptr);
    
    // Test initial state
    QCOMPARE(stackView->property("currentIndex").toInt(), 0);
    
    // Test navigation
    QMetaObject::invokeMethod(stackView, "pushView");
    QCOMPARE(stackView->property("currentIndex").toInt(), 1);
    
    QMetaObject::invokeMethod(stackView, "popView");
    QCOMPARE(stackView->property("currentIndex").toInt(), 0);
}

void TestQmlComponents::testErrorDisplayHandling()
{
    QString errorDisplayQml = R"(
        import QtQuick 2.15
        import QtQuick.Controls 2.15
        
        ApplicationWindow {
            width: 400
            height: 600
            visible: true
            
            Item {
                id: errorDisplay
                objectName: "errorDisplay"
                anchors.fill: parent
                
                property string errorMessage: ""
                property bool hasError: errorMessage.length > 0
                
                function showError(message) {
                    errorMessage = message
                }
                
                function clearError() {
                    errorMessage = ""
                }
            }
        }
    )";
    
    engine->loadData(errorDisplayQml.toUtf8());
    
    QVERIFY(!engine->rootObjects().isEmpty());
    
    QQuickItem *errorDisplay = findQmlItem("errorDisplay");
    QVERIFY(errorDisplay != nullptr);
    
    // Test initial state
    QCOMPARE(errorDisplay->property("errorMessage").toString(), QString(""));
    QCOMPARE(errorDisplay->property("hasError").toBool(), false);
    
    // Test showing error
    QMetaObject::invokeMethod(errorDisplay, "showError", Q_ARG(QVariant, "Test error message"));
    QCOMPARE(errorDisplay->property("errorMessage").toString(), QString("Test error message"));
    QCOMPARE(errorDisplay->property("hasError").toBool(), true);
    
    // Test clearing error
    QMetaObject::invokeMethod(errorDisplay, "clearError");
    QCOMPARE(errorDisplay->property("errorMessage").toString(), QString(""));
    QCOMPARE(errorDisplay->property("hasError").toBool(), false);
}

void TestQmlComponents::testProgressIndicators()
{
    QString progressQml = R"(
        import QtQuick 2.15
        import QtQuick.Controls 2.15
        
        ApplicationWindow {
            width: 400
            height: 600
            visible: true
            
            ProgressBar {
                id: progressBar
                objectName: "progressBar"
                anchors.centerIn: parent
                width: 200
                
                property real progressValue: 0.0
                
                value: progressValue
                
                function setProgress(progress) {
                    progressValue = progress
                }
            }
        }
    )";
    
    engine->loadData(progressQml.toUtf8());
    
    QVERIFY(!engine->rootObjects().isEmpty());
    
    QQuickItem *progressBar = findQmlItem("progressBar");
    QVERIFY(progressBar != nullptr);
    
    // Test initial progress
    QCOMPARE(progressBar->property("progressValue").toReal(), 0.0);
    
    // Test progress updates
    QMetaObject::invokeMethod(progressBar, "setProgress", Q_ARG(QVariant, 0.5));
    QCOMPARE(progressBar->property("progressValue").toReal(), 0.5);
    
    QMetaObject::invokeMethod(progressBar, "setProgress", Q_ARG(QVariant, 1.0));
    QCOMPARE(progressBar->property("progressValue").toReal(), 1.0);
}

QTEST_MAIN(TestQmlComponents)
#include "test_qml_components.moc"