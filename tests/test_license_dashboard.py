from __future__ import annotations
import importlib,os,sys

def test_admin_dashboard_flow(tmp_path,monkeypatch):
    monkeypatch.setenv('NUTRIDESK_LICENSE_DATA',str(tmp_path/'server'))
    monkeypatch.setenv('NUTRIDESK_COOKIE_SECURE','0')
    sys.modules.pop('license_server.main',None)
    import license_server.main as lm
    from fastapi.testclient import TestClient
    lm.LicenseSigner.generate(lm.paths.private_key,lm.paths.public_key)
    lm.admins.create_admin('admin@example.com','senha-admin-123')
    client=TestClient(lm.app)
    r=client.post('/admin/login',data={'email':'admin@example.com','password':'senha-admin-123'},follow_redirects=True);assert r.status_code==200;assert 'Liberar novo e-mail' in r.text
    import re
    csrf=re.search(r'name="csrf" value="([^"]+)"',r.text).group(1)
    r=client.post('/admin/accounts',data={'csrf':csrf,'display_name':'Cliente Teste','email':'cliente@example.com','plan':'Vitalício','max_devices':'1','offline_days':'30','expires_at':'','notes':''},follow_redirects=True);assert r.status_code==200;assert 'cliente@example.com' in r.text
    a=client.post('/api/v1/activate',json={'email':'cliente@example.com','password':'senha-cliente-123','machine_id':'pc-test','device_name':'Notebook','app_version':'4.0.0'});assert a.status_code==200;data=a.json();assert data['device_token'] and data['entitlement']
    a2=client.post('/api/v1/activate',json={'email':'cliente@example.com','password':'senha-errada','machine_id':'pc-2','device_name':'Outro','app_version':'4.0.0'});assert a2.status_code==401
