import os
import subprocess
import sys
import traceback

CURRENT_PATH = os.path.abspath(__file__)
START_KEY = 'start'


class SystemType:
    WINDOWS = 'win'
    LINUX = 'linux'
    command_separators: dict[str, str] = {
        WINDOWS: '&&',
        LINUX: ';'
    }

    @classmethod
    def isWindows(cls) -> bool:
        return sys.platform.startswith(cls.WINDOWS)

    @classmethod
    def isLinux(cls) -> bool:
        return sys.platform.startswith(cls.LINUX)

    @classmethod
    def command_separator(cls) -> str:
        if cls.isWindows():
            return cls.command_separators.get(cls.WINDOWS)
        elif cls.isLinux():
            return cls.command_separators.get(cls.LINUX)
        else:
            raise SystemError('Unknown system type')


if __name__ == '__main__' and len(sys.argv) <= 1:
    try:
        _start_command: list = ['echo']
        if SystemType.isWindows():
            _start_command = ['cmd', '/c', CURRENT_PATH, START_KEY]
        if SystemType.isLinux():
            _start_command = [['x-terminal-emulator', '-e', 'python', CURRENT_PATH, START_KEY]]
        p = subprocess.Popen(_start_command, shell=True, universal_newlines=True)
        sys.exit()
    except Exception:
        print(traceback.format_exc())
while True:
    pass
