"""Exclusão segura de cadastro e guarda de prontuários do NutriDesk."""
from __future__ import annotations

import pytest

from nutridesktop.data.database import Database
from nutridesktop.data.migrations import migrate, current_version
from nutridesktop.data.repositories import PatientRepository, AssessmentRepository
from nutridesktop.version import SCHEMA_VERSION


def test_schema_upgrade_preserves_patients_and_adds_archive_flag(tmp_path):
    db = Database(tmp_path / "existing.db")
    with db.connect() as conn:
        migrate(conn, 14)
        conn.execute("INSERT INTO pacientes(nome,sexo) VALUES('Paciente antigo','F')")
        conn.commit()
    assert db.initialize() == SCHEMA_VERSION
    with db.connect() as conn:
        assert current_version(conn) == SCHEMA_VERSION
        row = conn.execute("SELECT nome, arquivado_em FROM pacientes").fetchone()
        assert (row["nome"], row["arquivado_em"]) == ("Paciente antigo", None)


def test_delete_registration_without_clinical_records(tmp_path):
    db = Database(tmp_path / "blank.db")
    db.initialize()
    patients = PatientRepository(db)
    pid = patients.create("Cadastro incorreto", "F", "2000-01-01")
    assert patients.can_delete(pid)
    assert patients.remove(pid) == "deleted"
    assert patients.get(pid) is None
    assert not patients.list()
    with db.connect() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM timeline_events WHERE paciente_id=?", (pid,)
        ).fetchone()[0] == 0
        event = conn.execute(
            "SELECT action, details_json FROM audit_log "
            "WHERE entity_type='paciente' AND entity_id=? ORDER BY id DESC LIMIT 1",
            (pid,),
        ).fetchone()
        assert event["action"] == "delete_registration"
        assert "Cadastro incorreto" not in event["details_json"]


def test_delete_existing_consultation_archives_without_data_loss(tmp_path):
    db = Database(tmp_path / "history.db")
    db.initialize()
    patients = PatientRepository(db)
    pid = patients.create("Com prontuário", "M", "1991-01-01")
    AssessmentRepository(db).create(
        pid, {"data": "2026-10-20", "peso": 72, "altura_cm": 176, "idade": 35, "imc": 23.2}
    )
    assert not patients.can_delete(pid)
    assert patients.remove(pid) == "archived"
    assert not patients.list()
    assert [p["id"] for p in patients.list(archived=True)] == [pid]
    assert patients.get(pid)["arquivado_em"]
    assert len(AssessmentRepository(db).list(pid)) == 1
    assert patients.restore(pid)
    assert [p["id"] for p in patients.list()] == [pid]
    assert patients.list(archived=True) == []
    assert len(AssessmentRepository(db).list(pid)) == 1


def test_additional_timeline_event_blocks_destructive_deletion(tmp_path):
    db = Database(tmp_path / "timeline.db")
    db.initialize()
    patients = PatientRepository(db)
    pid = patients.create("Paciente acompanhado", "F")
    with db.transaction() as conn:
        conn.execute(
            "INSERT INTO timeline_events(paciente_id,event_type,event_date,title,entity_id) "
            "VALUES(?,?,?,?,?)",
            (pid, "orientacao", "2026-10-21", "Acompanhamento clínico", pid),
        )
    assert patients.remove(pid) == "archived"
    with db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM timeline_events WHERE paciente_id=?", (pid,)).fetchone()[0] == 2


def test_missing_patient_cannot_be_removed_or_restored(tmp_path):
    db = Database(tmp_path / "missing.db")
    db.initialize()
    patients = PatientRepository(db)
    with pytest.raises(ValueError, match="não localizado"):
        patients.remove(999999)
    with pytest.raises(ValueError, match="não localizado"):
        patients.restore(999999)


def test_ui_exposes_explicit_delete_archive_and_restore_actions():
    from pathlib import Path
    source = (Path(__file__).resolve().parents[1] / "nutridesktop/ui/refinement.py").read_text(encoding="utf-8")
    assert 'button("Excluir paciente", self.remove_selected_patient' in source
    assert 'button("Restaurar paciente", self.restore_selected_patient' in source
    assert "QMessageBox.question(" in source
    assert "Mostrar arquivados" in source


def test_ui_selected_patient_delete_and_restore_workflow(tmp_path, monkeypatch):
    from PySide6.QtWidgets import QApplication, QMessageBox
    from nutridesktop.data.database import db
    from nutridesktop.ui.application_window import MainWindow

    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(db, "path", tmp_path / "ui-patients.db")
    db.initialize()
    patients = PatientRepository(db)
    wrong = patients.create("Cadastro lançado por engano", "F", "2001-05-01")
    history = patients.create("Paciente com histórico", "M", "1988-09-09")
    AssessmentRepository(db).create(
        history, {"data": "2026-10-21", "peso": 76, "altura_cm": 178, "idade": 38, "imc": 24}
    )
    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.Yes)
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: pytest.fail("UI warning"))

    window = MainWindow()
    window.show_page("Pacientes")
    for pid in (wrong, history):
        target = next(
            i for i in range(window.patient_table.rowCount())
            if int(window.patient_table.item(i, 0).text()) == pid
        )
        window.patient_table.selectRow(target)
        window.remove_selected_patient()

    assert patients.get(wrong) is None
    assert patients.get(history)["arquivado_em"] is not None
    window.show_archived_patients.setChecked(True)
    assert window.patient_table.rowCount() == 1
    window.patient_table.selectRow(0)
    window.restore_selected_patient()
    assert patients.get(history)["arquivado_em"] is None
    assert patients.list(archived=True) == []
    window.close()
