from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from nutridesktop.core.paths import DB_PATH
from .migrations import migrate

class Database:
    def __init__(self,path:Path|str=DB_PATH): self.path=Path(path)
    def connect(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        c=sqlite3.connect(self.path); c.row_factory=sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON"); c.execute("PRAGMA journal_mode=WAL"); c.execute("PRAGMA busy_timeout=5000")
        return c
    def initialize(self):
        with self.connect() as c: return migrate(c)
    @contextmanager
    def transaction(self):
        c=self.connect()
        try:
            c.execute("BEGIN IMMEDIATE"); yield c; c.commit()
        except Exception:
            c.rollback(); raise
        finally: c.close()

db=Database()
