import hashlib,json,os,zipfile
from pathlib import Path
import pytest
from nutridesktop.version import SCHEMA_VERSION
from nutridesktop.data.database import Database
from nutridesktop.data.repositories import PatientRepository,AssessmentRepository,AnamnesisRepository,PlanRepository
from nutridesktop.services.auto_backup import AutoBackupService,BackupPolicy
from nutridesktop.services.patient_package import export_patient,import_patient
from nutridesktop.services.structured_export import export_json,export_csv_zip,export_xlsx
from nutridesktop.services.diagnostics import DiagnosticsService
from nutridesktop.services.update_service import UpdateService

def test_schema_p3_tables(tmp_path):
    db=Database(tmp_path/'p3.db');assert db.initialize()==SCHEMA_VERSION
    with db.connect() as c:
        assert c.execute("SELECT name FROM sqlite_master WHERE name='app_update_history'").fetchone()
        assert c.execute("SELECT name FROM sqlite_master WHERE name='backup_history'").fetchone()

def test_patient_nutri_roundtrip_with_password(tmp_path,monkeypatch):
    import nutridesktop.services.patient_package as pp
    db=Database(tmp_path/'src.db');db.initialize();pid=PatientRepository(db).create('Ana P3','F','1992-03-04','11999990000','ana@example.com')
    AssessmentRepository(db).create(pid,{'data':'2026-08-22','peso':60,'altura_cm':165,'idade':34,'imc':22.04})
    AnamnesisRepository(db).save_version(pid,{'Objetivo':'Saúde'})
    with db.transaction() as c:c.execute("INSERT INTO alimentos(descricao,kcal,proteina,origem) VALUES('Arroz teste',130,2.5,'Teste')")
    pl=PlanRepository(db);plan=pl.create(pid,'Plano P3',1900);pl.add_food(plan,'Almoço',1,100)
    files=tmp_path/'files';photos=tmp_path/'photos';files.mkdir();photos.mkdir();monkeypatch.setattr(pp,'PATIENT_FILES_DIR',files);monkeypatch.setattr(pp,'PATIENT_PHOTOS_DIR',photos)
    pkg=tmp_path/'ana.nutri';export_patient(pid,pkg,'senha-forte',db);assert pkg.read_bytes().startswith(pp.MAGIC)
    dst=Database(tmp_path/'dst.db');dst.initialize();newid=import_patient(pkg,'senha-forte',dst)
    assert PatientRepository(dst).get(newid)['nome']=='Ana P3';assert len(AssessmentRepository(dst).list(newid))==1;assert len(PlanRepository(dst).list(newid))==1

def test_structured_exports_are_well_formed(tmp_path):
    db=Database(tmp_path/'x.db');db.initialize();PatientRepository(db).create('A','M')
    j=export_json(tmp_path/'x.json',db);assert json.loads(j.read_text())['tables']['Pacientes'][0]['nome']=='A'
    z=export_csv_zip(tmp_path/'x.zip',db)
    with zipfile.ZipFile(z) as f:assert 'Pacientes.csv' in f.namelist()
    x=export_xlsx(tmp_path/'x.xlsx',db)
    with zipfile.ZipFile(x) as f:
        assert '[Content_Types].xml' in f.namelist();assert 'xl/workbook.xml' in f.namelist();assert any(n.startswith('xl/worksheets/sheet') for n in f.namelist())

def test_auto_backup_records_history_and_policy(tmp_path):
    db=Database(tmp_path/'x.db');db.initialize();PatientRepository(db).create('A','F');svc=AutoBackupService(db,tmp_path/'backups');svc.save_policy(BackupPolicy(True,'daily','startup',2,1,1));dest=svc.maybe_run('startup');assert dest and dest.exists()
    with db.connect() as c:r=c.execute("SELECT * FROM backup_history ORDER BY id DESC LIMIT 1").fetchone();assert r['trigger']=='auto:startup' and r['status']=='OK'

