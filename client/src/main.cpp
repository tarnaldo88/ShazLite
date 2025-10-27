#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QQmlContext>
#include <QDebug>

#include "audiorecorder.h"
#include "apiclient.h"

int main(int argc, char *argv[])
{
    QGuiApplication app(argc, argv);
    
    // Register QML types
    qmlRegisterType<AudioRecorder>("AudioFingerprinting", 1, 0, "AudioRecorder");
    qmlRegisterType<ApiClient>("AudioFingerprinting", 1, 0, "ApiClient");
    
    QQmlApplicationEngine engine;
    
    // Create and expose C++ objects to QML
    AudioRecorder audioRecorder;
    ApiClient apiClient;
    
    engine.rootContext()->setContextProperty("audioRecorder", &audioRecorder);
    engine.rootContext()->setContextProperty("apiClient", &apiClient);
    
    // Connect audioRecorder signals to apiClient
    QObject::connect(&audioRecorder, &AudioRecorder::recordingCompleted,
                     &apiClient, &ApiClient::identifyAudio);
    
    // Connect apiClient signals for debugging
    QObject::connect(&apiClient, &ApiClient::identificationResult,
                     [](const QJsonObject &result) {
                         qDebug() << "Identification result:" << result;
                     });
    
    QObject::connect(&apiClient, &ApiClient::identificationFailed,
                     [](const QString &error) {
                         qDebug() << "Identification failed:" << error;
                     });
    
    // Use a working QML directly
    engine.loadData(R"QML(
import QtQuick 2.15
import QtQuick.Controls 2.15

ApplicationWindow {
    width: 400
    height: 600
    visible: true
    title: "ShazLite by Torres"
    
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#2c2c2c" }
            GradientStop { position: 1.0; color: "#1a1a1a" }
        }
        
        Column {
            anchors.centerIn: parent
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
            
            Text {
                text: "ShazLite"
                font.pixelSize: 28
                font.bold: true
                color: "#ffffff"
                anchors.horizontalCenter: parent.horizontalCenter
            }
            
            Text {
                id: statusText
                text: {
                    if (typeof audioRecorder === "undefined") {
                        return "AudioRecorder not available"
                    } else if (!audioRecorder.hasPermission) {
                        return "Click to request microphone permission"
                    } else if (audioRecorder.isRecording) {
                        return "Recording... " + audioRecorder.recordingProgress + "%"
                    } else if (apiClient.isProcessing) {
                        return "Identifying song..."
                    } else {
                        return "Ready to record"
                    }
                }
                font.pixelSize: 16
                color: "#cccccc"
                anchors.horizontalCenter: parent.horizontalCenter
                wrapMode: Text.WordWrap
                width: parent.width * 0.8
                horizontalAlignment: Text.AlignHCenter
            }
            
            Button {
                text: audioRecorder.isRecording ? "Stop Recording" : "Record Audio"
                anchors.horizontalCenter: parent.horizontalCenter
                width: 200
                height: 60
                
                background: Rectangle {
                    color: parent.pressed ? "#0d7377" : (audioRecorder.isRecording ? "#e74c3c" : "#14a085")
                    radius: 30
                    border.color: audioRecorder.isRecording ? "#c0392b" : "#0d7377"
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
                
                onClicked: {
                    console.log("Record button clicked!")
                    console.log("audioRecorder available:", typeof audioRecorder !== "undefined")
                    
                    if (typeof audioRecorder !== "undefined") {
                        console.log("audioRecorder.hasPermission:", audioRecorder.hasPermission)
                        console.log("audioRecorder.isRecording:", audioRecorder.isRecording)
                        
                        if (!audioRecorder.hasPermission) {
                            console.log("Requesting permission...")
                            audioRecorder.requestPermission()
                        } else if (audioRecorder.isRecording) {
                            console.log("Stopping recording...")
                            audioRecorder.stopRecording()
                        } else {
                            console.log("Starting recording...")
                            audioRecorder.startRecording()
                        }
                    } else {
                        console.log("audioRecorder is not available!")
                    }
                }
            }
            
            ProgressBar {
                anchors.horizontalCenter: parent.horizontalCenter
                width: 200
                visible: audioRecorder.isRecording || apiClient.isProcessing
                value: {
                    if (audioRecorder.isRecording) {
                        return audioRecorder.recordingProgress / 100.0
                    } else if (apiClient.isProcessing) {
                        return apiClient.uploadProgress > 0 ? apiClient.uploadProgress / 100.0 : -1
                    }
                    return 0
                }
                indeterminate: apiClient.isProcessing && apiClient.uploadProgress === 0
            }
        }
    }
}
)QML");
    
    return app.exec();
}