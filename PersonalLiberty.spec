# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['focus_blocker_qt.py'],
    pathex=[],
    binaries=[],
    datas=[('productivity_ai.py', '.'), ('gamification.py', '.')],
    hiddenimports=['productivity_ai', 'numpy'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['torch', 'transformers', 'sentence_transformers', 'huggingface_hub', 'tokenizers', 'torchaudio', 'torchvision', 'cupy', 'triton'],
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
    icon=['icons\\app.ico'],
)
