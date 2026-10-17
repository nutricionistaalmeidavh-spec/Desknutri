"""Regression tests for clinical identity, imports and plan provenance."""
import csv
import pytest
from nutridesktop.data.database import Database
from nutridesktop.data.repositories import PatientRepository, AgendaRepository, PlanRepository, AssessmentRepository, LabRepository
from nutridesktop.services.import_center import preview_import, apply_import
from nutridesktop.services.consultations import complete_guided_consultation


def create_db(tmp_path):
    db = Database(tmp_path / "clinic.db")
    db.initialize()
    return db


def csv_file(path, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path


def test_guided_completion_reuses_existing_agenda_and_retries_safely(tmp_path):
    db = create_db(tmp_path)
    pid = PatientRepository(db).create("Ana", "F", "1990-01-01")
    appt = AgendaRepository(db).create(pid, "2026-11-12", "09:00")
    kwargs = dict(database=db, patient_id=pid, date_value="2026-11-12", time_value="09:00",
                  kind="Consulta", objective="Saúde", approach="Acompanhamento",
                  notes="Conduta", anamnesis="Anamnese teste", appointment_id=appt,
                  idempotency_key="consulta-ana-20261112")
    assert complete_guided_consultation(**kwargs) == appt
    assert complete_guided_consultation(**kwargs) == appt
    with db.connect() as c:
        assert c.execute("SELECT count(*) FROM consultas WHERE paciente_id=?", (pid,)).fetchone()[0] == 1
        assert c.execute("SELECT status FROM consultas WHERE id=?", (appt,)).fetchone()[0] == "Realizada"
        assert c.execute("SELECT count(*) FROM anamneses_paciente WHERE paciente_id=?", (pid,)).fetchone()[0] == 1


def test_failed_completion_rolls_back_every_record(tmp_path):
    db = create_db(tmp_path)
    pid = PatientRepository(db).create("Ana", "F", "1990-01-01")
    with pytest.raises(ValueError):
        complete_guided_consultation(database=db, patient_id=pid, date_value="2026-11-12",
            time_value="09:00", kind="Retorno", objective="Saúde", approach="Teste", notes="",
            anamnesis="Texto clínico", return_date="invalid-date", return_time="10:00",
            idempotency_key="rollback-1")
    with db.connect() as c:
        assert c.execute("SELECT count(*) FROM consultas").fetchone()[0] == 0
        assert c.execute("SELECT count(*) FROM anamneses_paciente").fetchone()[0] == 0


def test_plan_revision_never_creates_two_active_siblings(tmp_path):
    db = create_db(tmp_path)
    pid = PatientRepository(db).create("Ana", "F")
    plans = PlanRepository(db)
    root = plans.create(pid, "Plano base", 2000)
    second = plans.create_revision(root)
    third = plans.create_revision(root)
    with db.connect() as c:
        active = c.execute("SELECT id FROM planos WHERE paciente_id=? AND status='Ativo'", (pid,)).fetchall()
        assert [r["id"] for r in active] == [third]
    assert plans.list(pid)[0]["id"] == third


def test_importing_same_assessment_and_lab_twice_is_idempotent(tmp_path):
    db = create_db(tmp_path)
    pid = PatientRepository(db).create("Ana", "F", "1995-03-02", email="ana@example.com")
    assessments = csv_file(tmp_path / "ass.csv", [{"email":"ana@example.com","data":"2026-11-10","peso":"65.2","altura_cm":"167"}])
    labs = csv_file(tmp_path / "labs.csv", [{"email":"ana@example.com","data_coleta":"2026-11-10","painel":"Geral","marcador":"Glicemia","valor":"91","unidade":"mg/dL"}])
    assert apply_import(preview_import("assessments", assessments, db), db)["imported"] == 1
    assert apply_import(preview_import("assessments", assessments, db), db)["imported"] == 0
    assert len(AssessmentRepository(db).list(pid)) == 1
    assert apply_import(preview_import("labs", labs, db), db)["imported"] == 1
    assert apply_import(preview_import("labs", labs, db), db)["imported"] == 0
    assert len(LabRepository(db).list_results(pid)) == 1


def test_patient_duplicate_within_same_file_and_email_conflict(tmp_path):
    db = create_db(tmp_path)
    inp = csv_file(tmp_path / "patients.csv", [
        {"nome":"Ana", "sexo":"F", "data_nascimento":"1995-03-02", "email":"ana@example.com"},
        {"nome":"Ana", "sexo":"F", "data_nascimento":"1995-03-02", "email":"ana@example.com"}])
    preview = preview_import("patients", inp, db)
    assert len(preview.rows) == 1
    assert len(preview.skipped) == 1
    assert apply_import(preview, db)["imported"] == 1
    conflict = csv_file(tmp_path / "conflict.csv", [
        {"nome":"Outra Pessoa", "sexo":"F", "data_nascimento":"2001-08-08", "email":"ana@example.com"}])
    preview = preview_import("patients", conflict, db)
    assert preview.errors
    assert not preview.rows


def test_delivery_has_selected_plan_provenance(tmp_path):
    db = create_db(tmp_path)
    pid = PatientRepository(db).create("Ana", "F")
    plan_id = PlanRepository(db).create(pid, "Plano", 1900)
    cid = AgendaRepository(db).create(pid, "2026-11-12", "09:00")
    AgendaRepository(db).mark_plan_sent(cid, plan_id=plan_id)
    with db.connect() as c:
        row = c.execute("SELECT plano_id_enviado,plano_versao_enviada FROM consultas WHERE id=?", (cid,)).fetchone()
        assert row["plano_id_enviado"] == plan_id
        assert row["plano_versao_enviada"] == 1
