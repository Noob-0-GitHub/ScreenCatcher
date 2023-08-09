import threading
import traceback

import npyscreen


class Queue:
    def __init__(self, lenght: int = 64, *items):
        if not isinstance(lenght, int):
            raise TypeError('lenght must be an int')
        if lenght <= 0:
            raise ValueError('lenght must > 0')
        if len(items) > lenght:
            lenght = len(items)
        self.index = self.e_index = 0
        self._list_lenght = lenght
        if items:
            if len(items) > lenght:
                items = items[:lenght]
            self._list = list(items) + [None] * (lenght - len(items))
            self.index += len(items) % lenght
            self.q_lenght = len(items)
            self._wait = [0, True]
        else:
            self._list = [None] * lenght
            self.q_lenght = 0
            self._wait = [0, False]

    def enqueue(self, item):
        self._list[self.index] = item
        if self.index == self.e_index and self.q_lenght:
            if self._wait[0] == self.index and self._wait[1]:
                self._wait[0] = (self._wait[0] + 1) % self._list_lenght
            self.index = (self.index + 1) % self._list_lenght
            self.e_index = self.index
        else:
            self.index = (self.index + 1) % self._list_lenght
            self.q_lenght += 1
        self._wait[1] = True

    def dequeue(self, n: int = 1):
        if not isinstance(n, int):
            raise TypeError('n must be an int')
        if n <= 0:
            raise ValueError('n must > 0')
        _list = []
        for i in range(n):
            _list.append(self._list[self.e_index])
            if self.q_lenght == 0:
                break
            else:
                self.e_index = (self.e_index + 1) % self._list_lenght
                self.q_lenght -= 1
        if len(_list) > 1:
            return _list
        else:
            return _list[0]

    def clear(self, item=None):
        self._list = [item] * self._list_lenght
        self.q_lenght = self.index = self.e_index = 0
        self._wait = [0, False]

    def add(self, *items):
        for i in items:
            self.enqueue(i)

    def return_list(self):
        if self.q_lenght == 0:
            return []
        if self.index > self.e_index:
            _l = self._list[self.e_index:self.index][::-1]
        else:
            _l = self._list[:self.index][::-1] + self._list[self.e_index:][::-1]
        return _l

    def wait(self):
        while not self._wait[1]:
            pass
        if self.index >= self._wait[0]:
            _result = self._list[self._wait[0]:self.index]
        else:
            _result = self._list[self._wait[0]:] + self._list[:self.index]
        self._wait = [self.index, False]
        return _result

    def __repr__(self):
        return str(self.return_list())

    def __str__(self):
        return str(self.return_list())

    def __call__(self, *args, **kwargs):
        return self.return_list()


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


# class OutputBox(npyscreen.MultiLineAction):
#     _contained_widget = npyscreen.MultiLineAction
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.cursor_position = 0
#         self._content_widget = npyscreen.TitleText(name='test', screen=self)
#         for _i in range(3):
#             self.change_value(str(), _i)
#         self.print_queue = Queue(lenght=3)
#         for _ in self.entry_widget.values:
#             self.print_queue.add(str())
#
#     def when_cursor_moved(self):
#         # 防止光标在只读文本框中移动
#         self.cursor_position = 0
#
#     def change_value(self, content, line):
#         while len(self.entry_widget.values) <= line:
#             self.entry_widget.values.append(str())
#         self.entry_widget.values[line] = content
#
#     def display(self):
#         self.print_update()
#         super().display()
#
#     def print_update(self):
#         for i in range(len(self.values)):
#             self.change_value(content=self.print_queue.return_list()[i], line=i)

class MyMultiLine(npyscreen.MultiLine):
    def __init__(self, *args, **kwargs):
        super(MyMultiLine, self).__init__(*args, **kwargs)

    def update_value(self, new_value):
        # Ensure the new value is a list
        if not isinstance(new_value, list):
            raise ValueError("new_value must be a list")

        # Update the value and display the new value
        self.values = new_value
        self.display()


class OutputBox(npyscreen.BoxTitle):
    _contained_widget = MyMultiLine


class MainForm(npyscreen.FormBaseNew):
    def create(self):
        # Output文本框
        self.add(OutputBox, name="Output", max_height=5)

        # 添加一个Save按钮
        self.save_button = self.add(npyscreen.ButtonPress, name="Save", when_pressed_function=self.on_save)

        # 添加一个文本控件
        self.save_path_widget = self.add(npyscreen.TitleText, name="Path:")

        # 添加一个Start按钮
        self.start_button = self.add(npyscreen.ButtonPress, name="Start", when_pressed_function=self.on_start)

        # 添加一个Exit按钮
        self.exit_button = self.add(npyscreen.ButtonPress, name="Exit", when_pressed_function=self.exit_editing)

        self.set_editing(self.save_button)

    def afterEditing(self):
        self.parentApp.setNextForm(None)

    def on_start(self):
        pass

    def on_save(self):
        pass


class MainUI(npyscreen.NPSAppManaged):
    def __init__(self):
        super().__init__()
        self.main_form: MainForm = None

    def onStart(self):
        self.main_form = self.addForm('MAIN', MainForm, name="ScreenCatcher")


def set_text():
    output_widget:OutputBox= main_ui.main_form.get_widget("Output")
    while True:
        try:
            output_widget.entry_widget.update_values(['test'])
        except:
            pass


try:
    if __name__ == '__main__':
        main_ui = MainUI()
        main_ui.run()
except Exception as e:
    # 获取完整的异常信息，包括堆栈跟踪
    error_message = traceback.format_exc()
    print(error_message)
    while True:
        pass
