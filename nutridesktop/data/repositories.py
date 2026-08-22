from __future__ import annotations
import json, sqlite3, csv, os, shutil
from datetime import date, datetime
from pathlib import Path
from nutridesktop.core.paths import PATIENT_PHOTOS_DIR
from .database import Database, db

class BaseRepo:
    def __init__(self,database:Database=db): self.db=database

class PatientRepository(BaseRepo):
    def create(self,nome,sexo,nascimento="",telefone="",email="",observacoes=""):
        with self.db.transaction() as c:
            cur=c.execute("INSERT INTO pacientes(nome,sexo,data_nascimento,telefone,email,observacoes,atualizado_em) VALUES(?,?,?,?,?,?,CURRENT_TIMESTAMP)",(nome,sexo,nascimento,telefone,email,observacoes)); pid=cur.lastrowid
            self._event(c,pid,"paciente","Cadastro do paciente",pid,{})
            return pid
    def update(self,pid,**fields):
        allowed={"nome","sexo","data_nascimento","telefone","email","observacoes"}; data={k:v for k,v in fields.items() if k in allowed}
        if not data:return
        with self.db.transaction() as c:
            c.execute("UPDATE pacientes SET "+",".join(f"{k}=?" for k in data)+", atualizado_em=CURRENT_TIMESTAMP WHERE id=?",(*data.values(),pid))
            c.execute("INSERT INTO audit_log(entity_type,entity_id,action,details_json) VALUES('paciente',?,'update',?)",(pid,json.dumps(list(data))))
    def get(self,pid):
        with self.db.connect() as c:return c.execute("SELECT * FROM pacientes WHERE id=?",(pid,)).fetchone()
    def list(self,query=""):
        with self.db.connect() as c:
            return c.execute("SELECT * FROM pacientes WHERE nome LIKE ? ORDER BY nome",(f"%{query}%",)).fetchall()
    def _event(self,c,pid,typ,title,entity_id,meta):
        c.execute("INSERT INTO timeline_events(paciente_id,event_type,event_date,title,entity_id,metadata_json) VALUES(?,?,?,?,?,?)",(pid,typ,date.today().isoformat(),title,entity_id,json.dumps(meta,ensure_ascii=False)))

class AssessmentRepository(BaseRepo):
    def create(self,pid,data_dict):
        data={**data_dict,"paciente_id":pid}; cols=','.join(data); qs=','.join('?'*len(data))
        with self.db.transaction() as c:
            cur=c.execute(f"INSERT INTO avaliacoes({cols}) VALUES({qs})",tuple(data.values())); aid=cur.lastrowid
            self._snapshot(c,aid,"criação")
            c.execute("INSERT INTO timeline_events(paciente_id,event_type,event_date,title,entity_id) VALUES(?,?,?,?,?)",(pid,"avaliacao",data.get("data") or date.today().isoformat(),"Avaliação nutricional",aid)); return aid
    def update_versioned(self,aid,changes,motivo="Correção clínica"):
        with self.db.transaction() as c:
            before=c.execute("SELECT * FROM avaliacoes WHERE id=?",(aid,)).fetchone()
            if not before: raise KeyError(aid)
            self._snapshot(c,aid,motivo,dict(before))
            allowed=set(before.keys())-{"id","paciente_id"}; data={k:v for k,v in changes.items() if k in allowed}
            if data:c.execute("UPDATE avaliacoes SET "+','.join(f"{k}=?" for k in data)+" WHERE id=?",(*data.values(),aid))
            c.execute("INSERT INTO audit_log(entity_type,entity_id,action,details_json) VALUES('avaliacao',?,'revision',?)",(aid,json.dumps({"motivo":motivo,"campos":list(data)},ensure_ascii=False)))
    def _snapshot(self,c,aid,motivo,snapshot=None):
        row=snapshot or dict(c.execute("SELECT * FROM avaliacoes WHERE id=?",(aid,)).fetchone())
        ver=c.execute("SELECT COALESCE(MAX(versao),0)+1 FROM avaliacao_revisoes WHERE avaliacao_id=?",(aid,)).fetchone()[0]
        c.execute("INSERT INTO avaliacao_revisoes(avaliacao_id,versao,snapshot_json,motivo) VALUES(?,?,?,?)",(aid,ver,json.dumps(row,ensure_ascii=False,default=str),motivo))
    def list(self,pid):
        with self.db.connect() as c:return c.execute("SELECT * FROM avaliacoes WHERE paciente_id=? ORDER BY data,id",(pid,)).fetchall()
    def revisions(self,aid):
        with self.db.connect() as c:return c.execute("SELECT * FROM avaliacao_revisoes WHERE avaliacao_id=? ORDER BY versao DESC",(aid,)).fetchall()

