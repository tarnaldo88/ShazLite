import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    
    property string errorMessage: ""
    property string errorType: "general"  // "network", "timeout", "server", "general"
    property bool showRetryButton: true
    
    signal retryRequested()
    signal dismissRequested()
    
    color: "#ffffff"
    border.color: getErrorBorderColor()
    border.width: 2
    radius: 12
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 15
        
        // Error icon with animation
        Rectangle {
            Layout.alignment: Qt.AlignHCenter
            width: 60
            height: 60
            radius: 30
            color: getErrorColor()
            
            // Shake animation for emphasis
            SequentialAnimation on x {
                running: true
                loops: 1
                NumberAnimation { to: root.x + 5; duration: 100 }
                NumberAnimation { to: root.x - 5; duration: 100 }
                NumberAnimation { to: root.x + 3; duration: 100 }
                NumberAnimation { to: root.x - 3; duration: 100 }
                NumberAnimation { to: root.x; duration: 100 }
            }
            
            Label {
                anchors.centerIn: parent
                text: getErrorIcon()
                font.pixelSize: 30
                color: "white"
                font.bold: true
            }
        }
        
        // Error title
        Label {
            text: getErrorTitle()
            font.pixelSize: 20
            font.bold: true
            color: getErrorColor()
            horizontalAlignment: Text.AlignHCenter
            Layout.fillWidth: true
        }
        
        // Error message
        Label {
            text: root.errorMessage
            font.pixelSize: 14
            color: "#7f8c8d"
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }
        
        // Error-specific suggestions
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: suggestionsContent.implicitHeight + 20
            color: "#f8f9fa"
            border.color: "#dee2e6"
            border.width: 1
            radius: 8
            visible: getSuggestions().length > 0
            
            ColumnLayout {
                id: suggestionsContent
                anchors.fill: parent
                anchors.margins: 15
                spacing: 8
                
                Label {
                    text: "Suggestions:"
                    font.pixelSize: 12
                    font.bold: true
                    color: "#495057"
                }
                
                Repeater {
                    model: getSuggestions()
                    
                    Label {
                        text: "• " + modelData
                        font.pixelSize: 11
                        color: "#6c757d"
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                    }
                }
            }
        }
        
        // Action buttons
        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: 10
            spacing: 10
            
            Button {
                text: "Dismiss"
                Layout.fillWidth: true
                onClicked: root.dismissRequested()
            }
            
            Button {
                text: getRetryButtonText()
                Layout.fillWidth: true
                highlighted: true
                visible: root.showRetryButton
                onClicked: root.retryRequested()
            }
        }
    }
    
    function getErrorColor() {
        switch (root.errorType) {
            case "network": return "#dc3545"
            case "timeout": return "#fd7e14"
            case "server": return "#6f42c1"
            default: return "#e74c3c"
        }
    }
    
    function getErrorBorderColor() {
        return getErrorColor()
    }
    
    function getErrorIcon() {
        switch (root.errorType) {
            case "network": return "⚠"
            case "timeout": return "⏱"
            case "server": return "🔧"
            default: return "!"
        }
    }
    
    function getErrorTitle() {
        switch (root.errorType) {
            case "network": return "Connection Error"
            case "timeout": return "Request Timeout"
            case "server": return "Server Error"
            default: return "Error"
        }
    }
    
    function getRetryButtonText() {
        switch (root.errorType) {
            case "network": return "Retry Connection"
            case "timeout": return "Try Again"
            case "server": return "Retry Request"
            default: return "Try Again"
        }
    }
    
    function getSuggestions() {
        switch (root.errorType) {
            case "network":
                return [
                    "Check your internet connection",
                    "Verify the server is running",
                    "Try again in a few moments"
                ]
            case "timeout":
                return [
                    "The request took too long to complete",
                    "Check your network connection",
                    "The server might be busy, try again"
                ]
            case "server":
                return [
                    "The server encountered an error",
                    "Try uploading a different audio file",
                    "Contact support if the problem persists"
                ]
            default:
                return [
                    "Try recording again",
                    "Check your microphone permissions",
                    "Ensure audio quality is good"
                ]
        }
    }
}