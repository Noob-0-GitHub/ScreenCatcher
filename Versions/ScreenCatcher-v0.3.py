import json
import os
import shutil
import sys
import threading
import time
import traceback
from datetime import datetime
from typing import Callable, Any

import keyboard
import pyautogui
from PyQt5 import Qt as pyqt5Qt
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QApplication, QDialog, QFileDialog, QHBoxLayout, QKeySequenceEdit, QLabel, QLineEdit, \
    QMessageBox, QPushButton, QTextEdit, QVBoxLayout, QWidget, QDesktopWidget

from fpdf import FPDF

DATA_PATH = r'C:\ProgramData\ScreenCatcher'
version = 'v0.3'
intro = f"Welcome to use ScreenCatcher {version}\n欢迎使用ScreenCatcher {version}"
user_help = "Press \"{main.shortcuts_keys[0]}\" to Screenshot\nPress \"ESC\" to stop catching"


def get_attr(_obj: object, attr_name: str) -> Any:
    return eval(f"{attr_name}", _obj.__dict__)


def set_attr(_obj: object, attr_name: str, value: Any) -> Any:
    return exec(f"_obj.{attr_name}=value", {"_obj": _obj, "value": value})


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
    def __init__(self, text: str, parent, *args, add_space=True, tooltips=True, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.add_space = add_space
        self.setText(text)
        if tooltips:
            self.setToolTip(text)

    def setText(self, text: str) -> None:
        if self.add_space:
            text = text.replace(' ', ' ' * 2)
        super().setText(text)


class Main:
    def __init__(self):
        self.catching_state = False
        self.default_extension = ".pdf"
        self.filetypes = "PDF Files (*.pdf)"
        self.img_create_dir_path = DATA_PATH
        self.save_img_dir_path = None
        # 定义快捷键和对应的回调函数
        self.shortcuts_keys = ['v']
        self.shortcuts_callbacks = [self.screenshot_active_window]
        self.stop_shortcut = "Esc"
        self.pdf_to_clipboard = True
        self.save_pdf_dir_path = None
        self.pdf_save_name = None
        self.pdf_save_path = None
        self.key_listener_thread = None
        self.stop_listener_Thread = None
        self.main_ui: ScreenCatcherGUI = ScreenCatcherGUI(self)
        self.setting_manager = SettingsManager(self.main_ui, self)
        self.main_ui.show()

    def main_init(self):
        self.catching_state = False
        self.save_img_dir_path = None
        self.save_pdf_dir_path = None
        self.pdf_save_name = None
        self.pdf_save_path = None
        self.key_listener_thread = None
        self.stop_listener_Thread = None

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
        keys = self.shortcuts_keys
        callbacks: list = self.shortcuts_callbacks
        output("key_listener ON")
        while True:
            if not self.catching_state:
                output("key_listener OFF")
                return
            for key, callback in zip(keys, callbacks):
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
        if self.pdf_to_clipboard:
            try:
                self.copy_file_to_clipboard()
            except Exception:
                print(traceback.format_exc())
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

    def copy_file_to_clipboard(self, file_path: str = None):
        if file_path is None:
            file_path = self.pdf_save_path
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"\"{file_path}\" no found")
        clipboard = QApplication.clipboard()
        url_list = [pyqt5Qt.QUrl.fromLocalFile(file_path)]
        mime_data = pyqt5Qt.QMimeData()
        mime_data.setUrls(url_list)
        clipboard.setMimeData(mime_data)
        output(f"PDF\"{file_path}\" copy to clipboard")

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


# class KeyRecordButton(QPushButton):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.clicked.connect(self.on_button_press)
#
#     def on_button_press(self):
#         pass
#
#     def key_record(self):
#         pass


