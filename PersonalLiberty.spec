# -*- mode: python ; coding: utf-8 -*-

# Light build - no heavy AI libraries (torch, transformers, sentence-transformers)
# This reduces the app size from ~3GB to ~100MB

datas = [('productivity_ai.py', '.'), ('gamification.py', '.')]
binaries = []
hiddenimports = ['productivity_ai', 'numpy']

# Exclude heavy ML libraries that are no longer used
excludes = [
    'torch', 'transformers', 'sentence_transformers', 'huggingface_hub',
    'tokenizers', 'torchaudio', 'torchvision', 'cupy', 'triton'
]


a = Analysis(
    ['focus_blocker_qt.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
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
