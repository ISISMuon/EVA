# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files

a = Analysis(
    ['src/EVA/main.py', 'EVA.spec'],
    pathex=[],
    binaries=[],
    datas=[("src/EVA/databases", "src/EVA/databases"),
        ('src/EVA/resources', 'src/EVA/resources'),
           ("src/EVA/core/settings/defaults.ini", "src/EVA/core/settings"),
           ("src/EVA/core/settings/srim_defaults.txt", "src/EVA/core/settings"),
            ("src/srim", "srim"),
            ("icon.ico", ".")],
    hiddenimports=[],
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
    [],
    exclude_binaries=True,
    name='EVA',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    icon="icon.ico",
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='main',
)
