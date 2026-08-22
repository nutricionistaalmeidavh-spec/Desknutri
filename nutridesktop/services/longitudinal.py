from __future__ import annotations
from collections import defaultdict
from nutridesktop.data.repositories import PatientRepository,AssessmentRepository,AgendaRepository,PlanRepository,LabRepository,ClinicalPackRepository
from nutridesktop.services.labs import marker_series


def build_patient_comparison(patient_id,database=None):
    pr=PatientRepository(database) if database else PatientRepository()
    db=pr.db
    patient=pr.get(patient_id)
    if not patient:raise ValueError('Paciente não encontrado.')
    assessments=[dict(r) for r in AssessmentRepository(db).list(patient_id)]
    with db.connect() as c:
        consultations=[dict(r) for r in c.execute("SELECT * FROM consultas WHERE paciente_id=? ORDER BY data,hora,id",(patient_id,)).fetchall()]
    plans=[dict(r) for r in PlanRepository(db).list(patient_id)]
    lab_repo=LabRepository(db);by_marker=defaultdict(list)
    for r in lab_repo.list_results(patient_id):by_marker[r['marker_name']].append(r)
    labs={m:marker_series(patient_id,m,lab_repo) for m in sorted(by_marker)}
    packs={}
    pack_repo=ClinicalPackRepository(db)
    for active in pack_repo.active(patient_id):
        packs[active['pack_slug']]=[
            {**dict(r),'data_json':__import__('json').loads(r['data_json'] or '{}')}
            for r in reversed(pack_repo.records(patient_id,active['pack_slug']))
        ]
    return {'patient':dict(patient),'assessments':assessments,'labs':labs,'consultations':consultations,'plans':plans,'packs':packs}
