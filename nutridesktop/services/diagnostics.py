from __future__ import annotations
import importlib.metadata,json,os,platform,re,shutil,sqlite3,sys,zipfile
from datetime import datetime
from pathlib import Path
from nutridesktop.core.paths import DATA_DIR,DB_PATH,PATIENT_FILES_DIR,PATIENT_PHOTOS_DIR,LOG_DIR,SUPPORT_DIR
from nutridesktop.data.database import Database,db
from nutridesktop.data.migrations import current_version
from nutridesktop.version import VERSION_INFO

def _dir_size(path:Path):
    if not path.exists():return 0
    return sum(p.stat().st_size for p in path.rglob('*') if p.is_file())
def _pkg(name):
    try:return importlib.metadata.version(name)
    except Exception:return None
def _sanitize(text:str,patient_names=()):
    text=text.replace(str(DATA_DIR),'%NUTRIDESKTOP_DATA%')
    for name in sorted({str(n).strip() for n in patient_names if str(n).strip()},key=len,reverse=True):
        text=text.replace(name,'[PATIENT_REDACTED]')
    text=re.sub(r'(?i)\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b','[EMAIL_REDACTED]',text)
    text=re.sub(r'(?<!\d)(?:\+?55\s*)?(?:\(?\d{2}\)?\s*)?9?\d{4}[-\s]?\d{4}(?!\d)','[PHONE_REDACTED]',text)
    return text

class DiagnosticsService:
    def __init__(self,database:Database=db):self.db=database
    def collect(self):
        data={'generated_at':datetime.now().isoformat(),'versions':VERSION_INFO.as_dict(),'python':sys.version.split()[0],'platform':platform.platform(),'machine':platform.machine(),'database':{},'storage':{},'dependencies':{},'last_backup':None,'last_update':None}
        try:
            with self.db.connect() as c:
                data['database']={'path':str(self.db.path),'schema':current_version(c),'integrity':c.execute('PRAGMA integrity_check').fetchone()[0],'patients':c.execute('SELECT COUNT(*) FROM pacientes').fetchone()[0],'assessments':c.execute('SELECT COUNT(*) FROM avaliacoes').fetchone()[0],'plans':c.execute('SELECT COUNT(*) FROM planos').fetchone()[0],'appointments':c.execute('SELECT COUNT(*) FROM consultas').fetchone()[0]}
                try:
                    b=c.execute("SELECT * FROM backup_history WHERE status='OK' ORDER BY id DESC LIMIT 1").fetchone();data['last_backup']=dict(b) if b else None
                    u=c.execute("SELECT * FROM app_update_history ORDER BY id DESC LIMIT 1").fetchone();data['last_update']=dict(u) if u else None
                except sqlite3.OperationalError:pass
        except Exception as e:data['database']={'error':type(e).__name__+': '+str(e)}
        total,used,free=shutil.disk_usage(DATA_DIR)
        data['storage']={'database_bytes':DB_PATH.stat().st_size if DB_PATH.exists() else 0,'documents_bytes':_dir_size(PATIENT_FILES_DIR),'photos_bytes':_dir_size(PATIENT_PHOTOS_DIR),'disk_free_bytes':free,'disk_total_bytes':total}
        for pkg in ('PySide6','fpdf2','cryptography','matplotlib','pygrowthstandards','pandas'):data['dependencies'][pkg]=_pkg(pkg)
        data['who_available']=bool(data['dependencies'].get('pygrowthstandards'))
        data['frozen']=bool(getattr(sys,'frozen',False));return data
    def text(self):
        d=self.collect();dbi=d['database'];st=d['storage'];last=d.get('last_backup')
        lines=[f"NutriDesk {d['versions']['app']}",f"Schema: {d['versions']['schema']} | Clínico: {d['versions']['clinical']} | WHO: {d['versions']['who']}",f"Windows/SO: {d['platform']}",f"Banco: {dbi.get('integrity','ERRO')} | pacientes: {dbi.get('patients','?')} | avaliações: {dbi.get('assessments','?')}",f"Banco: {st['database_bytes']/1024/1024:.1f} MB | documentos: {st['documents_bytes']/1024/1024:.1f} MB | fotos: {st['photos_bytes']/1024/1024:.1f} MB",f"Espaço livre: {st['disk_free_bytes']/1024/1024/1024:.1f} GB",f"Último backup: {(last or {}).get('created_at','nenhum')}",f"WHO engine: {'OK' if d['who_available'] else 'não carregado'}"]
        return '\n'.join(lines)
    def create_support_bundle(self,path=None,include_logs=True):
        SUPPORT_DIR.mkdir(parents=True,exist_ok=True);path=Path(path or SUPPORT_DIR/f"NutriDesk-Diagnostico-{datetime.now().strftime('%Y%m%d-%H%M%S')}.zip")
        diag=self.collect();public=dict(diag);public['database']=dict(public['database']);public['database']['path']='%NUTRIDESKTOP_DATA%/nutridesktop.db'
        try:
            with self.db.connect() as c:patient_names=[r[0] for r in c.execute('SELECT nome FROM pacientes').fetchall()]
        except Exception:patient_names=[]
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('diagnostics.json',json.dumps(public,ensure_ascii=False,indent=2,default=str));z.writestr('README.txt','Pacote técnico do NutriDesk. Não contém banco de dados, prontuários, fotos ou documentos clínicos.\n')
            if include_logs:
                for log in sorted(LOG_DIR.glob('nutridesktop.log*'))[-3:]:
                    try:z.writestr('logs/'+log.name,_sanitize(log.read_text(encoding='utf-8',errors='replace'),patient_names))
                    except Exception:pass
        return path
