from __future__ import annotations
from dataclasses import dataclass,asdict
from datetime import datetime,timedelta
from pathlib import Path
import json
from nutridesktop.core.paths import BACKUP_DIR
from nutridesktop.data.database import Database,db
from .app_settings import AppSettings
from .backup import create_backup

@dataclass
class BackupPolicy:
    enabled:bool=True
    frequency:str='daily'          # daily | weekly
    run_at:str='close'             # startup | close | startup_or_close
    retain_daily:int=7
    retain_weekly:int=4
    retain_monthly:int=6
    def normalized(self):
        self.frequency=self.frequency if self.frequency in {'daily','weekly'} else 'daily'
        self.run_at=self.run_at if self.run_at in {'startup','close','startup_or_close'} else 'close'
        self.retain_daily=max(1,min(int(self.retain_daily),60));self.retain_weekly=max(0,min(int(self.retain_weekly),52));self.retain_monthly=max(0,min(int(self.retain_monthly),36));return self

class AutoBackupService:
    KEY='p3.backup_policy'
    def __init__(self,database:Database=db,backup_dir:Path=BACKUP_DIR):self.db=database;self.backup_dir=Path(backup_dir);self.settings=AppSettings(database)
    def policy(self):
        raw=self.settings.get(self.KEY,{}) or {}
        try:return BackupPolicy(**{k:v for k,v in raw.items() if k in BackupPolicy.__annotations__}).normalized()
        except Exception:return BackupPolicy()
    def save_policy(self,policy:BackupPolicy):self.settings.set(self.KEY,asdict(policy.normalized()))
    def _last(self):
        with self.db.connect() as c:return c.execute("SELECT * FROM backup_history WHERE status='OK' AND trigger LIKE 'auto:%' ORDER BY id DESC LIMIT 1").fetchone()
    def due(self,trigger):
        p=self.policy()
        if not p.enabled:return False
        if p.run_at!='startup_or_close' and p.run_at!=trigger:return False
        last=self._last()
        if not last:return True
        try:when=datetime.fromisoformat(str(last['created_at']).replace('Z','+00:00')).replace(tzinfo=None)
        except Exception:return True
        delta=datetime.now()-when
        return delta>=timedelta(days=7 if p.frequency=='weekly' else 1)
    def maybe_run(self,trigger='startup'):
        if not self.due(trigger):return None
        self.backup_dir.mkdir(parents=True,exist_ok=True)
        dest=self.backup_dir/f"AUTO_{datetime.now().strftime('%Y%m%d_%H%M%S')}.nbak"
        create_backup(dest,database=self.db,trigger=f'auto:{trigger}')
        self.prune();return dest
    def prune(self):
        p=self.policy();files=sorted(self.backup_dir.glob('AUTO_*.nbak'),key=lambda x:x.stat().st_mtime,reverse=True)
        if not files:return []
        keep=set();daily={};weekly={};monthly={}
        for f in files:
            dt=datetime.fromtimestamp(f.stat().st_mtime)
            daily.setdefault(dt.date().isoformat(),f);weekly.setdefault(f'{dt.isocalendar().year}-{dt.isocalendar().week:02d}',f);monthly.setdefault(dt.strftime('%Y-%m'),f)
        keep.update(list(daily.values())[:p.retain_daily]);keep.update(list(weekly.values())[:p.retain_weekly]);keep.update(list(monthly.values())[:p.retain_monthly])
        removed=[]
        for f in files:
            if f not in keep:
                try:f.unlink();removed.append(f)
                except OSError:pass
        return removed
    def last_summary(self):
        row=self._last()
        return dict(row) if row else None
