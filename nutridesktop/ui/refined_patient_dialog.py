"""Refino visual do prontuário sem duplicar regras clínicas do PatientDialog."""
from __future__ import annotations

from datetime import date, datetime, timedelta

from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from .common import button
from .design_system import Card, StatCard, muted, section_title
from .patient_dialog import PatientDialog as CorePatientDialog
from .view_models import age_label, age_on
from nutridesktop.ui_kit.components import PatientHeader, TimelineItem


class RefinedPatientDialog(CorePatientDialog):
    """Aplica PatientHeader e timeline canônica ao prontuário existente.

    Todos os tabs, repositories, cálculos e callbacks continuam pertencendo ao
    PatientDialog original. Esta classe altera apenas composição e apresentação.
    """

    def __init__(self, pid, parent=None):
        super().__init__(pid, parent)
        root = self.layout()
        old_header_item = root.takeAt(0)
        old_header = old_header_item.layout() if old_header_item else None
        if old_header:
            while old_header.count():
                child = old_header.takeAt(0)
                widget = child.widget()
                if widget:
                    widget.deleteLater()
        self.patient_header = PatientHeader(
            on_new_consultation=self.open_guided_consultation,
            on_edit=self.open_profile_editor,
            parent=self,
        )
        root.insertWidget(0, self.patient_header)
        self.refresh_header()

    def refresh_header(self):
        p = self.pr.get(self.pid)
        name = p["nome"] if p else "Paciente"
        meta = ""
        if p:
            sex = "Feminino" if p["sexo"] == "F" else "Masculino"
            meta = f"{age_label(p['data_nascimento'])}  •  {sex}  •  {p['telefone'] or 'sem telefone'}"
        if hasattr(self, "patient_header"):
            self.patient_header.set_patient(name, meta, self._next_appointment_text())
            return
        # Durante o __init__ da classe-base o cabeçalho canônico ainda não existe.
        if hasattr(self, "title"):
            self.title.setText(name)
        if hasattr(self, "header_meta"):
            self.header_meta.setText(meta)

    def _next_appointment_text(self) -> str:
        today = date.today()
        try:
            rows = self.ag.list(today.isoformat(), (today + timedelta(days=365)).isoformat())
        except Exception:
            return ""
        applicable = [
            row
            for row in rows
            if int(row["paciente_id"]) == int(self.pid)
            and row["status"] in {"Agendada", "Remarcada"}
        ]
        if not applicable:
            return "Sem retorno agendado"
        nxt = applicable[0]
        raw_date = str(nxt["data"])
        try:
            display_date = datetime.strptime(raw_date[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError:
            display_date = raw_date
        return f"Próximo atendimento: {display_date} às {nxt['hora']}"

    def summary_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 8, 0, 0)
        lay.setSpacing(12)
        p = self.pr.get(self.pid)
        assessments = self.ar.list(self.pid)
        latest = assessments[-1] if assessments else None
        plans = self.pl.list(self.pid)
        timeline = self.tr.list(self.pid)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.addWidget(
            StatCard(
                "Peso",
                f"{latest['peso']:.1f} kg" if latest and latest["peso"] is not None else "—",
                "Última avaliação",
            ),
            0,
            0,
        )
        grid.addWidget(
            StatCard(
                "IMC",
                f"{latest['imc']:.1f}" if latest and latest["imc"] is not None else "—",
                "Última avaliação",
            ),
            0,
            1,
        )
        grid.addWidget(
            StatCard(
                "Gordura corporal",
                f"{latest['pg_final']:.1f}%" if latest and latest["pg_final"] is not None else "—",
                "Composição corporal",
            ),
            0,
            2,
        )
        grid.addWidget(
            StatCard("Plano atual", plans[0]["nome"] if plans else "Nenhum", "Plano alimentar"),
            0,
            3,
        )
        lay.addLayout(grid)

        cols = QHBoxLayout()
        cols.setSpacing(12)
        left = Card()
        left.body.addWidget(section_title("Linha do tempo clínica"))
        if timeline:
            for event in timeline[:8]:
                detail = str(event.get("event_type", "")).replace("_", " ").capitalize()
                left.body.addWidget(
                    TimelineItem(
                        event.get("event_date", ""),
                        event.get("title", "Registro clínico"),
                        detail,
                    )
                )
        else:
            left.body.addWidget(
                muted("O histórico clínico aparecerá aqui conforme os atendimentos forem registrados.")
            )
        cols.addWidget(left, 2)

        right = Card()
        right.body.addWidget(section_title("Ações clínicas"))
        patient_age = age_on(p["data_nascimento"]) if p else None
        if patient_age is not None and patient_age <= 19:
            right.body.addWidget(button("Crescimento WHO", self.open_growth_context, variant="ghost"))
        if p and p["sexo"] == "F":
            right.body.addWidget(button("Gestação / lactação", self.open_maternal_context, variant="ghost"))
        right.body.addWidget(button("Exames laboratoriais", self.open_labs, variant="ghost"))
        right.body.addWidget(button("Packs clínicos", self.open_clinical_packs, variant="ghost"))
        right.body.addWidget(button("Comparação longitudinal", self.show_longitudinal_comparison, variant="ghost"))
        right.body.addWidget(button("Enviar via WhatsApp", self.open_whatsapp, variant="ghost"))
        right.body.addWidget(button("Gerar relatório", lambda: self.tabs.setCurrentIndex(5), variant="ghost"))
        right.body.addStretch()
        cols.addWidget(right, 1)
        lay.addLayout(cols)
        lay.addStretch()
        return w