class KeySequenceEdit(QKeySequenceEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cache the QLineEdit child object for later use
        self.line_edit_child = self.findChild(QLineEdit, "qt_keysequenceedit_lineedit")

    def keyPressEvent(self, event):
        try:
            super().keyPressEvent(event)
            # noinspection PyUnresolvedReferences
            seq_string = self.keySequence().toString(QKeySequence.NativeText)
            if seq_string:
                last_seq = seq_string.split(",")[-1].strip()
                self.setKeySequence(QKeySequence(last_seq))
                # Update the cached QLineEdit child object if it's available
                if self.line_edit_child:
                    # noinspection PyUnresolvedReferences
                    self.line_edit_child.setText(last_seq)

                # noinspection PyUnresolvedReferences
                # Emit editingFinished signal
                self.editingFinished.emit()
        except Exception:
            output(traceback.format_exc())


class KeyRecorder(QWidget):
    def __init__(self, parent, default_key=None):
        # parent = None
        super().__init__()
        self.parent = parent
        self.default_key = default_key
        # noinspection PyArgumentList
        self.keysequenceedit = KeySequenceEdit(self)
        # noinspection PyArgumentList
        button = QPushButton("Reset", self.parent, clicked=self.reset)
        layout = QHBoxLayout(self)
        layout.addWidget(self.keysequenceedit)
        layout.addWidget(button)
        if default_key is not None:
            self.keysequenceedit.setKeySequence(default_key)

    def reset(self):
        self.keysequenceedit.setKeySequence(self.default_key)

    # noinspection PyUnresolvedReferences
    def get_shortcut(self) -> str:
        sequence = self.keysequenceedit.keySequence()
        seq_string = sequence.toString(QKeySequence.NativeText)
        return seq_string


class SettingsContainer(dict):
    class SettingPair(list):
        def __init__(self, key, value, value_get_callback: Callable = None):
            super().__init__([key, value])
            self._key_index = 0
            self._value_index = 1
            self.value_get_callback = value_get_callback

        @property
        def key(self):
            return self.__getitem__(self._key_index)

        @property
        def value(self):
            return self.__getitem__(self._value_index)

        def set_value(self, _new_value):
            self.__setitem__(self._value_index, _new_value)

    def __init__(self, *args, _dict: dict = None, **kwargs):
        super().__init__(*args, **kwargs)
        if _dict is not None:
            _dict = _dict.copy()
            for note in _dict:
                _dict[note] = self.SettingPair(_dict[note][0], _dict[note][1])
            self.update(_dict)

    def add(self, note: str, key: str, value=None):
        self[note] = self.SettingPair(key=key, value=value)

    def get(self, __key: str) -> SettingPair | None:
        return super().get(__key)

    def deepcopy(self):
        _new = self.__class__(_dict=self)
        return _new


class SettingsManager:
    SETTINGS_PATH = os.path.join(DATA_PATH, f"ScreenCatcher-{version}-Settings.json")

    def __init__(self, parent, main_instance: Main, load_settings=True):
        self.parent: ScreenCatcherGUI = parent
        self.main_instance = main_instance

        self.settings: SettingsContainer[str, SettingsContainer.SettingPair] = SettingsContainer()
        self.settings.add(note='Screenshot Shortcut', key='shortcuts_keys[0]')

        if load_settings:
            self.load_settings()

    def settings_filter(self, main_instance: Main = None) -> SettingsContainer:
        if main_instance is None:
            main_instance = self.main_instance
        for note in self.settings:
            setting_pair = self.settings.get(note)
            setting_pair.set_value(get_attr(main_instance, setting_pair.key))
        print(self.settings)
        return self.settings

    def load_settings(self, defaults_settings: dict = None, settings_path: str = None, main_instance: Main = None):
        """Load settings from file. If file doesn't exist, return default settings."""
        if settings_path is None:
            settings_path = self.SETTINGS_PATH
        if main_instance is None:
            main_instance = self.main_instance
        if os.path.exists(settings_path):
            try:
                with open(settings_path, 'r') as file:
                    file_settings: dict = json.load(file)
                    if set(self.settings.keys()) == set(file_settings.keys()):
                        file_settings = SettingsContainer(_dict=file_settings)
                        self.settings.update(file_settings)
                    else:
                        self.register_settings(defaults_settings)
            except Exception:
                output(traceback.format_exc())
                self.register_settings()
        else:
            self.register_settings(defaults_settings)
        for note in self.settings:
            setting_pair = self.settings.get(note)
            set_attr(_obj=main_instance, attr_name=setting_pair.key, value=setting_pair.value)

    def save_settings(self, settings, settings_path: str = None):
        """Save settings to file."""
        if settings_path is None:
            settings_path = self.SETTINGS_PATH
        os.makedirs(DATA_PATH, exist_ok=True)  # Ensure directory exists
        try:
            with open(settings_path, 'w') as file:
                json.dump(settings, file)
        except Exception:
            output(traceback.format_exc())
            self.register_settings()

    def register_settings(self, defaults_settings: SettingsContainer = None):
        if defaults_settings is None:
            defaults_settings = self.settings_filter()
        self.save_settings(defaults_settings)
        self.settings.update(defaults_settings)

    def setting_dialog(self):
        return SettingsDialog(self.parent, self, self.settings)


class SettingsDialog(QDialog):
    def __init__(self, parent, setting_manager: SettingsManager, current_settings: SettingsContainer):
        super().__init__()
        # noinspection PyTypeChecker
        self.parent: ScreenCatcherGUI = parent
        self.setting_manager = setting_manager
        self.current_settings = current_settings
        self.new_settings = current_settings.deepcopy()
        self.setWindowTitle("Screen Catcher Settings")
        layout = QVBoxLayout()

        # ScreenshotShortcut setting
        screenshot_shortcut_layout = QHBoxLayout()
        screenshot_shortcut_layout.addWidget(QLabel("Screenshot Shortcut: "))
        self.screenshot_shortcut_keyrecorder = KeyRecorder(self, self.current_settings.get("Screenshot Shortcut").value)
        self.new_settings.get("Screenshot Shortcut").value_get_callback = (
            self.screenshot_shortcut_keyrecorder.get_shortcut)
        screenshot_shortcut_layout.addWidget(self.screenshot_shortcut_keyrecorder)
        layout.addLayout(screenshot_shortcut_layout)

        # Stop shortcut setting
        # self.stop_shortcut_edit = PushButton(f"{current_settings.stop_shortcut}", self()
        # layout.addWidget(QLabel("Stop Shortcut:"))
        # layout.addWidget(self.stop_shortcut_edit)

        # apply button and cancel Button
        apply_cancel_layout = QHBoxLayout()
        self.apply_button = PushButton("Apply", self)
        self.apply_button.setFixedWidth(128)
        self.apply_button.clicked.connect(self.apply_settings)
        self.cancel_button = PushButton("Cancel", self)
        self.cancel_button.setFixedWidth(128)
        self.cancel_button.clicked.connect(self.reject)
        apply_cancel_layout.addStretch()
        apply_cancel_layout.addWidget(self.apply_button)
        apply_cancel_layout.addWidget(self.cancel_button)
        layout.addLayout(apply_cancel_layout)

        self.setLayout(layout)
        self.setWindowModality(Qt.ApplicationModal)
        self.show()
        self.exec_()

    def apply_settings(self):
        for note in self.new_settings:
            setting_pair = self.new_settings.get(note)
            value_callback = setting_pair.value_get_callback
            if callable(value_callback):
                setting_pair.set_value(value_callback())
        self.setting_manager.save_settings(self.new_settings)
        self.setting_manager.load_settings()
        self.accept()  # Close the dialog


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
        # Settings button
        self.settings_button = PushButton('Settings', self)
        self.settings_button.setFont(self.button_font)
        self.settings_button.setFixedWidth(128)
        self.settings_button.clicked.connect(self.open_settings)
        # Exit button
        self.exit_button = PushButton('Exit', self)
        self.exit_button.setFont(self.button_font)
        self.exit_button.setFixedWidth(128)
        self.exit_button.clicked.connect(self.exit)
        start_stop_exit_layout.addWidget(self.start_stop_button)
        start_stop_exit_layout.addStretch()
        start_stop_exit_layout.addWidget(self.settings_button)
        start_stop_exit_layout.addWidget(self.exit_button)
        layout.addLayout(start_stop_exit_layout)

        self.setLayout(layout)
        self.setWindowTitle(f'ScreenCatcher-{version}')
        self.resize(self.window_width, self.window_height)
        self.setFocus()
        self.center()

        # self.setWindowOpacity(0.96)

        # Blur background
        # from BlurWindow.blurWindow import GlobalBlur
        # from PyQt5.QtCore import Qt
        # self.setAttribute(Qt.WA_TranslucentBackground)
        # self.output_lines.setAttribute(Qt.WA_TranslucentBackground)
        # GlobalBlur(self.winId(), Acrylic=False, Dark=True, QWidget=self)
        # self.setStyleSheet("background-color: rgba(0, 0, 0, 128)")

    def set_stay_ont_the_top(self, value=True, show=False):
        if value:
            self.setWindowFlags(Qt.WindowStaysOnTopHint)  # 置顶
        else:
            self.setWindowFlags(Qt.Widget)  # 取消置顶
        if show:
            self.show()

    def center(self):
        # 得到屏幕的尺寸
        screen = QDesktopWidget().screenGeometry()
        # 获取窗口尺寸
        size = self.geometry()
        # 计算居中窗口的左上角到屏幕左侧坐标的距离
        new_left = (screen.width() - size.width()) // 2
        # 计算居中窗口的左上角到屏幕上边坐标的距离
        new_top = (screen.height() - size.height()) // 2
        # 移动窗口, 因为move方法只接受整数，所以我们类型转换一下
        self.move(new_left, new_top)

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
                self.start_stop_button.setText("Start")
            else:
                self.start_stop_button.setChecked(not self.start_stop_button.isChecked())
        else:
            if self.parent.catching_start():
                self.start_stop_button.setText('Stop And Save')
            else:
                self.start_stop_button.setChecked(not self.start_stop_button.isChecked())
        self.update_start_stop_button_state()
        self.start_stop_button.setToolTip(self.start_stop_button.text())

    def open_settings(self):
        if self.parent.catching_state:
            QMessageBox.warning(self, "ScreenCatcher", "You cannot change settings while catching")
        else:
            try:
                self.parent.setting_manager.setting_dialog()
            except Exception:
                output(traceback.format_exc())

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
                if not self.parent.catching_stop():
                    return
            else:
                return
        self.close()
        app.closeAllWindows()


def output(_str, print_time=True, precis_time=False):
    while len(output_list):
        main.output(output_list.pop())
    print(_str)
    try:
        main.output(_str, print_time=print_time, precis_time=precis_time)
    except Exception:
        print(traceback.format_exc())
        output_list.append(_str)


if __name__ == '__main__':
    try:
        output_list = list()
        app = QApplication(sys.argv)

        import qt_material

        main = Main()
        main.main_ui.set_stay_ont_the_top(value=True, show=True)
        output(intro, print_time=False)
        output(user_help.format(main=main), print_time=False)
        qt_material.apply_stylesheet(app=app, theme="dark_lightgreen.xml")
        main.main_ui.set_stay_ont_the_top(value=False, show=True)
        sys.exit(app.exec_())
    except Exception:
        output(traceback.format_exc())
