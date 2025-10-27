import QtQuick 2.15
import QtQuick.Window 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import AudioFingerprinting 1.0

ApplicationWindow {
    id: window
    width: 400
    height: 600
    visible: true
    title: qsTr("Audio Fingerprinting")
    
    property bool isRecording: audioRecorder.isRecording
    property bool isProcessing: apiClient.isProcessing
    property var currentResult: null

    // Main content area
    StackView {
        id: stackView
        anchors.fill: parent
        initialItem: recordingView
    }

    // Recording view component
    Component {
        id: recordingView
        RecordingView {
            onRecordingCompleted: function(audioData) {
                apiClient.identifyAudio(audioData)
            }
            onShowResults: function(result) {
                currentResult = result
                stackView.push(resultsView)
            }
        }
    }

    // Results view component
    Component {
        id: resultsView
        ResultsView {
            result: currentResult
            onBackToRecording: {
                stackView.pop()
                currentResult = null
            }
        }
    }

    // Connect API client signals
    Connections {
        target: apiClient
        
        function onIdentificationResult(result) {
            if (stackView.currentItem && stackView.currentItem.showResults) {
                stackView.currentItem.showResults(result)
            }
        }
        
        function onIdentificationFailed(error) {
            if (stackView.currentItem && stackView.currentItem.showError) {
                stackView.currentItem.showError(error)
            }
        }
    }

    // Status bar
    footer: ToolBar {
        RowLayout {
            anchors.fill: parent
            
            Label {
                text: {
                    if (isRecording) return "Recording..."
                    if (isProcessing) return "Processing..."
                    return "Ready"
                }
                Layout.fillWidth: true
            }
            
            Button {
                text: "Settings"
                flat: true
                onClicked: {
                    // TODO: Open settings dialog
                }
            }
        }
    }
}