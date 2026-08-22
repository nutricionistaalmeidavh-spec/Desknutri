from __future__ import annotations
from nutridesktop.data.repositories import LabRepository


def flag_result(value, ref_min=None, ref_max=None):
    if value in (None,''):
        return ''
    try:v=float(value)
    except (TypeError,ValueError):return ''
    if ref_min is not None and v<float(ref_min):return 'baixo'
    if ref_max is not None and v>float(ref_max):return 'alto'
    return 'normal'


def marker_series(patient_id, marker, repo=None):
    repo=repo or LabRepository()
    rows=list(repo.list_results(patient_id,marker))
    rows.reverse()
    return [
        {
            'date':r['data_coleta'],
            'value':r['value_numeric'] if r['value_numeric'] is not None else r['value_text'],
            'unit':r['unit'] or '',
            'flag':r['flag'] or flag_result(r['value_numeric'],r['ref_min'],r['ref_max']),
            'ref_min':r['ref_min'],'ref_max':r['ref_max'],'result_id':r['id'],'panel_id':r['panel_id'],
        }
        for r in rows
    ]
