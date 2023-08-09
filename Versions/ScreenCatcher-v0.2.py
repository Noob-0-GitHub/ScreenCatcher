import os
import shutil
import sys
import threading
import time
import traceback
from datetime import datetime
from typing import Callable

import keyboard
import pyautogui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QFileDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, \
    QTextEdit, QMessageBox, QWidget
from fpdf import FPDF

version = 'v0.2'
intro = f"Welcome to use ScreenCatcher {version}\n欢迎使用ScreenCatcher {version}"


# wrapper class  装饰器类
class Threaded:
    daemon = True

    class Thread(threading.Thread):
        def __init__(self, target, args, kwargs, daemon=False):
            self.result = None
            self.target = target
            self.args = args
            self.kwargs = kwargs
            super().__init__(target=target, args=args, kwargs=kwargs, daemon=daemon)

        def run(self) -> None:
            self.result = self.target(*self.args, **self.kwargs)

    class ThreadedResult(object):
        def __init__(self, thread):
            self.thread: Threaded.Thread = thread
            self.thread.start()

        def __call__(self):
            return self.result

        def __repr__(self):
            return self.result

        def __int__(self):
            return int(self.result)

        def __float__(self):
            return float(self.result)

        def __str__(self):
            return str(self.result)

        def __bytes__(self):
            return bytes(self.result)

        @property
        def result(self):
            return self.thread.result

    def __init__(self, func):  # 接受函数
        self.func = func

    def __call__(self, *func_args, **func_kwargs):  # 返回函数
        thread = self.Thread(target=self.func, args=func_args, kwargs=func_kwargs, daemon=self.daemon)
        return self.ThreadedResult(thread=thread)


