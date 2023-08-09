import time

import npyscreen


class ClockForm(npyscreen.Form):
    def create(self):
        # 创建多行不可编辑文本框用于显示时钟
        self.clock_widget1 = self.add(npyscreen.MultiLineEdit, name="time1:", value="", editable=False, max_height=5)
        self.clock_widget2 = self.add(npyscreen.MultiLineEdit, name="time2:", value="", editable=False, max_height=5)
        self.update_clock()  # 更新时钟文本

    def update_clock(self):
        while True:
            current_time = time.strftime("%H:%M:%S", time.localtime())
            self.clock_widget1.value = current_time
            self.clock_widget2.value = current_time
            self.clock_widget1.display()
            self.clock_widget2.display()
            time.sleep(1)  # 每隔一秒更新一次时钟


class ClockApp(npyscreen.NPSAppManaged):
    def onStart(self):
        self.addForm("MAIN", ClockForm, name="clock")
        self.switchForm("MAIN")

    def while_waiting(self):
        # 在此处理其他事件
        pass


if __name__ == "__main__":
    app = ClockApp()
    app.run()