class FoodRepository(BaseRepo):
    def search(self,text,limit=50):
        with self.db.connect() as c:return c.execute("SELECT * FROM alimentos WHERE descricao LIKE ? ORDER BY descricao LIMIT ?",(f"%{text}%",limit)).fetchall()
    def get(self,fid):
        with self.db.connect() as c:return c.execute("SELECT * FROM alimentos WHERE id=?",(fid,)).fetchone()
    def import_csv(self,path,origin="Importado"):
        valid=invalid=0
        with open(path,encoding="utf-8-sig") as f:
            sample=f.read(4096);f.seek(0);dialect=csv.Sniffer().sniff(sample,delimiters=",;");reader=csv.DictReader(f,dialect=dialect)
            if not reader.fieldnames or "descricao" not in [x.strip().lower() for x in reader.fieldnames]:raise ValueError("CSV exige coluna descricao")
            with self.db.transaction() as c:
                for raw in reader:
                    row={str(k).strip().lower():(v or '').strip() for k,v in raw.items()}
                    desc=row.get('descricao','')
                    if not desc:invalid+=1;continue
                    def num(k):
                        try:return float(row.get(k,'').replace(',','.')) if row.get(k,'') else None
                        except ValueError:return None
                    c.execute("INSERT INTO alimentos(categoria,descricao,kcal,proteina,lipideos,carboidrato,fibra,origem) VALUES(?,?,?,?,?,?,?,?)",(row.get('categoria',''),desc,num('kcal'),num('proteina'),num('lipideos'),num('carboidrato'),num('fibra'),origin));valid+=1
        return {"valid":valid,"invalid":invalid}

