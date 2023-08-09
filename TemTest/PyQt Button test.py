import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QCheckBox
import qt_material

class ToggleSwitchWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        self.checkbox = QCheckBox("功能开关", self)
        self.checkbox.setChecked(False)
        self.checkbox.stateChanged.connect(self.toggle_switch)

        layout.addWidget(self.checkbox)

        self.setWindowTitle('Toggle Switch')
        self.setGeometry(100, 100, 300, 100)

    def toggle_switch(self, state):
        if state == 2:  # Qt.Checked
            # 在这里执行开关打开时的功能
            print("功能已开启")
        else:
            # 在这里执行开关关闭时的功能
            print("功能已关闭")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    qt_material.apply_stylesheet(app,"dark_lightgreen.xml")
    window = ToggleSwitchWidget()
    window.show()
    sys.exit(app.exec_())
