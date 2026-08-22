from __future__ import annotations
import base64, hashlib, hmac, os, time
from cryptography.fernet import Fernet

SCRYPT_N=2**14

def hash_pin(pin: str) -> str:
    if len(pin or "") < 4: raise ValueError("PIN deve ter ao menos 4 caracteres")
    salt=os.urandom(16)
    key=hashlib.scrypt(pin.encode(),salt=salt,n=SCRYPT_N,r=8,p=1,dklen=32)
    return "scrypt$"+base64.urlsafe_b64encode(salt).decode()+"$"+base64.urlsafe_b64encode(key).decode()

def verify_pin(pin: str, encoded: str) -> bool:
    try:
        _,s,k=encoded.split("$",2); salt=base64.urlsafe_b64decode(s); expected=base64.urlsafe_b64decode(k)
        actual=hashlib.scrypt(pin.encode(),salt=salt,n=SCRYPT_N,r=8,p=1,dklen=32)
        return hmac.compare_digest(actual,expected)
    except Exception: return False

def fernet_from_password(password: str, salt: bytes) -> Fernet:
    key=hashlib.scrypt(password.encode(),salt=salt,n=SCRYPT_N,r=8,p=1,dklen=32)
    return Fernet(base64.urlsafe_b64encode(key))

class SessionLock:
    def __init__(self, timeout_minutes=15): self.timeout=max(1,int(timeout_minutes))*60; self.last_activity=time.monotonic()
    def touch(self): self.last_activity=time.monotonic()
    def expired(self): return time.monotonic()-self.last_activity >= self.timeout
