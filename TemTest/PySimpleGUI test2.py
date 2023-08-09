import time

import PySimpleGUI


def format_time(seconds):
    # 将秒数转换为格式化时间（时:分:秒）
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"


def main():
    PySimpleGUI.theme('DarkBlue3')  # 设置PySimpleGUI主题

    layout = [
        [PySimpleGUI.Text("00:00:00", font=("Helvetica", 48), justification="center", key="-TIMER-")],
        [PySimpleGUI.Button("Start", key="-START-"), PySimpleGUI.Button("Pause", key="-PAUSE-"), PySimpleGUI.Button("Reset", key="-RESET-"),
         PySimpleGUI.Button("Exit")]
    ]

    window = PySimpleGUI.Window("计时器示例", layout, resizable=True, finalize=True)

    start_time = None
    paused_time = 0
    paused = False

    while True:
        event, values = window.read(timeout=10)

        if event == PySimpleGUI.WIN_CLOSED or event == "Exit":
            break

        if event == "-START-":
            if start_time is None:
                start_time = time.time() - paused_time
                paused = False

        elif event == "-PAUSE-":
            if start_time is not None and not paused:
                paused_time = time.time() - start_time
                paused = True

        elif event == "-RESET-":
            # 重置计时器并归零
            start_time = None
            paused_time = 0
            paused = False
            window["-TIMER-"].update(format_time(paused_time))  # 立即将计时器显示归零

        if start_time is not None and not paused:
            elapsed_time = time.time() - start_time
            formatted_time = format_time(elapsed_time)
            window["-TIMER-"].update(formatted_time)

    window.close()


if __name__ == "__main__":
    main()
