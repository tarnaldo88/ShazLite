#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QQmlContext>
#include <QDebug>
#include <iostream>

#include "audiorecorder.h"
#include "apiclient.h"

int main(int argc, char *argv[])
{
    std::cout << "Starting application..." << std::endl;
    
    QGuiApplication app(argc, argv);
    
    std::cout << "QGuiApplication created" << std::endl;
    
    // Register QML types
    qmlRegisterType<AudioRecorder>("AudioFingerprinting", 1, 0, "AudioRecorder");
    qmlRegisterType<ApiClient>("AudioFingerprinting", 1, 0, "ApiClient");
    
    std::cout << "QML types registered" << std::endl;
    
    QQmlApplicationEngine engine;
    
    // Create and expose C++ objects to QML
    AudioRecorder audioRecorder;
    ApiClient apiClient;
    
    engine.rootContext()->setContextProperty("audioRecorder", &audioRecorder);
    engine.rootContext()->setContextProperty("apiClient", &apiClient);
    
    std::cout << "C++ objects exposed to QML" << std::endl;
    
    // Create simple inline QML
    QString simpleQml = R"(
import QtQuick 2.15
import QtQuick.Controls 2.15

ApplicationWindow {
    width: 400
    height: 300
    visible: true
    title: "Simple Test"
    
    Column {
        anchors.centerIn: parent
        spacing: 20
        
        Text {
            text: "Simple QML Test"
            font.pixelSize: 20
            anchors.horizontalCenter: parent.horizontalCenter
        }
        
        Button {
            text: "Test Button"
            anchors.horizontalCenter: parent.horizontalCenter
            onClicked: {
                console.log("Button clicked!")
                console.log("audioRecorder available:", typeof audioRecorder !== "undefined")
            }
        }
    }
}
)";
    
    std::cout << "Loading simple QML..." << std::endl;
    
    engine.loadData(simpleQml.toUtf8());
    
    std::cout << "QML loaded, root objects: " << engine.rootObjects().size() << std::endl;
    
    if (engine.rootObjects().isEmpty()) {
        std::cout << "No root objects created!" << std::endl;
        return -1;
    }
    
    std::cout << "Starting event loop..." << std::endl;
    return app.exec();
}