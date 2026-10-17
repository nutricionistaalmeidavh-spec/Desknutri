from __future__ import annotations
import json
from pathlib import Path
from .paths import resource_dir, CONFIG_DIR

DEFAULT={"purchase_url":"https://github.com/nutricionistaalmeidavh-spec/Desknutri/releases/latest","whatsapp":"","support_message":"Preciso de suporte com o NutriDesk.","publisher":"NutriDesk"}

def load_commercial_config():
    candidates=[CONFIG_DIR/"commercial.json", resource_dir()/"config"/"commercial.json"]
    for p in candidates:
        if p.exists():
            try: return {**DEFAULT,**json.loads(p.read_text(encoding="utf-8"))}
            except Exception: pass
    return DEFAULT.copy()
