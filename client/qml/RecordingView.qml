import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "components"

Page {
    id: root
    
    property var lastRecordedAudio: null
    
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
            text: {
                if (!audioRecorder.hasPermission) {
                    return "Microphone permission required"
                } else if (audioRecorder.isRecording) {
                    return "Recording audio..."
                } else {
                    return "Tap the microphone to identify a song"
                }
            }
            font.pixelSize: 16
            color: !audioRecorder.hasPermission ? "#e74c3c" : "#7f8c8d"
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
            enabled: audioRecorder.hasPermission || !audioRecorder.isRecording
            
            onClicked: {
                if (!audioRecorder.hasPermission) {
                    audioRecorder.requestPermission()
                } else if (audioRecorder.isRecording) {
                    audioRecorder.stopRecording()
                } else {
                    audioRecorder.startRecording()
                }
            }
        }

        // Permission request button (when permission is denied)
        Button {
            text: "Grant Microphone Permission"
            Layout.alignment: Qt.AlignHCenter
            visible: !audioRecorder.hasPermission && !audioRecorder.isRecording
            
            onClicked: {
                audioRecorder.requestPermission()
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
                    // Show upload progress if available, otherwise indeterminate
                    return apiClient.uploadProgress > 0 ? apiClient.uploadProgress / 100.0 : -1
                }
                return 0
            }
            
            indeterminate: apiClient.isProcessing && apiClient.uploadProgress === 0
        }

        // Status text
        Label {
            text: {
                if (audioRecorder.isRecording) {
                    return `Recording: ${audioRecorder.recordingProgress}%`
                } else if (apiClient.isProcessing) {
                    if (apiClient.uploadProgress > 0 && apiClient.uploadProgress < 100) {
                        return `Uploading: ${apiClient.uploadProgress}%`
                    } else {
                        return "Identifying song..."
                    }
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

        // Loading indicator and cancel button
        ColumnLayout {
            Layout.alignment: Qt.AlignHCenter
            spacing: 15
            visible: apiClient.isProcessing

            LoadingIndicator {
                Layout.alignment: Qt.AlignHCenter
                running: apiClient.isProcessing
            }

            Button {
                text: "Cancel"
                Layout.alignment: Qt.AlignHCenter
                onClicked: apiClient.cancelCurrentRequest()
            }
        }

        // Audio format selection
        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            visible: !audioRecorder.isRecording && !apiClient.isProcessing
            spacing: 20

            Label {
                text: "Format:"
                font.pixelSize: 14
                color: "#7f8c8d"
            }

            ButtonGroup {
                id: formatGroup
            }

            RadioButton {
                text: "WAV"
                checked: audioRecorder.audioFormat === "wav"
                ButtonGroup.group: formatGroup
                onClicked: audioRecorder.audioFormat = "wav"
            }

            RadioButton {
                text: "MP3"
                checked: audioRecorder.audioFormat === "mp3"
                ButtonGroup.group: formatGroup
                onClicked: audioRecorder.audioFormat = "mp3"
                enabled: false // Disabled for now since MP3 encoding is not fully implemented
                opacity: 0.5
            }
        }
    }

    // Connect to audio recorder signals
    Connections {
        target: audioRecorder
        
        function onRecordingCompleted(audioData) {
            root.lastRecordedAudio = audioData
            root.recordingCompleted(audioData)
        }
        
        function onRecordingFailed(error) {
            root.showError(error)
        }
        
        function onPermissionGranted() {
            // Permission granted, user can now record
        }
        
        function onPermissionDenied() {
            root.showError("Microphone permission is required to record audio. Please enable it in your system settings.")
        }
    }

    // Connect to API client retry signals
    Connections {
        target: apiClient
        
        function onRetryAttempt(attempt, maxRetries) {
            retryStatusLabel.text = `Retrying... (${attempt}/${maxRetries})`
            retryStatusLabel.visible = true
        }
        
        function onIdentificationResult(result) {
            retryStatusLabel.visible = false
        }
        
        function onIdentificationFailed(error) {
            retryStatusLabel.visible = false
        }
    }

    // Retry status label
    Label {
        id: retryStatusLabel
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottomMargin: 20
        text: ""
        font.pixelSize: 12
        color: "#f39c12"
        visible: false
        
        background: Rectangle {
            color: "#fff3cd"
            border.color: "#ffeaa7"
            border.width: 1
            radius: 4
            anchors.fill: parent
            anchors.margins: -8
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