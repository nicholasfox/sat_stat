#!/usr/bin/env python3
"""Build sat_stat for Windows 11 using PyInstaller.

    pip install -r requirements-gui.txt
    python build.py

Output: dist/sat_stat/   (~35 MB, --onedir mode)
"""

import PyInstaller.__main__
import os

BASE = os.path.dirname(os.path.abspath(__file__))

PyInstaller.__main__.run([
    '--name=sat_stat',
    '--onedir',
    '--noconfirm',
    '--clean',
    f'--add-data={os.path.join(BASE, "templates")}:templates',
    f'--add-data={os.path.join(BASE, "tle_data.json")}:.',
    '--hidden-import=cheroot.wsgi',
    '--hidden-import=webview.platforms.winforms',
    '--console',
    os.path.join(BASE, 'analysis.py'),
])
