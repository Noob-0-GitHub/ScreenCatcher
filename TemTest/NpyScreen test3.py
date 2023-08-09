import datetime
import threading
from time import sleep

import npyscreen


class MainForm(npyscreen.Form):
    def create(self):
        self.date = self.add(npyscreen.TitleText, value=str(datetime.datetime.now()), editable=False, name='Something')

    def afterEditing(self):
        self.parentApp.setNextForm(None)


class TestApp(npyscreen.NPSAppManaged):

    def onStart(self):
        self.textual = MainForm()
        self.registerForm("MAIN", self.textual)

        thread_time = threading.Thread(target=self.update_time, args=())
        thread_time.daemon = True
        thread_time.start()

    def update_time(self):
        while True:
            self.textual.date.value = str(datetime.datetime.now())
            self.textual.display()


if __name__ == "__main__":
    App = TestApp()
    App.run()
