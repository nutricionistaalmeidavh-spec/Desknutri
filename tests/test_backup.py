from pathlib import Path
import nutridesktop.services.backup as backup
from nutridesktop.data.database import Database
from nutridesktop.data.repositories import PatientRepository

def test_backup_contains_db_docs_photos_and_validates(tmp_path,monkeypatch):
    data=tmp_path/'data';data.mkdir();dbpath=data/'nutridesktop.db';docs=data/'pacientes_arquivos';photos=data/'fotos_pacientes';docs.mkdir();photos.mkdir();(docs/'a.txt').write_text('doc');(photos/'b.jpg').write_bytes(b'photo')
    db=Database(dbpath);db.initialize();PatientRepository(db).create('A','F')
    monkeypatch.setattr(backup,'DB_PATH',dbpath);monkeypatch.setattr(backup,'PATIENT_FILES_DIR',docs);monkeypatch.setattr(backup,'PATIENT_PHOTOS_DIR',photos)
    out=tmp_path/'backup.nbak';backup.create_backup(out,'senha',db);info=backup.validate_backup(out,'senha');paths={x['path'] for x in info['manifest']['files']};assert 'nutridesktop.db' in paths;assert any(x.startswith('pacientes_arquivos/') for x in paths);assert any(x.startswith('fotos_pacientes/') for x in paths)
