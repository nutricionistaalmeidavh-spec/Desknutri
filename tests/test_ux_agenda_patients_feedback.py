"""Regressões de usabilidade em pacientes e agenda; execução Qt offscreen na CI."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QMessageBox,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from nutridesktop.ui.design_system import EmptyState
from nutridesktop.ui.refinement import UiRefinementMixin


def _app():
    return QApplication.instance() or QApplication([])


class _AgendaRepository:
    def __init__(self):
        self.calls = []
        self.fail = False
        self.statuses = []

    def list(self, start, end, status):
        self.calls.append((start, end, status))
        if self.fail:
            raise RuntimeError("não pode aparecer detalhe técnico")
        return [{
            "id": 7,
            "data": start,
            "hora": "09:00",
            "paciente_nome": "Paciente Exemplo",
            "tipo": "Retorno",
            "status": "Agendada",
            "duracao_min": 45,
        }]

    def set_status(self, appointment_id, status):
        self.statuses.append((appointment_id, status))


class _AgendaCore:
    def set_appointment_status(self, status):
        row = self.ag_table.currentRow()
        self.ag.set_status(int(self.ag_table.item(row, 0).text()), status)
        self.refresh_agenda()


class _AgendaHarness(UiRefinementMixin, _AgendaCore):
    def __init__(self):
        self.ag = _AgendaRepository()

    def page(self, _title, _subtitle=""):
        page = QWidget()
        return page, QVBoxLayout(page)

    def new_appointment(self):
        pass


def test_agenda_requires_explicit_selection_and_blocks_inverted_dates():
    _app()
    harness = _AgendaHarness()
    page = harness.agenda()
    assert page is not None
    assert harness.ag_table.editTriggers() == QAbstractItemView.NoEditTriggers
    assert harness.ag_table.rowCount() == 1
    assert all(not action.isEnabled() for action in harness.agenda_status_buttons.values())

    harness.ag_table.selectRow(0)
    assert all(action.isEnabled() for action in harness.agenda_status_buttons.values())
    assert "Paciente Exemplo" in harness.agenda_selection_hint.text()

    calls_before = len(harness.ag.calls)
    harness.ag_end.setDate(harness.ag_start.date().addDays(-1))
    harness.refresh_agenda()
    assert len(harness.ag.calls) == calls_before
    assert "data final" in harness.agenda_feedback.text()
    assert harness.agenda_feedback.isVisibleTo(page)
    assert not harness.agenda_empty.isVisibleTo(page)
    assert all(not action.isEnabled() for action in harness.agenda_status_buttons.values())


def test_agenda_error_is_not_reported_as_empty_result():
    _app()
    harness = _AgendaHarness()
    page = harness.agenda()
    harness.ag.fail = True
    harness.refresh_agenda()
    assert "Não foi possível carregar" in harness.agenda_feedback.text()
    assert "detalhe técnico" not in harness.agenda_feedback.text()
    assert not harness.agenda_empty.isVisibleTo(page)
    assert not any(a.isEnabled() for a in harness.agenda_status_buttons.values())


class _PatientRepository:
    def list(self, query=""):
        patients = [
            {"id": 1, "nome": "Ana Exemplo", "sexo": "F", "data_nascimento": "1994-01-01", "telefone": ""},
            {"id": 2, "nome": "Bruna Exemplo", "sexo": "F", "data_nascimento": "1995-01-01", "telefone": ""},
        ]
        return [p for p in patients if query.casefold() in p["nome"].casefold()]


class _PatientCore:
    def refresh_patients(self):
        rows = self.pr.list(self.patient_search.text())
        self.patient_table.setRowCount(len(rows))
        self.patient_table.setVisible(bool(rows))
        self.patient_empty.setVisible(not bool(rows))
        for r, patient in enumerate(rows):
            for c, value in enumerate((
                patient["id"], patient["nome"], patient["sexo"],
                patient["data_nascimento"], patient["telefone"]
            )):
                self.patient_table.setItem(r, c, QTableWidgetItem(str(value)))


class _PatientHarness(UiRefinementMixin, _PatientCore):
    def __init__(self):
        self.pr = _PatientRepository()
        self.opened = []

    def page(self, _title, _subtitle=""):
        page = QWidget()
        return page, QVBoxLayout(page)

    def new_patient(self):
        pass

    def new_consultation(self):
        pass

    def _open_patient_id(self, patient_id):
        self.opened.append(patient_id)


def test_patient_search_clears_old_selection_and_explains_zero_results():
    _app()
    harness = _PatientHarness()
    page = harness.patients()
    assert page is not None
    assert harness.patient_table.editTriggers() == QAbstractItemView.NoEditTriggers
    assert harness.patient_count.text() == "2 pacientes cadastrados"
    assert not harness.open_patient_button.isEnabled()

    harness.patient_table.selectRow(0)
    assert harness.open_patient_button.isEnabled()
    harness.patient_search.setText("Bruna")
    assert harness.patient_table.rowCount() == 1
    assert harness.patient_count.text() == "1 paciente encontrado"
    assert not harness.open_patient_button.isEnabled()
    harness.patient_table.selectRow(0)
    harness.open_patient()
    assert harness.opened == [2]

    harness.patient_search.setText("Inexistente")
    assert harness.patient_table.rowCount() == 0
    assert harness.patient_empty.title_label.text() == "Nenhum resultado para a busca"
    assert not harness.open_patient_button.isEnabled()


def test_empty_state_updates_content_without_duplicate_widgets():
    _app()
    state = EmptyState("Vazio", "Primeira mensagem")
    original_count = state.body.count()
    state.set_content("Resultado vazio", "Ajuste o filtro")
    assert state.title_label.text() == "Resultado vazio"
    assert state.message_label.text() == "Ajuste o filtro"
    assert state.body.count() == original_count


def test_agenda_requires_confirmation_before_absence_or_cancellation(monkeypatch):
    _app()
    harness = _AgendaHarness()
    page = harness.agenda()
    assert page is not None
    harness.set_appointment_status("Realizada")
    assert harness.ag.statuses == []
    harness.ag_table.selectRow(0)

    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.No)
    harness.set_appointment_status("Cancelada")
    assert harness.ag.statuses == []

    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.Yes)
    harness.set_appointment_status("Faltou")
    assert harness.ag.statuses == [(7, "Faltou")]
    assert not any(a.isEnabled() for a in harness.agenda_status_buttons.values())


def test_global_search_aliases_reach_operational_pages():
    assert UiRefinementMixin.PAGE_ALIASES["atualizações"] == "Atualizações"
    assert UiRefinementMixin.PAGE_ALIASES["exportacoes"] == "Exportações"
    assert UiRefinementMixin.PAGE_ALIASES["suporte"] == "Suporte"
