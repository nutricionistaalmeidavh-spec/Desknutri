from __future__ import annotations
import argparse,base64,json,os
from pathlib import Path
from datetime import date
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
ROOT=Path(__file__).resolve().parents[1]; ADMIN=ROOT/'license_admin'; CONFIG=ROOT/'config'; PRIV=ADMIN/'private_key.pem'; PUB=CONFIG/'license_public_key.pem'
def init():
    ADMIN.mkdir(exist_ok=True);CONFIG.mkdir(exist_ok=True)
    if PRIV.exists():raise SystemExit('Chave privada já existe; não sobrescrevendo.')
    key=Ed25519PrivateKey.generate(); PRIV.write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption())); PUB.write_bytes(key.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo)); print('OK. Guarde license_admin/private_key.pem fora do repositório e de backups enviados a clientes.')
def sign(serial,machine='*',expires=None):
    if not PRIV.exists():raise SystemExit('Execute init primeiro.')
    key=serialization.load_pem_private_key(PRIV.read_bytes(),password=None); data={'product':'NutriDesktop','serial':serial,'machine_id':machine,'issued':date.today().isoformat(),'expires':expires}; payload=json.dumps(data,separators=(',',':'),sort_keys=True).encode(); sig=key.sign(payload); enc=lambda b:base64.urlsafe_b64encode(b).decode().rstrip('=');print(enc(payload)+'.'+enc(sig))
if __name__=='__main__':
    p=argparse.ArgumentParser();s=p.add_subparsers(dest='cmd',required=True);s.add_parser('init');q=s.add_parser('sign');q.add_argument('--serial',required=True);q.add_argument('--machine',default='*');q.add_argument('--expires');a=p.parse_args(); init() if a.cmd=='init' else sign(a.serial,a.machine,a.expires)
