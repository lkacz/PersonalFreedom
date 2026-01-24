# -*- mode: python ; coding: utf-8 -*-
import os
import sys

# Find jaraco.text data files to include
jaraco_datas = []
try:
    import jaraco.text
    jaraco_path = os.path.dirname(jaraco.text.__file__)
    lorem_file = os.path.join(jaraco_path, 'Lorem ipsum.txt')
    if os.path.exists(lorem_file):
        jaraco_datas.append((lorem_file, 'jaraco/text'))
except ImportError:
    pass

# Also check setuptools vendor location
try:
    import setuptools
    setuptools_path = os.path.dirname(setuptools.__file__)
    vendor_lorem = os.path.join(setuptools_path, '_vendor', 'jaraco', 'text', 'Lorem ipsum.txt')
    if os.path.exists(vendor_lorem):
        jaraco_datas.append((vendor_lorem, 'setuptools/_vendor/jaraco/text'))
except ImportError:
    pass


a = Analysis(
    ['focus_blocker_qt.py'],
    pathex=[],
    binaries=[],
    datas=[('productivity_ai.py', '.'), ('gamification.py', '.')] + jaraco_datas,
    hiddenimports=['productivity_ai', 'PySide6'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PersonalLiberty',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
    uac_admin=True,
)
