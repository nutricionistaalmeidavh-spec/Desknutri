from __future__ import annotations
import argparse,base64,hashlib,json,os,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from nutridesktop.version import APP_VERSION,SCHEMA_VERSION,CLINICAL_CONTENT_VERSION,WHO_ENGINE_VERSION

def run(cmd):
    print('>',*map(str,cmd));subprocess.run(cmd,cwd=ROOT,check=True)
def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for ch in iter(lambda:f.read(1024*1024),b''):h.update(ch)
    return h.hexdigest()
def sign(payload,key_path):
    key=serialization.load_pem_private_key(Path(key_path).read_bytes(),password=None)
    if not isinstance(key,Ed25519PrivateKey):raise TypeError('A chave de release precisa ser Ed25519')
    raw=json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode();return base64.urlsafe_b64encode(key.sign(raw)).decode().rstrip('=')
def find_iscc():
    candidates=[os.environ.get('ISCC'),r'C:\Program Files (x86)\Inno Setup 6\ISCC.exe',r'C:\Program Files\Inno Setup 6\ISCC.exe']
    for c in candidates:
        if c and Path(c).exists():return c
    return shutil.which('ISCC.exe') or shutil.which('iscc')
def main():
    ap=argparse.ArgumentParser(description='Pipeline reproduzível de release do NutriDesktop')
    ap.add_argument('--private-key');ap.add_argument('--allow-unsigned',action='store_true');ap.add_argument('--base-url',default='');ap.add_argument('--channel',choices=['stable','beta'],default='stable');ap.add_argument('--notes-file',default='CHANGELOG.md');ap.add_argument('--mandatory',action='store_true');ap.add_argument('--skip-build',action='store_true');ap.add_argument('--installer');ap.add_argument('--rollback-installer');ap.add_argument('--rollback-url');a=ap.parse_args()
    if not a.private_key and not a.allow_unsigned:raise SystemExit('Informe --private-key ou use --allow-unsigned para release manual sem manifesto de atualização.')
    run([sys.executable,'-m','pytest','-q']);run([sys.executable,'-m','compileall','-q','app.py','nutridesktop'])
    if not a.skip_build:
        if os.name!='nt':raise SystemExit('Build do EXE/instalador requer Windows. Use --skip-build apenas para validar manifesto em outro SO.')
        run([sys.executable,'-m','PyInstaller','--clean','nutridesktop.spec']);iscc=find_iscc()
        if not iscc:raise SystemExit('Inno Setup ISCC.exe não encontrado')
        run([iscc,f'/DMyAppVersion={APP_VERSION}','NutriDesktop.iss'])
    installer=Path(a.installer) if a.installer else ROOT/'installer'/f'NutriDesktop-Setup-{APP_VERSION}.exe'
    if not installer.exists():raise SystemExit(f'Instalador ausente: {installer}')
    release=ROOT/'release';release.mkdir(exist_ok=True);target=release/installer.name
    if installer.resolve()!=target.resolve():shutil.copy2(installer,target)
    notes=(ROOT/a.notes_file).read_text(encoding='utf-8') if (ROOT/a.notes_file).exists() else f'NutriDesktop {APP_VERSION}'
    base=a.base_url.rstrip('/')
    installer_url=f'{base}/{target.name}' if base else target.name
    payload={'product':'NutriDesktop','version':APP_VERSION,'channel':a.channel,'schema_version':SCHEMA_VERSION,'clinical_content_version':CLINICAL_CONTENT_VERSION,'who_engine_version':WHO_ENGINE_VERSION,'published_at':datetime.now(timezone.utc).isoformat(),'installer_url':installer_url,'sha256':sha(target),'mandatory':a.mandatory,'notes':notes[:12000]}
    if a.rollback_installer:
        rb=Path(a.rollback_installer);rb_target=release/rb.name
        if rb.resolve()!=rb_target.resolve():shutil.copy2(rb,rb_target)
        payload['rollback']={'version':'previous','installer_url':a.rollback_url or ((f'{base}/{rb_target.name}') if base else rb_target.name),'sha256':sha(rb_target)}
    if a.private_key:
        doc={'payload':payload,'signature':sign(payload,a.private_key)}
        (release/'version.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding='utf-8')
    else:
        print('Aviso: UPDATE_SIGNING_PRIVATE_KEY_B64 ausente; version.json não será publicado. O instalador e os checksums permanecem válidos para distribuição manual.')
    checks=[f"{sha(p)}  {p.name}" for p in sorted(release.iterdir()) if p.is_file() and p.name!='SHA256SUMS.txt'];(release/'SHA256SUMS.txt').write_text('\n'.join(checks)+'\n',encoding='utf-8')
    print(f'Release pronta em {release}')
if __name__=='__main__':main()