class PlanRepository(BaseRepo):
    def create(self,pid,nome,vet_meta,obs="",parent_plan_id=None):
        with self.db.transaction() as c:
            ver=1
            if parent_plan_id:
                row=c.execute("SELECT COALESCE(MAX(version_no),0)+1 FROM planos WHERE id=? OR parent_plan_id=?",(parent_plan_id,parent_plan_id)).fetchone(); ver=row[0]
            cur=c.execute("INSERT INTO planos(paciente_id,nome,data,vet_meta,observacoes,parent_plan_id,version_no,status) VALUES(?,?,?,?,?,?,?,'Ativo')",(pid,nome,date.today().isoformat(),vet_meta,obs,parent_plan_id,ver)); plan=cur.lastrowid
            c.execute("INSERT INTO timeline_events(paciente_id,event_type,event_date,title,entity_id) VALUES(?,?,?,?,?)",(pid,"plano",date.today().isoformat(),f"Plano alimentar v{ver}",plan)); return plan
    def add_food(self,plan_id,meal,food_id,grams):
        with self.db.transaction() as c:c.execute("INSERT INTO plano_itens(plano_id,refeicao,alimento_id,quantidade_g) VALUES(?,?,?,?)",(plan_id,meal,food_id,grams)); self._snapshot(c,plan_id)
    def add_recipe(self,plan_id,meal,recipe_id,portions):
        with self.db.transaction() as c:c.execute("INSERT INTO plano_itens(plano_id,refeicao,receita_id,quantidade_porcoes,quantidade_g) VALUES(?,?,?,?,0)",(plan_id,meal,recipe_id,portions)); self._snapshot(c,plan_id)
    def set_target(self,plan_id,nutrient,target,unit="g",minv=None,maxv=None):
        with self.db.transaction() as c:c.execute("INSERT INTO plano_metas(plano_id,nutriente,meta,unidade,limite_min,limite_max) VALUES(?,?,?,?,?,?) ON CONFLICT(plano_id,nutriente) DO UPDATE SET meta=excluded.meta,unidade=excluded.unidade,limite_min=excluded.limite_min,limite_max=excluded.limite_max",(plan_id,nutrient,target,unit,minv,maxv))
    def set_meal_distribution(self,plan_id,meal,pct):
        with self.db.transaction() as c:c.execute("INSERT INTO refeicao_metas(plano_id,refeicao,percentual_vet) VALUES(?,?,?) ON CONFLICT(plano_id,refeicao) DO UPDATE SET percentual_vet=excluded.percentual_vet",(plan_id,meal,pct))
    def create_revision(self,plan_id,name=None):
        with self.db.transaction() as c:
            old=c.execute("SELECT * FROM planos WHERE id=?",(plan_id,)).fetchone()
            if not old:raise KeyError(plan_id)
            root=old['parent_plan_id'] or old['id'];ver=c.execute("SELECT COALESCE(MAX(version_no),0)+1 FROM planos WHERE id=? OR parent_plan_id=?",(root,root)).fetchone()[0]
            cur=c.execute("INSERT INTO planos(paciente_id,nome,data,vet_meta,observacoes,parent_plan_id,version_no,status) VALUES(?,?,?,?,?,?,?,'Ativo')",(old['paciente_id'],name or old['nome'],date.today().isoformat(),old['vet_meta'],old['observacoes'],root,ver));new=cur.lastrowid
            c.execute("UPDATE planos SET status='Histórico' WHERE id=?",(plan_id,))
            old_item_ids=[r['id'] for r in c.execute("SELECT id FROM plano_itens WHERE plano_id=? ORDER BY id",(plan_id,)).fetchall()]
            c.execute("INSERT INTO plano_itens(plano_id,refeicao,alimento_id,quantidade_g,receita_id,quantidade_porcoes) SELECT ?,refeicao,alimento_id,quantidade_g,receita_id,quantidade_porcoes FROM plano_itens WHERE plano_id=? ORDER BY id",(new,plan_id))
            new_item_ids=[r['id'] for r in c.execute("SELECT id FROM plano_itens WHERE plano_id=? ORDER BY id",(new,)).fetchall()]
            item_map=dict(zip(old_item_ids,new_item_ids))
            for sub in c.execute("SELECT * FROM plano_substituicoes WHERE plano_id=? ORDER BY id",(plan_id,)).fetchall():
                mapped=item_map.get(sub['plano_item_id'])
                if mapped:c.execute("INSERT INTO plano_substituicoes(plano_id,plano_item_id,alternative_food_id,quantidade_g,note) VALUES(?,?,?,?,?)",(new,mapped,sub['alternative_food_id'],sub['quantidade_g'],sub['note']))
            c.execute("INSERT INTO plano_metas(plano_id,nutriente,meta,unidade,limite_min,limite_max) SELECT ?,nutriente,meta,unidade,limite_min,limite_max FROM plano_metas WHERE plano_id=?",(new,plan_id))
            c.execute("INSERT INTO refeicao_metas(plano_id,refeicao,percentual_vet) SELECT ?,refeicao,percentual_vet FROM refeicao_metas WHERE plano_id=?",(new,plan_id))
            c.execute("INSERT INTO timeline_events(paciente_id,event_type,event_date,title,entity_id) VALUES(?,?,?,?,?)",(old['paciente_id'],'plano',date.today().isoformat(),f'Plano alimentar v{ver}',new));return new
    def list(self,pid):
        with self.db.connect() as c:return c.execute("SELECT * FROM planos WHERE paciente_id=? ORDER BY id DESC",(pid,)).fetchall()
    def items(self,plan_id):
        with self.db.connect() as c:
            return c.execute("""SELECT pi.*,a.descricao,a.kcal,a.proteina,a.lipideos,a.carboidrato,a.fibra,
                a.calcio,a.ferro,a.zinco,a.magnesio,a.vitamina_c,a.sodio,a.potassio,r.nome recipe_name
                FROM plano_itens pi LEFT JOIN alimentos a ON a.id=pi.alimento_id
                LEFT JOIN receitas r ON r.id=pi.receita_id WHERE pi.plano_id=? ORDER BY pi.id""",(plan_id,)).fetchall()
    def add_substitution(self,plan_id,plan_item_id,alternative_food_id,grams,note=""):
        with self.db.transaction() as c:
            item=c.execute("SELECT id FROM plano_itens WHERE id=? AND plano_id=?",(plan_item_id,plan_id)).fetchone()
            if not item:raise ValueError('Item do plano não encontrado.')
            return c.execute("INSERT INTO plano_substituicoes(plano_id,plano_item_id,alternative_food_id,quantidade_g,note) VALUES(?,?,?,?,?)",(plan_id,plan_item_id,alternative_food_id,grams,note)).lastrowid
    def substitutions(self,plan_id):
        with self.db.connect() as c:return c.execute("""SELECT ps.*,base.descricao base_name,alt.descricao alternative_name,pi.refeicao
            FROM plano_substituicoes ps JOIN plano_itens pi ON pi.id=ps.plano_item_id
            LEFT JOIN alimentos base ON base.id=pi.alimento_id LEFT JOIN alimentos alt ON alt.id=ps.alternative_food_id
            WHERE ps.plano_id=? ORDER BY pi.refeicao,ps.id""",(plan_id,)).fetchall()
    def _snapshot(self,c,plan_id):
        plan=dict(c.execute("SELECT * FROM planos WHERE id=?",(plan_id,)).fetchone()); items=[dict(r) for r in c.execute("SELECT * FROM plano_itens WHERE plano_id=?",(plan_id,))]; ver=c.execute("SELECT COALESCE(MAX(versao),0)+1 FROM plano_versoes WHERE plano_id=?",(plan_id,)).fetchone()[0]
        c.execute("INSERT INTO plano_versoes(plano_id,versao,snapshot_json) VALUES(?,?,?)",(plan_id,ver,json.dumps({"plan":plan,"items":items},ensure_ascii=False,default=str)))

