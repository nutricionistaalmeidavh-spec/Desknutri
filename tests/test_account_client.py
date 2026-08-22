from __future__ import annotations
import pytest
from nutridesktop.core.secret_store import protect_text,unprotect_text
from nutridesktop.data.database import Database
from nutridesktop.services.account_licensing import AccountLicenseService,AccountLicenseError

def test_local_secret_roundtrip(tmp_path,monkeypatch):
    # A função usa a pasta de configuração do processo; apenas prova roundtrip criptográfico.
    value=protect_text('token-super-secreto');assert unprotect_text(value)=='token-super-secreto';assert 'token-super-secreto' not in value

def test_server_requires_https_for_remote(tmp_path):
    db=Database(tmp_path/'db.sqlite');db.initialize();svc=AccountLicenseService(db)
    with pytest.raises(AccountLicenseError) as exc:svc.set_server_url('http://licencas.exemplo.com')
    assert exc.value.code=='https_required'

def test_localhost_http_allowed(tmp_path):
    db=Database(tmp_path/'db.sqlite');db.initialize();svc=AccountLicenseService(db);svc.set_server_url('http://127.0.0.1:8000');assert svc.server_url()=='http://127.0.0.1:8000'
