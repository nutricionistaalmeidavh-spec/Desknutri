from __future__ import annotations
import hashlib, json, os, shutil, sqlite3, tempfile, zipfile
from datetime import datetime, timezone
from pathlib import Path
from nutridesktop.core.paths import DB_PATH, PATIENT_FILES_DIR, PATIENT_PHOTOS_DIR, DATA_DIR
from nutridesktop.core.security import fernet_from_password
from nutridesktop.version import APP_VERSION, SCHEMA_VERSION
from nutridesktop.data.database import Database, db
from nutridesktop.data.migrations import current_version

MANIFEST='manifest.json'; ENC_MAGIC=b'NUTRIBAK1\n'

def _sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for ch in iter(lambda:f.read(1024*1024),b''):h.update(ch)
    return h.hexdigest()

def _safe_members(zf):
    for m in zf.infolist():
        p=Path(m.filename)
        if p.is_absolute() or '..' in p.parts: raise ValueError('Backup contém caminho inseguro')
        yield m

def create_backup(destination,password=None,database:Database=db,trigger="manual",record_history=True):
    destination=Path(destination); destination.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); snapshot=td/'nutridesktop.db'
        src=database.connect(); dst=sqlite3.connect(snapshot)
        try: src.backup(dst)
        finally: src.close(); dst.close()
        files=[]
        with zipfile.ZipFile(td/'backup.zip','w',zipfile.ZIP_DEFLATED) as z:
            z.write(snapshot,'nutridesktop.db'); files.append({'path':'nutridesktop.db','sha256':_sha(snapshot)})
            for folder,name in ((PATIENT_FILES_DIR,'pacientes_arquivos'),(PATIENT_PHOTOS_DIR,'fotos_pacientes')):
                if folder.exists():
                    for p in folder.rglob('*'):
                        if p.is_file():
                            arc=(Path(name)/p.relative_to(folder)).as_posix(); z.write(p,arc); files.append({'path':arc,'sha256':_sha(p)})
            manifest={'format':2,'app_version':APP_VERSION,'schema_version':SCHEMA_VERSION,'created_at':datetime.now(timezone.utc).isoformat(),'files':files}
            z.writestr(MANIFEST,json.dumps(manifest,ensure_ascii=False,indent=2))
        raw=(td/'backup.zip').read_bytes()
        if password:
            salt=os.urandom(16); encrypted=fernet_from_password(password,salt).encrypt(raw); destination.write_bytes(ENC_MAGIC+salt+encrypted)
        else: destination.write_bytes(raw)
    if record_history:
        try:
            digest=_sha(destination)
            with database.transaction() as c:
                c.execute("INSERT INTO backup_history(path,sha256,size_bytes,status,encrypted,trigger) VALUES(?,?,?,?,?,?)",(str(destination),digest,destination.stat().st_size,"OK",1 if password else 0,trigger))
        except Exception:
            pass
    return destination

def _decrypt_if_needed(path,password):
    raw=Path(path).read_bytes()
    if not raw.startswith(ENC_MAGIC):return raw
    if not password:raise ValueError('Backup criptografado exige senha')
    salt=raw[len(ENC_MAGIC):len(ENC_MAGIC)+16]; token=raw[len(ENC_MAGIC)+16:]
    return fernet_from_password(password,salt).decrypt(token)

def validate_backup(path,password=None):
    raw=_decrypt_if_needed(path,password)
    with tempfile.TemporaryDirectory() as td:
        zp=Path(td)/'b.zip';zp.write_bytes(raw)
        with zipfile.ZipFile(zp) as z:
            _safe_members(z); manifest=json.loads(z.read(MANIFEST))
            if manifest.get('format')!=2:raise ValueError('Formato de backup não suportado')
            z.extractall(Path(td)/'x',members=list(_safe_members(z))); x=Path(td)/'x'
            for item in manifest['files']:
                p=x/item['path']
                if not p.is_file() or _sha(p)!=item['sha256']:raise ValueError(f"Falha de integridade: {item['path']}")
            conn=sqlite3.connect(x/'nutridesktop.db')
            try:
                integrity=conn.execute('PRAGMA integrity_check').fetchone()[0]
                if integrity!='ok':raise ValueError('SQLite integrity_check falhou')
                schema=current_version(conn)
            finally:conn.close()
            return {'manifest':manifest,'schema_version':schema}

def restore_backup(path,password=None,database:Database=db):
    validation=validate_backup(path,password); raw=_decrypt_if_needed(path,password)
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); zp=td/'b.zip';zp.write_bytes(raw); stage=td/'stage';stage.mkdir()
        with zipfile.ZipFile(zp) as z:z.extractall(stage,members=list(_safe_members(z)))
        rollback=td/'rollback'; rollback.mkdir()
        for p in (DB_PATH,PATIENT_FILES_DIR,PATIENT_PHOTOS_DIR):
            if Path(p).exists():
                target=rollback/Path(p).name
                if Path(p).is_dir():shutil.copytree(p,target)
                else:shutil.copy2(p,target)
        try:
            shutil.copy2(stage/'nutridesktop.db',DB_PATH)
            for src_name,dst in (('pacientes_arquivos',PATIENT_FILES_DIR),('fotos_pacientes',PATIENT_PHOTOS_DIR)):
                src=stage/src_name
                if dst.exists():shutil.rmtree(dst)
                if src.exists():shutil.copytree(src,dst)
                else:dst.mkdir(parents=True,exist_ok=True)
            database.initialize()
        except Exception:
            rbdb=rollback/'nutridesktop.db'
            if rbdb.exists():shutil.copy2(rbdb,DB_PATH)
            for nm,dst in (('pacientes_arquivos',PATIENT_FILES_DIR),('fotos_pacientes',PATIENT_PHOTOS_DIR)):
                if dst.exists():shutil.rmtree(dst)
                src=rollback/nm
                if src.exists():shutil.copytree(src,dst)
            raise
    return validation