from __future__ import annotations
import logging, re
from logging.handlers import RotatingFileHandler
from .paths import LOG_DIR

SENSITIVE_PATTERNS = [
    re.compile(r"(?i)(nome|email|telefone|cpf|anamnese|queixa|medicamento)\s*[=:]\s*[^,;\n]+"),
]
class RedactingFormatter(logging.Formatter):
    def format(self, record):
        text=super().format(record)
        for pat in SENSITIVE_PATTERNS: text=pat.sub(lambda m: m.group(1)+"=[REDACTED]", text)
        return text

def configure_logging():
    logger=logging.getLogger("nutridesktop")
    if logger.handlers: return logger
    logger.setLevel(logging.INFO)
    h=RotatingFileHandler(LOG_DIR/"nutridesktop.log", maxBytes=1_500_000, backupCount=4, encoding="utf-8")
    h.setFormatter(RedactingFormatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logger.addHandler(h); return logger
