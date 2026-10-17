from __future__ import annotations
from dataclasses import dataclass,field
from pathlib import Path
import json,re,unicodedata
from datetime import date
import pandas as pd
from nutridesktop.data.repositories import ImportHistoryRepository

ALIASES={
    'nome':'nome','nome_completo':'nome','paciente':'nome','paciente_nome':'nome',
    'sexo':'sexo','genero':'sexo','genero_sexo':'sexo',
    'nascimento':'data_nascimento','data_nascimento':'data_nascimento','data_de_nascimento':'data_nascimento',
    'telefone':'telefone','celular':'telefone','whatsapp':'telefone',
    'email':'email','e_mail':'email','paciente_email':'email',
    'observacoes':'observacoes','observacao':'observacoes','notas':'observacoes',
    'paciente_id':'paciente_id','id_paciente':'paciente_id',
    'data':'data','data_avaliacao':'data','data_da_avaliacao':'data',
    'peso':'peso','peso_kg':'peso','altura':'altura_cm','altura_cm':'altura_cm','imc':'imc','gordura':'pg_final','gordura_corporal':'pg_final','cintura':'cintura',
    'data_coleta':'data_coleta','data_da_coleta':'data_coleta','coleta':'data_coleta',
    'painel':'painel','panel':'painel','grupo_exames':'painel','marcador':'marcador','exame':'marcador','analito':'marcador',
    'valor':'valor','resultado':'valor','unidade':'unidade','unit':'unidade','ref_min':'ref_min','referencia_min':'ref_min','minimo':'ref_min','ref_max':'ref_max','referencia_max':'ref_max','maximo':'ref_max','laboratorio':'laboratorio',
}

@dataclass
class ImportPreview:
    kind:str
    source_path:str
    source_name:str
    total_rows:int
    rows:list[dict]=field(default_factory=list)
    skipped:list[dict]=field(default_factory=list)
    errors:list[dict]=field(default_factory=list)


def _key(value):
    s=unicodedata.normalize('NFKD',str(value or '')).encode('ascii','ignore').decode().lower().strip()
    s=re.sub(r'[^a-z0-9]+','_',s).strip('_')
    return ALIASES.get(s,s)


def _text(value):
    if value is None:return ''
    s=str(value).strip()
    return '' if s.lower() in {'nan','none','nat'} else s


def _num(value):
    s=_text(value).replace(',','.')
    if not s:return None
    try:return float(s)
    except ValueError:return None


def _load(path):
    path=Path(path)
    if path.suffix.lower() in {'.xlsx','.xls'}:
        df=pd.read_excel(path,dtype=str).fillna('')
    else:
        df=pd.read_csv(path,dtype=str,sep=None,engine='python',keep_default_na=False).fillna('')
    rows=[]
    for raw in df.to_dict(orient='records'):
        row={_key(k):_text(v) for k,v in raw.items()}
        rows.append(row)
    return rows


def _sex(value):
    s=_text(value).lower()
    if s in {'f','feminino','female','mulher'}:return 'F'
    if s in {'m','masculino','male','homem'}:return 'M'
    return _text(value)[:1].upper() if _text(value) else ''


def _existing_patients(database):
    with database.connect() as c:rows=c.execute('SELECT * FROM pacientes').fetchall()
    return [dict(r) for r in rows]


def _resolve_patient(row,patients):
    """Avoid identifying a patient by an ambiguous name or inconsistent e-mail."""
    pid=_text(row.get('paciente_id'))
    name=_text(row.get('nome')).casefold()
    birth=_text(row.get('data_nascimento'))
    email=_text(row.get('email')).lower()
    if pid:
        matches=[p for p in patients if str(p['id'])==pid]
        if not matches:raise ValueError('ID de paciente não encontrado')
        result=matches[0]
    elif email:
        matches=[p for p in patients if _text(p.get('email')).lower()==email]
        if len(matches)>1:raise ValueError('E-mail duplicado em vários pacientes; concilie os cadastros')
        result=matches[0] if matches else None
    else:
        result=None
    if result:
        if name and _text(result.get('nome')).casefold()!=name:
            raise ValueError('Nome divergente do paciente identificado por ID/e-mail')
        if birth and _text(result.get('data_nascimento'))!=birth:
            raise ValueError('Nascimento divergente do paciente identificado por ID/e-mail')
        if email and _text(result.get('email')).lower() not in ('',email):
            raise ValueError('E-mail divergente do paciente identificado por nome/nascimento')
        return result
    if birth and name:
        matches=[p for p in patients if _text(p.get('nome')).casefold()==name and _text(p.get('data_nascimento'))==birth]
        if len(matches)>1:raise ValueError('Nome e nascimento ambíguos: concilie os cadastros')
        if matches:
            result=matches[0]
            if email and _text(result.get('email')).lower() not in ('',email):
                raise ValueError('Conflito de e-mail para paciente com mesmo nome e nascimento')
            return result
    return None

