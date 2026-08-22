from __future__ import annotations
from collections import OrderedDict
from datetime import date,datetime

NAV_GROUPS=OrderedDict([
    ('TRABALHO',['Dashboard','Pacientes','Agenda']),
    ('CONTEÚDO',['Biblioteca']),
    ('SISTEMA',['Conta','Configurações']),
])


def age_on(birth: str|None, on_date: date|None=None) -> int|None:
    if not birth:return None
    try:b=date.fromisoformat(str(birth)[:10])
    except Exception:return None
    d=on_date or date.today()
    return d.year-b.year-((d.month,d.day)<(b.month,b.day))


def age_label(birth: str|None, on_date: date|None=None) -> str:
    age=age_on(birth,on_date)
    return 'Idade não informada' if age is None else f'{age} anos'


def friendly_error(exc: BaseException) -> str:
    if exc.__class__.__name__ in {'ValidationError','AccountLicenseError'} and str(exc):return str(exc)
    raw=str(exc or '').lower()
    if isinstance(exc,(ConnectionError,TimeoutError)) or any(k in raw for k in ('connection','timeout','timed out','network','httpsconnectionpool','urlopen')):
        return 'Não foi possível acessar o serviço. Verifique sua conexão com a internet e tente novamente.'
    if 'permission' in raw or 'access denied' in raw:
        return 'O NutriDesk não tem permissão para concluir esta operação. Verifique o acesso ao arquivo ou pasta.'
    if 'locked' in raw and 'database' in raw:
        return 'Os dados estão temporariamente ocupados. Aguarde alguns segundos e tente novamente.'
    return 'Não foi possível concluir a operação. Tente novamente; se o problema continuar, abra Suporte em Configurações.'


def consultation_counts(appointments, pending_plans=()):
    rows=list(appointments)
    return {'today':len(rows),'pending_plans':len(list(pending_plans))}
