from pathlib import Path
import pytest
from nutridesktop.data.database import Database
from nutridesktop.data.repositories import PatientRepository,FoodRepository,PlanRepository,RecipeRepository,TemplateRepository
from nutridesktop.core.security import hash_pin,verify_pin
from nutridesktop.services.templates import render_template
from nutridesktop.services.plans import recipe_nutrients,plan_nutrients,substitute

def test_pin_hash_and_verify():
    h=hash_pin('1234');assert '1234' not in h;assert verify_pin('1234',h);assert not verify_pin('9999',h)
def test_template_render(): assert render_template('Olá {{ paciente.nome }}',{'paciente':{'nome':'Ana'}})=='Olá Ana'
def test_recipe_as_composite_and_plan(tmp_path):
    db=Database(tmp_path/'x.db');db.initialize();p=PatientRepository(db);pid=p.create('A','F')
    with db.transaction() as c:
        c.execute("INSERT INTO alimentos(descricao,kcal,proteina,carboidrato,lipideos) VALUES('Food',100,10,15,2)")
    rr=RecipeRepository(db);rid=rr.create('Receita',servings=2);rr.add_ingredient(rid,1,200);n=recipe_nutrients(rid,rr);assert n['kcal']==pytest.approx(100);assert n['proteina']==pytest.approx(10)
    pl=PlanRepository(db);plan=pl.create(pid,'Plano',1800);pl.add_recipe(plan,'Lanche',rid,1);total,_=plan_nutrients(plan,pl);assert total['kcal']==pytest.approx(100)
def test_substitution_matches_energy(tmp_path):
    db=Database(tmp_path/'x.db');db.initialize();
    with db.transaction() as c:
        c.execute("INSERT INTO alimentos(descricao,kcal,proteina) VALUES('A',100,10)");c.execute("INSERT INTO alimentos(descricao,kcal,proteina) VALUES('B',200,20)")
    opts=substitute(1,100,'',FoodRepository(db));b=next(o for o in opts if o['food_id']==2);assert b['grams']==50

def test_legacy_document_migration(tmp_path,monkeypatch):
    import nutridesktop.services.documents as documents
    from nutridesktop.services.documents import DocumentService
    db=Database(tmp_path/'x.db');db.initialize();pid=PatientRepository(db).create('A','F');legacy=tmp_path/'legacy.pdf';legacy.write_bytes(b'pdf')
    managed=tmp_path/'managed';managed.mkdir();monkeypatch.setattr(documents,'PATIENT_FILES_DIR',managed)
    with db.transaction() as c:c.execute("INSERT INTO documentos_paciente(paciente_id,tipo,nome_arquivo,caminho,data,managed) VALUES(?,?,?,?,?,0)",(pid,'PDF','legacy.pdf',str(legacy),'2026-01-01'))
    res=DocumentService(db).migrate_legacy_documents();assert res['migrated']==1
    with db.connect() as c:r=c.execute('SELECT * FROM documentos_paciente').fetchone();assert r['managed']==1;assert Path(r['caminho']).exists();assert r['sha256']

def test_ed25519_license_validation(tmp_path,monkeypatch):
    import base64,json
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    import nutridesktop.services.licensing as licensing
    private=Ed25519PrivateKey.generate();pub=tmp_path/'pub.pem';pub.write_bytes(private.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo));monkeypatch.setattr(licensing,'PUBLIC_KEY_LOCATIONS',[pub])
    payload=json.dumps({'product':'NutriDesktop','serial':'TEST-1','machine_id':'*','issued':'2026-01-01','expires':None},separators=(',',':'),sort_keys=True).encode();enc=lambda b:base64.urlsafe_b64encode(b).decode().rstrip('=');license_text=enc(payload)+'.'+enc(private.sign(payload));data=licensing.validate(license_text);assert data['serial']=='TEST-1'

def test_complete_report_is_generated(tmp_path):
    from nutridesktop.services.reports import generate_complete_report
    db=Database(tmp_path/'report.db');db.initialize();pid=PatientRepository(db).create('Paciente Teste','F','1990-01-01');path=tmp_path/'r.pdf';generate_complete_report(pid,path,sections={'patient'},database=db);assert path.exists() and path.stat().st_size>100

def test_plan_targets_and_meal_distribution_alerts(tmp_path):
    from nutridesktop.services.plans import target_status,meal_distribution_status
    db=Database(tmp_path/'targets.db');db.initialize();pid=PatientRepository(db).create('A','F')
    with db.transaction() as c:c.execute("INSERT INTO alimentos(descricao,kcal,proteina,carboidrato,lipideos) VALUES('Food',100,10,10,2)")
    pl=PlanRepository(db);plan=pl.create(pid,'Plano',1000);pl.add_food(plan,'Almoço',1,300);pl.set_target(plan,'proteina',100,'g',90,110);pl.set_meal_distribution(plan,'Almoço',50)
    status=target_status(plan,pl);assert status[0]['status']=='baixo'
    dist=meal_distribution_status(plan,pl);assert dist[0]['expected_kcal']==pytest.approx(500);assert dist[0]['actual_kcal']==pytest.approx(300);assert dist[0]['status']=='baixo'

def test_protocol_versions_are_immutable(tmp_path):
    from nutridesktop.data.repositories import ProtocolRepository
    db=Database(tmp_path/'protocol.db');db.initialize();repo=ProtocolRepository(db)
    first=repo.save('teste','1.0','Título','Fonte','Adultos','Conteúdo A')
    assert repo.save('teste','1.0','Título','Fonte','Adultos','Conteúdo A')==first
    with pytest.raises(ValueError):repo.save('teste','1.0','Título','Fonte','Adultos','Conteúdo alterado')
    repo.save('teste','1.1','Título','Fonte','Adultos','Conteúdo alterado');assert len(repo.list('teste'))==2

def test_complete_report_with_anamnesis_evolution_and_identity(tmp_path):
    from nutridesktop.services.reports import generate_complete_report
    from nutridesktop.data.repositories import AssessmentRepository,AnamnesisRepository
    db=Database(tmp_path/'report_full.db');db.initialize();pid=PatientRepository(db).create('José Ávila','M','1990-01-01')
    with db.transaction() as c:c.execute("INSERT INTO configuracoes(chave,valor) VALUES('profissional_nome','Nutricionista Débora')")
    AnamnesisRepository(db).save_version(pid,{'Objetivo':'Reeducação alimentar','Observações e conduta':'Acompanhar evolução'})
    AssessmentRepository(db).create(pid,{'data':'2026-08-22','peso':80,'altura_cm':180,'idade':36,'imc':24.69,'pg_final':20,'massa_magra':64,'vet':2200})
    path=tmp_path/'full.pdf';generate_complete_report(pid,path,database=db);assert path.exists() and path.stat().st_size>500

def test_local_protection_fails_closed_off_windows(tmp_path):
    import os
    from nutridesktop.services.local_protection import LocalProtectionService
    svc=LocalProtectionService(tmp_path/'data')
    if os.name!='nt':
        with pytest.raises(RuntimeError):svc.enable()
