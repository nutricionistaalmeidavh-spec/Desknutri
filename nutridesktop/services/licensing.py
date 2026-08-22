from __future__ import annotations
import base64, json, platform, hashlib, uuid
from datetime import date, datetime, timezone
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from nutridesktop.core.paths import resource_dir, CONFIG_DIR
from nutridesktop.data.database import Database, db

PUBLIC_KEY_LOCATIONS=[resource_dir()/'config'/'license_public_key.pem',CONFIG_DIR/'license_public_key.pem']
SERVER_PUBLIC_KEY_LOCATIONS=[CONFIG_DIR/'license_server_public_jwk.json',resource_dir()/'config'/'license_server_public_jwk.json']

def machine_id(): return hashlib.sha256(f"{platform.node()}-{uuid.getnode()}".encode()).hexdigest()[:24]

def _b64url_decode(text:str)->bytes:
    return base64.urlsafe_b64decode(text+'='*(-len(text)%4))

def _public_key():
    for p in PUBLIC_KEY_LOCATIONS:
        if p.exists():return serialization.load_pem_public_key(p.read_bytes())
    raise RuntimeError('Chave pública de licença não configurada.')

def _server_public_key():
    for p in SERVER_PUBLIC_KEY_LOCATIONS:
        if p.exists():
            data=json.loads(p.read_text(encoding='utf-8'))
            if data.get('kty')!='OKP' or data.get('crv')!='Ed25519' or not data.get('x'):
                raise RuntimeError('Chave pública do servidor de licenças inválida.')
            return Ed25519PublicKey.from_public_bytes(_b64url_decode(data['x']))
    raise RuntimeError('Chave pública do servidor de licenças ainda não foi obtida.')

def set_server_public_jwk(jwk:dict)->Path:
    if jwk.get('kty')!='OKP' or jwk.get('crv')!='Ed25519' or not jwk.get('x'):
        raise ValueError('Chave pública de licença inválida.')
    # Valida o material antes de persistir.
    Ed25519PublicKey.from_public_bytes(_b64url_decode(str(jwk['x'])))
    CONFIG_DIR.mkdir(parents=True,exist_ok=True)
    target=CONFIG_DIR/'license_server_public_jwk.json'
    target.write_text(json.dumps({'kty':'OKP','crv':'Ed25519','x':jwk['x']},ensure_ascii=False),encoding='utf-8')
    return target

def has_server_public_key()->bool:
    return any(p.exists() for p in SERVER_PUBLIC_KEY_LOCATIONS)

def _parts(text:str):
    try:
        payload64,sig64=text.strip().split('.',1)
        raw=_b64url_decode(payload64)
        sig=_b64url_decode(sig64)
        return payload64,raw,sig,json.loads(raw)
    except Exception as e:raise ValueError('Formato de licença inválido') from e

def decode_license(text):
    _,raw,sig,data=_parts(text)
    return raw,sig,data

def _parse_iso(value:str|None):
    if not value:return None
    return datetime.fromisoformat(value.replace('Z','+00:00'))

def validate(text,bind_machine=True):
    payload64,raw,sig,data=_parts(text)
    if data.get('iss')=='NutriDesk Licensing':
        key=_server_public_key()
        # O servidor assina a representação base64url do payload.
        key.verify(sig,payload64.encode('ascii'))
        if data.get('status')!='active':raise ValueError('Licença inativa')
        now=datetime.now(timezone.utc)
        offline_until=_parse_iso(data.get('offline_until'))
        if offline_until and now>offline_until:raise ValueError('Autorização offline expirada')
        license_expires=_parse_iso(data.get('expires_at'))
        if license_expires and now>license_expires:raise ValueError('Licença expirada')
        if bind_machine and data.get('device_id') not in (None,'*',machine_id()):raise ValueError('Licença vinculada a outro computador')
        return {
            'product':'NutriDesktop',
            'expires':offline_until.date().isoformat() if offline_until else None,
            'machine_id':data.get('device_id'),
            'plan':data.get('plan'),
            'email':data.get('email'),
            'server_managed':True,
            'offline_until':data.get('offline_until'),
            'license_expires_at':data.get('expires_at'),
            'license_id':data.get('license_id'),
        }
    key=_public_key();key.verify(sig,raw)
    if data.get('product')!='NutriDesktop':raise ValueError('Licença de outro produto')
    if data.get('expires') and date.today()>date.fromisoformat(data['expires']):raise ValueError('Licença expirada')
    if bind_machine and data.get('machine_id') not in (None,'*',machine_id()):raise ValueError('Licença vinculada a outro computador')
    return data

def activate(text,database:Database=db):
    data=validate(text)
    with database.transaction() as c:
        c.execute("INSERT OR REPLACE INTO configuracoes(chave,valor) VALUES('license_v2',?)",(text.strip(),))
        c.execute("INSERT OR REPLACE INTO configuracoes(chave,valor) VALUES('license_machine_id',?)",(machine_id(),))
    return data

def current(database:Database=db):
    with database.connect() as c:r=c.execute("SELECT valor FROM configuracoes WHERE chave='license_v2'").fetchone()
    if not r:return None
    try:return validate(r[0])
    except Exception:return None