class RecipeRepository(BaseRepo):
    def create(self,name,category="",servings=1,method="",tags=""):
        with self.db.transaction() as c:return c.execute("INSERT INTO receitas(nome,categoria,tags,porcoes,modo_preparo) VALUES(?,?,?,?,?)",(name,category,tags,servings,method)).lastrowid
    def add_ingredient(self,rid,food_id,grams):
        with self.db.transaction() as c:c.execute("INSERT INTO receita_ingredientes(receita_id,alimento_id,quantidade_g) VALUES(?,?,?)",(rid,food_id,grams))
    def ingredients(self,rid):
        with self.db.connect() as c:return c.execute("SELECT ri.*,a.* FROM receita_ingredientes ri JOIN alimentos a ON a.id=ri.alimento_id WHERE ri.receita_id=?",(rid,)).fetchall()
    def list(self):
        with self.db.connect() as c:return c.execute("SELECT * FROM receitas ORDER BY nome").fetchall()

class AnamnesisRepository(BaseRepo):
    def save_version(self,pid,data,typ="Consulta nutricional"):
        with self.db.transaction() as c:
            ver=c.execute("SELECT COALESCE(MAX(versao),0)+1 FROM anamneses_paciente WHERE paciente_id=?",(pid,)).fetchone()[0]
            content="\n".join(f"{k}: {v}" for k,v in data.items() if str(v).strip())
            cur=c.execute("INSERT INTO anamneses_paciente(paciente_id,nome_modelo,conteudo,data,tipo,dados_json,versao) VALUES(?,?,?,?,?,?,?)",(pid,typ,content,date.today().isoformat(),typ,json.dumps(data,ensure_ascii=False),ver));aid=cur.lastrowid
            c.execute("INSERT INTO timeline_events(paciente_id,event_type,event_date,title,entity_id) VALUES(?,?,?,?,?)",(pid,'anamnese',date.today().isoformat(),f'Anamnese v{ver}',aid));return aid
    def list(self,pid):
        with self.db.connect() as c:return c.execute("SELECT * FROM anamneses_paciente WHERE paciente_id=? ORDER BY versao DESC,id DESC",(pid,)).fetchall()
    def data(self,row):
        try:return json.loads(row['dados_json'] or '{}')
        except Exception:return {}

class PhotoRepository(BaseRepo):
    def add(self,pid,source,obs="",photo_date=None):
        source=Path(source);folder=PATIENT_PHOTOS_DIR/str(pid);folder.mkdir(parents=True,exist_ok=True);target=folder/(f"{date.today().strftime('%Y%m%d')}_{os.urandom(4).hex()}{source.suffix.lower() or '.jpg'}");shutil.copy2(source,target)
        with self.db.transaction() as c:
            cur=c.execute("INSERT INTO fotos_paciente(paciente_id,data,observacao,caminho) VALUES(?,?,?,?)",(pid,photo_date or date.today().isoformat(),obs,str(target)));fid=cur.lastrowid
            c.execute("INSERT INTO timeline_events(paciente_id,event_type,event_date,title,entity_id) VALUES(?,?,?,?,?)",(pid,'foto',photo_date or date.today().isoformat(),'Foto de evolução',fid));return fid
    def list(self,pid):
        with self.db.connect() as c:return c.execute("SELECT * FROM fotos_paciente WHERE paciente_id=? ORDER BY data,id",(pid,)).fetchall()

