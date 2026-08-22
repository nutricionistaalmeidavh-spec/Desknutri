param([Parameter(Mandatory=$true)][string]$RepoPath)
$ErrorActionPreference='Stop'
$Source=Split-Path -Parent $MyInvocation.MyCommand.Path
$Repo=(Resolve-Path $RepoPath).Path
if (!(Test-Path (Join-Path $Repo 'app.py'))) { throw "app.py não encontrado no repositório alvo." }
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$backup=Join-Path $Repo ".nutridesktop_p3_backup\$stamp"
New-Item -ItemType Directory -Force -Path $backup | Out-Null
$files=@('app.py','requirements.txt','requirements-dev.txt','nutridesktop.spec','NutriDesktop.iss','gerar_instalador.bat','GERAR_RELEASE.ps1','CHANGELOG.md','VERIFICAR_V3_P3.ps1','ROLLBACK_V3_P3.ps1','README_P3.md','MATRIZ_P3_29_35.md')
$dirs=@('nutridesktop','tools','tests','.github')
foreach($f in $files){
  $src=Join-Path $Source $f; if(!(Test-Path $src)){continue}
  $dst=Join-Path $Repo $f
  if(Test-Path $dst){$bd=Join-Path $backup $f;New-Item -ItemType Directory -Force -Path (Split-Path $bd) | Out-Null;Copy-Item $dst $bd -Force}
  Copy-Item $src $dst -Force
}
foreach($dir in $dirs){
  $src=Join-Path $Source $dir;if(!(Test-Path $src)){continue};$dst=Join-Path $Repo $dir
  if(Test-Path $dst){Copy-Item $dst (Join-Path $backup $dir) -Recurse -Force}
  Copy-Item $src $Repo -Recurse -Force
}
# Config é mesclado para nunca apagar commercial.json/update_public.pem do usuário.
$cfgSrc=Join-Path $Source 'config';$cfgDst=Join-Path $Repo 'config';New-Item -ItemType Directory -Force -Path $cfgDst | Out-Null
if(Test-Path $cfgSrc){Get-ChildItem $cfgSrc -File | ForEach-Object {if($_.Name -notin @('commercial.json','update_public.pem')){Copy-Item $_.FullName (Join-Path $cfgDst $_.Name) -Force}}}
$gitignore=Join-Path $Repo '.gitignore';if(Test-Path $gitignore){Copy-Item $gitignore (Join-Path $backup '.gitignore') -Force}else{New-Item -ItemType File -Path $gitignore|Out-Null}
$rules=@('.release/update_private.pem','update_private.pem','release/','installer/','dist/','build/','.nutridesktop_p3_backup/','*.nutri','*.nbak')
$current=(Get-Content $gitignore -ErrorAction SilentlyContinue);foreach($rule in $rules){if($current -notcontains $rule){Add-Content -Path $gitignore -Value $rule}}
Write-Host "P3 aplicada. Backup reversível em: $backup"
Write-Host "Execute .\VERIFICAR_V3_P3.ps1 antes de gerar release."
