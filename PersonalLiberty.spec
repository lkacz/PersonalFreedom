# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['focus_blocker_qt.py'],
    pathex=[],
    binaries=[],
    datas=[('icons', 'icons'), ('entitidex', 'entitidex'), ('city', 'city'), ('voices', 'voices')],
    hiddenimports=['PySide6.QtCore', 'PySide6.QtWidgets', 'PySide6.QtGui', 'gamification', 'productivity_ai', 'city', 'entitidex'],
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
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icons\\app.ico'],
)