def preview_import(kind,path,database):
    kind={'pacientes':'patients','avaliacoes':'assessments','exames':'labs'}.get(kind,kind)
    raw_rows=_load(path);preview=ImportPreview(kind,str(path),Path(path).name,len(raw_rows));patients=_existing_patients(database);staged=list(patients)
    for idx,row in enumerate(raw_rows,start=2):
        try:
            if kind=='patients':
                name=_text(row.get('nome'));sex=_sex(row.get('sexo'));birth=_text(row.get('data_nascimento'))
                if not name:raise ValueError('Nome obrigatório')
                candidate={'nome':name,'sexo':sex or 'F','data_nascimento':birth,'telefone':_text(row.get('telefone')),'email':_text(row.get('email')).lower(),'observacoes':_text(row.get('observacoes')),'_row':idx}
                dup=_resolve_patient(candidate,staged)
                if dup:preview.skipped.append({**candidate,'reason':'Paciente duplicado','existing_id':dup['id']})
                else:
                    preview.rows.append(candidate)
                    staged.append({**candidate,'id':f"preview-{idx}"})
            elif kind=='assessments':
                patient=_resolve_patient(row,patients)
                if not patient:raise ValueError('Paciente não localizado por ID/e-mail/nome+nascimento')
                data=_text(row.get('data'))
                if not data:raise ValueError('Data da avaliação obrigatória')
                candidate={'paciente_id':patient['id'],'data':data,'peso':_num(row.get('peso')),'altura_cm':_num(row.get('altura_cm')),'imc':_num(row.get('imc')),'pg_final':_num(row.get('pg_final')),'cintura':_num(row.get('cintura')),'_row':idx}
                preview.rows.append(candidate)
            elif kind=='labs':
                patient=_resolve_patient(row,patients)
                if not patient:raise ValueError('Paciente não localizado por ID/e-mail/nome+nascimento')
                collected=_text(row.get('data_coleta'));marker=_text(row.get('marcador'))
                if not collected or not marker:raise ValueError('Data de coleta e marcador são obrigatórios')
                candidate={'paciente_id':patient['id'],'data_coleta':collected,'painel':_text(row.get('painel')) or 'Exames importados','laboratorio':_text(row.get('laboratorio')),'marcador':marker,'valor':_text(row.get('valor')),'unidade':_text(row.get('unidade')),'ref_min':_num(row.get('ref_min')),'ref_max':_num(row.get('ref_max')),'_row':idx}
                preview.rows.append(candidate)
            else:raise ValueError('Tipo de importação não suportado')
        except Exception as e:preview.errors.append({'row':idx,'reason':str(e),'data':row})
    return preview


