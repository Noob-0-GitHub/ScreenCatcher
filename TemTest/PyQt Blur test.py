import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt
from BlurWindow.blurWindow import GlobalBlur
from qt_material import apply_stylesheet


class MainWindow(QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(500, 400)

        GlobalBlur(self.winId(), Dark=True, QWidget=self)

        apply_stylesheet(self, theme="dark_lightgreen.xml")

        layout = QVBoxLayout(self)
        label = QLabel("Hello, Blurred Background!", self)
        layout.addWidget(label)

        button = QPushButton("Click Me", self)
        button.clicked.connect(self.on_button_click)
        layout.addWidget(button)

    def on_button_click(self):
        print("Button Clicked!")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec_())
