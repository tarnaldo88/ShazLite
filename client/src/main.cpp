#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QQmlContext>
#include <QQuickStyle>
#include <QDebug>
#include <QQuickWindow>
#include <QLoggingCategory>
#include <QFile>

#include "audiorecorder.h"
#include "apiclient.h"

int main(int argc, char *argv[])
{
    QGuiApplication app(argc, argv);
    
    // Set Qt Quick Controls style to one that supports customization
    QQuickStyle::setStyle("Material");
    
    // Set application properties
    app.setApplicationName("ShazLite by Torres");
    app.setApplicationVersion("1.0.0");
    app.setOrganizationName("Torres ShazLite");
    app.setOrganizationDomain("ShazLiteTorres.com");
    
    // Register QML types - this must be done before loading QML
    qmlRegisterType<AudioRecorder>("AudioFingerprinting", 1, 0, "AudioRecorder");
    qmlRegisterType<ApiClient>("AudioFingerprinting", 1, 0, "ApiClient");
    
    QQmlApplicationEngine engine;
    
    // Create and expose C++ objects to QML
    AudioRecorder audioRecorder;
    ApiClient apiClient;
    
    engine.rootContext()->setContextProperty("audioRecorder", &audioRecorder);
    engine.rootContext()->setContextProperty("apiClient", &apiClient);
    
    // Load main QML file - try different resource paths
    QStringList possiblePaths = {
        "qrc:/AudioFingerprinting/qml/Main.qml",
        "qrc:/qt/qml/AudioFingerprinting/qml/Main.qml", 
        "qrc:/qml/Main.qml",
        "qrc:/Main.qml"
    };
    
    QUrl workingUrl;
    for (const QString &path : possiblePaths) {
        QUrl testUrl(path);
        qDebug() << "Testing QML path:" << testUrl;
        
        // Check if resource exists
        QFile file(testUrl.toString());
        if (file.exists()) {
            qDebug() << "Found QML file at:" << testUrl;
            workingUrl = testUrl;
            break;
        } else {
            qDebug() << "QML file not found at:" << testUrl;
        }
    }
    
    if (workingUrl.isEmpty()) {
        qDebug() << "No QML file found, falling back to simple QML";
        engine.loadData(R"(
            import QtQuick 2.15
            import QtQuick.Window 2.15
            import QtQuick.Controls 2.15
            
            ApplicationWindow {
                width: 400
                height: 600
                visible: true
                title: "ShazLite by Torres"
                
                // Dark gradient background
                background: Rectangle {
                    gradient: Gradient {
                        GradientStop { position: 0.0; color: "#2c2c2c" }
                        GradientStop { position: 1.0; color: "#1a1a1a" }
                    }
                }
                
                Column {
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 30
                    
                    // Logo at the top center
                    Image {
                        id: logo
                        source: "qrc:/AudioFingerprinting/public/ShazLiteTorres.png"
                        width: 180
                        height: 180
                        fillMode: Image.PreserveAspectFit
                        anchors.horizontalCenter: parent.horizontalCenter
                        anchors.topMargin: 40
                    }
                    
                    // Spacer to push content down
                    Item {
                        width: 1
                        height: 60
                    }
                    
                    // Main content area
                    Column {
                        anchors.horizontalCenter: parent.horizontalCenter
                        spacing: 20
                        
                        Text {
                            text: "ShazLite"
                            font.pixelSize: 28
                            font.bold: true
                            color: "#ffffff"
                            anchors.horizontalCenter: parent.horizontalCenter
                        }
                        
                        Text {
                            text: "Audio Fingerprinting Client"
                            font.pixelSize: 16
                            color: "#cccccc"
                            anchors.horizontalCenter: parent.horizontalCenter
                        }
                        
                        Button {
                            text: "Record Audio"
                            anchors.horizontalCenter: parent.horizontalCenter
                            width: 200
                            height: 50
                            
                            background: Rectangle {
                                color: parent.pressed ? "#0d7377" : "#14a085"
                                radius: 25
                                border.color: "#0d7377"
                                border.width: 2
                            }
                            
                            contentItem: Text {
                                text: parent.text
                                font.pixelSize: 16
                                font.bold: true
                                color: "#ffffff"
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            
                            onClicked: console.log("Record button clicked")
                        }
                    }
                }
            }
        )");
    } else {
        qDebug() << "Loading QML from:" << workingUrl;
        engine.load(workingUrl);
    }
    
    qDebug() << "QML load completed. Root objects count:" << engine.rootObjects().size();
    
    if (engine.rootObjects().isEmpty()) {
        qDebug() << "No root objects created - QML loading failed";
        return -1;
    }
    
    qDebug() << "QML loaded successfully";
    
    // Ensure the window is visible
    QObject *rootObject = engine.rootObjects().first();
    if (rootObject) {
        qDebug() << "Root object type:" << rootObject->metaObject()->className();
        QQuickWindow *window = qobject_cast<QQuickWindow*>(rootObject);
        if (window) {
            qDebug() << "Found window, showing it";
            window->show();
            window->raise();
            window->requestActivate();
        } else {
            qDebug() << "Root object is not a QQuickWindow";
        }
    }
    
    qDebug() << "Starting event loop";
    return app.exec();
}
