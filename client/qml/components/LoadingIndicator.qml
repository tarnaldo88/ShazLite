import QtQuick 2.15

Item {
    id: root
    
    property bool running: false
    property color color: "#3498db"
    
    width: 40
    height: 40
    
    // Spinning dots
    Repeater {
        model: 8
        
        Rectangle {
            width: 6
            height: 6
            radius: 3
            color: root.color
            opacity: 0.2 + 0.8 * (1.0 - index / 8.0)
            
            property real angle: index * 45
            
            x: root.width / 2 - width / 2 + Math.cos(angle * Math.PI / 180) * 15
            y: root.height / 2 - height / 2 + Math.sin(angle * Math.PI / 180) * 15
            
            SequentialAnimation on opacity {
                running: root.running
                loops: Animation.Infinite
                
                PauseAnimation { duration: index * 100 }
                NumberAnimation { to: 1.0; duration: 400 }
                NumberAnimation { to: 0.2; duration: 400 }
                PauseAnimation { duration: (8 - index - 1) * 100 }
            }
        }
    }
    
    // Alternative: Simple rotating circle
    Rectangle {
        id: spinner
        anchors.centerIn: parent
        width: 30
        height: 30
        radius: 15
        color: "transparent"
        border.color: root.color
        border.width: 3
        visible: false // Use dots by default
        
        Rectangle {
            width: 6
            height: 6
            radius: 3
            color: root.color
            anchors.top: parent.top
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.topMargin: -3
        }
        
        RotationAnimation on rotation {
            running: root.running && spinner.visible
            loops: Animation.Infinite
            duration: 1000
            from: 0
            to: 360
        }
    }
}