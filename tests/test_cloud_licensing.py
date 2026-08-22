from __future__ import annotations
import base64,json
from datetime import datetime,timedelta,timezone
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from nutridesktop.services import licensing
from nutridesktop.services.account_licensing import AccountLicenseService
from nutridesktop.data.database import Database


def b64(data:bytes)->str:
    return base64.urlsafe_b64encode(data).decode().rstrip('=')


def test_server_managed_license_verifies_and_binds_machine(tmp_path,monkeypatch):
    private=Ed25519PrivateKey.generate();public=private.public_key();raw=public.public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
    key_path=tmp_path/'server_jwk.json';key_path.write_text(json.dumps({'kty':'OKP','crv':'Ed25519','x':b64(raw)}))
    monkeypatch.setattr(licensing,'SERVER_PUBLIC_KEY_LOCATIONS',[key_path])
    body={'iss':'NutriDesk Licensing','v':1,'license_id':'abc','email':'cliente@example.com','plan':'Vitalicio','status':'active','device_id':licensing.machine_id(),'issued_at':datetime.now(timezone.utc).isoformat(),'offline_until':(datetime.now(timezone.utc)+timedelta(days=30)).isoformat(),'expires_at':None}
    payload=b64(json.dumps(body,separators=(',',':')).encode());sig=b64(private.sign(payload.encode('ascii')));token=payload+'.'+sig
    data=licensing.validate(token)
    assert data['server_managed'] is True
    assert data['email']=='cliente@example.com'
    assert data['plan']=='Vitalicio'


def test_cloud_server_derives_account_endpoint(tmp_path):
    database=Database(tmp_path/'db.sqlite');database.initialize();svc=AccountLicenseService(database)
    svc.set_server_url('https://example.supabase.co/functions/v1/nutridesk-licensing')
    assert svc.configured()
    assert svc._account_url()=='https://example.supabase.co/functions/v1/nutridesk-account'
