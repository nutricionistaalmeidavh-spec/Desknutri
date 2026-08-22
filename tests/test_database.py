import json,sqlite3
from pathlib import Path
from nutridesktop.data.database import Database
from nutridesktop.data.repositories import PatientRepository,AssessmentRepository,PlanRepository,AgendaRepository,AnamnesisRepository
from nutridesktop.version import SCHEMA_VERSION

def test_migrations_are_idempotent(tmp_path):
    db=Database(tmp_path/'test.db');assert db.initialize()==SCHEMA_VERSION;assert db.initialize()==SCHEMA_VERSION
    with db.connect() as c:assert c.execute('SELECT version FROM schema_meta').fetchone()[0]==SCHEMA_VERSION;assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
def test_patient_update_and_timeline(tmp_path):
    db=Database(tmp_path/'test.db');db.initialize();p=PatientRepository(db);pid=p.create('Ana','F','2000-01-01');p.update(pid,telefone='1199');assert p.get(pid)['telefone']=='1199'
def test_assessment_revision_preserves_snapshot(tmp_path):
    db=Database(tmp_path/'test.db');db.initialize();p=PatientRepository(db);pid=p.create('A','F');a=AssessmentRepository(db);aid=a.create(pid,{'data':'2026-01-01','peso':60,'altura_cm':165,'idade':30,'imc':22});a.update_versioned(aid,{'peso':61},'correção');revs=a.revisions(aid);assert len(revs)>=2;assert json.loads(revs[-1]['snapshot_json'])['peso'] in (60,61)
def test_plan_revision_clones_items_and_targets(tmp_path):
    db=Database(tmp_path/'test.db');db.initialize();p=PatientRepository(db);pid=p.create('A','M');
    with db.transaction() as c:c.execute("INSERT INTO alimentos(descricao,kcal,proteina) VALUES('Arroz',130,2.5)")
    pr=PlanRepository(db);plan=pr.create(pid,'Plano',2000);pr.add_food(plan,'Almoço',1,100);pr.set_target(plan,'proteina',120,'g');new=pr.create_revision(plan);assert len(pr.items(new))==1
    with db.connect() as c:assert c.execute('SELECT COUNT(*) FROM plano_metas WHERE plano_id=?',(new,)).fetchone()[0]==1
def test_anamnesis_versions(tmp_path):
    db=Database(tmp_path/'test.db');db.initialize();p=PatientRepository(db);pid=p.create('A','F');r=AnamnesisRepository(db);r.save_version(pid,{'Queixa':'x'});r.save_version(pid,{'Queixa':'y'});rows=r.list(pid);assert [rows[0]['versao'],rows[1]['versao']]==[2,1]
def test_agenda_recurrence_materializes_future_events(tmp_path):
    db=Database(tmp_path/'test.db');db.initialize();p=PatientRepository(db);pid=p.create('A','F');a=AgendaRepository(db);a.create(pid,'2026-01-01','09:00',recurrence={'frequencia':'Semanal','intervalo':1,'ate_data':'2026-01-22'});assert len(a.list('2026-01-01','2026-01-31'))==4
