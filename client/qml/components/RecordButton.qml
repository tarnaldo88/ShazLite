import QtQuick 2.15
import QtQuick.Controls 2.15

Button {
    id: root
    
    property bool isRecording: false
    property real progress: 0.0
    
    width: 120
    height: 120
    
    background: Rectangle {
        anchors.fill: parent
        radius: width / 2
        color: {
            if (!root.enabled) return "#bdc3c7"
            return root.isRecording ? "#e74c3c" : "#3498db"
        }
        border.color: {
            if (!root.enabled) return "#95a5a6"
            return root.isRecording ? "#c0392b" : "#2980b9"
        }
        border.width: 3
        
        // Pulse animation when recording
        SequentialAnimation on scale {
            running: root.isRecording
            loops: Animation.Infinite
            NumberAnimation { to: 1.1; duration: 800; easing.type: Easing.InOutQuad }
            NumberAnimation { to: 1.0; duration: 800; easing.type: Easing.InOutQuad }
        }
        
        // Progress ring
        Rectangle {
            anchors.fill: parent
            radius: width / 2
            color: "transparent"
            border.color: "#ffffff"
            border.width: 4
            opacity: root.isRecording ? 0.8 : 0
            
            // Progress arc (simplified as opacity change)
            opacity: root.isRecording ? (0.3 + 0.7 * root.progress / 100.0) : 0
            
            Behavior on opacity {
                NumberAnimation { duration: 200 }
            }
        }
    }
    
    contentItem: Item {
        anchors.fill: parent
        
        // Microphone icon
        Rectangle {
            anchors.centerIn: parent
            width: 40
            height: 50
            radius: 20
            color: root.enabled ? "white" : "#7f8c8d"
            visible: !root.isRecording
            
            Rectangle {
                anchors.bottom: parent.bottom
                anchors.horizontalCenter: parent.horizontalCenter
                width: 60
                height: 20
                radius: 10
                color: root.enabled ? "white" : "#7f8c8d"
                anchors.bottomMargin: -10
            }
            
            Rectangle {
                anchors.top: parent.bottom
                anchors.horizontalCenter: parent.horizontalCenter
                width: 4
                height: 15
                color: root.enabled ? "white" : "#7f8c8d"
                anchors.topMargin: 5
            }
        }
        
        // Stop icon when recording
        Rectangle {
            anchors.centerIn: parent
            width: 30
            height: 30
            radius: 4
            color: root.enabled ? "white" : "#7f8c8d"
            visible: root.isRecording
        }
    }
    
    // Hover effect
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: root.enabled ? Qt.PointingHandCursor : Qt.ForbiddenCursor
        onClicked: {
            if (root.enabled) {
                root.clicked()
            }
        }
        
        onEntered: {
            if (root.enabled && !root.isRecording) {
                parent.background.scale = 1.05
            }
        }
        
        onExited: {
            if (root.enabled && !root.isRecording) {
                parent.background.scale = 1.0
            }
        }
    }
    
    Behavior on background.scale {
        NumberAnimation { duration: 150; easing.type: Easing.OutQuad }
    }
}