class TimelineRepository(BaseRepo):
    def list(self,pid):
        with self.db.connect() as c:
            explicit=[dict(r) for r in c.execute("SELECT * FROM timeline_events WHERE paciente_id=?",(pid,))]
            # Include legacy records not yet represented as explicit events.
            for r in c.execute("SELECT id,data,status FROM consultas WHERE paciente_id=?",(pid,)): explicit.append({"event_date":r['data'],"event_type":"consulta","title":f"Consulta - {r['status']}","entity_id":r['id'],"metadata_json":"{}"})
            return sorted(explicit,key=lambda x:(x.get('event_date') or '',x.get('entity_id') or 0),reverse=True)

class AgendaRepository(BaseRepo):
    def create(self,pid,data,hora,tipo="Consulta",observacoes="",duration=60,return_of=None,recurrence=None):
        from calendar import monthrange
        def next_date(d,freq,interval):
            if freq=='Semanal':return d+__import__('datetime').timedelta(days=7*interval)
            if freq=='Quinzenal':return d+__import__('datetime').timedelta(days=14*interval)
            if freq=='Mensal':
                month=d.month-1+interval;year=d.year+month//12;month=month%12+1;day=min(d.day,monthrange(year,month)[1]);return date(year,month,day)
            return None
        with self.db.transaction() as c:
            cur=c.execute("INSERT INTO consultas(paciente_id,data,hora,status,observacoes,tipo,retorno_de_id,duracao_min) VALUES(?,?,?,'Agendada',?,?,?,?)",(pid,data,hora,observacoes,tipo,return_of,duration)); cid=cur.lastrowid
            if recurrence:
                freq=recurrence.get('frequencia');interval=int(recurrence.get('intervalo',1));until=recurrence.get('ate_data');c.execute("INSERT INTO consulta_recorrencias(consulta_id,frequencia,intervalo,ate_data) VALUES(?,?,?,?)",(cid,freq,interval,until))
                if until and freq:
                    current=date.fromisoformat(data);end=date.fromisoformat(until);parent=cid
                    while True:
                        current=next_date(current,freq,interval)
                        if not current or current>end:break
                        c.execute("INSERT INTO consultas(paciente_id,data,hora,status,observacoes,tipo,retorno_de_id,duracao_min) VALUES(?,?,?,'Agendada',?,?,?,?)",(pid,current.isoformat(),hora,observacoes,tipo,parent,duration))
            return cid
    def list(self,start=None,end=None,status=None):
        q="SELECT c.*,p.nome paciente_nome FROM consultas c JOIN pacientes p ON p.id=c.paciente_id WHERE 1=1"; args=[]
        if start:q+=" AND c.data>=?";args.append(start)
        if end:q+=" AND c.data<=?";args.append(end)
        if status:q+=" AND c.status=?";args.append(status)
        q+=" ORDER BY c.data,c.hora"
        with self.db.connect() as c:return c.execute(q,args).fetchall()
    def set_status(self,cid,status):
        if status not in {"Agendada","Realizada","Faltou","Cancelada","Remarcada"}: raise ValueError(status)
        with self.db.transaction() as c:
            finished = __import__('datetime').datetime.now().isoformat(timespec='seconds') if status=='Realizada' else None
            c.execute("UPDATE consultas SET status=?,finalizada_em=COALESCE(?,finalizada_em) WHERE id=?",(status,finished,cid))
    def update_clinical_context(self,cid,objetivo=None,abordagem=None,observacoes=None):
        with self.db.transaction() as c:
            c.execute("UPDATE consultas SET objetivo=COALESCE(?,objetivo),abordagem=COALESCE(?,abordagem),observacoes=COALESCE(?,observacoes) WHERE id=?",(objetivo,abordagem,observacoes,cid))
    def mark_plan_sent(self,cid,when=None):
        stamp=when or __import__('datetime').datetime.now().isoformat(timespec='seconds')
        with self.db.transaction() as c:c.execute("UPDATE consultas SET plano_enviado_em=? WHERE id=?",(stamp,cid))
    def pending_plan_delivery(self):
        q="""SELECT c.*,p.nome paciente_nome FROM consultas c JOIN pacientes p ON p.id=c.paciente_id
             WHERE c.status='Realizada' AND c.plano_enviado_em IS NULL
             AND c.id=(SELECT c2.id FROM consultas c2 WHERE c2.paciente_id=c.paciente_id AND c2.status='Realizada' ORDER BY c2.data DESC,c2.hora DESC,c2.id DESC LIMIT 1)
             ORDER BY c.data DESC,c.hora DESC"""
        with self.db.connect() as c:return c.execute(q).fetchall()
    def objective_distribution(self):
        q="""SELECT c.objetivo,COUNT(*) n FROM consultas c
             WHERE c.status='Realizada' AND TRIM(COALESCE(c.objetivo,''))<>''
             AND c.id=(SELECT c2.id FROM consultas c2 WHERE c2.paciente_id=c.paciente_id AND c2.status='Realizada' ORDER BY c2.data DESC,c2.hora DESC,c2.id DESC LIMIT 1)
             GROUP BY c.objetivo ORDER BY n DESC,c.objetivo"""
        with self.db.connect() as c:return {r['objetivo']:r['n'] for r in c.execute(q)}
    def latest_pending_plan(self,pid):
        with self.db.connect() as c:
            return c.execute("SELECT * FROM consultas WHERE paciente_id=? AND status='Realizada' AND plano_enviado_em IS NULL ORDER BY data DESC,hora DESC,id DESC LIMIT 1",(pid,)).fetchone()
    def mark_latest_plan_sent(self,pid,when=None):
        row=self.latest_pending_plan(pid)
        if not row:return None
        self.mark_plan_sent(row['id'],when);return row['id']

