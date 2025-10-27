import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Page {
    id: root
    
    property var result: null
    
    signal backToRecording()

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

            // Result card
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: resultContent.implicitHeight + 40
                color: "#ffffff"
                border.color: "#e1e8ed"
                border.width: 1
                radius: 12

                ColumnLayout {
                    id: resultContent
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 15

                    // Success/failure indicator
                    Rectangle {
                        Layout.alignment: Qt.AlignHCenter
                        width: 60
                        height: 60
                        radius: 30
                        color: hasMatch ? "#27ae60" : "#e74c3c"
                        
                        property bool hasMatch: result && result.song_id !== undefined

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

                    // No match message
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 10
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
                            text: "We couldn't identify this song. Try recording in a quieter environment or closer to the audio source."
                            font.pixelSize: 14
                            color: "#7f8c8d"
                            horizontalAlignment: Text.AlignHCenter
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
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
                visible: result && result.confidence !== undefined

                ColumnLayout {
                    id: detailsContent
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 15

                    Label {
                        text: "Match Details"
                        font.pixelSize: 18
                        font.bold: true
                        color: "#2c3e50"
                    }

                    GridLayout {
                        Layout.fillWidth: true
                        columns: 2
                        columnSpacing: 20
                        rowSpacing: 10

                        Label {
                            text: "Confidence:"
                            font.bold: true
                            color: "#34495e"
                        }

                        Label {
                            text: result ? `${Math.round((result.confidence || 0) * 100)}%` : ""
                            color: "#27ae60"
                        }

                        Label {
                            text: "Matches:"
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
                            text: "Position:"
                            font.bold: true
                            color: "#34495e"
                            visible: result && result.time_offset_ms !== undefined
                        }

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
                            visible: result && result.time_offset_ms !== undefined
                        }
                    }
                }
            }

            // Action buttons
            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: 20

                Button {
                    text: "Record Again"
                    Layout.fillWidth: true
                    highlighted: true
                    onClicked: root.backToRecording()
                }
            }
        }
    }
}