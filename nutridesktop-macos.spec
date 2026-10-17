# -*- mode: python ; coding: utf-8 -*-
"""Pacote macOS nativo; o spec Windows continua independente."""
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
from nutridesktop.version import APP_VERSION

pgs_data = collect_data_files("pygrowthstandards")
pgs_hidden = collect_submodules("pygrowthstandards")

a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=[],
    datas=[("data", "data"), ("config", "config")] + pgs_data,
    hiddenimports=["PySide6", "fpdf", "matplotlib"] + pgs_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="NutriDesktop",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="NutriDesk",
)
app = BUNDLE(
    coll,
    name="NutriDesk.app",
    icon=None,
    bundle_identifier="br.com.artisys.nutridesk",
    info_plist={
        "CFBundleName": "NutriDesk",
        "CFBundleDisplayName": "NutriDesk",
        "CFBundleShortVersionString": APP_VERSION,
        "CFBundleVersion": APP_VERSION,
        "NSHighResolutionCapable": True,
    },
)
