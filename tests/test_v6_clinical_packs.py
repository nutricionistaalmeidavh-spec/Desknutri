from nutridesktop.data.database import Database
from nutridesktop.data.repositories import PatientRepository,ClinicalPackRepository


def make_db(tmp_path):
    db=Database(tmp_path/'packs.db');db.initialize();return db


def test_all_v6_pack_definitions_and_sibo_is_non_diagnostic():
    from nutridesktop.clinical.packs import PACK_DEFINITIONS,pack_defaults,SIBO_STATUSES
    assert set(PACK_DEFINITIONS)=={'materno_infantil','esportiva','metabolica','renal','bariatrica','gastrointestinal','sibo'}
    assert 'diagnostico_automatico' not in pack_defaults('sibo')
    assert SIBO_STATUSES==('suspeito_registrado','encaminhado','confirmado_por_registro_externo','resolvido')
    for slug in PACK_DEFINITIONS:
        assert PACK_DEFINITIONS[slug]['label']
        assert isinstance(pack_defaults(slug),dict)


def test_pack_snapshots_preserve_unknown_fields(tmp_path):
    from nutridesktop.services.clinical_packs import save_pack_snapshot,latest_pack_snapshot
    db=make_db(tmp_path);pid=PatientRepository(db).create('A','F','1990-01-01')
    rid=save_pack_snapshot(pid,'gastrointestinal',{'bristol':4,'campo_futuro':'preservar'},'2026-08-01',ClinicalPackRepository(db))
    snap=latest_pack_snapshot(pid,'gastrointestinal',ClinicalPackRepository(db))
    assert snap['id']==rid and snap['campo_futuro']=='preservar' and snap['bristol']==4


def test_maternal_and_gi_helpers_are_bounded():
    from nutridesktop.clinical.maternal import gestational_weight_progress
    from nutridesktop.services.clinical_packs import normalize_bristol,normalize_symptom_score,normalize_sibo_status
    p=gestational_weight_progress(60,66,22)
    assert p['gain_kg']==6
    assert p['pre_bmi']==22
    assert normalize_bristol(0)==1 and normalize_bristol(9)==7
    assert normalize_symptom_score(-2)==0 and normalize_symptom_score(14)==10
    assert normalize_sibo_status('confirmado_por_registro_externo')=='confirmado_por_registro_externo'
