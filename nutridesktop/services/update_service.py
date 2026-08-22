from __future__ import annotations
import base64,hashlib,json,os,subprocess,sys,tempfile,urllib.request,urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from nutridesktop.core.paths import CONFIG_DIR,resource_dir,UPDATE_DIR
from nutridesktop.data.database import Database,db
from nutridesktop.version import APP_VERSION,RELEASE_CHANNEL
from .app_settings import AppSettings

PUBLIC_KEY_LOCATIONS=[CONFIG_DIR/'update_public.pem',resource_dir()/'config'/'update_public.pem']
RESULT_FILE=UPDATE_DIR/'last_update_result.json'

@dataclass(frozen=True)
class UpdateInfo:
    version:str;channel:str;installer_url:str;sha256:str;notes:str='';mandatory:bool=False;published_at:str='';rollback:dict|None=None

def _b64d(s:str)->bytes:return base64.urlsafe_b64decode(s+'='*((4-len(s)%4)%4))
def _canonical(payload:dict)->bytes:return json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
def _version_tuple(v:str):
    core=v.split('-',1)[0];parts=[]
    for x in core.split('.'):
        try:parts.append(int(x))
        except ValueError:parts.append(0)
    return tuple((parts+[0,0,0])[:3])
def is_newer(candidate,current=APP_VERSION):return _version_tuple(candidate)>_version_tuple(current)
def sha256_file(path:Path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def _load_public_key()->Ed25519PublicKey:
    for p in PUBLIC_KEY_LOCATIONS:
        if p.exists():
            key=serialization.load_pem_public_key(p.read_bytes())
            if not isinstance(key,Ed25519PublicKey):raise ValueError('Chave pública de atualização não é Ed25519')
            return key
    raise FileNotFoundError('Configure config/update_public.pem antes de habilitar atualizações comerciais.')

def _read_url(url:str)->bytes:
    p=Path(url)
    if p.exists():return p.read_bytes()
    with urllib.request.urlopen(url,timeout=12) as r:return r.read()

def verify_manifest_document(doc:dict)->dict:
    payload=doc.get('payload');signature=doc.get('signature')
    if not isinstance(payload,dict) or not signature:raise ValueError('Manifesto de atualização inválido')
    if os.environ.get('NUTRIDESKTOP_ALLOW_UNSIGNED_UPDATES')=='1' and signature=='DEV':return payload
    _load_public_key().verify(_b64d(signature),_canonical(payload));return payload

class UpdateService:
    MANIFEST_KEY='p3.update_manifest_url';AUTO_KEY='p3.update_auto';CHANNEL_KEY='p3.update_channel'
    def __init__(self,database:Database=db):self.db=database;self.settings=AppSettings(database)
    def manifest_url(self):return self.settings.get(self.MANIFEST_KEY,'') or ''
    def set_manifest_url(self,url):self.settings.set(self.MANIFEST_KEY,(url or '').strip())
    def auto_check(self):return bool(self.settings.get(self.AUTO_KEY,True))
    def set_auto_check(self,value):self.settings.set(self.AUTO_KEY,bool(value))
    def channel(self):return self.settings.get(self.CHANNEL_KEY,RELEASE_CHANNEL) or RELEASE_CHANNEL
    def set_channel(self,value):self.settings.set(self.CHANNEL_KEY,value if value in {'stable','beta'} else 'stable')
    def check(self,url=None)->UpdateInfo|None:
        url=(url or self.manifest_url()).strip()
        if not url:return None
        doc=json.loads(_read_url(url).decode('utf-8'));payload=verify_manifest_document(doc)
        if payload.get('product')!='NutriDesktop':raise ValueError('Manifesto não pertence ao NutriDesk')
        if payload.get('channel','stable')!=self.channel():return None
        if not is_newer(str(payload['version'])):return None
        def resolve(ref):
            if not ref:return ref
            if Path(url).exists():return str((Path(url).resolve().parent/ref).resolve()) if not Path(ref).is_absolute() else ref
            return urllib.parse.urljoin(url,ref)
        rb=dict(payload.get('rollback') or {})
        if rb.get('installer_url'):rb['installer_url']=resolve(rb['installer_url'])
        return UpdateInfo(version=str(payload['version']),channel=payload.get('channel','stable'),installer_url=resolve(payload['installer_url']),sha256=payload['sha256'].lower(),notes=payload.get('notes',''),mandatory=bool(payload.get('mandatory',False)),published_at=payload.get('published_at',''),rollback=rb or None)
    def _download(self,url:str,dest:Path,expected:str):
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(_read_url(url))
        actual=sha256_file(dest)
        if actual.lower()!=expected.lower():dest.unlink(missing_ok=True);raise ValueError('SHA-256 do instalador não confere com o manifesto assinado')
        return dest
    def stage(self,info:UpdateInfo):
        installer=self._download(info.installer_url,UPDATE_DIR/f'NutriDesktop-Setup-{info.version}.exe',info.sha256)
        rollback_installer=None
        rb=info.rollback or {}
        if rb.get('installer_url') and rb.get('sha256'):
            try:rollback_installer=self._download(rb['installer_url'],UPDATE_DIR/f"NutriDesktop-Setup-{rb.get('version',APP_VERSION)}-rollback.exe",rb['sha256'])
            except Exception:rollback_installer=None
        return installer,rollback_installer
    def _runner_script(self):
        p=UPDATE_DIR/'apply_update.ps1'
        p.write_text(r'''param([int]$ParentPid,[string]$Installer,[string]$AppExe,[string]$RollbackInstaller,[string]$ResultFile,[string]$FromVersion,[string]$TargetVersion)
$ErrorActionPreference='Stop'
function Write-Result([string]$status,[string]$details){
  $obj=@{from_version=$FromVersion;to_version=$TargetVersion;status=$status;details=$details;time=(Get-Date).ToString('o')}
  $obj | ConvertTo-Json -Compress | Set-Content -Encoding UTF8 $ResultFile
}
try {
  try { Wait-Process -Id $ParentPid -Timeout 60 -ErrorAction SilentlyContinue } catch {}
  $p=Start-Process -FilePath $Installer -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/CLOSEAPPLICATIONS' -Wait -PassThru
  if($p.ExitCode -ne 0){ throw "installer_exit_$($p.ExitCode)" }
  $h=Start-Process -FilePath $AppExe -ArgumentList '--healthcheck' -Wait -PassThru
  if($h.ExitCode -eq 0){ Write-Result 'success' 'healthcheck_ok'; Start-Process -FilePath $AppExe; exit 0 }
  if($RollbackInstaller -and (Test-Path $RollbackInstaller)){
    $r=Start-Process -FilePath $RollbackInstaller -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/CLOSEAPPLICATIONS' -Wait -PassThru
    $rh=Start-Process -FilePath $AppExe -ArgumentList '--healthcheck' -Wait -PassThru
    if($r.ExitCode -eq 0 -and $rh.ExitCode -eq 0){ Write-Result 'rolled_back' 'new_version_healthcheck_failed'; Start-Process -FilePath $AppExe; exit 2 }
  }
  Write-Result 'failed' 'healthcheck_failed_without_successful_rollback'; exit 3
} catch { Write-Result 'failed' $_.Exception.Message; exit 4 }
''',encoding='utf-8');return p
    def launch_staged(self,info:UpdateInfo,installer:Path,rollback_installer:Path|None=None):
        if os.name!='nt':raise RuntimeError('Aplicação automática de update está disponível no Windows.')
        app_exe=Path(sys.executable if getattr(sys,'frozen',False) else sys.argv[0]).resolve()
        script=self._runner_script();args=['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(script),'-ParentPid',str(os.getpid()),'-Installer',str(installer),'-AppExe',str(app_exe),'-RollbackInstaller',str(rollback_installer or ''),'-ResultFile',str(RESULT_FILE),'-FromVersion',APP_VERSION,'-TargetVersion',info.version]
        flags=getattr(subprocess,'CREATE_NEW_PROCESS_GROUP',0)|getattr(subprocess,'DETACHED_PROCESS',0)
        subprocess.Popen(args,creationflags=flags,close_fds=True);return True
    def record_result(self):
        if not RESULT_FILE.exists():return None
        try:data=json.loads(RESULT_FILE.read_text(encoding='utf-8-sig'))
        except Exception:return None
        with self.db.transaction() as c:c.execute("INSERT INTO app_update_history(from_version,to_version,status,manifest_url,details_json) VALUES(?,?,?,?,?)",(data.get('from_version'),data.get('to_version'),data.get('status'),self.manifest_url(),json.dumps(data,ensure_ascii=False)))
        RESULT_FILE.unlink(missing_ok=True);return data
    def history(self,limit=20):
        with self.db.connect() as c:return c.execute("SELECT * FROM app_update_history ORDER BY id DESC LIMIT ?",(limit,)).fetchall()
