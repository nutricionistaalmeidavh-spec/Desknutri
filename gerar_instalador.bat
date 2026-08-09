@echo off
setlocal EnableExtensions
python -m pip install -r requirements.txt pyinstaller
if errorlevel 1 exit /b 1
python -m PyInstaller nutridesktop.spec --noconfirm --clean
if errorlevel 1 exit /b 1
set "ISCC_PATH="
for %%I in (ISCC.exe) do set "ISCC_PATH=%%~$PATH:I"
if not defined ISCC_PATH if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC_PATH=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not defined ISCC_PATH if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC_PATH=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not defined ISCC_PATH if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC_PATH=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not defined ISCC_PATH if exist "%ProgramFiles%\Inno Setup 7\ISCC.exe" set "ISCC_PATH=%ProgramFiles%\Inno Setup 7\ISCC.exe"
if not defined ISCC_PATH (
  echo.
  echo ERRO: Inno Setup 6 ou 7 nao foi encontrado.
  echo Instale-o gratuitamente em https://jrsoftware.org/isdl.php
  echo Depois execute este arquivo novamente para gerar installer\NutriDesktop-Setup.exe.
  exit /b 1
)
"%ISCC_PATH%" /Qp NutriDesktop.iss
if errorlevel 1 exit /b 1
echo.
echo Instalador Windows criado em installer\NutriDesktop-Setup.exe
