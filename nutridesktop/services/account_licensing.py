from __future__ import annotations

import json
import os
import platform
import socket
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from nutridesktop.core.config import load_commercial_config
from nutridesktop.core.secret_store import protect_text, unprotect_text
from nutridesktop.data.database import Database, db
from nutridesktop.services import licensing
from nutridesktop.version import APP_VERSION


class AccountLicenseError(Exception):
    def __init__(self, code: str, message: str, status: int | None = None):
        super().__init__(message); self.code=code; self.message=message; self.status=status


@dataclass(frozen=True)
class AccountState:
    email: str
    server_url: str
    last_refresh: str | None
    last_error: str | None
    has_device_token: bool


class AccountLicenseService:
    def __init__(self, database: Database = db): self.db=database

    def _row(self):
        with self.db.connect() as c:
            try:return c.execute("SELECT * FROM account_license_state WHERE id=1").fetchone()
            except Exception:return None

    def state(self) -> AccountState:
        row=self._row();cfg=load_commercial_config();default_url=str(cfg.get("license_server_url") or "").strip().rstrip("/")
        if not row:return AccountState("",default_url,None,None,False)
        return AccountState(row["email"] or "",row["server_url"] or default_url,row["last_refresh"],row["last_error"],bool(row["device_token_enc"]))

    def server_url(self) -> str: return self.state().server_url.rstrip("/")
    def _is_cloud(self)->bool:return '/functions/v1/nutridesk-licensing' in self.server_url()
    def _account_url(self)->str:
        base=self.server_url()
        return base.rsplit('/',1)[0]+'/nutridesk-account' if self._is_cloud() else base
    def configured(self) -> bool:
        return bool(self.server_url()) if self._is_cloud() else bool(self.server_url()) and any(p.exists() for p in licensing.PUBLIC_KEY_LOCATIONS)

    def set_server_url(self, url: str) -> None:
        url=(url or "").strip().rstrip("/"); self._validate_url(url,allow_empty=True)
        st=self.state();row=self._row()
        with self.db.transaction() as c:
            c.execute("""INSERT INTO account_license_state(id,email,server_url,device_token_enc,last_refresh,last_error,updated_at)
                         VALUES(1,?,?,?,?,?,CURRENT_TIMESTAMP)
                         ON CONFLICT(id) DO UPDATE SET server_url=excluded.server_url,updated_at=CURRENT_TIMESTAMP""",
                      (st.email,url,row["device_token_enc"] if row else None,st.last_refresh,st.last_error))

    def _validate_url(self,url:str,allow_empty=False):
        if not url and allow_empty:return
        p=urllib.parse.urlparse(url)
        if p.scheme not in {"https","http"}:raise AccountLicenseError("invalid_server","Endereço do servidor de licenças inválido.")
        if p.scheme=="http" and p.hostname not in {"127.0.0.1","localhost","::1"} and os.environ.get("NUTRIDESKTOP_ALLOW_INSECURE_LICENSE_SERVER")!="1":
            raise AccountLicenseError("https_required","O servidor de licenças precisa usar HTTPS.")

    def _map_error(self,message:str,status:int|None):
        low=message.lower()
        if 'bloquead' in low:return 'account_blocked'
        if 'expirad' in low:return 'license_expired'
        if 'dispositivo não autorizado' in low:return 'device_not_authorized'
        if status==401:return 'invalid_credentials'
        return 'server_error'

    def _request_json(self,url:str,payload:dict|None=None,timeout=8,method='POST'):
        self._validate_url(url)
        data=None if payload is None else json.dumps(payload).encode('utf-8')
        req=urllib.request.Request(url,data=data,headers={"Content-Type":"application/json","User-Agent":f"NutriDesktop/{APP_VERSION}"},method=method)
        try:
            with urllib.request.urlopen(req,timeout=timeout) as resp:return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            try:
                body=json.loads(e.read().decode("utf-8"));message=body.get('error') or body.get('message') or f'Erro HTTP {e.code}'
            except Exception:message=f'Erro HTTP {e.code}'
            raise AccountLicenseError(self._map_error(message,e.code),message,e.code)
        except (urllib.error.URLError,TimeoutError,socket.timeout) as e:raise AccountLicenseError("offline","Não foi possível acessar o servidor de licenças.") from e

    def _post_legacy(self,path:str,payload:dict):return self._request_json(self.server_url()+path,payload)
    def _cloud_action(self,action:str,payload:dict,account=False):return self._request_json(self._account_url() if account else self.server_url(),{"action":action,**payload})

    def _ensure_server_key(self):
        if licensing.has_server_public_key():return
        data=self._request_json(self.server_url(),None,method='GET')
        key=data.get('public_key')
        if not isinstance(key,dict):raise AccountLicenseError('server_key','O servidor não forneceu uma chave pública válida.')
        licensing.set_server_public_jwk(key)

    def _save(self,email:str,device_token:str|None,last_error:str|None=None):
        row=self._row();enc=protect_text(device_token) if device_token else (row["device_token_enc"] if row else None)
        with self.db.transaction() as c:
            c.execute("""INSERT INTO account_license_state(id,email,server_url,device_token_enc,last_refresh,last_error,updated_at)
                         VALUES(1,?,?,?,?,?,CURRENT_TIMESTAMP)
                         ON CONFLICT(id) DO UPDATE SET email=excluded.email,server_url=excluded.server_url,device_token_enc=excluded.device_token_enc,last_refresh=excluded.last_refresh,last_error=excluded.last_error,updated_at=CURRENT_TIMESTAMP""",
                      (email,self.server_url(),enc,datetime.now().isoformat(timespec="seconds") if not last_error else (row["last_refresh"] if row else None),last_error))

    def _token(self)->str:
        row=self._row();return unprotect_text(row["device_token_enc"] if row else None)

    def activate(self,email:str,password:str):
        if len(password or "")<8:raise AccountLicenseError("weak_password","A senha deve ter pelo menos 8 caracteres.")
        if self._is_cloud():
            self._ensure_server_key()
            data=self._cloud_action('login',{"email":email.strip().lower(),"password":password,"device_id":licensing.machine_id(),"device_name":platform.node() or "Computador","app_version":APP_VERSION})
            entitlement=f"{data['payload']}.{data['signature']}"
            result=licensing.activate(entitlement,self.db);self._save(data.get('license',{}).get('email',email.strip().lower()),data["device_token"]);return result
        data=self._post_legacy("/api/v1/activate",{"email":email.strip().lower(),"password":password,"machine_id":licensing.machine_id(),"device_name":platform.node() or "Computador","app_version":APP_VERSION})
        licensing.activate(data["entitlement"],self.db);self._save(data.get("email",email.strip().lower()),data["device_token"]);return licensing.validate(data["entitlement"])

    def refresh(self,force=True):
        token=self._token()
        if not token:raise AccountLicenseError("not_activated","Este computador ainda não possui sessão de licença.")
        try:
            if self._is_cloud():
                self._ensure_server_key();data=self._cloud_action('renew',{"device_token":token,"device_id":licensing.machine_id(),"app_version":APP_VERSION});entitlement=f"{data['payload']}.{data['signature']}"
                result=licensing.activate(entitlement,self.db);self._save(data.get('license',{}).get('email',self.state().email),None);return result
            data=self._post_legacy("/api/v1/refresh",{"device_token":token,"machine_id":licensing.machine_id(),"app_version":APP_VERSION})
            licensing.activate(data["entitlement"],self.db);self._save(data.get("email",self.state().email),None);return licensing.validate(data["entitlement"])
        except AccountLicenseError as e:
            self._save(self.state().email,None,e.message)
            if e.code in {'device_not_authorized','account_blocked','license_inactive','license_expired'}:
                with self.db.transaction() as c:
                    c.execute("DELETE FROM configuracoes WHERE chave IN ('license_v2','license_machine_id')")
                    if e.code=='device_not_authorized':c.execute("UPDATE account_license_state SET device_token_enc=NULL WHERE id=1")
            raise

    def refresh_if_due(self):
        current=licensing.current(self.db);st=self.state();due=not st.last_refresh
        if st.last_refresh:
            try:due=datetime.fromisoformat(st.last_refresh)<datetime.now()-timedelta(hours=24)
            except Exception:due=True
        if current:
            try:due=due or date.fromisoformat(current["expires"])<=date.today()+timedelta(days=7)
            except Exception:pass
        if due:return self.refresh()
        return current

    def unlink_current(self):
        token=self._token()
        if token:
            if self._is_cloud():self._cloud_action('unlink-device',{"device_token":token,"device_id":licensing.machine_id()},account=True)
            else:self._post_legacy("/api/v1/unlink",{"device_token":token,"machine_id":licensing.machine_id()})
        with self.db.transaction() as c:
            c.execute("DELETE FROM configuracoes WHERE chave IN ('license_v2','license_machine_id')")
            c.execute("UPDATE account_license_state SET device_token_enc=NULL,last_refresh=NULL,last_error=NULL,updated_at=CURRENT_TIMESTAMP WHERE id=1")

    def change_password(self,current_password:str,new_password:str):
        st=self.state()
        if not st.email:raise AccountLicenseError("not_activated","Nenhuma conta está vinculada a este computador.")
        if len(new_password or "")<8:raise AccountLicenseError("weak_password","A nova senha deve ter pelo menos 8 caracteres.")
        if self._is_cloud():return self._cloud_action('change-password',{"email":st.email,"current_password":current_password,"new_password":new_password},account=True)
        return self._post_legacy("/api/v1/change-password",{"email":st.email,"current_password":current_password,"new_password":new_password})
