from __future__ import annotations
from .dri_lifecycle import recommendations
FAIXAS=[('Baixo peso',-1e9,18.5,12.5,18.0),('Peso adequado',18.5,25,11.5,16.0),('Sobrepeso',25,30,7.0,11.5),('Obesidade',30,1e9,5.0,9.0)]
ENERGY_EXTRA={'1º trimestre':0,'2º trimestre':340,'3º trimestre':452,'Lactação 0-6 meses':500}
def gestational_weight_range(pre_bmi):
    for name,lo,hi,gmin,gmax in FAIXAS:
        if lo<=pre_bmi<hi:return {'classification':name,'gain_min':gmin,'gain_max':gmax}
def maternal_reference(phase):
    if phase.startswith('Lactação'):return {'energy_extra_kcal':ENERGY_EXTRA[phase],'dri':recommendations(30,'F',lactating=True)}
    return {'energy_extra_kcal':ENERGY_EXTRA[phase],'dri':recommendations(30,'F',pregnant=True)}

def gestational_weight_progress(pre_weight,current_weight,pre_bmi):
    pre=float(pre_weight);current=float(current_weight);bmi=float(pre_bmi)
    ref=gestational_weight_range(bmi) or {}
    gain=round(current-pre,2)
    return {'pre_bmi':bmi,'gain_kg':gain,'classification':ref.get('classification',''),'recommended_total_min':ref.get('gain_min'),'recommended_total_max':ref.get('gain_max')}
