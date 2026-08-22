from __future__ import annotations
import json
from nutridesktop.data.database import Database, db

class AppSettings:
    """Typed JSON-backed settings stored in the existing configuracoes table."""
    def __init__(self, database: Database = db): self.db=database
    def get(self,key,default=None):
        with self.db.connect() as c:
            row=c.execute("SELECT valor FROM configuracoes WHERE chave=?",(key,)).fetchone()
        if not row:return default
        raw=row['valor']
        try:return json.loads(raw)
        except Exception:return raw
    def set(self,key,value):
        raw=json.dumps(value,ensure_ascii=False,separators=(',',':'))
        with self.db.transaction() as c:
            c.execute("INSERT INTO configuracoes(chave,valor) VALUES(?,?) ON CONFLICT(chave) DO UPDATE SET valor=excluded.valor",(key,raw))
    def delete(self,key):
        with self.db.transaction() as c:c.execute("DELETE FROM configuracoes WHERE chave=?",(key,))