def apply_import(preview,database):
    imported=0
    newly_skipped=0
    with database.transaction() as c:
        if preview.kind=='patients':
            patients=[dict(x) for x in c.execute("SELECT * FROM pacientes")]
            for r in preview.rows:
                existing=_resolve_patient(r,patients)
                if existing:
                    newly_skipped+=1
                    continue
                cur=c.execute("INSERT INTO pacientes(nome,sexo,data_nascimento,telefone,email,observacoes,atualizado_em) VALUES(?,?,?,?,?,?,CURRENT_TIMESTAMP)",(r['nome'],r['sexo'],r['data_nascimento'],r['telefone'],r['email'],r['observacoes']))
                pid=cur.lastrowid
                patients.append({**r,'id':pid})
                c.execute("INSERT INTO timeline_events(paciente_id,event_type,event_date,title,entity_id,metadata_json) VALUES(?,?,?,?,?,?)",(pid,'paciente',date.today().isoformat(),'Paciente importado',pid,json.dumps({'source':preview.source_name},ensure_ascii=False)))
                imported+=1
        elif preview.kind=='assessments':
            for r in preview.rows:
                data={k:v for k,v in r.items() if k in {'paciente_id','data','peso','altura_cm','imc','pg_final','cintura'} and v is not None}
                if not c.execute("SELECT 1 FROM pacientes WHERE id=?",(r['paciente_id'],)).fetchone():
                    raise ValueError(f"Paciente #{r['paciente_id']} não encontrado na aplicação da importação")
                # A repeat of the same measurement is not a new clinical event.
                criteria=" AND ".join(f"{key} IS ?" for key in data)
                if c.execute(f"SELECT id FROM avaliacoes WHERE {criteria} LIMIT 1",tuple(data.values())).fetchone():
                    newly_skipped+=1
                    continue
                cols=','.join(data);qs=','.join('?'*len(data))
                cur=c.execute(f"INSERT INTO avaliacoes({cols}) VALUES({qs})",tuple(data.values()));aid=cur.lastrowid
                c.execute("INSERT INTO avaliacao_revisoes(avaliacao_id,versao,snapshot_json,motivo) VALUES(?,1,?,'importação')",(aid,json.dumps({**data,'id':aid},ensure_ascii=False,default=str)))
                c.execute("INSERT INTO timeline_events(paciente_id,event_type,event_date,title,entity_id) VALUES(?,?,?,?,?)",(r['paciente_id'],'avaliacao',r['data'],'Avaliação importada',aid))
                imported+=1
        elif preview.kind=='labs':
            panel_cache={}
            for r in preview.rows:
                key=(r['paciente_id'],r['data_coleta'],r['painel'],r['laboratorio'])
                panel_id=panel_cache.get(key)
                if panel_id is None:
                    row=c.execute("SELECT id FROM lab_panels WHERE paciente_id=? AND data_coleta=? AND nome=? AND COALESCE(laboratorio,'')=? ORDER BY id DESC LIMIT 1",key).fetchone()
                    if row:
                        panel_id=row['id']
                    else:
                        panel_id=c.execute("INSERT INTO lab_panels(paciente_id,nome,data_coleta,laboratorio) VALUES(?,?,?,?)",key).lastrowid
                        c.execute("INSERT INTO timeline_events(paciente_id,event_type,event_date,title,entity_id) VALUES(?,?,?,?,?)",(r['paciente_id'],'laboratorio',r['data_coleta'],f"Exames - {r['painel']}",panel_id))
                    panel_cache[key]=panel_id
                numeric=_num(r['valor']);value_text='' if numeric is not None else r['valor']
                previous=c.execute("""SELECT id FROM lab_results
                    WHERE panel_id=? AND marker_name=? COLLATE NOCASE
                    AND value_numeric IS ? AND value_text IS ? AND unit IS ?
                    AND ref_min IS ? AND ref_max IS ? LIMIT 1""",
                    (panel_id,r['marcador'],numeric,value_text,r['unidade'],r['ref_min'],r['ref_max'])).fetchone()
                if previous:
                    newly_skipped+=1
                    continue
                flag=''
                if numeric is not None:
                    if r['ref_min'] is not None and numeric<r['ref_min']:flag='baixo'
                    elif r['ref_max'] is not None and numeric>r['ref_max']:flag='alto'
                    else:flag='normal'
                c.execute("INSERT INTO lab_results(panel_id,marker_name,value_numeric,value_text,unit,ref_min,ref_max,flag) VALUES(?,?,?,?,?,?,?,?)",(panel_id,r['marcador'],numeric,value_text,r['unidade'],r['ref_min'],r['ref_max'],flag))
                imported+=1
        else:raise ValueError('Tipo de importação não suportado')
    skipped=len(preview.skipped)+newly_skipped
    ImportHistoryRepository(database).record(preview.kind,preview.source_name,preview.total_rows,imported,skipped,len(preview.errors),{'errors':preview.errors[:100]})
    return {'total':preview.total_rows,'imported':imported,'skipped':skipped,'invalid':len(preview.errors)}