class TemplateRepository(BaseRepo):
    def save(self,name,typ,content,template_id=None,style_key=None,specialty_tags=None,is_default=None,preview_json=None):
        style_key=style_key or 'clean_clinical'
        specialty_tags='' if specialty_tags is None else (specialty_tags if isinstance(specialty_tags,str) else ','.join(specialty_tags))
        preview_payload='{}' if preview_json is None else (preview_json if isinstance(preview_json,str) else json.dumps(preview_json,ensure_ascii=False))
        with self.db.transaction() as c:
            if template_id:
                current=c.execute("SELECT * FROM document_templates WHERE id=?",(template_id,)).fetchone()
                if not current:raise KeyError(template_id)
                final_style=style_key if style_key is not None else current['style_key']
                final_tags=specialty_tags if specialty_tags is not None else current['specialty_tags']
                final_preview=preview_payload if preview_json is not None else current['preview_json']
                final_default=int(bool(is_default)) if is_default is not None else int(current['is_default'] or 0)
                c.execute("UPDATE document_templates SET nome=?,tipo=?,conteudo=?,style_key=?,specialty_tags=?,is_default=?,preview_json=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",(name,typ,content,final_style,final_tags,final_default,final_preview,template_id))
                if final_default:self._clear_other_defaults(c,typ,template_id)
                return template_id
            cur=c.execute("INSERT INTO document_templates(nome,tipo,conteudo,style_key,specialty_tags,is_default,preview_json) VALUES(?,?,?,?,?,?,?)",(name,typ,content,style_key,specialty_tags,int(bool(is_default)),preview_payload));tid=cur.lastrowid
            if is_default:self._clear_other_defaults(c,typ,tid)
            return tid
    def _clear_other_defaults(self,c,typ,keep_id):
        c.execute("UPDATE document_templates SET is_default=0 WHERE tipo=? AND id<>?",(typ,keep_id))
    def set_default(self,template_id,typ=None):
        with self.db.transaction() as c:
            row=c.execute("SELECT tipo FROM document_templates WHERE id=?",(template_id,)).fetchone()
            if not row:raise KeyError(template_id)
            actual=typ or row['tipo'];c.execute("UPDATE document_templates SET is_default=0 WHERE tipo=?",(actual,));c.execute("UPDATE document_templates SET is_default=1,updated_at=CURRENT_TIMESTAMP WHERE id=?",(template_id,))
    def default(self,typ):
        with self.db.connect() as c:return c.execute("SELECT * FROM document_templates WHERE ativo=1 AND tipo=? AND is_default=1 ORDER BY id DESC LIMIT 1",(typ,)).fetchone()
    def list(self,typ=None):
        with self.db.connect() as c:return c.execute("SELECT * FROM document_templates WHERE ativo=1"+(" AND tipo=?" if typ else "")+" ORDER BY tipo,is_default DESC,nome",((typ,) if typ else ())).fetchall()

