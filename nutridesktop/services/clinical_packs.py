from __future__ import annotations
from nutridesktop.clinical.packs import PACK_DEFINITIONS,pack_defaults,SIBO_STATUSES
from nutridesktop.data.repositories import ClinicalPackRepository


def normalize_bristol(value):
    try:v=int(round(float(value)))
    except (TypeError,ValueError):v=4
    return min(7,max(1,v))


def normalize_symptom_score(value):
    try:v=int(round(float(value)))
    except (TypeError,ValueError):v=0
    return min(10,max(0,v))


def normalize_sibo_status(value):
    if value not in SIBO_STATUSES:raise ValueError('Status SIBO inválido para registro clínico.')
    return value


def normalize_pack_data(slug,data):
    if slug not in PACK_DEFINITIONS:raise KeyError(slug)
    merged=pack_defaults(slug);merged.update(dict(data or {}))
    if slug=='gastrointestinal':merged['bristol']=normalize_bristol(merged.get('bristol'))
    if slug=='sibo':
        merged['status']=normalize_sibo_status(merged.get('status'))
        merged['score_sintomas']=normalize_symptom_score(merged.get('score_sintomas'))
    return merged


def save_pack_snapshot(patient_id,slug,data,record_date=None,repo=None):
    repo=repo or ClinicalPackRepository();repo.activate(patient_id,slug)
    normalized=normalize_pack_data(slug,data)
    return repo.save_record(patient_id,slug,normalized,record_date)


def latest_pack_snapshot(patient_id,slug,repo=None):
    repo=repo or ClinicalPackRepository();row=repo.latest_record(patient_id,slug)
    if not row:return None
    payload=dict(row.pop('data_json',{}) or {})
    payload.update({'id':row['id'],'record_date':row['record_date'],'pack_slug':row['pack_slug']})
    return payload
