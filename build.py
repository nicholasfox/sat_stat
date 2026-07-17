#!/usr/bin/env python3
"""Build sat_stat for Windows 11 using PyInstaller.

    pip install -r requirements-gui.txt
    python build.py

Output: dist/sat_stat/   (~35 MB, --onedir mode)
"""

import PyInstaller.__main__
import os

BASE = os.path.dirname(os.path.abspath(__file__))
sep = ';' if os.name == 'nt' else ':'

PyInstaller.__main__.run([
    '--name=sat_stat',
    '--onedir',
    '--noconfirm',
    '--clean',
    f'--add-data={BASE}{os.sep}templates{os.sep}templates',
    f'--add-data={BASE}{os.sep}tle_data.json{os.sep}.',
    '--hidden-import=cheroot.wsgi',
    '--hidden-import=webview.platforms.winforms',
    '--windowed',
    f'{BASE}{os.sep}analysis.py',
])
