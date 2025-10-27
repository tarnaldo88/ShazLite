import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "components"

Page {
    id: root
    
    signal recordingCompleted(var audioData)
    signal showResults(var result)
    signal showError(string error)

    ColumnLayout {
        anchors.centerIn: parent
        spacing: 40
        width: Math.min(parent.width * 0.8, 300)

        // App title
        Label {
            text: "Audio Fingerprinting"
            font.pixelSize: 28
            font.bold: true
            color: "#2c3e50"
            Layout.alignment: Qt.AlignHCenter
        }

        // Instructions
        Label {
            text: audioRecorder.isRecording ? 
                  "Recording audio..." : 
                  "Tap the microphone to identify a song"
            font.pixelSize: 16
            color: "#7f8c8d"
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignHCenter
        }

        // Record button
        RecordButton {
            id: recordButton
            Layout.alignment: Qt.AlignHCenter
            isRecording: audioRecorder.isRecording
            progress: audioRecorder.recordingProgress
            
            onClicked: {
                if (audioRecorder.isRecording) {
                    audioRecorder.stopRecording()
                } else {
                    audioRecorder.startRecording()
                }
            }
        }

        // Progress indicator
        ProgressBar {
            id: progressBar
            Layout.fillWidth: true
            Layout.preferredHeight: 8
            visible: audioRecorder.isRecording || apiClient.isProcessing
            
            value: {
                if (audioRecorder.isRecording) {
                    return audioRecorder.recordingProgress / 100.0
                } else if (apiClient.isProcessing) {
                    return -1 // Indeterminate
                }
                return 0
            }
            
            indeterminate: apiClient.isProcessing
        }

        // Status text
        Label {
            text: {
                if (audioRecorder.isRecording) {
                    return `Recording: ${audioRecorder.recordingProgress}%`
                } else if (apiClient.isProcessing) {
                    return "Identifying song..."
                } else if (audioRecorder.errorMessage) {
                    return audioRecorder.errorMessage
                }
                return ""
            }
            font.pixelSize: 14
            color: audioRecorder.errorMessage ? "#e74c3c" : "#34495e"
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignHCenter
            visible: text.length > 0
        }

        // Loading indicator
        LoadingIndicator {
            Layout.alignment: Qt.AlignHCenter
            visible: apiClient.isProcessing
            running: apiClient.isProcessing
        }
    }

    // Connect to audio recorder signals
    Connections {
        target: audioRecorder
        
        function onRecordingCompleted(audioData) {
            root.recordingCompleted(audioData)
        }
        
        function onRecordingFailed(error) {
            root.showError(error)
        }
    }

    // Error dialog
    Dialog {
        id: errorDialog
        anchors.centerIn: parent
        title: "Error"
        standardButtons: Dialog.Ok
        
        property string errorMessage: ""
        
        Label {
            text: errorDialog.errorMessage
            wrapMode: Text.WordWrap
        }
    }

    function showError(error) {
        errorDialog.errorMessage = error
        errorDialog.open()
    }
}