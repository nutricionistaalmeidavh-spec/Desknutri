from __future__ import annotations
import csv
from datetime import date, timedelta
from pathlib import Path
from nutridesktop.core.paths import resource_dir
from .database import Database,db

DEMO_PATIENT_SEED_KEY='demo.patient.seeded.v1'

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

def seed_demo_patient(database:Database=db):
    """Cria uma única demonstração clínica somente em uma instalação realmente vazia.

    O marcador em ``configuracoes`` garante que o paciente não volte a aparecer se
    o usuário removê-lo depois. Bases que já possuem pacientes apenas recebem o
    marcador e permanecem intocadas.
    """
    with database.transaction() as c:
        already=c.execute('SELECT valor FROM configuracoes WHERE chave=?',(DEMO_PATIENT_SEED_KEY,)).fetchone()
        if already:return None
        if c.execute('SELECT COUNT(*) FROM pacientes').fetchone()[0]>0:
            c.execute("INSERT INTO configuracoes(chave,valor) VALUES(?,?)",(DEMO_PATIENT_SEED_KEY,'1'))
            return None

        cur=c.execute(
            """INSERT INTO pacientes(nome,sexo,data_nascimento,telefone,email,observacoes,atualizado_em)
               VALUES(?,?,?,?,?,?,CURRENT_TIMESTAMP)""",
            ('Mariana Souza • Demonstração','F','1994-03-18','','',
             'Paciente fictícia para demonstração do NutriDesk. Dados sem vínculo com pessoa real.'),
        )
        pid=cur.lastrowid
        today=date.today()
        c.execute(
            "INSERT INTO timeline_events(paciente_id,event_type,event_date,title,entity_id,metadata_json) VALUES(?,?,?,?,?,?)",
            (pid,'paciente',(today-timedelta(days=120)).isoformat(),'Cadastro do paciente demonstrativo',pid,'{}'),
        )

        height=168.0
        samples=[
            (today-timedelta(days=120),82.4,31.5,92.0,56.4),
            (today-timedelta(days=65),79.8,29.2,88.0,56.5),
            (today-timedelta(days=14),77.1,27.6,84.0,55.8),
        ]
        for when,weight,body_fat,waist,lean_mass in samples:
            bmi=round(weight/((height/100)**2),1)
            fat_mass=round(weight*(body_fat/100),1)
            aid=c.execute(
                """INSERT INTO avaliacoes(
                    paciente_id,data,peso,altura_cm,idade,imc,cintura,bia_pg,pg_final,origem_pg,
                    massa_gorda,massa_magra,atividade,fator_atividade,vet,ptn_gkg,ptn_g,lip_pct,lip_g,cho_g,observacoes
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (pid,when.isoformat(),weight,height,32,bmi,waist,body_fat,body_fat,'Demonstração',
                 fat_mass,lean_mass,'Moderadamente ativo',1.55,1800,1.4,round(weight*1.4,1),30,
                 60.0,round((1800-(weight*1.4*4)-540)/4,1),'Avaliação fictícia para demonstração.'),
            ).lastrowid
            c.execute(
                "INSERT INTO timeline_events(paciente_id,event_type,event_date,title,entity_id,metadata_json) VALUES(?,?,?,?,?,?)",
                (pid,'avaliacao',when.isoformat(),'Avaliação nutricional demonstrativa',aid,'{}'),
            )

        plan_id=c.execute(
            """INSERT INTO planos(paciente_id,nome,data,vet_meta,observacoes,version_no,status)
               VALUES(?,?,?,?,?,1,'Ativo')""",
            (pid,'Plano exemplo',today.isoformat(),1800,'Plano fictício para demonstração.'),
        ).lastrowid
        c.execute(
            "INSERT INTO timeline_events(paciente_id,event_type,event_date,title,entity_id,metadata_json) VALUES(?,?,?,?,?,?)",
            (pid,'plano',today.isoformat(),'Plano alimentar demonstrativo',plan_id,'{}'),
        )
        c.execute("INSERT INTO configuracoes(chave,valor) VALUES(?,?)",(DEMO_PATIENT_SEED_KEY,'1'))
        return pid
