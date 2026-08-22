from __future__ import annotations
import hashlib, os, shutil
from datetime import date
from pathlib import Path
from nutridesktop.core.paths import PATIENT_FILES_DIR
from nutridesktop.data.database import Database, db

def _safe_name(name:str):
    return ''.join(c if c.isalnum() or c in '._- ' else '_' for c in name).strip() or 'arquivo'

def sha256_file(path:Path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

class DocumentService:
    def __init__(self,database:Database=db): self.db=database
    def patient_dir(self,pid:int):
        p=PATIENT_FILES_DIR/str(pid); p.mkdir(parents=True,exist_ok=True); return p
    def import_file(self,pid:int,source:str|Path,typ='Documento',display_name=None):
        source=Path(source)
        if not source.is_file(): raise FileNotFoundError(source)
        target=self.patient_dir(pid)/(f"{date.today().isoformat()}_{os.urandom(3).hex()}_{_safe_name(display_name or source.name)}")
        shutil.copy2(source,target); digest=sha256_file(target)
        with self.db.transaction() as c:
            cur=c.execute("INSERT INTO documentos_paciente(paciente_id,tipo,nome_arquivo,caminho,data,managed,sha256) VALUES(?,?,?,?,?,?,?)",(pid,typ,display_name or source.name,str(target),date.today().isoformat(),1,digest)); did=cur.lastrowid
            c.execute("INSERT INTO timeline_events(paciente_id,event_type,event_date,title,entity_id,metadata_json) VALUES(?,?,?,?,?,'{}')",(pid,'documento',date.today().isoformat(),f'{typ}: {display_name or source.name}',did)); return did
    def register_generated(self,pid:int,generated_path:str|Path,typ='Relatório'):
        return self.import_file(pid,generated_path,typ)
    def migrate_legacy_documents(self):
        """Copies legacy external document paths into managed storage without deleting originals."""
        migrated=missing=already=0
        with self.db.transaction() as c:
            rows=c.execute("SELECT * FROM documentos_paciente ORDER BY id").fetchall()
            for row in rows:
                src=Path(row['caminho'] or '')
                if row['managed'] and src.exists(): already+=1;continue
                if not src.is_file(): missing+=1;continue
                patient_dir=self.patient_dir(row['paciente_id'])
                try:
                    if src.resolve().is_relative_to(patient_dir.resolve()):target=src
                    else:
                        target=patient_dir/(f"legacy_{row['id']}_{_safe_name(row['nome_arquivo'] or src.name)}")
                        if not target.exists():shutil.copy2(src,target)
                    c.execute("UPDATE documentos_paciente SET caminho=?,managed=1,sha256=? WHERE id=?",(str(target),sha256_file(target),row['id']));migrated+=1
                except Exception: missing+=1
        return {'migrated':migrated,'missing':missing,'already':already}
    def list(self,pid):
        with self.db.connect() as c:return c.execute("SELECT * FROM documentos_paciente WHERE paciente_id=? ORDER BY id DESC",(pid,)).fetchall()
    def verify(self,doc_id):
        with self.db.connect() as c:row=c.execute("SELECT * FROM documentos_paciente WHERE id=?",(doc_id,)).fetchone()
        if not row:return False,'Registro não encontrado'
        p=Path(row['caminho'])
        if not p.exists():return False,'Arquivo ausente'
        if row['sha256'] and sha256_file(p)!=row['sha256']:return False,'Checksum divergente'
        return True,'OK'
