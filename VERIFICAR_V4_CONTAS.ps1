$ErrorActionPreference='Stop'
python --version
python -c "import sys; assert sys.version_info >= (3,11); print('python_ok',sys.version.split()[0])"
python -m pip install -r requirements-dev.txt
python -m pip install -r license_server\requirements.txt
python -m compileall -q app.py nutridesktop tools license_server
python -m pytest -q tests
python -c "from nutridesktop.data.database import db; from nutridesktop.version import VERSION_INFO; print('schema',db.initialize()); print('versions',VERSION_INFO.as_dict())"
python -c "import fastapi,uvicorn,cryptography; print('license_server_dependencies_ok')"
Write-Host 'V4 Conta + Licenças verificada.'
Write-Host 'Para configurar o painel: .\CONFIGURAR_LICENCAS.ps1 -AdminEmail voce@email.com -ServerUrl https://seu-servidor'
