from __future__ import annotations
import hashlib,json,os,shutil,tempfile,zipfile
from datetime import datetime,date
from pathlib import Path
from nutridesktop.core.paths import PATIENT_FILES_DIR,PATIENT_PHOTOS_DIR
from nutridesktop.core.security import fernet_from_password
from nutridesktop.data.database import Database,db
from nutridesktop.version import VERSION_INFO
from .documents import sha256_file

MAGIC=b'NUTRIPKG1\n';MANIFEST='manifest.json';DATA='patient.json'
def _sha_bytes(b):return hashlib.sha256(b).hexdigest()
def _encrypt(raw,password):
    if not password:return raw
    salt=os.urandom(16);return MAGIC+salt+fernet_from_password(password,salt).encrypt(raw)
def _decrypt(raw,password):
    if not raw.startswith(MAGIC):return raw
    if not password:raise ValueError('Pacote .nutri criptografado exige senha')
    salt=raw[len(MAGIC):len(MAGIC)+16];return fernet_from_password(password,salt).decrypt(raw[len(MAGIC)+16:])
def _dicts(c,sql,args):return [dict(r) for r in c.execute(sql,args).fetchall()]

def export_patient(pid,path,password=None,database:Database=db):
    with database.connect() as c:
        patient=c.execute('SELECT * FROM pacientes WHERE id=?',(pid,)).fetchone()
        if not patient:raise KeyError(pid)
        payload={'patient':dict(patient),'assessments':_dicts(c,'SELECT * FROM avaliacoes WHERE paciente_id=? ORDER BY id',(pid,)),'assessment_revisions':_dicts(c,'SELECT ar.* FROM avaliacao_revisoes ar JOIN avaliacoes a ON a.id=ar.avaliacao_id WHERE a.paciente_id=? ORDER BY ar.avaliacao_id,ar.versao',(pid,)),'anamneses':_dicts(c,'SELECT * FROM anamneses_paciente WHERE paciente_id=? ORDER BY id',(pid,)),'consultations':_dicts(c,'SELECT * FROM consultas WHERE paciente_id=? ORDER BY id',(pid,)),'consultation_recurrences':_dicts(c,'SELECT cr.* FROM consulta_recorrencias cr JOIN consultas co ON co.id=cr.consulta_id WHERE co.paciente_id=? ORDER BY cr.id',(pid,)),'consultation_links':_dicts(c,'SELECT cl.* FROM consulta_links cl JOIN consultas co ON co.id=cl.consulta_id WHERE co.paciente_id=? ORDER BY cl.id',(pid,)),'growth':_dicts(c,'SELECT * FROM growth_measurements WHERE paciente_id=? ORDER BY id',(pid,)),'timeline':_dicts(c,'SELECT * FROM timeline_events WHERE paciente_id=? ORDER BY id',(pid,)),'plans':[],'documents':_dicts(c,'SELECT * FROM documentos_paciente WHERE paciente_id=? ORDER BY id',(pid,)),'photos':_dicts(c,'SELECT * FROM fotos_paciente WHERE paciente_id=? ORDER BY id',(pid,))}
        for pl in _dicts(c,'SELECT * FROM planos WHERE paciente_id=? ORDER BY id',(pid,)):
            items=[]
            for it in _dicts(c,'SELECT * FROM plano_itens WHERE plano_id=? ORDER BY id',(pl['id'],)):
                if it.get('alimento_id'):
                    f=c.execute('SELECT * FROM alimentos WHERE id=?',(it['alimento_id'],)).fetchone();it['food']=dict(f) if f else None
                if it.get('receita_id'):
                    r=c.execute('SELECT * FROM receitas WHERE id=?',(it['receita_id'],)).fetchone();rec=dict(r) if r else None
                    if rec:
                        ingredients=[]
                        for ing in _dicts(c,'SELECT * FROM receita_ingredientes WHERE receita_id=? ORDER BY id',(r['id'],)):
                            f=c.execute('SELECT * FROM alimentos WHERE id=?',(ing['alimento_id'],)).fetchone();ing['food']=dict(f) if f else None;ingredients.append(ing)
                        rec['ingredients']=ingredients
                    it['recipe']=rec
                items.append(it)
            pl['items']=items;pl['targets']=_dicts(c,'SELECT * FROM plano_metas WHERE plano_id=?',(pl['id'],));pl['meal_targets']=_dicts(c,'SELECT * FROM refeicao_metas WHERE plano_id=?',(pl['id'],));pl['snapshots']=_dicts(c,'SELECT * FROM plano_versoes WHERE plano_id=? ORDER BY versao',(pl['id'],));payload['plans'].append(pl)
    for collection,prefix in ((payload['documents'],'documents'),(payload['photos'],'photos')):
        for row in collection:
            src=Path(row.get('caminho') or '')
            row['archive_path']=f"files/{prefix}/{row['id']}_{src.name}" if src.is_file() else None
    data_bytes=json.dumps(payload,ensure_ascii=False,default=str,separators=(',',':')).encode()
    with tempfile.TemporaryDirectory() as td:
        zp=Path(td)/'p.zip';files=[{'path':DATA,'sha256':_sha_bytes(data_bytes)}]
        with zipfile.ZipFile(zp,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr(DATA,data_bytes)
            for collection in (payload['documents'],payload['photos']):
                for row in collection:
                    ap=row.get('archive_path');src=Path(row.get('caminho') or '')
                    if ap and src.is_file():z.write(src,ap);files.append({'path':ap,'sha256':sha256_file(src)})
            manifest={'format':1,'type':'NutriDesktopPatient','exported_at':datetime.now().isoformat(),'versions':VERSION_INFO.as_dict(),'files':files}
            z.writestr(MANIFEST,json.dumps(manifest,ensure_ascii=False,indent=2))
        Path(path).write_bytes(_encrypt(zp.read_bytes(),password))
    return Path(path)

def _ensure_food(c,food):
    if not food:return None
    row=c.execute('SELECT id FROM alimentos WHERE descricao=? AND COALESCE(origem,\'\')=COALESCE(?,\'\') ORDER BY id LIMIT 1',(food.get('descricao'),food.get('origem'))).fetchone()
    if row:return row['id']
    allowed=['categoria','descricao','kcal','proteina','lipideos','carboidrato','fibra','calcio','magnesio','fosforo','ferro','sodio','potassio','cobre','zinco','tiamina','riboflavina','piridoxina','niacina','vitamina_c','origem'];vals=[food.get(k) for k in allowed];cur=c.execute(f"INSERT INTO alimentos({','.join(allowed)}) VALUES({','.join('?'*len(allowed))})",vals);return cur.lastrowid

def _ensure_recipe(c,rec):
    if not rec:return None
    row=c.execute('SELECT id FROM receitas WHERE nome=? ORDER BY id LIMIT 1',(rec.get('nome'),)).fetchone()
    if row:return row['id']
    cur=c.execute('INSERT INTO receitas(nome,categoria,tags,porcoes,modo_preparo) VALUES(?,?,?,?,?)',(rec.get('nome'),rec.get('categoria'),rec.get('tags'),rec.get('porcoes'),rec.get('modo_preparo')));rid=cur.lastrowid
    for ing in rec.get('ingredients',[]):c.execute('INSERT INTO receita_ingredientes(receita_id,alimento_id,quantidade_g) VALUES(?,?,?)',(rid,_ensure_food(c,ing.get('food')),ing.get('quantidade_g')))
    return rid

def import_patient(path,password=None,database:Database=db):
    raw=_decrypt(Path(path).read_bytes(),password)
    with tempfile.TemporaryDirectory() as td:
        zp=Path(td)/'p.zip';zp.write_bytes(raw);stage=Path(td)/'x';stage.mkdir()
        with zipfile.ZipFile(zp) as z:
            for m in z.infolist():
                p=Path(m.filename)
                if p.is_absolute() or '..' in p.parts:raise ValueError('Pacote contém caminho inseguro')
            manifest=json.loads(z.read(MANIFEST));z.extractall(stage)
        if manifest.get('type')!='NutriDesktopPatient' or manifest.get('format')!=1:raise ValueError('Formato .nutri não suportado')
        for f in manifest['files']:
            p=stage/f['path']
            if not p.is_file() or sha256_file(p)!=f['sha256']:raise ValueError(f"Checksum inválido: {f['path']}")
        payload=json.loads((stage/DATA).read_text(encoding='utf-8'));old=payload['patient']
        with database.transaction() as c:
            name=old.get('nome') or 'Paciente importado';existing=c.execute('SELECT 1 FROM pacientes WHERE nome=? AND COALESCE(data_nascimento,\'\')=COALESCE(?,\'\')',(name,old.get('data_nascimento'))).fetchone()
            if existing:name=f'{name} (importado {date.today().isoformat()})'
            cur=c.execute('INSERT INTO pacientes(nome,sexo,data_nascimento,telefone,email,observacoes,atualizado_em) VALUES(?,?,?,?,?,?,CURRENT_TIMESTAMP)',(name,old.get('sexo','F'),old.get('data_nascimento'),old.get('telefone'),old.get('email'),old.get('observacoes')));pid=cur.lastrowid
            assessment_map={}
            for a in payload.get('assessments',[]):
                cols=[k for k in a if k not in {'id','paciente_id'}];cur=c.execute(f"INSERT INTO avaliacoes(paciente_id,{','.join(cols)}) VALUES(?,{','.join('?'*len(cols))})",(pid,*[a[k] for k in cols]));assessment_map[a.get('id')]=cur.lastrowid
            for r in payload.get('assessment_revisions',[]):
                mapped=assessment_map.get(r.get('avaliacao_id'))
                if mapped:c.execute('INSERT INTO avaliacao_revisoes(avaliacao_id,versao,snapshot_json,motivo,created_at) VALUES(?,?,?,?,?)',(mapped,r.get('versao'),r.get('snapshot_json'),r.get('motivo'),r.get('created_at')))
            for a in payload.get('anamneses',[]):c.execute('INSERT INTO anamneses_paciente(paciente_id,nome_modelo,conteudo,data,tipo,dados_json,versao) VALUES(?,?,?,?,?,?,?)',(pid,a.get('nome_modelo'),a.get('conteudo'),a.get('data'),a.get('tipo'),a.get('dados_json'),a.get('versao')))
            for g in payload.get('growth',[]):c.execute('INSERT INTO growth_measurements(paciente_id,data,idade_dias,peso,altura_cm,imc,waz,haz,bmiz,wfhz,source) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(pid,g.get('data'),g.get('idade_dias'),g.get('peso'),g.get('altura_cm'),g.get('imc'),g.get('waz'),g.get('haz'),g.get('bmiz'),g.get('wfhz'),g.get('source','WHO')))
            plan_map={}
            for pl in payload.get('plans',[]):
                cur=c.execute('INSERT INTO planos(paciente_id,nome,data,vet_meta,observacoes,parent_plan_id,version_no,status) VALUES(?,?,?,?,?,NULL,?,?)',(pid,pl.get('nome'),pl.get('data'),pl.get('vet_meta'),pl.get('observacoes'),pl.get('version_no') or 1,pl.get('status') or 'Histórico'));newpl=cur.lastrowid;plan_map[pl.get('id')]=newpl
                for it in pl.get('items',[]):c.execute('INSERT INTO plano_itens(plano_id,refeicao,alimento_id,quantidade_g,receita_id,quantidade_porcoes) VALUES(?,?,?,?,?,?)',(newpl,it.get('refeicao'),_ensure_food(c,it.get('food')),it.get('quantidade_g'),_ensure_recipe(c,it.get('recipe')),it.get('quantidade_porcoes')))
                for t in pl.get('targets',[]):c.execute('INSERT OR REPLACE INTO plano_metas(plano_id,nutriente,meta,unidade,limite_min,limite_max) VALUES(?,?,?,?,?,?)',(newpl,t.get('nutriente'),t.get('meta'),t.get('unidade'),t.get('limite_min'),t.get('limite_max')))
                for t in pl.get('meal_targets',[]):c.execute('INSERT OR REPLACE INTO refeicao_metas(plano_id,refeicao,percentual_vet) VALUES(?,?,?)',(newpl,t.get('refeicao'),t.get('percentual_vet')))
                for snap in pl.get('snapshots',[]):c.execute('INSERT INTO plano_versoes(plano_id,versao,snapshot_json,created_at) VALUES(?,?,?,?)',(newpl,snap.get('versao'),snap.get('snapshot_json'),snap.get('created_at')))
            consult_map={}
            for a in payload.get('consultations',[]):
                cur=c.execute('INSERT INTO consultas(paciente_id,data,hora,status,observacoes,tipo,retorno_de_id,duracao_min) VALUES(?,?,?,?,?,?,NULL,?)',(pid,a.get('data'),a.get('hora'),a.get('status'),a.get('observacoes'),a.get('tipo'),a.get('duracao_min') or 60));consult_map[a.get('id')]=cur.lastrowid
            for a in payload.get('consultations',[]):
                if a.get('retorno_de_id') in consult_map:c.execute('UPDATE consultas SET retorno_de_id=? WHERE id=?',(consult_map[a.get('retorno_de_id')],consult_map[a.get('id')]))
            for r in payload.get('consultation_recurrences',[]):
                mapped=consult_map.get(r.get('consulta_id'))
                if mapped:c.execute('INSERT INTO consulta_recorrencias(consulta_id,frequencia,intervalo,ate_data) VALUES(?,?,?,?)',(mapped,r.get('frequencia'),r.get('intervalo'),r.get('ate_data')))
            for l in payload.get('consultation_links',[]):
                mapped=consult_map.get(l.get('consulta_id'))
                if mapped:c.execute('INSERT INTO consulta_links(consulta_id,tipo,entity_id) VALUES(?,?,?)',(mapped,l.get('tipo'),l.get('entity_id')))
            for ev in payload.get('timeline',[]):c.execute('INSERT INTO timeline_events(paciente_id,event_type,event_date,title,entity_id,metadata_json) VALUES(?,?,?,?,NULL,?)',(pid,ev.get('event_type'),ev.get('event_date'),ev.get('title'),ev.get('metadata_json') or '{}'))
        # Files are copied after DB transaction; failed copy raises and leaves an import trace rather than corrupting existing data.
        for row in payload.get('documents',[]):
            ap=row.get('archive_path')
            if ap and (stage/ap).is_file():
                d=PATIENT_FILES_DIR/str(pid);d.mkdir(parents=True,exist_ok=True);dst=d/Path(ap).name;shutil.copy2(stage/ap,dst)
                with database.transaction() as c:c.execute('INSERT INTO documentos_paciente(paciente_id,tipo,nome_arquivo,caminho,data,managed,sha256) VALUES(?,?,?,?,?,1,?)',(pid,row.get('tipo'),row.get('nome_arquivo'),str(dst),row.get('data'),sha256_file(dst)))
        for row in payload.get('photos',[]):
            ap=row.get('archive_path')
            if ap and (stage/ap).is_file():
                d=PATIENT_PHOTOS_DIR/str(pid);d.mkdir(parents=True,exist_ok=True);dst=d/Path(ap).name;shutil.copy2(stage/ap,dst)
                with database.transaction() as c:c.execute('INSERT INTO fotos_paciente(paciente_id,data,observacao,caminho) VALUES(?,?,?,?)',(pid,row.get('data'),row.get('observacao'),str(dst)))
        return pid
