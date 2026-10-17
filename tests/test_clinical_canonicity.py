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


def test_transaction_rolls_back_if_anamnesis_write_fails(tmp_path):
    import sqlite3
    db = create_db(tmp_path)
    pid = PatientRepository(db).create("Falha", "F")
    with db.transaction() as c:
        c.execute("""CREATE TRIGGER reject_guided_anamnesis BEFORE INSERT ON anamneses_paciente
                     BEGIN SELECT RAISE(FAIL, 'forced error'); END""")
    with pytest.raises(sqlite3.IntegrityError):
        complete_guided_consultation(database=db, patient_id=pid,
            date_value="2026-11-15", time_value="13:00", kind="Consulta",
            anamnesis="Observação importante", idempotency_key="force-failure")
    with db.connect() as c:
        assert c.execute("SELECT COUNT(*) FROM consultas").fetchone()[0] == 0
        assert c.execute("SELECT COUNT(*) FROM manual_pending_actions").fetchone()[0] == 0


def test_guided_completion_reuses_matching_scheduled_slot_without_explicit_id(tmp_path):
    db = create_db(tmp_path)
    pid = PatientRepository(db).create("Ana", "F")
    scheduled = AgendaRepository(db).create(pid, "2026-11-20", "13:00")
    actual = complete_guided_consultation(database=db, patient_id=pid,
        date_value="2026-11-20", time_value="13:00", kind="Consulta",
        idempotency_key="match-existing")
    assert actual == scheduled


def test_existing_plan_cannot_be_assigned_to_other_patient(tmp_path):
    db = create_db(tmp_path)
    ana = PatientRepository(db).create("Ana", "F")
    bia = PatientRepository(db).create("Bia", "F")
    plan_id = PlanRepository(db).create(ana, "Plano Ana", 2100)
    cid = AgendaRepository(db).create(bia, "2026-11-21", "08:00")
    with pytest.raises(ValueError):
        AgendaRepository(db).mark_plan_sent(cid, plan_id=plan_id)
    with pytest.raises(ValueError):
        complete_guided_consultation(database=db, patient_id=bia,
            date_value="2026-11-21", time_value="08:00", kind="Consulta",
            appointment_id=cid, plan_id=plan_id, plan_delivered=True,
            idempotency_key="wrong-patient")
    with db.connect() as c:
        row = c.execute("SELECT status,plano_enviado_em FROM consultas WHERE id=?", (cid,)).fetchone()
        assert row["status"] == "Agendada"
        assert row["plano_enviado_em"] is None


def test_measurement_read_model_keeps_its_source(tmp_path):
    db = create_db(tmp_path)
    pid = PatientRepository(db).create("Ana", "F")
    AssessmentRepository(db).create(pid, {"data":"2026-01-01", "peso":65, "altura_cm":170})
    with db.transaction() as c:
        c.execute("""INSERT INTO growth_measurements(paciente_id,data,idade_dias,peso,altura_cm)
                     VALUES(?,?,?,?,?)""", (pid,"2026-05-01",1000,67,171))
    latest = AssessmentRepository(db).latest_body_measurement(pid)
    assert latest["peso"] == 67
    assert latest["origem"] == "Crescimento WHO"


def test_deferred_tasks_resolve_only_when_work_is_saved(tmp_path):
    db = create_db(tmp_path)
    pid = PatientRepository(db).create("Ana", "F")
    complete_guided_consultation(database=db, patient_id=pid,
        date_value="2026-11-21",time_value="11:00",kind="Consulta",
        request_reassessment=True,request_plan_update=True,idempotency_key="pending-tasks")
    with db.connect() as c:
        assert c.execute("SELECT COUNT(*) FROM manual_pending_actions WHERE resolved_at IS NULL").fetchone()[0] == 2
    AssessmentRepository(db).create(pid,{"data":"2026-11-21","peso":62.0})
    with db.connect() as c:
        pending = c.execute("SELECT kind FROM manual_pending_actions WHERE resolved_at IS NULL").fetchall()
        assert [x["kind"] for x in pending] == ["plan_update_after_consultation"]
    PlanRepository(db).create(pid, "Plano novo", 2000)
    with db.connect() as c:
        assert c.execute("SELECT COUNT(*) FROM manual_pending_actions WHERE resolved_at IS NULL").fetchone()[0] == 0


def test_schema_14_reconciles_legacy_multiple_active_versions(tmp_path):
    from nutridesktop.data.migrations import migrate
    db = Database(tmp_path / "legacy.db")
    with db.connect() as c:
        migrate(c, target=13)
        pid = c.execute("INSERT INTO pacientes(nome,sexo) VALUES('Ana','F')").lastrowid
        root = c.execute("INSERT INTO planos(paciente_id,nome,status,version_no) VALUES(?,'Base','Ativo',1)", (pid,)).lastrowid
        c.execute("INSERT INTO planos(paciente_id,nome,status,parent_plan_id,version_no) VALUES(?,'V2','Ativo',?,2)", (pid,root))
        c.commit()
    db.initialize()
    with db.connect() as c:
        rows = c.execute("SELECT status FROM planos ORDER BY id").fetchall()
        assert [x["status"] for x in rows] == ["Histórico", "Ativo"]
