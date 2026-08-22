from __future__ import annotations
from nutridesktop.core.security import hash_pin, verify_pin
from nutridesktop.data.database import Database, db
class SecuritySettings:
    def __init__(self,database:Database=db):self.db=database
    def get(self):
        with self.db.connect() as c:return c.execute('SELECT * FROM security_state WHERE id=1').fetchone()
    def set_pin(self,pin):
        h=hash_pin(pin)
        with self.db.transaction() as c:c.execute("UPDATE security_state SET pin_hash=?,updated_at=CURRENT_TIMESTAMP WHERE id=1",(h,))
    def verify(self,pin):
        row=self.get();return bool(row and row['pin_hash'] and verify_pin(pin,row['pin_hash']))
    def set_auto_lock(self,minutes):
        with self.db.transaction() as c:c.execute("UPDATE security_state SET auto_lock_minutes=?,updated_at=CURRENT_TIMESTAMP WHERE id=1",(max(1,int(minutes)),))
    def set_backup_encryption(self,enabled):
        with self.db.transaction() as c:c.execute("UPDATE security_state SET backup_encryption=?,updated_at=CURRENT_TIMESTAMP WHERE id=1",(1 if enabled else 0,))
