#!/usr/bin/env python3
#


import sys
import platform
import os
from pathlib import Path

this_script = os.path.abspath(__file__)
this_dir = os.path.dirname(this_script)
dir_of_project: Path = Path(this_dir).parent
dir_root = os.path.abspath(dir_of_project.absolute())

def install_req():
    os.chdir(dir_root)
    if platform.system() == 'Windows':
        os.system(f'pip.exe install --upgrade pip')
        os.system(f'pip.exe install -r requirements.txt')
    elif platform.system() == 'Linux':
        os.system(f'pip3 install --upgrade pip')
        os.system(f'pip3 install -r requirements.txt')

def compile_code():
    """
    - Windows:
        pip install pyinstaller

    - Linux:
        sudo apt install pyinstaller

    pyinstaller --onefile --windowed seu_script.py
    pyinstaller --onefile --windowed main.py

    """
    os.chdir(dir_root)

    if platform.system() == 'Windows':
        os.system(f'python.exe -m pip install pyinstaller')
        
    elif platform.system() == 'Linux':
        # sudo apt install python3-types-pyinstaller
        pass

    os.system(f'pyinstaller --onefile --windowed main.py')


def main():
    install_req()
    compile_code()


if __name__ == '__main__':
    main()