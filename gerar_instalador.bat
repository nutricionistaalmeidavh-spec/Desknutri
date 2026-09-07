@echo off
setlocal
python -m pip install -r requirements-dev.txt
python -m PyInstaller --clean --noconfirm nutridesktop.spec
if errorlevel 1 exit /b 1
for /f "usebackq delims=" %%V in (`python -c "from nutridesktop.version import APP_VERSION; print(APP_VERSION)"`) do set "APP_VERSION=%%V"
if not defined APP_VERSION (
  echo Nao foi possivel ler APP_VERSION de nutridesktop\version.py.
  exit /b 2
)
where ISCC.exe >nul 2>nul
if errorlevel 1 (
  if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
  if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
) else set "ISCC=ISCC.exe"
if not defined ISCC (
  echo Inno Setup ISCC.exe nao encontrado.
  exit /b 3
)
"%ISCC%" NutriDesktop.iss
if errorlevel 1 exit /b 4
echo Instalador criado em installer\NutriDesktop-Setup-%APP_VERSION%.exe
endlocal