class ProtocolRepository(BaseRepo):
    def save(self,slug,version,title,source,target,content):
        with self.db.transaction() as c:
            existing=c.execute("SELECT * FROM clinical_protocols WHERE slug=? AND versao=?",(slug,version)).fetchone()
            if existing:
                same=(existing['titulo']==title and (existing['fonte'] or '')==(source or '') and (existing['publico_alvo'] or '')==(target or '') and existing['conteudo']==content)
                if same:return existing['id']
                raise ValueError('Esta versão do protocolo já existe. Informe uma nova versão para preservar o histórico.')
            return c.execute("INSERT INTO clinical_protocols(slug,versao,titulo,fonte,publico_alvo,conteudo,ativo) VALUES(?,?,?,?,?,?,1)",(slug,version,title,source,target,content)).lastrowid
    def list(self,slug=None):
        with self.db.connect() as c:return c.execute("SELECT * FROM clinical_protocols"+(" WHERE slug=?" if slug else "")+" ORDER BY slug,versao DESC",((slug,) if slug else ())).fetchall()

class LabRepository(BaseRepo):
    def create_panel(self,pid,name,collected_date,laboratory="",notes=""):
        with self.db.transaction() as c:
            cur=c.execute("INSERT INTO lab_panels(paciente_id,nome,data_coleta,laboratorio,observacoes) VALUES(?,?,?,?,?)",(pid,name,collected_date,laboratory,notes));panel_id=cur.lastrowid
            c.execute("INSERT INTO timeline_events(paciente_id,event_type,event_date,title,entity_id) VALUES(?,?,?,?,?)",(pid,'laboratorio',collected_date,f'Exames - {name}',panel_id));return panel_id
    def add_result(self,panel_id,marker,value=None,unit="",ref_min=None,ref_max=None,value_text="",flag=None,notes="",needs_review=False):
        numeric=None
        if value not in (None,''):
            try:numeric=float(value)
            except (TypeError,ValueError):value_text=str(value)
        if flag is None and numeric is not None:
            if ref_min is not None and numeric<float(ref_min):flag='baixo'
            elif ref_max is not None and numeric>float(ref_max):flag='alto'
            else:flag='normal'
        with self.db.transaction() as c:
            return c.execute("INSERT INTO lab_results(panel_id,marker_name,value_numeric,value_text,unit,ref_min,ref_max,flag,notes,needs_review) VALUES(?,?,?,?,?,?,?,?,?,?)",(panel_id,marker,numeric,value_text,unit,ref_min,ref_max,flag,notes,1 if needs_review else 0)).lastrowid
    def get_result(self,result_id):
        with self.db.connect() as c:return c.execute("SELECT lr.*,lp.paciente_id,lp.data_coleta,lp.nome panel_name FROM lab_results lr JOIN lab_panels lp ON lp.id=lr.panel_id WHERE lr.id=?",(result_id,)).fetchone()
    def list_panels(self,pid):
        with self.db.connect() as c:return c.execute("SELECT * FROM lab_panels WHERE paciente_id=? ORDER BY data_coleta DESC,id DESC",(pid,)).fetchall()
    def list_results(self,pid,marker=None):
        q="SELECT lr.*,lp.paciente_id,lp.data_coleta,lp.nome panel_name FROM lab_results lr JOIN lab_panels lp ON lp.id=lr.panel_id WHERE lp.paciente_id=?";args=[pid]
        if marker:q+=" AND lower(lr.marker_name)=lower(?)";args.append(marker)
        q+=" ORDER BY lp.data_coleta DESC,lr.id DESC"
        with self.db.connect() as c:return c.execute(q,args).fetchall()
    def mark_reviewed(self,result_id,when=None):
        stamp=when or datetime.now().isoformat(timespec='seconds')
        with self.db.transaction() as c:c.execute("UPDATE lab_results SET needs_review=0,reviewed_at=? WHERE id=?",(stamp,result_id))
    def pending_review(self):
        with self.db.connect() as c:return c.execute("SELECT lr.*,lp.paciente_id,lp.data_coleta,p.nome paciente_nome FROM lab_results lr JOIN lab_panels lp ON lp.id=lr.panel_id JOIN pacientes p ON p.id=lp.paciente_id WHERE lr.needs_review=1 AND lr.reviewed_at IS NULL ORDER BY lp.data_coleta DESC,lr.id DESC").fetchall()

