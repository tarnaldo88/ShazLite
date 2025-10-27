import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "components"

Page {
    id: root
    
    property var result: null
    property bool isLoading: false
    property string errorMessage: ""
    property bool hasError: errorMessage.length > 0
    
    signal backToRecording()
    signal retryIdentification()

    header: ToolBar {
        RowLayout {
            anchors.fill: parent
            
            Button {
                text: "← Back"
                flat: true
                onClicked: root.backToRecording()
            }
            
            Label {
                text: "Results"
                font.bold: true
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
            }
            
            // Spacer
            Item {
                Layout.preferredWidth: 60
            }
        }
    }

    ScrollView {
        anchors.fill: parent
        contentWidth: availableWidth

        ColumnLayout {
            width: parent.width
            spacing: 30
            anchors.margins: 20

            // Loading state
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: loadingContent.implicitHeight + 40
                color: "#ffffff"
                border.color: "#e1e8ed"
                border.width: 1
                radius: 12
                visible: root.isLoading

                ColumnLayout {
                    id: loadingContent
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 20

                    ProcessingAnimation {
                        Layout.alignment: Qt.AlignHCenter
                        running: root.isLoading
                        stage: {
                            // Determine stage based on API client state if available
                            if (typeof apiClient !== "undefined") {
                                if (apiClient.uploadProgress > 0 && apiClient.uploadProgress < 100) {
                                    return "uploading"
                                } else if (apiClient.isProcessing) {
                                    return "processing"
                                }
                            }
                            return "matching"
                        }
                        progress: {
                            if (typeof apiClient !== "undefined" && apiClient.uploadProgress > 0) {
                                return apiClient.uploadProgress / 100.0
                            }
                            return 0.0
                        }
                    }

                    Label {
                        text: "Identifying Song"
                        font.pixelSize: 20
                        font.bold: true
                        color: "#2c3e50"
                        horizontalAlignment: Text.AlignHCenter
                        Layout.fillWidth: true
                    }

                    Label {
                        text: "Analyzing your audio sample using advanced fingerprinting technology"
                        font.pixelSize: 14
                        color: "#7f8c8d"
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }

                    // Progress steps
                    RowLayout {
                        Layout.fillWidth: true
                        Layout.topMargin: 10
                        spacing: 20

                        Repeater {
                            model: ["Upload", "Process", "Match"]
                            
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                
                                Rectangle {
                                    Layout.alignment: Qt.AlignHCenter
                                    width: 24
                                    height: 24
                                    radius: 12
                                    color: {
                                        var currentStage = loadingContent.parent.parent.parent.stage || "uploading"
                                        var stages = ["uploading", "processing", "matching"]
                                        var currentIndex = stages.indexOf(currentStage)
                                        return index <= currentIndex ? "#28a745" : "#dee2e6"
                                    }
                                    
                                    Label {
                                        anchors.centerIn: parent
                                        text: index + 1
                                        font.pixelSize: 12
                                        font.bold: true
                                        color: {
                                            var currentStage = loadingContent.parent.parent.parent.stage || "uploading"
                                            var stages = ["uploading", "processing", "matching"]
                                            var currentIndex = stages.indexOf(currentStage)
                                            return index <= currentIndex ? "white" : "#6c757d"
                                        }
                                    }
                                }
                                
                                Label {
                                    text: modelData
                                    font.pixelSize: 10
                                    color: "#6c757d"
                                    Layout.alignment: Qt.AlignHCenter
                                }
                            }
                        }
                    }
                }
            }

            // Error state
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: errorContent.implicitHeight + 40
                color: "#ffffff"
                border.color: "#e74c3c"
                border.width: 2
                radius: 12
                visible: root.hasError && !root.isLoading

                ColumnLayout {
                    id: errorContent
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 15

                    Rectangle {
                        Layout.alignment: Qt.AlignHCenter
                        width: 60
                        height: 60
                        radius: 30
                        color: "#e74c3c"

                        Label {
                            anchors.centerIn: parent
                            text: "!"
                            font.pixelSize: 30
                            color: "white"
                            font.bold: true
                        }
                    }

                    Label {
                        text: "Error"
                        font.pixelSize: 24
                        font.bold: true
                        color: "#e74c3c"
                        horizontalAlignment: Text.AlignHCenter
                        Layout.fillWidth: true
                    }

                    Label {
                        text: root.errorMessage
                        font.pixelSize: 14
                        color: "#7f8c8d"
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }

                    Button {
                        text: "Try Again"
                        Layout.alignment: Qt.AlignHCenter
                        highlighted: true
                        onClicked: root.retryIdentification()
                    }
                }
            }

            // Result card
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: resultContent.implicitHeight + 40
                color: "#ffffff"
                border.color: "#e1e8ed"
                border.width: 1
                radius: 12
                visible: !root.isLoading && !root.hasError

                ColumnLayout {
                    id: resultContent
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 15

                    // Success/failure indicator with animation
                    Rectangle {
                        Layout.alignment: Qt.AlignHCenter
                        width: 60
                        height: 60
                        radius: 30
                        color: hasMatch ? "#27ae60" : "#e74c3c"
                        
                        property bool hasMatch: result && result.song_id !== undefined

                        // Pulse animation for successful match
                        SequentialAnimation on scale {
                            running: hasMatch && !root.isLoading
                            loops: 1
                            NumberAnimation { to: 1.2; duration: 300; easing.type: Easing.OutQuad }
                            NumberAnimation { to: 1.0; duration: 300; easing.type: Easing.InQuad }
                        }

                        Label {
                            anchors.centerIn: parent
                            text: parent.hasMatch ? "✓" : "✗"
                            font.pixelSize: 30
                            color: "white"
                            font.bold: true
                        }
                    }

                    // Song information
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 10
                        visible: result && result.song_id !== undefined

                        Label {
                            text: result ? (result.title || "Unknown Title") : ""
                            font.pixelSize: 24
                            font.bold: true
                            color: "#2c3e50"
                            horizontalAlignment: Text.AlignHCenter
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }

                        Label {
                            text: result ? (result.artist || "Unknown Artist") : ""
                            font.pixelSize: 18
                            color: "#7f8c8d"
                            horizontalAlignment: Text.AlignHCenter
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }

                        Label {
                            text: result ? (result.album || "") : ""
                            font.pixelSize: 14
                            color: "#95a5a6"
                            horizontalAlignment: Text.AlignHCenter
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                            visible: text.length > 0
                        }
                    }

                    // No match message with enhanced feedback
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 15
                        visible: !result || result.song_id === undefined

                        Label {
                            text: "Song Not Found"
                            font.pixelSize: 24
                            font.bold: true
                            color: "#e74c3c"
                            horizontalAlignment: Text.AlignHCenter
                            Layout.fillWidth: true
                        }

                        Label {
                            text: "We couldn't identify this song in our database."
                            font.pixelSize: 16
                            color: "#7f8c8d"
                            horizontalAlignment: Text.AlignHCenter
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: tipsContent.implicitHeight + 20
                            color: "#f8f9fa"
                            border.color: "#dee2e6"
                            border.width: 1
                            radius: 8

                            ColumnLayout {
                                id: tipsContent
                                anchors.fill: parent
                                anchors.margins: 15
                                spacing: 8

                                Label {
                                    text: "Tips for better results:"
                                    font.pixelSize: 14
                                    font.bold: true
                                    color: "#495057"
                                }

                                Label {
                                    text: "• Record in a quieter environment"
                                    font.pixelSize: 12
                                    color: "#6c757d"
                                    Layout.fillWidth: true
                                }

                                Label {
                                    text: "• Get closer to the audio source"
                                    font.pixelSize: 12
                                    color: "#6c757d"
                                    Layout.fillWidth: true
                                }

                                Label {
                                    text: "• Ensure the song is playing clearly"
                                    font.pixelSize: 12
                                    color: "#6c757d"
                                    Layout.fillWidth: true
                                }
                            }
                        }
                    }
                }
            }

            // Match details (if available)
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: detailsContent.implicitHeight + 40
                color: "#f8f9fa"
                border.color: "#e1e8ed"
                border.width: 1
                radius: 12
                visible: result && result.confidence !== undefined && !root.isLoading && !root.hasError

                ColumnLayout {
                    id: detailsContent
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 20

                    Label {
                        text: "Match Details"
                        font.pixelSize: 18
                        font.bold: true
                        color: "#2c3e50"
                    }

                    // Confidence indicator
                    ConfidenceIndicator {
                        Layout.alignment: Qt.AlignHCenter
                        confidence: result ? (result.confidence || 0) : 0
                        animated: !root.isLoading
                    }

                    // Additional match information
                    GridLayout {
                        Layout.fillWidth: true
                        columns: 2
                        columnSpacing: 20
                        rowSpacing: 15

                        Label {
                            text: "Fingerprint Matches:"
                            font.bold: true
                            color: "#34495e"
                            visible: result && result.match_count !== undefined
                        }

                        Label {
                            text: result ? (result.match_count || 0).toString() : ""
                            color: "#34495e"
                            visible: result && result.match_count !== undefined
                        }

                        Label {
                            text: "Song Position:"
                            font.bold: true
                            color: "#34495e"
                            visible: result && result.time_offset_ms !== undefined
                        }

                        RowLayout {
                            visible: result && result.time_offset_ms !== undefined
                            
                            Label {
                                text: {
                                    if (result && result.time_offset_ms !== undefined) {
                                        const seconds = Math.round(result.time_offset_ms / 1000)
                                        const minutes = Math.floor(seconds / 60)
                                        const remainingSeconds = seconds % 60
                                        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
                                    }
                                    return ""
                                }
                                color: "#34495e"
                            }
                            
                            Rectangle {
                                width: 16
                                height: 16
                                radius: 8
                                color: "#17a2b8"
                                
                                Label {
                                    anchors.centerIn: parent
                                    text: "▶"
                                    font.pixelSize: 8
                                    color: "white"
                                }
                            }
                        }
                    }

                    // Processing time (if available)
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: processingInfo.implicitHeight + 16
                        color: "#ffffff"
                        border.color: "#dee2e6"
                        border.width: 1
                        radius: 6
                        visible: result && result.processing_time_ms !== undefined

                        RowLayout {
                            id: processingInfo
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 10

                            Rectangle {
                                width: 20
                                height: 20
                                radius: 10
                                color: "#28a745"

                                Label {
                                    anchors.centerIn: parent
                                    text: "⚡"
                                    font.pixelSize: 10
                                    color: "white"
                                }
                            }

                            Label {
                                text: `Processed in ${result ? Math.round(result.processing_time_ms || 0) : 0}ms`
                                font.pixelSize: 12
                                color: "#6c757d"
                                Layout.fillWidth: true
                            }
                        }
                    }
                }
            }

            // Action buttons
            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: 20
                spacing: 15
                visible: !root.isLoading

                Button {
                    text: "Record Again"
                    Layout.fillWidth: true
                    highlighted: true
                    onClicked: root.backToRecording()
                }

                Button {
                    text: "Retry"
                    Layout.fillWidth: true
                    visible: root.hasError
                    onClicked: root.retryIdentification()
                }
            }
        }
    }
}