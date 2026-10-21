"""Regressão: prontuário acessível em notebooks no modo paisagem."""
from __future__ import annotations

from PySide6.QtWidgets import QApplication, QScrollArea

from nutridesktop.data.database import db
from nutridesktop.data.repositories import PatientRepository
from nutridesktop.ui.refined_patient_dialog import RefinedPatientDialog


def test_all_patient_workspace_tabs_scroll_at_notebook_dimensions(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(db, "path", tmp_path / "responsive-patient.db")
    db.initialize()
    pid = PatientRepository().create("Paciente de teste", "F", "1995-06-12")

    dialog = RefinedPatientDialog(pid)
    dialog.resize(860, 530)
    dialog.show()
    app.processEvents()

    assert dialog.tabs.count() == 6
    for index in range(dialog.tabs.count()):
        dialog.tabs.setCurrentIndex(index)
        app.processEvents()
        scroll = dialog.tabs.widget(index)
        assert isinstance(scroll, QScrollArea), (
            f"Aba {dialog.tabs.tabText(index)} precisa permitir rolagem "
            "sem exigir monitor em modo retrato"
        )
        assert scroll.widgetResizable()
        assert scroll.widget() is not None

    # Resumo é reconstruído ao retornar à primeira aba: mantém rolagem.
    dialog.tabs.setCurrentIndex(1)
    dialog.tabs.setCurrentIndex(0)
    app.processEvents()
    assert isinstance(dialog.tabs.widget(0), QScrollArea)
    dialog.close()


def test_prontuario_initial_size_respects_available_landscape_screen(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(db, "path", tmp_path / "patient-viewport.db")
    db.initialize()
    pid = PatientRepository().create("Paciente responsivo", "M", "1989-05-04")
    dialog = RefinedPatientDialog(pid)
    available = dialog.screen().availableGeometry()
    assert dialog.width() <= available.width()
    assert dialog.height() <= available.height()
    dialog.close()
