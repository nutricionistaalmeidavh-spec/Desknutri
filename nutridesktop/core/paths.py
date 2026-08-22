from __future__ import annotations
import os, sys
from pathlib import Path

APP_NAME = "NutriDesktop"

def app_data_dir() -> Path:
    override = os.environ.get("NUTRIDESKTOP_DATA_DIR")
    if override:
        base = Path(override)
    elif os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / APP_NAME
    else:
        base = Path.home() / ".local" / "share" / APP_NAME
    base.mkdir(parents=True, exist_ok=True)
    return base

def resource_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parents[2]

DATA_DIR = app_data_dir()
DB_PATH = DATA_DIR / "nutridesktop.db"
PATIENT_FILES_DIR = DATA_DIR / "pacientes_arquivos"
PATIENT_PHOTOS_DIR = DATA_DIR / "fotos_pacientes"
BACKUP_DIR = DATA_DIR / "backups"
LOG_DIR = DATA_DIR / "logs"
CONFIG_DIR = DATA_DIR / "config"
UPDATE_DIR = DATA_DIR / "updates"
EXPORT_DIR = DATA_DIR / "exports"
SUPPORT_DIR = DATA_DIR / "support"
for _p in (PATIENT_FILES_DIR, PATIENT_PHOTOS_DIR, BACKUP_DIR, LOG_DIR, CONFIG_DIR, UPDATE_DIR, EXPORT_DIR, SUPPORT_DIR):
    _p.mkdir(parents=True, exist_ok=True)
