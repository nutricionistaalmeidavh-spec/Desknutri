from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

PRODUCT = "NutriDesktop"


def utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def _b64e(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _b64d(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def hash_password(password: str) -> str:
    if len(password or "") < 8:
        raise ValueError("A senha deve ter pelo menos 8 caracteres.")
    salt = secrets.token_bytes(16)
    n, r, p = 2**14, 8, 1
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=n, r=r, p=p, dklen=32)
    return f"scrypt${n}${r}${p}${_b64e(salt)}${_b64e(digest)}"


def verify_password(password: str, encoded: str | None) -> bool:
    if not encoded:
        return False
    try:
        kind, ns, rs, ps, salt64, digest64 = encoded.split("$", 5)
        if kind != "scrypt":
            return False
        actual = hashlib.scrypt(
            password.encode("utf-8"), salt=_b64d(salt64), n=int(ns), r=int(rs), p=int(ps), dklen=32
        )
        return hmac.compare_digest(actual, _b64d(digest64))
    except Exception:
        return False


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ServerPaths:
    data_dir: Path
    db_path: Path
    private_key: Path
    public_key: Path
    secret_file: Path

    @classmethod
    def from_env(cls) -> "ServerPaths":
        data = Path(os.environ.get("NUTRIDESK_LICENSE_DATA", "license_server_data")).expanduser().resolve()
        data.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(data,0o700)
        except OSError:
            pass
        return cls(
            data,
            Path(os.environ.get("NUTRIDESK_LICENSE_DB", data / "licenses.db")),
            Path(os.environ.get("NUTRIDESK_LICENSE_PRIVATE_KEY", data / "license_private.pem")),
            Path(os.environ.get("NUTRIDESK_LICENSE_PUBLIC_KEY", data / "license_public.pem")),
            data / "server_secret.txt",
        )


class LicenseStore:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        c = sqlite3.connect(self.db_path)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON")
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA busy_timeout=5000")
        return c

    def initialize(self) -> None:
        with self.connect() as c:
            c.executescript(
                """
                CREATE TABLE IF NOT EXISTS admins(
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT NOT NULL UNIQUE,
                  password_hash TEXT NOT NULL,
                  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS accounts(
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT NOT NULL UNIQUE,
                  display_name TEXT,
                  password_hash TEXT,
                  status TEXT NOT NULL DEFAULT 'pending',
                  claimed_at TEXT,
                  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  updated_at TEXT
                );
                CREATE TABLE IF NOT EXISTS licenses(
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  account_id INTEGER NOT NULL,
                  product TEXT NOT NULL DEFAULT 'NutriDesktop',
                  plan TEXT NOT NULL DEFAULT 'Vitalício',
                  status TEXT NOT NULL DEFAULT 'active',
                  max_devices INTEGER NOT NULL DEFAULT 1,
                  offline_days INTEGER NOT NULL DEFAULT 30,
                  expires_at TEXT,
                  notes TEXT,
                  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  updated_at TEXT,
                  UNIQUE(account_id, product),
                  FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS devices(
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  license_id INTEGER NOT NULL,
                  machine_id TEXT NOT NULL,
                  device_name TEXT,
                  device_token_hash TEXT,
                  app_version TEXT,
                  activated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  last_seen TEXT,
                  revoked_at TEXT,
                  UNIQUE(license_id, machine_id),
                  FOREIGN KEY(license_id) REFERENCES licenses(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS events(
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  account_id INTEGER,
                  event_type TEXT NOT NULL,
                  details_json TEXT NOT NULL DEFAULT '{}',
                  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE SET NULL
                );
                CREATE INDEX IF NOT EXISTS idx_devices_license_active ON devices(license_id, revoked_at);
                CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at, id);
                """
            )
        try:
            os.chmod(self.db_path,0o600)
        except OSError:
            pass

    def event(self, c: sqlite3.Connection, account_id: int | None, kind: str, details: dict[str, Any] | None = None) -> None:
        c.execute(
            "INSERT INTO events(account_id,event_type,details_json,created_at) VALUES(?,?,?,?)",
            (account_id, kind, json.dumps(details or {}, ensure_ascii=False), utcnow()),
        )


class LicenseSigner:
    def __init__(self, private_key_path: str | Path):
        self.path = Path(private_key_path)

    def private_key(self) -> Ed25519PrivateKey:
        if not self.path.exists():
            raise RuntimeError("Chave privada de licenças não configurada no servidor.")
        key = serialization.load_pem_private_key(self.path.read_bytes(), password=None)
        if not isinstance(key, Ed25519PrivateKey):
            raise RuntimeError("A chave privada configurada não é Ed25519.")
        return key

    def sign(self, payload: dict[str, Any]) -> str:
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        sig = self.private_key().sign(raw)
        return f"{_b64e(raw)}.{_b64e(sig)}"

    @staticmethod
    def generate(private_path: str | Path, public_path: str | Path) -> tuple[Path, Path]:
        private_path, public_path = Path(private_path), Path(public_path)
        private_path.parent.mkdir(parents=True, exist_ok=True)
        public_path.parent.mkdir(parents=True, exist_ok=True)
        key = Ed25519PrivateKey.generate()
        private_path.write_bytes(
            key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
        )
        public_path.write_bytes(
            key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        )
        try:
            os.chmod(private_path, 0o600)
        except OSError:
            pass
        return private_path, public_path


class LicenseError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


class LicenseService:
    def __init__(self, store: LicenseStore, signer: LicenseSigner):
        self.store, self.signer = store, signer

    def _account_license(self, c: sqlite3.Connection, email: str):
        return c.execute(
            """SELECT a.*, l.id license_id, l.product, l.plan, l.status license_status,
                      l.max_devices,l.offline_days,l.expires_at,l.notes
               FROM accounts a LEFT JOIN licenses l ON l.account_id=a.id AND l.product=?
               WHERE a.email=?""",
            (PRODUCT, normalize_email(email)),
        ).fetchone()

    def _validate_account_license(self, row: sqlite3.Row | None) -> None:
        if not row:
            raise LicenseError("email_not_authorized", "Este e-mail ainda não foi liberado para o NutriDesktop.", 403)
        if row["status"] == "blocked":
            raise LicenseError("account_blocked", "Esta conta está bloqueada. Entre em contato com o suporte.", 403)
        if not row["license_id"]:
            raise LicenseError("license_missing", "Não existe licença NutriDesktop vinculada a esta conta.", 403)
        if row["license_status"] != "active":
            raise LicenseError("license_inactive", "A licença desta conta não está ativa.", 403)
        if row["expires_at"] and date.today() > date.fromisoformat(row["expires_at"]):
            raise LicenseError("license_expired", "A licença desta conta expirou.", 403)

    def _entitlement(self, row: sqlite3.Row, device_id: int, machine_id: str) -> str:
        offline_days = max(1, min(int(row["offline_days"] or 30), 365))
        until = date.today() + timedelta(days=offline_days)
        if row["expires_at"]:
            until = min(until, date.fromisoformat(row["expires_at"]))
        return self.signer.sign(
            {
                "product": PRODUCT,
                "account_id": row["id"],
                "email": row["email"],
                "license_id": row["license_id"],
                "device_id": device_id,
                "machine_id": machine_id,
                "plan": row["plan"],
                "issued_at": utcnow(),
                "expires": until.isoformat(),
                "license_expires": row["expires_at"],
                "offline_days": offline_days,
                "server_managed": True,
            }
        )

    def activate(self, email: str, password: str, machine_id: str, device_name: str, app_version: str) -> dict[str, Any]:
        email = normalize_email(email)
        if not email or "@" not in email:
            raise LicenseError("invalid_email", "Informe um e-mail válido.")
        if not machine_id:
            raise LicenseError("invalid_device", "Identificação do computador ausente.")
        with self.store.connect() as c:
            row = self._account_license(c, email)
            self._validate_account_license(row)
            first_claim = not bool(row["password_hash"])
            if first_claim:
                try:
                    encoded = hash_password(password)
                except ValueError as e:
                    raise LicenseError("weak_password", str(e)) from e
                c.execute(
                    "UPDATE accounts SET password_hash=?,status='active',claimed_at=?,updated_at=? WHERE id=?",
                    (encoded, utcnow(), utcnow(), row["id"]),
                )
                self.store.event(c, row["id"], "account_claimed", {"machine_id": machine_id})
                row = self._account_license(c, email)
            elif not verify_password(password, row["password_hash"]):
                self.store.event(c, row["id"], "login_failed", {"machine_id": machine_id})
                raise LicenseError("invalid_credentials", "E-mail ou senha incorretos.", 401)

            device = c.execute(
                "SELECT * FROM devices WHERE license_id=? AND machine_id=?",
                (row["license_id"], machine_id),
            ).fetchone()
            token = secrets.token_urlsafe(32)
            if device and not device["revoked_at"]:
                c.execute(
                    "UPDATE devices SET device_name=?,device_token_hash=?,app_version=?,last_seen=? WHERE id=?",
                    (device_name, token_hash(token), app_version, utcnow(), device["id"]),
                )
                device_id = int(device["id"])
            else:
                active_count = c.execute(
                    "SELECT COUNT(*) FROM devices WHERE license_id=? AND revoked_at IS NULL", (row["license_id"],)
                ).fetchone()[0]
                if active_count >= int(row["max_devices"] or 1):
                    raise LicenseError(
                        "device_limit",
                        f"Esta licença já atingiu o limite de {row['max_devices']} dispositivo(s).",
                        409,
                    )
                if device:
                    c.execute(
                        "UPDATE devices SET device_name=?,device_token_hash=?,app_version=?,activated_at=?,last_seen=?,revoked_at=NULL WHERE id=?",
                        (device_name, token_hash(token), app_version, utcnow(), utcnow(), device["id"]),
                    )
                    device_id = int(device["id"])
                else:
                    cur = c.execute(
                        """INSERT INTO devices(license_id,machine_id,device_name,device_token_hash,app_version,activated_at,last_seen)
                           VALUES(?,?,?,?,?,?,?)""",
                        (row["license_id"], machine_id, device_name, token_hash(token), app_version, utcnow(), utcnow()),
                    )
                    device_id = int(cur.lastrowid)
            self.store.event(c, row["id"], "device_activated", {"device_id": device_id, "machine_id": machine_id})
            c.commit()
            row = self._account_license(c, email)
            return {
                "entitlement": self._entitlement(row, device_id, machine_id),
                "device_token": token,
                "email": row["email"],
                "display_name": row["display_name"],
                "plan": row["plan"],
                "max_devices": row["max_devices"],
                "first_claim": first_claim,
            }

    def refresh(self, device_token: str, machine_id: str, app_version: str) -> dict[str, Any]:
        th = token_hash(device_token or "")
        with self.store.connect() as c:
            device = c.execute(
                """SELECT d.*,l.account_id,a.email FROM devices d
                   JOIN licenses l ON l.id=d.license_id JOIN accounts a ON a.id=l.account_id
                   WHERE d.device_token_hash=? AND d.machine_id=? AND d.revoked_at IS NULL""",
                (th, machine_id),
            ).fetchone()
            if not device:
                raise LicenseError("device_not_authorized", "Este computador não está autorizado ou foi desvinculado.", 401)
            row = self._account_license(c, device["email"])
            self._validate_account_license(row)
            c.execute("UPDATE devices SET last_seen=?,app_version=? WHERE id=?", (utcnow(), app_version, device["id"]))
            self.store.event(c, row["id"], "license_refreshed", {"device_id": device["id"]})
            c.commit()
            return {
                "entitlement": self._entitlement(row, int(device["id"]), machine_id),
                "email": row["email"],
                "plan": row["plan"],
                "max_devices": row["max_devices"],
            }

    def unlink(self, device_token: str, machine_id: str) -> None:
        with self.store.connect() as c:
            device = c.execute(
                """SELECT d.*,l.account_id FROM devices d JOIN licenses l ON l.id=d.license_id
                   WHERE d.device_token_hash=? AND d.machine_id=? AND d.revoked_at IS NULL""",
                (token_hash(device_token or ""), machine_id),
            ).fetchone()
            if not device:
                raise LicenseError("device_not_authorized", "Dispositivo não encontrado.", 404)
            c.execute("UPDATE devices SET revoked_at=?,device_token_hash=NULL WHERE id=?", (utcnow(), device["id"]))
            self.store.event(c, device["account_id"], "device_unlinked", {"device_id": device["id"]})
            c.commit()

    def change_password(self, email: str, current_password: str, new_password: str) -> None:
        with self.store.connect() as c:
            account = c.execute("SELECT * FROM accounts WHERE email=?", (normalize_email(email),)).fetchone()
            if not account or not verify_password(current_password, account["password_hash"]):
                raise LicenseError("invalid_credentials", "Senha atual incorreta.", 401)
            try:
                encoded = hash_password(new_password)
            except ValueError as e:
                raise LicenseError("weak_password", str(e)) from e
            c.execute("UPDATE accounts SET password_hash=?,updated_at=? WHERE id=?", (encoded, utcnow(), account["id"]))
            self.store.event(c, account["id"], "password_changed", {})
            c.commit()


class AdminService:
    def __init__(self, store: LicenseStore):
        self.store = store

    def create_admin(self, email: str, password: str) -> int:
        email = normalize_email(email)
        encoded = hash_password(password)
        with self.store.connect() as c:
            cur = c.execute("INSERT INTO admins(email,password_hash) VALUES(?,?)", (email, encoded))
            c.commit()
            return int(cur.lastrowid)

    def verify_admin(self, email: str, password: str):
        with self.store.connect() as c:
            row = c.execute("SELECT * FROM admins WHERE email=?", (normalize_email(email),)).fetchone()
            return row if row and verify_password(password, row["password_hash"]) else None

    def authorize_email(self, email: str, display_name: str = "", plan: str = "Vitalício", max_devices: int = 1,
                        offline_days: int = 30, expires_at: str | None = None, notes: str = "") -> int:
        email = normalize_email(email)
        if not email or "@" not in email:
            raise ValueError("E-mail inválido")
        max_devices = max(1, min(int(max_devices), 50))
        offline_days = max(1, min(int(offline_days), 365))
        if expires_at:
            date.fromisoformat(expires_at)
        with self.store.connect() as c:
            existing = c.execute("SELECT id FROM accounts WHERE email=?", (email,)).fetchone()
            if existing:
                raise ValueError("Este e-mail já está cadastrado.")
            cur = c.execute(
                "INSERT INTO accounts(email,display_name,status,updated_at) VALUES(?,?,'pending',?)",
                (email, display_name.strip(), utcnow()),
            )
            aid = int(cur.lastrowid)
            c.execute(
                """INSERT INTO licenses(account_id,product,plan,status,max_devices,offline_days,expires_at,notes,updated_at)
                   VALUES(?,?,?,'active',?,?,?,?,?)""",
                (aid, PRODUCT, plan.strip() or "Vitalício", max_devices, offline_days, expires_at or None, notes, utcnow()),
            )
            self.store.event(c, aid, "email_authorized", {"plan": plan, "max_devices": max_devices})
            c.commit()
            return aid

    def reset_password(self, account_id: int) -> None:
        with self.store.connect() as c:
            c.execute("UPDATE accounts SET password_hash=NULL,status=CASE WHEN status='blocked' THEN 'blocked' ELSE 'pending' END,claimed_at=NULL,updated_at=? WHERE id=?", (utcnow(), account_id))
            self.store.event(c, account_id, "password_reset_by_admin", {})
            c.commit()

    def set_account_blocked(self, account_id: int, blocked: bool) -> None:
        with self.store.connect() as c:
            if blocked:
                status='blocked'
            else:
                row=c.execute("SELECT password_hash FROM accounts WHERE id=?",(account_id,)).fetchone();status='active' if row and row[0] else 'pending'
            c.execute("UPDATE accounts SET status=?,updated_at=? WHERE id=?", (status, utcnow(), account_id))
            self.store.event(c, account_id, "account_blocked" if blocked else "account_unblocked", {})
            c.commit()

    def update_license(self, account_id: int, plan: str, max_devices: int, offline_days: int,
                       expires_at: str | None, status: str, notes: str = "") -> None:
        if expires_at:
            date.fromisoformat(expires_at)
        with self.store.connect() as c:
            c.execute(
                """UPDATE licenses SET plan=?,max_devices=?,offline_days=?,expires_at=?,status=?,notes=?,updated_at=?
                   WHERE account_id=? AND product=?""",
                (plan, max(1, int(max_devices)), max(1, min(int(offline_days), 365)), expires_at or None,
                 status if status in {"active", "blocked"} else "active", notes, utcnow(), account_id, PRODUCT),
            )
            self.store.event(c, account_id, "license_updated", {"plan": plan, "max_devices": max_devices})
            c.commit()

    def revoke_device(self, device_id: int) -> None:
        with self.store.connect() as c:
            row = c.execute("SELECT d.*,l.account_id FROM devices d JOIN licenses l ON l.id=d.license_id WHERE d.id=?", (device_id,)).fetchone()
            if row:
                c.execute("UPDATE devices SET revoked_at=?,device_token_hash=NULL WHERE id=?", (utcnow(), device_id))
                self.store.event(c, row["account_id"], "device_revoked_by_admin", {"device_id": device_id})
                c.commit()

    def stats(self) -> dict[str, int]:
        with self.store.connect() as c:
            return {
                "accounts": c.execute("SELECT COUNT(*) FROM accounts").fetchone()[0],
                "active": c.execute("SELECT COUNT(*) FROM accounts WHERE status='active'").fetchone()[0],
                "pending": c.execute("SELECT COUNT(*) FROM accounts WHERE password_hash IS NULL AND status!='blocked'").fetchone()[0],
                "blocked": c.execute("SELECT COUNT(*) FROM accounts WHERE status='blocked'").fetchone()[0],
                "devices": c.execute("SELECT COUNT(*) FROM devices WHERE revoked_at IS NULL").fetchone()[0],
            }

    def list_accounts(self):
        with self.store.connect() as c:
            return c.execute(
                """SELECT a.*,l.plan,l.status license_status,l.max_devices,l.offline_days,l.expires_at,
                          (SELECT COUNT(*) FROM devices d WHERE d.license_id=l.id AND d.revoked_at IS NULL) device_count
                   FROM accounts a LEFT JOIN licenses l ON l.account_id=a.id AND l.product=? ORDER BY a.id DESC""",
                (PRODUCT,),
            ).fetchall()

    def get_account(self, account_id: int):
        with self.store.connect() as c:
            account = c.execute(
                """SELECT a.*,l.id license_id,l.plan,l.status license_status,l.max_devices,l.offline_days,l.expires_at,l.notes
                   FROM accounts a LEFT JOIN licenses l ON l.account_id=a.id AND l.product=? WHERE a.id=?""",
                (PRODUCT, account_id),
            ).fetchone()
            devices = c.execute("SELECT * FROM devices WHERE license_id=? ORDER BY id DESC", (account["license_id"],)).fetchall() if account and account["license_id"] else []
            events = c.execute("SELECT * FROM events WHERE account_id=? ORDER BY id DESC LIMIT 40", (account_id,)).fetchall()
            return account, devices, events


def get_or_create_server_secret(paths: ServerPaths) -> bytes:
    env = os.environ.get("NUTRIDESK_SERVER_SECRET")
    if env:
        return env.encode("utf-8")
    if paths.secret_file.exists():
        return paths.secret_file.read_text(encoding="utf-8").strip().encode("utf-8")
    secret = secrets.token_urlsafe(48)
    paths.secret_file.write_text(secret, encoding="utf-8")
    try:
        os.chmod(paths.secret_file, 0o600)
    except OSError:
        pass
    return secret.encode("utf-8")


def make_session(secret: bytes, admin_id: int, email: str, ttl_hours: int = 8) -> tuple[str, str]:
    csrf = secrets.token_urlsafe(24)
    payload = {"admin_id": admin_id, "email": email, "csrf": csrf, "exp": int(datetime.now(timezone.utc).timestamp()) + ttl_hours * 3600}
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    sig = hmac.new(secret, raw, hashlib.sha256).digest()
    return f"{_b64e(raw)}.{_b64e(sig)}", csrf


def parse_session(secret: bytes, token: str | None) -> dict[str, Any] | None:
    if not token:
        return None
    try:
        raw64, sig64 = token.split(".", 1)
        raw, sig = _b64d(raw64), _b64d(sig64)
        if not hmac.compare_digest(sig, hmac.new(secret, raw, hashlib.sha256).digest()):
            return None
        data = json.loads(raw)
        if int(data["exp"]) < int(datetime.now(timezone.utc).timestamp()):
            return None
        return data
    except Exception:
        return None
