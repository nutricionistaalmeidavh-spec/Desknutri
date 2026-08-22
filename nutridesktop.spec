# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
pgs_data=collect_data_files('pygrowthstandards')
pgs_hidden=collect_submodules('pygrowthstandards')
a=Analysis(['app.py'],pathex=[],binaries=[],datas=[('data','data'),('config','config')]+pgs_data,hiddenimports=['PySide6','fpdf','matplotlib']+pgs_hidden,hookspath=[],hooksconfig={},runtime_hooks=[],excludes=[],noarchive=False)
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,a.binaries,a.datas,[],name='NutriDesktop',debug=False,bootloader_ignore_signals=False,strip=False,upx=True,console=False,icon='icon.ico')
