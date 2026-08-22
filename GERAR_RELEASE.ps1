param(
  [Parameter(Mandatory=$true)][string]$PrivateKey,
  [string]$BaseUrl="",
  [ValidateSet("stable","beta")][string]$Channel="stable",
  [string]$RollbackInstaller="",
  [string]$RollbackUrl="",
  [switch]$Mandatory
)
$ErrorActionPreference="Stop"
python -m pip install -r requirements-dev.txt
$args=@("tools/build_release.py","--private-key",$PrivateKey,"--channel",$Channel)
if($BaseUrl){$args += @("--base-url",$BaseUrl)}
if($RollbackInstaller){$args += @("--rollback-installer",$RollbackInstaller)}
if($RollbackUrl){$args += @("--rollback-url",$RollbackUrl)}
if($Mandatory){$args += "--mandatory"}
python @args
