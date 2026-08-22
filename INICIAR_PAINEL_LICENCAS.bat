@echo off
setlocal
set NUTRIDESK_COOKIE_SECURE=0
python -m pip install -r license_server\requirements.txt
if errorlevel 1 exit /b 1
python -m uvicorn license_server.main:app --host 127.0.0.1 --port 8000
endlocal
