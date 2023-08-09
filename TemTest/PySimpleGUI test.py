import datetime

import PySimpleGUI as sg


class TerminalApp(sg.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.current_command = ""

    def execute_command(self, command):
        if command.lower() == "hello":
            return "Hello, World!"
        elif command.lower() == "date":
            return str(datetime.datetime.now())
        elif command.lower() == "exit":
            return "Exiting..."
        else:
            return f"Unknown command: {command}"

    def run(self):
        layout = [
            [sg.Text("模拟终端", font=("Helvetica", 16))],
            [sg.Output(size=(80, 20), font=("Helvetica", 12))],
            [sg.Input(do_not_clear=True, font=("Helvetica", 12), key="-INPUT-")],
            [sg.Button("执行", bind_return_key=True), sg.Button("退出")]
        ]

        self.layout(layout)
        self.finalize()

        while True:
            event, values = self.read()

            if event == sg.WIN_CLOSED or event == "退出":
                break

            if event == "执行":
                self.current_command = values["-INPUT-"]
                output = self.execute_command(self.current_command)
                print(f"> {self.current_command}")
                print(output)
                print()

        self.close()


if __name__ == "__main__":
    app = TerminalApp("模拟终端示例", resizable=True)
    app.run()
