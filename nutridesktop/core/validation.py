from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, date
import re

class ValidationError(ValueError): pass

def required_text(value, label="Campo", max_len=300):
    text = (value or "").strip()
    if not text: raise ValidationError(f"{label} é obrigatório.")
    if len(text) > max_len: raise ValidationError(f"{label} excede {max_len} caracteres.")
    return text

def optional_text(value, max_len=4000):
    text = (value or "").strip()
    if len(text) > max_len: raise ValidationError(f"Texto excede {max_len} caracteres.")
    return text

def number(value, label, minimum=None, maximum=None, allow_none=False):
    if value in (None, "") and allow_none: return None
    try: n = float(str(value).replace(",", "."))
    except Exception as exc: raise ValidationError(f"{label} deve ser numérico.") from exc
    if minimum is not None and n < minimum: raise ValidationError(f"{label} deve ser ≥ {minimum}.")
    if maximum is not None and n > maximum: raise ValidationError(f"{label} deve ser ≤ {maximum}.")
    return n

def integer(value, label, minimum=None, maximum=None, allow_none=False):
    n = number(value, label, minimum, maximum, allow_none)
    return None if n is None else int(n)

def iso_date(value, label="Data", allow_blank=False):
    text=(value or "").strip()
    if not text and allow_blank: return ""
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try: return datetime.strptime(text, fmt).date().isoformat()
        except ValueError: pass
    raise ValidationError(f"{label} deve estar em AAAA-MM-DD ou DD/MM/AAAA.")

def email(value):
    text=(value or "").strip()
    if text and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", text): raise ValidationError("E-mail inválido.")
    return text

def anthropometry(weight, height_cm, age_years):
    return {
        "peso": number(weight,"Peso",1,500),
        "altura_cm": number(height_cm,"Altura",30,250),
        "idade": number(age_years,"Idade",0,120),
    }
