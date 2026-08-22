from __future__ import annotations
import csv
from pathlib import Path
from nutridesktop.core.paths import resource_dir
from .database import Database,db

def _num(v):
    if v is None:return None
    v=str(v).strip()
    if v in ('','NA','Tr','*'):return None
    try:return float(v.replace(',','.'))
    except ValueError:return None

def seed_taco(database:Database=db):
    path=resource_dir()/'data'/'alimentos_taco.csv'
    if not path.exists():return 0
    with database.transaction() as c:
        if c.execute('SELECT COUNT(*) FROM alimentos').fetchone()[0]>0:return 0
        rows=[]
        with path.open(encoding='utf-8') as f:
            reader=csv.reader(f);next(reader,None)
            for row in reader:
                if len(row)<28:continue
                rows.append((row[1].strip(),row[2].strip(),_num(row[4]),_num(row[6]),_num(row[7]),_num(row[9]),_num(row[10]),_num(row[12]),_num(row[13]),_num(row[15]),_num(row[16]),_num(row[17]),_num(row[18]),_num(row[19]),_num(row[20]),_num(row[24]),_num(row[25]),_num(row[26]),_num(row[27]),_num(row[28] if len(row)>28 else None)))
        c.executemany('''INSERT INTO alimentos(categoria,descricao,kcal,proteina,lipideos,carboidrato,fibra,calcio,magnesio,fosforo,ferro,sodio,potassio,cobre,zinco,tiamina,riboflavina,piridoxina,niacina,vitamina_c) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',rows)
        return len(rows)
def seed_legacy_content(database:Database=db):
    try:import content_seed
    except Exception:return
    with database.transaction() as c:
        try:
            if c.execute('SELECT COUNT(*) FROM receitas').fetchone()[0]==0:content_seed.seed_receitas(c)
            if c.execute('SELECT COUNT(*) FROM planos_modelo').fetchone()[0]==0:content_seed.seed_planos_modelo(c)
            if c.execute('SELECT COUNT(*) FROM diretrizes').fetchone()[0]==0:content_seed.seed_diretrizes(c)
            if c.execute('SELECT COUNT(*) FROM anamneses_modelo').fetchone()[0]==0:content_seed.seed_anamneses(c)
            if hasattr(content_seed,'atualizar_e_completar_diretrizes'):content_seed.atualizar_e_completar_diretrizes(c)
        except Exception:
            # Content seed is optional compatibility; clinical core must still start.
            pass
