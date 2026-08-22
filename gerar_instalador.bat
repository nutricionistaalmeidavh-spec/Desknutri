@echo off
setlocal
python -m pip install -r requirements-dev.txt
python -m PyInstaller --clean --noconfirm nutridesktop.spec
if errorlevel 1 exit /b 1
where ISCC.exe >nul 2>nul
if errorlevel 1 (
  if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
  if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
) else set "ISCC=ISCC.exe"
if not defined ISCC (
  echo Inno Setup ISCC.exe nao encontrado.
  exit /b 2
)
"%ISCC%" NutriDesktop.iss
if errorlevel 1 exit /b 3
echo Instalador criado em installer\NutriDesktop-Setup-4.0.0.exe
endlocal
