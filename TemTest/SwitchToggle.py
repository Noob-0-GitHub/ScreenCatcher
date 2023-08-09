from PyQt5 import QtWidgets
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication, QPushButton, QStyleFactory


class ToggleButton(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self)

        self.color = QColor(0, 0, 0)
        self.setGeometry(300, 300, 280, 170)
        self.setWindowTitle('ToggleButton')
        self.red = QPushButton('Red', self)
        self.red.setCheckable(True)
        self.red.move(10, 10)
        self.red.clicked.connect(self.setRed)
        self.green = QPushButton('Green', self)
        self.green.setCheckable(True)
        self.green.move(10, 60)
        self.green.clicked.connect(self.setGreen)
        self.blue = QPushButton('Blue', self)
        self.blue.setCheckable(True)
        self.blue.move(10, 110)
        self.blue.clicked.connect(self.setBlue)
        self.square = QtWidgets.QWidget(self)
        self.square.setGeometry(150, 20, 100, 100)
        self.square.setStyleSheet('QWidget{background-color:%s}' % self.color.name())
        QApplication.setStyle(QStyleFactory.create('cleanlooks'))

    def setRed(self):
        if self.red.isChecked():
            self.color.setRed(255)
        else:
            self.color.setRed(0)

        self.square.setStyleSheet('QWidget{background-color:%s}' % self.color.name())

    def setGreen(self):
        if self.green.isChecked():
            self.color.setGreen(255)
        else:
            self.color.setGreen(0)

        self.square.setStyleSheet('QWidget{background-color:%s}' % self.color.name())

    def setBlue(self):
        if self.blue.isChecked():
            self.color.setBlue(255)
        else:
            self.color.setBlue(0)

        self.square.setStyleSheet('QWidget{background-color:%s}' % self.color.name())


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    qb = ToggleButton()
    qb.show()
    sys.exit(app.exec_())
