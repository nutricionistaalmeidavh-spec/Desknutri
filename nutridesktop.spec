# -*- mode: python ; coding: utf-8 -*-
# Arquivo de configuração do PyInstaller para o NutriDesktop.
# Gera um único .exe (Windows), sem janela de terminal, com a base TACO
# e o ícone embutidos.
#
# Para gerar o executável, rode (no Windows, dentro desta pasta):
#     pyinstaller nutridesktop.spec
#
# O resultado final aparece em dist/NutriDesktop.exe

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[('data', 'data')],  # inclui a base de alimentos TACO dentro do .exe
    hiddenimports=['PySide6', 'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets', 'fpdf'],
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
    a.binaries,
    a.datas,
    [],
    name='NutriDesktop',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,       # sem janela preta de terminal atrás do programa
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)
