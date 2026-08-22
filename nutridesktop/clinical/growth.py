"""WHO 2006/2007 growth adapter using packaged LMS reference data.

The runtime dependency `pygrowthstandards` embeds pre-processed WHO reference
records for 0-19 years. We call its functional z-score/percentile API rather
than maintaining approximate medians in application code.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import erf,sqrt

@dataclass
class GrowthResult:
    indicator:str; zscore:float|None; percentile:float|None; classification:str; source:str="WHO 2006/2007"

def _classify(ind,z):
    if z is None:return "Não calculado"
    if ind=="bmi":
        if z < -3:return "Magreza acentuada"
        if z < -2:return "Magreza"
        if z <= 1:return "Eutrofia"
        if z <= 2:return "Sobrepeso"
        if z <= 3:return "Obesidade"
        return "Obesidade grave"
    if ind=="stature":
        if z < -3:return "Muito baixa estatura para idade"
        if z < -2:return "Baixa estatura para idade"
        return "Estatura adequada para idade"
    if ind=="weight":
        if z < -3:return "Muito baixo peso para idade"
        if z < -2:return "Baixo peso para idade"
        if z <= 2:return "Peso adequado para idade"
        return "Peso elevado para idade"
    if ind=="weight_stature":
        if z < -3:return "Magreza acentuada"
        if z < -2:return "Magreza"
        if z <= 1:return "Eutrofia"
        if z <= 2:return "Risco de sobrepeso"
        if z <= 3:return "Sobrepeso"
        return "Obesidade"
    return "Sem classificação"

def _api():
    try:
        from pygrowthstandards import functional
        return functional
    except ImportError as exc:
        raise RuntimeError("Instale pygrowthstandards>=0.1.3 para cálculos WHO oficiais.") from exc

def assess(sex:str,age_days:int,weight_kg=None,height_cm=None):
    if sex not in {"M","F"}: raise ValueError("Sexo deve ser M ou F")
    if age_days<0 or age_days>int(19*365.25)+10: raise ValueError("WHO 2006/2007 suportado até 19 anos")
    api=_api(); out={}
    def calc(alias,value,indicator,**kwargs):
        if value is None:return None
        z=float(api.zscore(alias,float(value),sex,age_days=age_days,**kwargs))
        # Package percentile returns normal CDF in [0,1].
        p=float(api.percentile(alias,float(value),sex,age_days=age_days,**kwargs))*100
        return GrowthResult(indicator,z,p,_classify(indicator,z))
    if weight_kg is not None:
        try: out["weight_age"]=calc("weight",weight_kg,"weight")
        except (ValueError,KeyError): out["weight_age"]=None
    if height_cm is not None:
        out["height_age"]=calc("stature",height_cm,"stature")
    if weight_kg is not None and height_cm is not None:
        bmi=weight_kg/(height_cm/100)**2; out["bmi_age"]=calc("bmi",bmi,"bmi")
        if age_days <= int(5*365.25):
            out["weight_height"]=calc("weight_stature",weight_kg,"weight_stature",x_var_type="stature",x_value=height_cm)
    return out
