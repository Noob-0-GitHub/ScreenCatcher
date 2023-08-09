from PyQt5 import QtCore, QtGui, QtWidgets


class KeySequenceEdit(QtWidgets.QKeySequenceEdit):
    def keyPressEvent(self, event):
        super(KeySequenceEdit, self).keyPressEvent(event)
        seq_string = self.keySequence().toString(QtGui.QKeySequence.NativeText)
        if seq_string:
            last_seq = seq_string.split(",")[-1].strip()
            le = self.findChild(QtWidgets.QLineEdit, "qt_keysequenceedit_lineedit")
            self.setKeySequence(QtGui.QKeySequence(last_seq))
            le.setText(last_seq)
            self.editingFinished.emit()

class PushButton(QtWidgets.QPushButton):
    def setText(self, text: str) -> None:
        super().setText(text)
class Widget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(Widget, self).__init__(parent)
        self._keysequenceedit = KeySequenceEdit(editingFinished=self.on_editingFinished)
        button = QtWidgets.QPushButton("clear", clicked=self._keysequenceedit.clear)
        button.setText("clear")
        hlay = QtWidgets.QHBoxLayout(self)
        hlay.addWidget(self._keysequenceedit)
        hlay.addWidget(button)

    @QtCore.pyqtSlot()
    def on_editingFinished(self):
        sequence = self._keysequenceedit.keySequence()
        seq_string = sequence.toString(QtGui.QKeySequence.NativeText)
        print("sequence: ", seq_string)


if __name__ == '__main__':
    import sys, qt_material

    app = QtWidgets.QApplication(sys.argv)
    qt_material.apply_stylesheet(app, "dark_lightgreen.xml")
    w = Widget()
    w.show()
    sys.exit(app.exec_())