def test_github_release_update_and_checksum(tmp_path,monkeypatch):
    import nutridesktop.services.update_service as us
    version='99.0.0';installer_name=f'NutriDesktop-Setup-{version}.exe';payload=b'installer-v999';digest=hashlib.sha256(payload).hexdigest()
    release={'tag_name':f'v{version}','draft':False,'prerelease':False,'body':'Teste','published_at':'2026-09-07T00:00:00Z','html_url':'https://github.com/example/release','assets':[{'name':installer_name,'browser_download_url':'https://example/setup.exe'},{'name':'SHA256SUMS.txt','browser_download_url':'https://example/SHA256SUMS.txt'}]}
    monkeypatch.setattr(us,'_read_json',lambda url:release)
    def fake_read(url):
        if url.endswith('SHA256SUMS.txt'):return f'{digest}  {installer_name}\n'.encode()
        if url.endswith('setup.exe'):return payload
        raise AssertionError(url)
    monkeypatch.setattr(us,'_read_url',fake_read);monkeypatch.setattr(us,'UPDATE_DIR',tmp_path/'updates')
    db=Database(tmp_path/'u.db');db.initialize();svc=UpdateService(db);info=svc.check();assert info and info.version==version and info.sha256==digest
    staged,_=svc.stage(info);assert staged.read_bytes()==payload

def test_support_bundle_excludes_database_and_patient_files(tmp_path,monkeypatch):
    import nutridesktop.services.diagnostics as dg
    db=Database(tmp_path/'x.db');db.initialize();PatientRepository(db).create('Nome Sensível','F')
    monkeypatch.setattr(dg,'DATA_DIR',tmp_path);monkeypatch.setattr(dg,'DB_PATH',tmp_path/'x.db');monkeypatch.setattr(dg,'PATIENT_FILES_DIR',tmp_path/'docs');monkeypatch.setattr(dg,'PATIENT_PHOTOS_DIR',tmp_path/'photos');monkeypatch.setattr(dg,'LOG_DIR',tmp_path/'logs');monkeypatch.setattr(dg,'SUPPORT_DIR',tmp_path/'support')
    (tmp_path/'logs').mkdir();(tmp_path/'logs'/'nutridesktop.log').write_text('Paciente Nome Sensível email=ana@example.com telefone=11999999999')
    out=DiagnosticsService(db).create_support_bundle(tmp_path/'support.zip')
    with zipfile.ZipFile(out) as z:
        names=z.namelist();assert not any(n.endswith('.db') for n in names);assert not any('pacientes_arquivos' in n for n in names);log=z.read('logs/nutridesktop.log').decode();assert 'ana@example.com' not in log and '11999999999' not in log and 'Nome Sensível' not in log

def test_patient_nutri_carries_documents_and_photos(tmp_path,monkeypatch):
    import nutridesktop.services.patient_package as pp
    db=Database(tmp_path/'srcfiles.db');db.initialize();pid=PatientRepository(db).create('Com Arquivos','M')
    doc=tmp_path/'laudo.pdf';doc.write_bytes(b'%PDF-file-test');photo=tmp_path/'foto.jpg';photo.write_bytes(b'jpg-file-test')
    with db.transaction() as c:
        c.execute("INSERT INTO documentos_paciente(paciente_id,tipo,nome_arquivo,caminho,data,managed,sha256) VALUES(?,?,?,?,?,1,'x')",(pid,'Laudo','laudo.pdf',str(doc),'2026-08-22'))
        c.execute("INSERT INTO fotos_paciente(paciente_id,data,observacao,caminho) VALUES(?,?,?,?)",(pid,'2026-08-22','frente',str(photo)))
    pkg=tmp_path/'files.nutri';export_patient(pid,pkg,None,db)
    dst=Database(tmp_path/'dstfiles.db');dst.initialize();destdocs=tmp_path/'destdocs';destphotos=tmp_path/'destphotos';monkeypatch.setattr(pp,'PATIENT_FILES_DIR',destdocs);monkeypatch.setattr(pp,'PATIENT_PHOTOS_DIR',destphotos)
    newid=import_patient(pkg,None,dst)
    with dst.connect() as c:
        d=c.execute('SELECT * FROM documentos_paciente WHERE paciente_id=?',(newid,)).fetchone();p=c.execute('SELECT * FROM fotos_paciente WHERE paciente_id=?',(newid,)).fetchone()
    assert d and Path(d['caminho']).read_bytes()==doc.read_bytes();assert p and Path(p['caminho']).read_bytes()==photo.read_bytes()
