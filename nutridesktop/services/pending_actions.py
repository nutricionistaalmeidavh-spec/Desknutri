from __future__ import annotations
from datetime import date, datetime, timedelta
from nutridesktop.data.repositories import AgendaRepository,AssessmentRepository,LabRepository,ClinicalPackRepository,PendingActionRepository,PatientRepository


def _action(kind,pid,name,title,detail,severity='media',entity_id=None):
    return {'kind':kind,'patient_id':pid,'patient_name':name,'title':title,'detail':detail,'severity':severity,'entity_id':entity_id}


def collect_pending_actions(database=None,today=None,stale_days=90):
    today=today or date.today(); pr=PatientRepository(database) if database else PatientRepository(); db=pr.db
    ag=AgendaRepository(db); actions=[]; seen=set()
    def add(a):
        key=(a['kind'],a['patient_id'],a.get('entity_id'))
        if key not in seen:seen.add(key);actions.append(a)

    for row in ag.pending_plan_delivery():
        add(_action('plan_not_sent',row['paciente_id'],row['paciente_nome'],'Plano alimentar não enviado',f"Consulta de {row['data']} ainda sem envio registrado.",'alta',row['id']))

    with db.connect() as c:
        latest_completed=c.execute("""SELECT c.*,p.nome paciente_nome FROM consultas c JOIN pacientes p ON p.id=c.paciente_id
            WHERE c.status='Realizada' AND c.id=(SELECT c2.id FROM consultas c2 WHERE c2.paciente_id=c.paciente_id AND c2.status='Realizada' ORDER BY c2.data DESC,c2.hora DESC,c2.id DESC LIMIT 1)""").fetchall()
        for row in latest_completed:
            future=c.execute("SELECT id FROM consultas WHERE paciente_id=? AND data>? AND status NOT IN ('Cancelada','Faltou') LIMIT 1",(row['paciente_id'],today.isoformat())).fetchone()
            if not future:add(_action('return_not_scheduled',row['paciente_id'],row['paciente_nome'],'Retorno sem agendamento',f"Última consulta realizada em {row['data']}.",'media',row['id']))

    cutoff=today-timedelta(days=stale_days)
    for p in pr.list():
        assessments=AssessmentRepository(db).list(p['id'])
        latest=assessments[-1] if assessments else None
        if latest is None or date.fromisoformat(latest['data'])<cutoff:
            detail='Paciente sem avaliação registrada.' if latest is None else f"Última avaliação em {latest['data']}."
            add(_action('stale_assessment',p['id'],p['nome'],'Avaliação desatualizada',detail,'media',latest['id'] if latest else None))

    for r in LabRepository(db).pending_review():
        add(_action('lab_review',r['paciente_id'],r['paciente_nome'],'Exame aguardando revisão',f"{r['marker_name']} • coleta {r['data_coleta']}",'alta',r['id']))

    packs=ClinicalPackRepository(db)
    for p in pr.list():
        for active in packs.active(p['id']):
            if packs.latest_record(p['id'],active['pack_slug']) is None:
                add(_action('pack_checkpoint',p['id'],p['nome'],'Pack clínico sem acompanhamento',f"{active['pack_slug'].replace('_',' ').title()} está ativo e ainda não possui registro.",'baixa',active['id']))

    for r in PendingActionRepository(db).open_actions():
        add(_action('manual',r['paciente_id'],r['paciente_nome'],r['title'],r['detail'] or '',r['severity'] or 'media',r['id']))

    severity_order={'alta':0,'media':1,'baixa':2}
    actions.sort(key=lambda x:(severity_order.get(x['severity'],1),x['patient_name'],x['title']))
    return actions