class ClinicalPackRepository(BaseRepo):
    def activate(self,pid,slug):
        with self.db.transaction() as c:
            row=c.execute("SELECT id FROM patient_clinical_packs WHERE paciente_id=? AND pack_slug=?",(pid,slug)).fetchone()
            if row:c.execute("UPDATE patient_clinical_packs SET ativo=1,deactivated_at=NULL WHERE id=?",(row['id'],));return row['id']
            return c.execute("INSERT INTO patient_clinical_packs(paciente_id,pack_slug,ativo) VALUES(?,?,1)",(pid,slug)).lastrowid
    def deactivate(self,pid,slug):
        with self.db.transaction() as c:c.execute("UPDATE patient_clinical_packs SET ativo=0,deactivated_at=CURRENT_TIMESTAMP WHERE paciente_id=? AND pack_slug=?",(pid,slug))
    def active(self,pid):
        with self.db.connect() as c:return c.execute("SELECT * FROM patient_clinical_packs WHERE paciente_id=? AND ativo=1 ORDER BY pack_slug",(pid,)).fetchall()
    def save_record(self,pid,slug,data,record_date=None,notes=""):
        day=record_date or date.today().isoformat();payload=json.dumps(data,ensure_ascii=False,default=str)
        with self.db.transaction() as c:
            cur=c.execute("INSERT INTO clinical_pack_records(paciente_id,pack_slug,record_date,data_json,notes) VALUES(?,?,?,?,?)",(pid,slug,day,payload,notes));rid=cur.lastrowid
            c.execute("INSERT INTO timeline_events(paciente_id,event_type,event_date,title,entity_id,metadata_json) VALUES(?,?,?,?,?,?)",(pid,'pack_clinico',day,f'Acompanhamento - {slug}',rid,json.dumps({'pack_slug':slug},ensure_ascii=False)));return rid
    def records(self,pid,slug=None):
        q="SELECT * FROM clinical_pack_records WHERE paciente_id=?";args=[pid]
        if slug:q+=" AND pack_slug=?";args.append(slug)
        q+=" ORDER BY record_date DESC,id DESC"
        with self.db.connect() as c:return c.execute(q,args).fetchall()
    def latest_record(self,pid,slug):
        rows=self.records(pid,slug)
        if not rows:return None
        out=dict(rows[0]);
        try:out['data_json']=json.loads(out['data_json'] or '{}')
        except Exception:out['data_json']={}
        return out

class PendingActionRepository(BaseRepo):
    def create(self,pid,kind,title,detail="",severity="media",due_date=None):
        with self.db.transaction() as c:return c.execute("INSERT INTO manual_pending_actions(paciente_id,kind,title,detail,severity,due_date) VALUES(?,?,?,?,?,?)",(pid,kind,title,detail,severity,due_date)).lastrowid
    def resolve(self,action_id,when=None):
        stamp=when or datetime.now().isoformat(timespec='seconds')
        with self.db.transaction() as c:c.execute("UPDATE manual_pending_actions SET resolved_at=? WHERE id=?",(stamp,action_id))
    def open_actions(self,pid=None):
        q="SELECT a.*,p.nome paciente_nome FROM manual_pending_actions a JOIN pacientes p ON p.id=a.paciente_id WHERE a.resolved_at IS NULL";args=[]
        if pid is not None:q+=" AND a.paciente_id=?";args.append(pid)
        q+=" ORDER BY CASE a.severity WHEN 'alta' THEN 0 WHEN 'media' THEN 1 ELSE 2 END,a.due_date,a.id"
        with self.db.connect() as c:return [dict(r) for r in c.execute(q,args).fetchall()]

class ImportHistoryRepository(BaseRepo):
    def record(self,kind,source,total,imported,skipped,invalid,details=None):
        with self.db.transaction() as c:return c.execute("INSERT INTO import_history(import_kind,source_name,total_rows,imported_rows,skipped_rows,invalid_rows,details_json) VALUES(?,?,?,?,?,?,?)",(kind,source,total,imported,skipped,invalid,json.dumps(details or {},ensure_ascii=False,default=str))).lastrowid
    def list(self,limit=100):
        with self.db.connect() as c:return c.execute("SELECT * FROM import_history ORDER BY created_at DESC,id DESC LIMIT ?",(limit,)).fetchall()
