from __future__ import annotations

import base64
import os
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from .paths import CONFIG_DIR

_KEY_FILE = CONFIG_DIR / "local_secret.key"


def _fallback_key() -> bytes:
    if _KEY_FILE.exists():
        raw = _KEY_FILE.read_bytes()
        if len(raw) == 32:
            return raw
    raw = os.urandom(32)
    _KEY_FILE.write_bytes(raw)
    try:
        os.chmod(_KEY_FILE, 0o600)
    except OSError:
        pass
    return raw


def _dpapi_protect(data: bytes) -> bytes | None:
    if os.name != "nt":
        return None
    try:
        import ctypes
        from ctypes import wintypes
        class DATA_BLOB(ctypes.Structure):
            _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]
        def blob(b: bytes):
            buf = ctypes.create_string_buffer(b)
            return DATA_BLOB(len(b), ctypes.cast(buf, ctypes.POINTER(ctypes.c_byte))), buf
        in_blob, in_buf = blob(data); out_blob = DATA_BLOB()
        ok = ctypes.windll.crypt32.CryptProtectData(ctypes.byref(in_blob), "NutriDesktop", None, None, None, 0, ctypes.byref(out_blob))
        if not ok: return None
        try: return ctypes.string_at(out_blob.pbData, out_blob.cbData)
        finally: ctypes.windll.kernel32.LocalFree(out_blob.pbData)
    except Exception:
        return None


def _dpapi_unprotect(data: bytes) -> bytes | None:
    if os.name != "nt":
        return None
    try:
        import ctypes
        from ctypes import wintypes
        class DATA_BLOB(ctypes.Structure):
            _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]
        buf = ctypes.create_string_buffer(data)
        in_blob = DATA_BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_byte))); out_blob = DATA_BLOB()
        ok = ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob))
        if not ok: return None
        try: return ctypes.string_at(out_blob.pbData, out_blob.cbData)
        finally: ctypes.windll.kernel32.LocalFree(out_blob.pbData)
    except Exception:
        return None


def protect_text(text: str) -> str:
    raw = text.encode("utf-8")
    protected = _dpapi_protect(raw)
    if protected is not None:
        return "dpapi:" + base64.urlsafe_b64encode(protected).decode()
    key = _fallback_key(); nonce = os.urandom(12); enc = AESGCM(key).encrypt(nonce, raw, b"NutriDesktop-account-license")
    return "aesgcm:" + base64.urlsafe_b64encode(nonce + enc).decode()


def unprotect_text(value: str | None) -> str:
    if not value: return ""
    try:
        kind, payload = value.split(":", 1); raw = base64.urlsafe_b64decode(payload)
        if kind == "dpapi":
            dec = _dpapi_unprotect(raw)
            if dec is None: return ""
            return dec.decode("utf-8")
        if kind == "aesgcm":
            return AESGCM(_fallback_key()).decrypt(raw[:12], raw[12:], b"NutriDesktop-account-license").decode("utf-8")
    except Exception:
        return ""
    return ""
