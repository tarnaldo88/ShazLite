import QtQuick 2.15
import QtQuick.Window 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
// import AudioFingerprinting 1.0

ApplicationWindow {
    id: window
    width: 400
    height: 600
    visible: true
    title: qsTr("ShazLite by Torres")
    
    property bool isRecording: audioRecorder.isRecording
    property bool isProcessing: apiClient.isProcessing
    property var currentResult: null
    
    // Dark gradient background
    background: Rectangle {
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#2c2c2c" }
            GradientStop { position: 1.0; color: "#1a1a1a" }
        }
    }

    // Logo at the top center
    Image {
        id: logo
        source: "qrc:/AudioFingerprinting/public/ShazLiteTorres.png"
        width: 100
        height: 100
        fillMode: Image.PreserveAspectFit
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        anchors.topMargin: 20
        z: 10 // Ensure logo stays on top
    }

    // Main content area
    StackView {
        id: stackView
        anchors.fill: parent
        anchors.topMargin: 140 // Make room for the logo
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
            isLoading: apiClient.isProcessing
            
            onBackToRecording: {
                stackView.pop()
                currentResult = null
            }
            
            onRetryIdentification: {
                // Get the last recorded audio from recording view if available
                var recordingPage = stackView.get(0)
                if (recordingPage && recordingPage.lastRecordedAudio) {
                    apiClient.identifyAudio(recordingPage.lastRecordedAudio)
                } else {
                    // Go back to recording view to record again
                    stackView.pop()
                    currentResult = null
                }
            }
        }
    }

    // Connect API client signals
    Connections {
        target: apiClient
        
        function onIdentificationResult(result) {
            currentResult = result
            
            // If we're on recording view, navigate to results
            if (stackView.currentItem && stackView.currentItem.showResults) {
                stackView.currentItem.showResults(result)
            } else if (stackView.depth === 1) {
                // Navigate to results view
                stackView.push(resultsView)
            } else {
                // Update existing results view
                var resultsPage = stackView.get(stackView.depth - 1)
                if (resultsPage) {
                    resultsPage.result = result
                    resultsPage.isLoading = false
                    resultsPage.errorMessage = ""
                }
            }
        }
        
        function onIdentificationFailed(error) {
            // Determine error type for better UX
            var errorType = "general"
            if (error.includes("timeout") || error.includes("Timeout")) {
                errorType = "timeout"
            } else if (error.includes("network") || error.includes("Network") || error.includes("connection")) {
                errorType = "network"
            } else if (error.includes("server") || error.includes("Server") || error.includes("500")) {
                errorType = "server"
            }
            
            if (stackView.currentItem && stackView.currentItem.showError) {
                stackView.currentItem.showError(error)
            } else if (stackView.depth === 1) {
                // Navigate to results view with error
                currentResult = null
                var resultsComponent = stackView.push(resultsView)
                if (resultsComponent) {
                    resultsComponent.isLoading = false
                    resultsComponent.errorMessage = error
                }
            } else {
                // Update existing results view with error
                var resultsPage = stackView.get(stackView.depth - 1)
                if (resultsPage) {
                    resultsPage.result = null
                    resultsPage.isLoading = false
                    resultsPage.errorMessage = error
                }
            }
        }
    }

    // Status bar
    footer: ToolBar {
        background: Rectangle {
            color: "#1a1a1a"
            border.color: "#333333"
            border.width: 1
        }
        
        RowLayout {
            anchors.fill: parent
            
            Label {
                text: {
                    if (isRecording) return "Recording..."
                    if (isProcessing) return "Processing..."
                    return "Ready"
                }
                color: "#ffffff"
                Layout.fillWidth: true
            }
            
            Button {
                text: "Settings"
                flat: true
                
                background: Rectangle {
                    color: parent.pressed ? "#333333" : "transparent"
                    radius: 4
                }
                
                contentItem: Text {
                    text: parent.text
                    color: "#cccccc"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                
                onClicked: {
                    // TODO: Open settings dialog
                }
            }
        }
    }
}