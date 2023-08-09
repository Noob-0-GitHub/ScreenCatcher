import curses
import os
import tkinter as tk
from datetime import datetime
from tkinter import filedialog
from typing import List, Tuple

import keyboard
import pyautogui
from fpdf import FPDF


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


def ask_save_path_and_name(default_extension: str, default_name: str = None, filetypes: List[Tuple[str, str]] = None):
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


def save_img_as_pdf(img_dir_path: str, pdf_save_path: str = None):
    if pdf_save_path is None:
        pdf_save_path: str = os.path.join(img_dir_path, "%s.pdf" % current_time_str())
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
def shortcut_listener(callbacks: dict):
    def on_key(event):
        if event.event_type == keyboard.KEY_DOWN:
            key = event.name
            if key in callbacks.keys():
                print(f'Pressed {key}')
                callbacks[key]()

    keyboard.on_press(on_key)


def screenshot_active_window(save_dir_path: str, save_img_name: str):
    save_img_path = os.path.join(save_dir_path, save_img_name)
    _img = pyautogui.screenshot(save_img_path)
    output(f"{current_time_str()}save screenshot to \"{save_img_path}\"")


def _main():
    filetypes = [("PDF Files", "*.pdf")]
    img_save_path = r'C:\Users\Anthony-XKN\Desktop'
    save_dir_path, pdf_save_name = ask_save_path_and_name(default_extension='.pdf', default_name=current_time_str(),
                                                          filetypes=filetypes)
    pdf_save_path = os.path.join(save_dir_path, pdf_save_name)
    # 定义快捷键和对应的回调函数
    shortcuts = {
        "v": lambda: screenshot_active_window(img_save_path, current_time_str())
    }
    shortcut_listener(shortcuts)
    # 监听ESC键，长按三秒后退出程序
    esc_pressed_time = 0
    while True:
        if keyboard.is_pressed("esc"):
            if esc_pressed_time == 0:
                esc_pressed_time = time.time()
            elif time.time() - esc_pressed_time >= 3:
                print("Saving")
                break
        else:
            esc_pressed_time = 0
    save_img_as_pdf(img_dir_path=img_save_path, pdf_save_path=pdf_save_path)


# class Main:
#     def __init__(self):
#         self.catching_state = False
#         self.default_extension = ".pdf"
#         self.filetypes = [("PDF Files", "*.pdf")]
#         self.img_create_dir_path = r'C:\Users\Anthony-XKN\Desktop'
#         self.save_img_dir_path = None
#         # 定义快捷键和对应的回调函数
#         self.shortcuts = {
#             "v": self.screenshot_active_window
#         }
#         self.stop_shortcut = "Esc"
#         self.save_pdf_dir_path = None
#         self.pdf_save_name = None
#         self.pdf_save_path = None
#         self.catching_shortcut_listener = None
#         self.main_UI = MainUI(parent=self)
#         self.main_UI.run()
#
#     def screenshot_active_window(self, save_dir_path: str = None, save_img_name: str = None):
#         if save_dir_path is None:
#             save_dir_path = self.save_img_dir_path
#         if save_img_name is None:
#             save_img_name = current_time_str()
#         save_img_path = os.path.join(save_dir_path, save_img_name)
#         _img = pyautogui.screenshot(save_img_path)
#         output(f"{current_time_str()}save screenshot to \"{save_img_path}\"")
#
#     @Threaded
#     def stop_listener(self, callback: Callable, stop_shortcut: str = None, press_time: int = 1):
#         if stop_shortcut is None:
#             stop_shortcut = self.stop_shortcut
#         # 长按 press_time 秒后触发回调函数
#         esc_pressed_time = 0
#         while self.catching_state:
#             if keyboard.is_pressed(stop_shortcut):
#                 if esc_pressed_time == 0:
#                     esc_pressed_time = press_time.time()
#                 elif press_time.time() - esc_pressed_time >= press_time:
#                     print("Saving")
#                     break
#             else:
#                 esc_pressed_time = 0
#         callback()
#
#     def create_tem_img_dir(self, name: str = None, path: str = None):
#         if name is None:
#             name = current_time_str()
#         if path is None:
#             path = self.img_create_dir_path
#         new_tem_dir_path = os.path.join(path, name)
#         os.makedirs(new_tem_dir_path)
#         return new_tem_dir_path
#
#     def select_pdf_save_path(self):
#         self.save_pdf_dir_path, self.pdf_save_name = ask_save_path_and_name(default_extension=self.default_extension,
#                                                                             default_name=current_time_str(),
#                                                                             filetypes=self.filetypes)
#         self.pdf_save_path = os.path.join(self.save_pdf_dir_path, self.pdf_save_name)
#         self.update_save_path_widget()
#         return self.pdf_save_path
#
#     def update_save_path_widget(self):
#         try:
#             self.main_UI.main_form.save_path_widget = self.pdf_save_path
#         except AttributeError:
#             return
#
#     def catching_start(self):
#         if self.catching_state:
#             output('warning: Already in catching!')
#         self.save_img_dir_path = self.create_tem_img_dir()
#         if self.pdf_save_name == self.pdf_save_path is None:
#             self.select_pdf_save_path()
#         # 启动键盘监听线程
#         self.catching_shortcut_listener = shortcut_listener(self.stop_shortcut)
#         self.stop_listener(self.catching_stop, self.stop_shortcut)
#         self.catching_state = True
#
#     def catching_stop(self):
#         if self.catching_state is False:
#             output('warning: No current catching!')
#         self.catching_state = False
#         self.save_pdf()
#
#     def save_pdf(self, img_dir_path: str = None, pdf_save_path: str = None):
#         if img_dir_path is None:
#             img_dir_path = self.save_img_dir_path
#         if pdf_save_path is None:
#             pdf_save_path = self.pdf_save_path
#         save_img_as_pdf(img_dir_path=img_dir_path, pdf_save_path=pdf_save_path)
#
#     def exit(self):
#         self.main_UI.exit()
#
#     def output(self, _str):
#         # self.main_UI.main_form.output_box.print_queue.add(_str)
#         self.main_UI.main_form.output_box.set_value(_str)
#         self.main_UI.main_form.output_box.display()
# def output(_str):
#     try:
#         _main.output(_str)
#     except Exception:
#         error_message = traceback.format_exc()
#         print(error_message)
#         print(_str)
# @Threaded
# def print_test():
#     while True:
#         try:
#             _main.output(f"test {current_time_str()}")
#         except Exception as _e:
#             print(f"{current_time_str()}{_e}")
version = 'v0.1'
intro = f"""
Welcome to use ScreenCatcher {version} 
欢迎使用ScreenCatcher {version}
Command list命令列表:
save: to select PDF-save path 选择PDF保存位置
start: Start catching 启动屏幕捕捉(需要选择保存位置)
stop: Stop catching 停止屏幕捕捉(自动保存PDF)
exit: 退出程序
"""


def main(stdscr: curses):
    stdscr.clear()
    stdscr.addstr(intro)
    stdscr.refresh()
    stdscr.getkey()


def end():
    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()


if __name__ == '__main__':
    curses.wrapper(main)
# if __name__ == '__main__':
#     try:
#         _main()
#     except Exception as e:
#         # 获取完整的异常信息，包括堆栈跟踪
#         output(traceback.format_exc())
#         while True:
#             output(current_time_str())
