import QtQuick 2.15
import QtQuick.Window 2.15

Window {
    width: 400
    height: 300
    visible: true
    title: "Test Window"
    
    Rectangle {
        anchors.fill: parent
        color: "lightblue"
        
        Text {
            anchors.centerIn: parent
            text: "Hello Qt!"
            font.pixelSize: 24
        }
    }
}