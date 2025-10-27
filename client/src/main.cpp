#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QQmlContext>
#include <QIcon>

#include "audiorecorder.h"
#include "apiclient.h"

int main(int argc, char *argv[])
{
    QGuiApplication app(argc, argv);
    
    // Set application properties
    app.setApplicationName("Audio Fingerprinting Client");
    app.setApplicationVersion("1.0.0");
    app.setOrganizationName("Audio Fingerprinting");
    app.setOrganizationDomain("audiofingerprinting.com");
    
    // Register QML types
    qmlRegisterType<AudioRecorder>("AudioFingerprinting", 1, 0, "AudioRecorder");
    qmlRegisterType<ApiClient>("AudioFingerprinting", 1, 0, "ApiClient");
    
    QQmlApplicationEngine engine;
    
    // Create and expose C++ objects to QML
    AudioRecorder audioRecorder;
    ApiClient apiClient;
    
    engine.rootContext()->setContextProperty("audioRecorder", &audioRecorder);
    engine.rootContext()->setContextProperty("apiClient", &apiClient);
    
    // Load main QML file
    const QUrl url(QStringLiteral("qrc:/AudioFingerprinting/qml/Main.qml"));
    QObject::connect(&engine, &QQmlApplicationEngine::objectCreated,
                     &app, [url](QObject *obj, const QUrl &objUrl) {
        if (!obj && url == objUrl)
            QCoreApplication::exit(-1);
    }, Qt::QueuedConnection);
    
    engine.load(url);
    
    return app.exec();
}