class PushButton(QPushButton):
    def __init__(self, text: str, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        text = text.replace(' ', ' ' * 2)
        self.setText(text)


class Main:
    def __init__(self):
        self.stop_flag = False
        self.catching_state = False
        self.default_extension = ".pdf"
        self.filetypes = "PDF Files (*.pdf)"
        self.img_create_dir_path = r'C:\ProgramData\ScreenCatcher'
        self.save_img_dir_path = None
        # 定义快捷键和对应的回调函数
        self.shortcuts = {
            "v": self.screenshot_active_window
        }
        self.stop_shortcut = "Esc"
        self.save_pdf_dir_path = None
        self.pdf_save_name = None
        self.pdf_save_path = None
        self.key_listener_thread = None
        self.stop_listener_Thread = None
        self.main_ui = ScreenCatcherGUI(self)
        self.main_ui.show()

    def main_init(self):
        self.stop_flag = False
        self.catching_state = False
        self.save_img_dir_path = None
        self.save_pdf_dir_path = None
        self.pdf_save_name = None
        self.pdf_save_path = None
        self.key_listener_thread = None
        self.stop_listener_Thread = None

    def load_setting(self, setting=None):
        pass

    @staticmethod
    def current_time_str(year=True, month=True, day=True, hour=True, minute=True, second=True, microsecond=True) -> str:
        now = datetime.now()

        components = []
        if year:
            components.append(f"{now.year}")
        if month:
            components.append(f"{now.month:02d}")
        if day:
            components.append(f"{now.day:02d}")
        if hour:
            components.append(f"{now.hour:02d}")
        if minute:
            components.append(f"{now.minute:02d}")
        if second:
            components.append(f"{now.second:02d}")
        if microsecond:
            components.append(f"{now.microsecond}")

        formatted_time = ".".join(components)
        return formatted_time

    def has_img_with_extension(self, extension: str, dir_path: str = None):
        if dir_path is None:
            dir_path = self.save_img_dir_path
        if not os.path.isdir(dir_path):
            raise ValueError(f"Path\"{dir_path}\" no found")
        for filename in os.listdir(dir_path):
            if filename.endswith(extension):
                return True
        return False

    def ask_save_path_and_name(self, default_name: str, default_extension: str = None,
                               filetypes: str = None) -> (str, None):
        if default_extension is None:
            default_extension = self.default_extension
        if filetypes is None:
            filetypes = self.filetypes
        file_path, _ = QFileDialog.getSaveFileName(None, "Save File", default_name, filetypes, default_extension)

        if file_path:
            # 如果用户没有输入文件后缀名，则自动添加 .pdf 后缀
            if not file_path.endswith(".pdf"):
                file_path += ".pdf"
            # 获取所选文件夹路径和文件名
            save_dir_path, save_name = os.path.split(file_path)
            self.pdf_save_path, self.pdf_save_name, self.save_pdf_dir_path = file_path, save_name, save_dir_path
            return file_path
        else:
            return None

    def screenshot_active_window(self, save_dir_path: str = None, save_img_name: str = None):
        if save_dir_path is None:
            save_dir_path = self.save_img_dir_path
        if save_img_name is None:
            save_img_name = self.current_time_str()
        save_img_path = os.path.join(save_dir_path, save_img_name + '.png')
        _img = pyautogui.screenshot(save_img_path)
        output(f"Save screenshot to \"{save_img_path}\"")

    def save_img_as_pdf(self, img_dir_path: str, pdf_save_path: str = None):
        if pdf_save_path is None:
            pdf_save_path: str = os.path.join(img_dir_path, "%s.pdf" % self.current_time_str())
        pdf = FPDF()
        pdf.set_auto_page_break(False)  # 自动分页设为False
        image_list = list(os.listdir(img_dir_path))
        for image in image_list:
            if not image.endswith(".png"):
                continue
            pdf.add_page()
            pdf.image(os.path.join(img_dir_path, image), w=190)  # 指定宽高
        pdf.output(pdf_save_path)

    @Threaded
    def key_listener(self):
        callbacks: dict = self.shortcuts
        output("key_listener ON")
        while True:
            if not self.catching_state:
                output("key_listener OFF")
                return
            for key, callback in callbacks.items():
                if keyboard.is_pressed(key):
                    callback()

    @Threaded
    def stop_listener(self, callback: Callable = None, stop_shortcut: str = None, press_time: int = 1):
        if callback is None:
            callback: Callable = self.catching_stop
        if stop_shortcut is None:
            stop_shortcut = self.stop_shortcut
        # 长按 press_time 秒后触发回调函数
        esc_pressed_time = 0
        while True:
            if not self.catching_state:
                return
            if keyboard.is_pressed(stop_shortcut):
                if esc_pressed_time == 0:
                    esc_pressed_time = time.time()
                elif time.time() - esc_pressed_time >= press_time:
                    break
            else:
                esc_pressed_time = 0
        callback()

    def create_tem_img_dir(self, name: str = None, path: str = None):
        if name is None:
            name = self.current_time_str()
        if path is None:
            path = self.img_create_dir_path
        new_tem_dir_path = os.path.join(path, name)
        os.makedirs(new_tem_dir_path)
        output(f"New temporary dir of img is created at \"{new_tem_dir_path}\"")
        return new_tem_dir_path

    def select_pdf_save_path(self):
        pdf_save_path = self.ask_save_path_and_name(self.current_time_str())
        if pdf_save_path:
            self.pdf_save_path = pdf_save_path
            output(f"PDF is going to save at \"{pdf_save_path}\"")
            self.main_ui.update_path_line()
        return self.pdf_save_path

    def catching_start(self) -> bool:
        if self.catching_state:
            output('Warning: Already in catching!')
            return False
        if self.pdf_save_path is None:
            self.select_pdf_save_path()
        if self.pdf_save_path is None:
            return False
        self.save_img_dir_path = self.create_tem_img_dir()
        self.catching_state = True
        output("Catching start")
        # 启动键盘监听线程
        self.key_listener_thread: Threaded.ThreadedResult = self.key_listener(self)
        self.stop_listener_Thread: Threaded.ThreadedResult = self.stop_listener(self)
        return True

    def catching_stop(self) -> bool:
        if self.catching_state is False:
            output('Warning: No current catching!')
            return False
        self.catching_state = False
        self.key_listener_thread.thread.join(15)
        output('Stop catching')
        self.save_pdf()
        self.main_init()
        self.main_ui.update_path_line()
        return True

    def save_pdf(self, img_dir_path: str = None, pdf_save_path: str = None):
        if img_dir_path is None:
            img_dir_path = self.save_img_dir_path
        if pdf_save_path is None:
            pdf_save_path = self.pdf_save_path
        original_pdf_save_path = os.path.join(self.save_img_dir_path, self.current_time_str() + ".pdf")
        if self.has_img_with_extension(".png"):
            self.save_img_as_pdf(img_dir_path=img_dir_path, pdf_save_path=original_pdf_save_path)
            output(f"PDF\"{original_pdf_save_path}\" saved")
            shutil.copy(original_pdf_save_path, pdf_save_path)
            output(f"PDF\"{pdf_save_path}\" saved")
        else:
            output(f"Saving: No img file found in \"{img_dir_path}\"")
            output("No PDF saved")

    def output(self, _str, print_time=True, precis_time=False) -> bool:
        if print_time:
            _time = self.current_time_str(year=precis_time, month=precis_time, day=precis_time, microsecond=precis_time)
            _str = f"[{_time}]{_str}"
        try:
            return self.main_ui.output(_str)
        except Exception:
            return False

    @staticmethod
    def exit():
        sys.exit()


class ScreenCatcherGUI(QWidget):
    def __init__(self, parent: Main):
        super().__init__()
        self.parent = parent
        self.window_size = 64
        self.window_width = self.window_size * 16
        self.window_height = self.window_size * 9
        self.line_font_size = 10
        self.line_font = self.font()
        self.line_font.setPointSize(self.line_font_size)
        self.button_font_size = 8
        self.button_font = self.font()
        self.button_font.setPointSize(self.button_font_size)
        # init ui
        layout = QVBoxLayout()

        # Output text box
        self.output_lines = QTextEdit(self)
        self.output_lines.setReadOnly(True)
        self.output_lines.setFontPointSize(self.line_font_size)
        self.output_lines.setLineWrapMode(QTextEdit.NoWrap)
        layout.addWidget(self.output_lines)

        # Select-Save-Path button and Path-line edit
        path_layout = QHBoxLayout()
        self.path_button = PushButton('Select Save Path', self)
        self.path_button.setFont(self.button_font)
        self.path_button.setFixedWidth(256)
        self.path_button.clicked.connect(self.select_path)
        self.path_line = QLineEdit(self)
        self.path_line.setFont(self.line_font)
        self.path_line.textChanged.connect(self.save_path_is_changed)
        path_layout.addWidget(self.path_button)
        path_layout.addWidget(self.path_line)
        layout.addLayout(path_layout)

        # Start/Stop button
        start_stop_exit_layout = QHBoxLayout()
        self.start_stop_button = PushButton('Start', self)
        self.start_stop_button.setFont(self.button_font)
        self.start_stop_button.clicked.connect(self.toggle_start_stop_button)
        self.start_stop_button.setCheckable(True)
        self.start_stop_button.setFixedWidth(192)
        self.start_stop_button_state = self.parent.catching_state
        # Exit button
        self.exit_button = PushButton('Exit', self)
        self.exit_button.setFont(self.button_font)
        self.exit_button.setFixedWidth(128)
        self.exit_button.clicked.connect(self.exit)
        start_stop_exit_layout.addWidget(self.start_stop_button)
        start_stop_exit_layout.addStretch()
        start_stop_exit_layout.addWidget(self.exit_button)
        layout.addLayout(start_stop_exit_layout)

        self.setLayout(layout)
        self.setWindowTitle(f'ScreenCatcher-{version}')
        self.setFixedSize(self.window_width, self.window_height)
        self.setFixedSize(self.window_width, self.window_height)
        self.setFocusPolicy(Qt.StrongFocus)

    def update_path_line(self):
        self.path_line.setText(self.parent.pdf_save_path)

    def update_start_stop_button_state(self):
        self.start_stop_button_state = self.parent.catching_state

    def select_path(self):
        self.parent.select_pdf_save_path()

    def save_path_is_changed(self):
        new_path = self.path_line.text()
        if os.path.exists(new_path):
            self.parent.pdf_save_path = new_path
            self.update_path_line()

    def save_path_edit_finished(self):
        if not self.path_line.text() == self.parent.pdf_save_path:
            output(f"Path\"{self.path_line.text()}\" no found")
            self.select_path()

    def toggle_start_stop_button(self):
        if not self.start_stop_button.isChecked():
            if self.parent.catching_stop():
                self.start_stop_button.setText('Start')
            else:
                self.start_stop_button.setChecked(not self.start_stop_button.isChecked())
        else:
            if self.parent.catching_start():
                self.start_stop_button.setText('Stop And Save')
            else:
                self.start_stop_button.setChecked(not self.start_stop_button.isChecked())
        self.update_start_stop_button_state()

    def output(self, _str) -> bool:
        try:
            self.output_lines.append(_str)
        except Exception:
            return False
        return True

    def exit(self):
        if self.parent.catching_state:
            _reply = QMessageBox.question(self, "ScreenCatcher",
                                          "The catching is not finished\nAre you sure to stop and save?")
            if _reply == QMessageBox.Yes:
                self.parent.catching_stop()
            else:
                return
        self.close()


def output(_str, print_time=True, precis_time=False):
    print(_str)
    try:
        main.output(_str, print_time=print_time, precis_time=precis_time)
    except Exception:
        print(traceback.format_exc())


if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)

        import qt_material

        qt_material.apply_stylesheet(app=app, theme="dark_lightgreen.xml")
        main = Main()
        output(intro, print_time=False)
        sys.exit(app.exec_())
    except Exception:
        output(traceback.format_exc())
