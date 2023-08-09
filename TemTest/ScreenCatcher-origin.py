import os
import sys
import threading
import tkinter as tk
import traceback
from datetime import datetime
from tkinter import filedialog
from typing import List, Tuple, Callable

import keyboard
import pyautogui
from fpdf import FPDF

version = 'v0.1'
intro = f"""
Welcome to use ScreenCatcher {version} 
欢迎使用ScreenCatcher {version}
"""


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


# def _main():
#     filetypes = [("PDF Files", "*.pdf")]
#     img_save_path = r'C:\Users\Anthony-XKN\Desktop'
#     save_dir_path, pdf_save_name = self.ask_save_path_and_name(default_extension='.pdf', default_name=
#                                                           self.current_time_str(), filetypes=filetypes)
#     pdf_save_path = os.path.join(save_dir_path, pdf_save_name)
#     # 定义快捷键和对应的回调函数
#     shortcuts = {
#         "v": lambda: screenshot_active_window(img_save_path, self.current_time_str())
#     }
#
#     # 启动键盘监听线程
#     listener_thread = threading.Thread(target=shortcut_listener, args=(shortcuts,), daemon=True)
#     listener_thread.start()
#
#     # 监听ESC键，长按三秒后退出程序
#     esc_pressed_time = 0
#     while True:
#         if keyboard.is_pressed("esc"):
#             if esc_pressed_time == 0:
#                 esc_pressed_time = time.time()
#             elif time.time() - esc_pressed_time >= 3:
#                 print("Saving")
#                 break
#         else:
#             esc_pressed_time = 0
#     save_img_as_pdf(img_dir_path=img_save_path, pdf_save_path=pdf_save_path)


class Main:
    def __init__(self):
        self.stop_flag = False
        self.catching_state = False
        self.default_extension = ".pdf"
        self.filetypes = [("PDF Files", "*.pdf")]
        self.img_create_dir_path = r'C:\Users\Anthony-XKN\Desktop'
        self.save_img_dir_path = None
        # 定义快捷键和对应的回调函数
        self.shortcuts = {
            "v": self.screenshot_active_window
        }
        self.stop_shortcut = "Esc"
        self.save_pdf_dir_path = None
        self.pdf_save_name = None
        self.pdf_save_path = None
        self.catching_shortcut_listener = None
        self.command = {
            "start": self.catching_start,
            "save": self.save_pdf,
            "stop": self.catching_stop,
            "exit": self.exit
        }

    @staticmethod
    def current_time_str() -> str:
        now = datetime.now()
        year = now.year
        month = now.month
        day = now.day
        hour = now.hour
        minute = now.minute
        second = now.second
        microsecond = now.microsecond

        formatted_time = f"{year}.{month}.{day}.{hour:02d}.{minute:02d}.{second:02d}.{microsecond}"
        return formatted_time

    @staticmethod
    def ask_save_path_and_name(default_extension: str, default_name: str = None,
                               filetypes: List[Tuple[str, str]] = None):
        root = tk.Tk()
        root.withdraw()  # 隐藏tk窗口

        file_path = filedialog.asksaveasfilename(defaultextension=default_extension, filetypes=filetypes,
                                                 initialfile=default_name)

        if file_path:
            # 获取所选文件夹路径和文件名
            save_path, save_name = os.path.split(file_path)

            # 如果用户没有输入文件后缀名，则自动添加 .pdf 后缀
            if not save_name.endswith(".pdf"):
                save_name += ".pdf"

            return save_path, save_name
        else:
            return None, None

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

    @staticmethod
    @Threaded
    def key_listener(callbacks: dict):
        def on_key(event):
            if event.event_type == keyboard.KEY_DOWN:
                key = event.name
                if key in callbacks.keys():
                    print(f'Pressed {key}')
                    callbacks[key]()

        keyboard.on_press(on_key)

    def screenshot_active_window(self, save_dir_path: str = None, save_img_name: str = None):
        if save_dir_path is None:
            save_dir_path = self.save_img_dir_path
        if save_img_name is None:
            save_img_name = self.current_time_str()
        save_img_path = os.path.join(save_dir_path, save_img_name)
        _img = pyautogui.screenshot(save_img_path)
        output(f"{self.current_time_str()}save screenshot to \"{save_img_path}\"")

    @Threaded
    def stop_listener(self, callback: Callable, stop_shortcut: str = None, press_time: int = 1):
        if stop_shortcut is None:
            stop_shortcut = self.stop_shortcut
        # 长按 press_time 秒后触发回调函数
        esc_pressed_time = 0
        while self.catching_state:
            if keyboard.is_pressed(stop_shortcut):
                if esc_pressed_time == 0:
                    esc_pressed_time = press_time.time()
                elif press_time.time() - esc_pressed_time >= press_time:
                    print("Saving")
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
        return new_tem_dir_path

    def ask_pdf_save_path(self):
        self.save_pdf_dir_path, self.pdf_save_name = self.ask_save_path_and_name(
            default_extension=self.default_extension,
            default_name=self.current_time_str(),
            filetypes=self.filetypes)
        self.pdf_save_path = os.path.join(self.save_pdf_dir_path, self.pdf_save_name)
        return self.pdf_save_path

    def catching_start(self):
        if self.catching_state:
            output('warning: Already in catching!')
        self.save_img_dir_path = self.create_tem_img_dir()
        if self.pdf_save_name == self.pdf_save_path is None:
            self.ask_pdf_save_path()
        # 启动键盘监听线程
        self.catching_shortcut_listener = self.key_listener(self.stop_shortcut)
        self.stop_listener(self.catching_stop, self.stop_shortcut)
        self.catching_state = True

    def catching_stop(self):
        if self.catching_state is False:
            output('warning: No current catching!')
        self.catching_state = False
        self.save_pdf()

    def save_pdf(self, img_dir_path: str = None, pdf_save_path: str = None):
        if img_dir_path is None:
            img_dir_path = self.save_img_dir_path
        if pdf_save_path is None:
            pdf_save_path = self.pdf_save_path
        self.save_img_as_pdf(img_dir_path=img_dir_path, pdf_save_path=pdf_save_path)

    @staticmethod
    def exit():
        sys.exit()


def output(_str):
    print(_str)


if __name__ == '__main__':
    try:
        main = Main()
    except Exception:
        while True:
            output(traceback.format_exc())
