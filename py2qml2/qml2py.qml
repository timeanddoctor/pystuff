import QtQuick 2.10
import QtQuick.Controls 2.1
import QtQuick.Window 2.2

ApplicationWindow {
    title: qsTr("Test")
    width: 640
    height: 480
    visible: true
    Column{
        TextField{
            id: tf
            text: "Hello"
        }
        Button {
            text: qsTr("Click Me")
            onClicked: backend.text = tf.text
        }
    }
}
