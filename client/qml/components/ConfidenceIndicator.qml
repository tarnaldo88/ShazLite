import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: root
    
    property real confidence: 0.0
    property bool animated: true
    
    width: 200
    height: 60
    
    Rectangle {
        anchors.fill: parent
        color: "#f8f9fa"
        border.color: "#dee2e6"
        border.width: 1
        radius: 8
        
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 5
            
            RowLayout {
                Layout.fillWidth: true
                
                Label {
                    text: "Confidence"
                    font.pixelSize: 12
                    font.bold: true
                    color: "#495057"
                }
                
                Label {
                    text: `${Math.round(root.confidence * 100)}%`
                    font.pixelSize: 14
                    font.bold: true
                    color: getConfidenceColor()
                    Layout.alignment: Qt.AlignRight
                }
            }
            
            // Progress bar for confidence
            Rectangle {
                Layout.fillWidth: true
                height: 8
                color: "#e9ecef"
                radius: 4
                
                Rectangle {
                    id: confidenceBar
                    height: parent.height
                    radius: 4
                    color: getConfidenceColor()
                    width: 0
                    
                    NumberAnimation on width {
                        running: root.animated
                        to: parent.width * root.confidence
                        duration: 1000
                        easing.type: Easing.OutQuad
                    }
                }
            }
            
            Label {
                text: getConfidenceText()
                font.pixelSize: 10
                color: "#6c757d"
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
            }
        }
    }
    
    function getConfidenceColor() {
        if (root.confidence >= 0.8) return "#28a745"  // High confidence - green
        if (root.confidence >= 0.6) return "#ffc107"  // Medium confidence - yellow
        if (root.confidence >= 0.4) return "#fd7e14"  // Low confidence - orange
        return "#dc3545"  // Very low confidence - red
    }
    
    function getConfidenceText() {
        if (root.confidence >= 0.8) return "High confidence match"
        if (root.confidence >= 0.6) return "Good match"
        if (root.confidence >= 0.4) return "Possible match"
        return "Low confidence"
    }
}