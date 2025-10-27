import QtQuick 2.15
import QtQuick.Controls 2.15

Item {
    id: root
    
    property bool running: false
    property string stage: "uploading"  // "uploading", "processing", "matching"
    property real progress: 0.0  // 0.0 to 1.0
    
    width: 120
    height: 120
    
    // Background circle
    Rectangle {
        anchors.centerIn: parent
        width: 100
        height: 100
        radius: 50
        color: "transparent"
        border.color: "#e9ecef"
        border.width: 4
    }
    
    // Progress circle
    Canvas {
        id: progressCanvas
        anchors.centerIn: parent
        width: 100
        height: 100
        
        property real angle: root.progress * 360
        
        onAngleChanged: requestPaint()
        
        onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)
            
            // Draw progress arc
            ctx.beginPath()
            ctx.arc(width/2, height/2, 46, -Math.PI/2, (-Math.PI/2) + (angle * Math.PI/180))
            ctx.lineWidth = 4
            ctx.strokeStyle = getStageColor()
            ctx.lineCap = "round"
            ctx.stroke()
        }
    }
    
    // Center icon
    Rectangle {
        anchors.centerIn: parent
        width: 60
        height: 60
        radius: 30
        color: getStageColor()
        
        // Pulse animation
        SequentialAnimation on scale {
            running: root.running
            loops: Animation.Infinite
            NumberAnimation { to: 1.1; duration: 1000; easing.type: Easing.InOutQuad }
            NumberAnimation { to: 1.0; duration: 1000; easing.type: Easing.InOutQuad }
        }
        
        Label {
            anchors.centerIn: parent
            text: getStageIcon()
            font.pixelSize: 24
            color: "white"
            font.bold: true
        }
    }
    
    // Stage label
    Label {
        anchors.top: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.topMargin: 10
        text: getStageText()
        font.pixelSize: 14
        font.bold: true
        color: getStageColor()
    }
    
    // Rotating dots around the circle
    Repeater {
        model: 8
        
        Rectangle {
            width: 6
            height: 6
            radius: 3
            color: getStageColor()
            opacity: 0.3 + 0.7 * (1.0 - index / 8.0)
            
            property real baseAngle: index * 45
            property real currentAngle: baseAngle + (root.running ? rotationAnimation.angle : 0)
            
            x: root.width / 2 - width / 2 + Math.cos(currentAngle * Math.PI / 180) * 60
            y: root.height / 2 - height / 2 + Math.sin(currentAngle * Math.PI / 180) * 60
            
            NumberAnimation {
                id: rotationAnimation
                target: rotationAnimation
                property: "angle"
                running: root.running
                loops: Animation.Infinite
                from: 0
                to: 360
                duration: 3000
            }
        }
    }
    
    function getStageColor() {
        switch (root.stage) {
            case "uploading": return "#17a2b8"
            case "processing": return "#ffc107"
            case "matching": return "#28a745"
            default: return "#6c757d"
        }
    }
    
    function getStageIcon() {
        switch (root.stage) {
            case "uploading": return "↑"
            case "processing": return "⚙"
            case "matching": return "🔍"
            default: return "•"
        }
    }
    
    function getStageText() {
        switch (root.stage) {
            case "uploading": return "Uploading..."
            case "processing": return "Processing..."
            case "matching": return "Matching..."
            default: return "Working..."
        }
    }
}