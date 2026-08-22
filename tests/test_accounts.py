from __future__ import annotations
from pathlib import Path
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from license_server.core import AdminService,LicenseError,LicenseService,LicenseSigner,LicenseStore,hash_password,verify_password

@pytest.fixture
def server(tmp_path):
    store=LicenseStore(tmp_path/'licenses.db');store.initialize();priv=tmp_path/'private.pem';pub=tmp_path/'public.pem';LicenseSigner.generate(priv,pub)
    return store,AdminService(store),LicenseService(store,LicenseSigner(priv)),pub

def decode_with_public(token,pub):
    import base64,json
    p64,s64=token.split('.',1);raw=base64.urlsafe_b64decode(p64+'='*(-len(p64)%4));sig=base64.urlsafe_b64decode(s64+'='*(-len(s64)%4));key=serialization.load_pem_public_key(Path(pub).read_bytes());key.verify(sig,raw);return json.loads(raw)

def test_password_hash_roundtrip():
    encoded=hash_password('senha-segura-123');assert verify_password('senha-segura-123',encoded);assert not verify_password('outra',encoded)

def test_first_claim_then_password_required(server):
    store,admin,svc,pub=server;aid=admin.authorize_email('cliente@example.com','Cliente')
    first=svc.activate('CLIENTE@example.com','minhasenha','pc-1','Notebook','4.0.0');assert first['first_claim'] is True
    payload=decode_with_public(first['entitlement'],pub);assert payload['email']=='cliente@example.com';assert payload['machine_id']=='pc-1'
    again=svc.activate('cliente@example.com','minhasenha','pc-1','Notebook','4.0.0');assert again['first_claim'] is False
    with pytest.raises(LicenseError) as exc:svc.activate('cliente@example.com','senha-errada','pc-2','Outro','4.0.0')
    assert exc.value.code=='invalid_credentials'

def test_email_not_pre_authorized_cannot_register(server):
    _,_,svc,_=server
    with pytest.raises(LicenseError) as exc:svc.activate('desconhecido@example.com','minhasenha','pc','PC','4.0.0')
    assert exc.value.code=='email_not_authorized'

def test_device_limit_and_revoke(server):
    _,admin,svc,_=server;aid=admin.authorize_email('a@b.com',max_devices=1)
    one=svc.activate('a@b.com','12345678','pc-1','PC 1','4.0.0')
    with pytest.raises(LicenseError) as exc:svc.activate('a@b.com','12345678','pc-2','PC 2','4.0.0')
    assert exc.value.code=='device_limit'
    account,devices,_=admin.get_account(aid);admin.revoke_device(devices[0]['id'])
    two=svc.activate('a@b.com','12345678','pc-2','PC 2','4.0.0');assert two['device_token']

def test_refresh_uses_device_token_not_password(server):
    _,admin,svc,pub=server;admin.authorize_email('r@b.com',offline_days=15)
    act=svc.activate('r@b.com','12345678','pc-r','PC','4.0.0');ref=svc.refresh(act['device_token'],'pc-r','4.0.1');payload=decode_with_public(ref['entitlement'],pub);assert payload['offline_days']==15

def test_blocked_account_refresh_fails(server):
    _,admin,svc,_=server;aid=admin.authorize_email('block@b.com');act=svc.activate('block@b.com','12345678','pc','PC','4.0.0');admin.set_account_blocked(aid,True)
    with pytest.raises(LicenseError) as exc:svc.refresh(act['device_token'],'pc','4.0.0')
    assert exc.value.code=='account_blocked'

def test_admin_password_reset_allows_new_password_but_old_stops(server):
    _,admin,svc,_=server;aid=admin.authorize_email('reset@b.com');svc.activate('reset@b.com','senha-antiga','pc','PC','4.0.0');admin.reset_password(aid)
    svc.activate('reset@b.com','senha-nova-123','pc','PC','4.0.0')
    with pytest.raises(LicenseError):svc.activate('reset@b.com','senha-antiga','pc','PC','4.0.0')

def test_change_password(server):
    _,admin,svc,_=server;admin.authorize_email('change@b.com');svc.activate('change@b.com','senha-atual','pc','PC','4.0.0');svc.change_password('change@b.com','senha-atual','senha-novissima')
    with pytest.raises(LicenseError):svc.activate('change@b.com','senha-atual','pc','PC','4.0.0')
    svc.activate('change@b.com','senha-novissima','pc','PC','4.0.0')

def test_server_never_stores_plain_password_or_device_token(server):
    store,admin,svc,_=server;aid=admin.authorize_email('secret@b.com');result=svc.activate('secret@b.com','senha-super-secreta','pc-secret','PC','4.0.0')
    with store.connect() as c:
        a=c.execute('SELECT password_hash FROM accounts WHERE id=?',(aid,)).fetchone();d=c.execute('SELECT device_token_hash FROM devices').fetchone()
    assert 'senha-super-secreta' not in a['password_hash'];assert result['device_token'] not in d['device_token_hash'];assert len(d['device_token_hash'])==64
