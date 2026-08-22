from datetime import date, timedelta
from nutridesktop.data.database import Database
from nutridesktop.data.repositories import (
    PatientRepository, AssessmentRepository, AgendaRepository, PlanRepository,
    LabRepository, ClinicalPackRepository, PendingActionRepository, ImportHistoryRepository,
)
from nutridesktop.version import SCHEMA_VERSION


def make_db(tmp_path):
    database=Database(tmp_path/'v6.db')
    assert database.initialize()==SCHEMA_VERSION
    return database


def test_schema_13_core_repositories(tmp_path):
    database=make_db(tmp_path)
    p=PatientRepository(database); pid=p.create('Maria','F','1990-05-01',telefone='(16) 99999-1111')
    labs=LabRepository(database)
    panel_id=labs.create_panel(pid,'Metabólico','2026-08-20','Laboratório X')
    result_id=labs.add_result(panel_id,'Glicemia',101,'mg/dL',70,99,notes='Jejum')
    result=labs.get_result(result_id)
    assert result['marker_name']=='Glicemia' and result['value_numeric']==101
    assert labs.list_results(pid,'Glicemia')[0]['panel_id']==panel_id

    packs=ClinicalPackRepository(database)
    packs.activate(pid,'materno_infantil')
    packs.activate(pid,'gastrointestinal')
    assert {r['pack_slug'] for r in packs.active(pid)}=={'materno_infantil','gastrointestinal'}
    rec_id=packs.save_record(pid,'gastrointestinal',{'bristol':4,'sintomas':['distensão']},'2026-08-21')
    rec=packs.latest_record(pid,'gastrointestinal')
    assert rec['id']==rec_id and rec['data_json']['bristol']==4

    pending=PendingActionRepository(database)
    action_id=pending.create(pid,'manual','Revisar exames','Comparar com consulta anterior','alta')
    assert pending.open_actions(pid)[0]['id']==action_id
    pending.resolve(action_id)
    assert pending.open_actions(pid)==[]

    history=ImportHistoryRepository(database)
    hid=history.record('patients','clientes.csv',10,8,1,1,{'ok':True})
    assert history.list()[0]['id']==hid


def test_lab_flags_series_and_longitudinal_comparison(tmp_path):
    from nutridesktop.services.labs import flag_result, marker_series
    from nutridesktop.services.longitudinal import build_patient_comparison
    database=make_db(tmp_path);p=PatientRepository(database);pid=p.create('João','M','1985-01-01')
    assert flag_result(68,70,99)=='baixo'
    assert flag_result(92,70,99)=='normal'
    assert flag_result(120,70,99)=='alto'
    labs=LabRepository(database)
    pa=labs.create_panel(pid,'Metabólico','2026-01-01');labs.add_result(pa,'Glicemia',90,'mg/dL',70,99)
    pb=labs.create_panel(pid,'Metabólico','2026-06-01');labs.add_result(pb,'Glicemia',103,'mg/dL',70,99)
    series=marker_series(pid,'Glicemia',labs)
    assert [x['value'] for x in series]==[90.0,103.0]
    ar=AssessmentRepository(database);ar.create(pid,{'data':'2026-01-10','peso':80,'altura_cm':175,'idade':41,'imc':26.1})
    ag=AgendaRepository(database);cid=ag.create(pid,'2026-06-02','10:00');ag.update_clinical_context(cid,'Saúde geral','Equilibrada');ag.set_status(cid,'Realizada')
    plan=PlanRepository(database).create(pid,'Plano 1',2100)
    payload=build_patient_comparison(pid,database)
    assert payload['patient']['id']==pid
    assert payload['assessments'][0]['peso']==80
    assert payload['labs']['Glicemia'][-1]['value']==103.0
    assert payload['consultations'][-1]['objetivo']=='Saúde geral'
    assert payload['plans'][0]['id']==plan


def test_smart_pending_actions_cover_clinical_and_operational_gaps(tmp_path):
    from nutridesktop.services.pending_actions import collect_pending_actions
    database=make_db(tmp_path);p=PatientRepository(database);pid=p.create('Paciente','F','1990-01-01')
    ag=AgendaRepository(database);cid=ag.create(pid,'2026-01-01','09:00');ag.set_status(cid,'Realizada')
    AssessmentRepository(database).create(pid,{'data':'2025-01-01','peso':70,'altura_cm':165,'idade':35,'imc':25.7})
    labs=LabRepository(database);panel=labs.create_panel(pid,'Renal','2026-01-02');labs.add_result(panel,'Creatinina',1.3,'mg/dL',0.5,1.1,needs_review=True)
    ClinicalPackRepository(database).activate(pid,'renal')
    PendingActionRepository(database).create(pid,'manual','Solicitar recordatório','Enviar antes do retorno','media')
    actions=collect_pending_actions(database,today=date(2026,8,22))
    kinds={a['kind'] for a in actions}
    assert {'plan_not_sent','return_not_scheduled','stale_assessment','lab_review','pack_checkpoint','manual'} <= kinds
    assert len([a for a in actions if a['kind']=='plan_not_sent'])==1


def test_whatsapp_output_builds_safe_prefilled_links():
    from nutridesktop.services.whatsapp import normalize_br_phone,build_whatsapp_url,message_for
    assert normalize_br_phone('(16) 99999-1111')=='5516999991111'
    assert normalize_br_phone('+55 16 99999-1111')=='5516999991111'
    msg=message_for('plan','Maria',{'date':'22/08/2026'})
    assert 'Maria' in msg and 'plano alimentar' in msg.lower()
    url=build_whatsapp_url('(16) 99999-1111',msg)
    assert url.startswith('https://wa.me/5516999991111?text=')
    assert '%20' in url or '+' in url
    for kind in ['return','exam','followup']:
        assert message_for(kind,'Maria')
