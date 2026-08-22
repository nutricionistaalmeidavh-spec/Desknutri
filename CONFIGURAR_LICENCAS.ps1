param(
  [Parameter(Mandatory=$true)][string]$AdminEmail,
  [string]$ServerUrl='http://127.0.0.1:8000'
)
$ErrorActionPreference='Stop'
python -m pip install -r license_server\requirements.txt
if (!(Test-Path 'license_server_data\license_private.pem')) { python -m license_server.admin_cli init-keys }
try { python -m license_server.admin_cli init-admin --email $AdminEmail } catch { Write-Host 'Administrador pode já existir; continue se for o caso.' }
python -m license_server.admin_cli copy-public-key --to config\license_public_key.pem
$cfgPath='config\commercial.json'
if (Test-Path $cfgPath) { $cfg=Get-Content $cfgPath -Raw | ConvertFrom-Json } else { $cfg=Get-Content 'config\commercial.example.json' -Raw | ConvertFrom-Json }
$cfg.license_server_url=$ServerUrl
$cfg | ConvertTo-Json -Depth 8 | Set-Content $cfgPath -Encoding UTF8
Write-Host "Licenciamento configurado para $ServerUrl"
Write-Host 'Inicie o painel local com .\INICIAR_PAINEL_LICENCAS.bat'
