$ErrorActionPreference='Stop'
python --version
python -c "import sys; assert sys.version_info >= (3,11); print('python_ok',sys.version.split()[0])"
python -m pip install -r requirements-dev.txt
python -m compileall -q app.py nutridesktop tools
python -m pytest -q tests
python -c "from nutridesktop.data.database import db; from nutridesktop.version import VERSION_INFO; print('schema',db.initialize()); print('versions',VERSION_INFO.as_dict())"
python -c "import PySide6,fpdf,cryptography,matplotlib,pygrowthstandards,pandas; print('runtime_dependencies_ok')"
Write-Host 'P3 verificada. Para instalador: .\gerar_instalador.bat'
Write-Host 'Para release assinada: gere a chave com python tools\update_key_admin.py <pasta-segura> e execute .\GERAR_RELEASE.ps1 -PrivateKey <update_private.pem>'
