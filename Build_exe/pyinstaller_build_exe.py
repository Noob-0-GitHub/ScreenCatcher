import os
import sys

import PyInstaller.__main__


def run(file_path):
    PyInstaller.__main__.run([
        "-F",
        "-w",
        f"{file_path}",
    ])


build_dir = os.path.abspath(".")
main_dir = os.path.abspath("..")
py_file_path = str()
py_files = list()
for file_name in os.listdir(main_dir):
    if file_name.endswith(".py"):
        py_file_path = os.path.join(main_dir, file_name)
        py_files.append(py_file_path)
if len(py_files) != 1:
    print("Python file not sure")
    py_file_path = input("Path >> ")
    if not len(py_file_path):
        sys.exit()
run(file_path=py_file_path)
