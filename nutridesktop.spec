# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

pgs_data = collect_data_files('pygrowthstandards')
pgs_hidden = collect_submodules('pygrowthstandards')

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[('data', 'data'), ('config', 'config')] + pgs_data,
    hiddenimports=['PySide6', 'fpdf', 'matplotlib'] + pgs_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe_options = {}
icon_path = Path('icon.ico')
if icon_path.is_file():
    exe_options['icon'] = str(icon_path)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='NutriDesktop',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    **exe_options,
)
