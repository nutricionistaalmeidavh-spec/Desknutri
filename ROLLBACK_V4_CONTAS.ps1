param([Parameter(Mandatory=$true)][string]$BackupPath,[Parameter(Mandatory=$true)][string]$RepoPath)
$ErrorActionPreference='Stop'
$Backup=(Resolve-Path $BackupPath).Path;$Repo=(Resolve-Path $RepoPath).Path
$files=@('app.py','requirements.txt','requirements-dev.txt','nutridesktop.spec','NutriDesktop.iss','gerar_instalador.bat','GERAR_RELEASE.ps1','CHANGELOG.md','VERIFICAR_V4_CONTAS.ps1','CONFIGURAR_LICENCAS.ps1','INICIAR_PAINEL_LICENCAS.bat','README_V4_CONTAS.md','.gitignore')
$dirs=@('nutridesktop','license_server','tools','tests','.github')
foreach($f in $files){$p=Join-Path $Repo $f;if(Test-Path $p){Remove-Item $p -Force}}
foreach($d in $dirs){$p=Join-Path $Repo $d;if(Test-Path $p){Remove-Item $p -Recurse -Force}}
Get-ChildItem -Force $Backup|ForEach-Object{Copy-Item $_.FullName $Repo -Recurse -Force}
Write-Host 'Rollback V4 concluído.'
