from __future__ import annotations

from uuid import uuid4
from PySide6.QtCore import QDate, QTime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QDateEdit,
    QTimeEdit, QTextEdit, QCheckBox, QStackedWidget, QWidget, QFormLayout,
)
from .common import button, show_error
from .design_system import muted
from nutridesktop.data.repositories import PlanRepository
from nutridesktop.services.consultations import complete_guided_consultation

CONSULTATION_STEPS = [
    "Dados da consulta", "Anamnese", "Avaliação", "Plano alimentar",
    "Orientações", "Retorno",
]


class ConsultationDialog(QDialog):
    def __init__(self, patients, agenda_repo, parent=None, patient_id=None):
        super().__init__(parent)
        self.patients = list(patients)
        self.ag = agenda_repo
        self.plans = PlanRepository(self.ag.db)
        self.created_consultation_id = None
        self.post_finish_focus = None
        self._completion_key = str(uuid4())
        self._submitting = False
        self.setWindowTitle("Consulta guiada • NutriDesk")
        self.resize(980, 700)
        root = QVBoxLayout(self)
        head = QHBoxLayout()
        head.addWidget(QLabel("Consulta guiada"))
        head.addStretch()
        self.step_label = QLabel()
        head.addWidget(self.step_label)
        root.addLayout(head)
        self.progress = QLabel()
        root.addWidget(self.progress)
        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)
        self._build_steps(patient_id)
        nav = QHBoxLayout()
        self.back = button("Voltar", self.previous)
        self.next = button("Avançar", self.advance, True)
        nav.addWidget(self.back)
        nav.addStretch()
        nav.addWidget(button("Cancelar", self.reject))
        nav.addWidget(self.next)
        root.addLayout(nav)
        self._sync()

    def _build_steps(self, patient_id):
        page = QWidget()
        form = QFormLayout(page)
        self.patient = QComboBox()
        for patient in self.patients:
            self.patient.addItem(patient["nome"], patient["id"])
        if patient_id is not None:
            index = self.patient.findData(patient_id)
            if index >= 0:
                self.patient.setCurrentIndex(index)
        self.appointment = QComboBox()
        self.appointment.setToolTip(
            "Escolha o agendamento existente para concluir sem duplicá-lo."
        )
        self.when = QDateEdit()
        self.when.setCalendarPopup(True)
        self.when.setDate(QDate.currentDate())
        self.time = QTimeEdit()
        self.time.setTime(QTime.currentTime())
        self.kind = QComboBox()
        self.kind.addItems(["Consulta inicial", "Retorno", "Teleconsulta"])
        self.objective = QComboBox()
        self.objective.setEditable(True)
        self.objective.addItems(["Emagrecimento", "Ganho de massa", "Reeducação alimentar", "Saúde geral"])
        self.approach = QComboBox()
        self.approach.setEditable(True)
        self.approach.addItems(["Alimentação equilibrada", "Plano individualizado", "Educação nutricional"])
        for label, control in (
            ("Paciente", self.patient), ("Agendamento", self.appointment),
            ("Data", self.when), ("Hora", self.time), ("Tipo", self.kind),
            ("Objetivo principal", self.objective), ("Abordagem nutricional", self.approach),
        ):
            form.addRow(label, control)
        self.stack.addWidget(page)

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(muted("A anamnese será registrada como nova versão no prontuário ao concluir."))
        self.anamnesis = QTextEdit()
        self.anamnesis.setPlaceholderText("Queixa, rotina, evolução, observações e conduta...")
        layout.addWidget(self.anamnesis)
        self.stack.addWidget(page)

        page = QWidget()
        layout = QVBoxLayout(page)
        self.reassess = QCheckBox("Registrar reavaliação em seguida no prontuário")
        self.reassess.setChecked(False)
        layout.addWidget(self.reassess)
        layout.addWidget(muted(
            "A reavaliação só será concluída quando você registrar medidas na área Avaliações. "
            "Até lá aparecerá como pendência, sem gerar medições fictícias."
        ))
        layout.addStretch()
        self.stack.addWidget(page)

        page = QWidget()
        form = QFormLayout(page)
        self.plan_delivery = QComboBox()
        self.plan_delivery.addItems([
            "Entrega pendente (não registrar envio)",
            "Plano já entregue ao paciente (confirmar manualmente)",
        ])
        self.delivered_plan = QComboBox()
        self.update_plan = QCheckBox("Atualizar/criar plano alimentar após a consulta")
        self.update_plan.setChecked(False)
        form.addRow("Situação de entrega", self.plan_delivery)
        form.addRow("Plano entregue (versão ativa)", self.delivered_plan)
        form.addRow("", self.update_plan)
        form.addRow("", muted(
            "Gerar um PDF não confirma entrega. Só marque como entregue se o paciente "
            "já recebeu o plano selecionado. Atualizações futuras ficam como pendência."
        ))
        self.plan_delivery.currentIndexChanged.connect(self._delivery_changed)
        self.stack.addWidget(page)

        page = QWidget()
        layout = QVBoxLayout(page)
        self.guidance = QTextEdit()
        self.guidance.setPlaceholderText("Orientações combinadas com o paciente...")
        layout.addWidget(self.guidance)
        self.stack.addWidget(page)

        page = QWidget()
        form = QFormLayout(page)
        self.schedule_return = QCheckBox("Agendar retorno")
        self.return_date = QDateEdit()
        self.return_date.setCalendarPopup(True)
        self.return_date.setDate(QDate.currentDate().addDays(30))
        self.return_time = QTimeEdit()
        self.return_time.setTime(QTime(9, 0))
        form.addRow("", self.schedule_return)
        form.addRow("Data do retorno", self.return_date)
        form.addRow("Hora", self.return_time)
        self.stack.addWidget(page)

        self.patient.currentIndexChanged.connect(self._patient_changed)
        self.appointment.currentIndexChanged.connect(self._appointment_changed)
        self._patient_changed()

    def _patient_changed(self, *_):
        patient_id = self.patient.currentData()
        old_selection = self.appointment.currentData()
        self.appointment.blockSignals(True)
        self.appointment.clear()
        self.appointment.addItem("Nova consulta (sem agendamento)", None)
        if patient_id is not None:
            appointments = [
                appointment for appointment in self.ag.list()
                if appointment["paciente_id"] == patient_id
                and appointment["status"] in ("Agendada", "Remarcada")
            ]
            for appointment in appointments:
                self.appointment.addItem(
                    f"#{appointment['id']} • {appointment['data']} {appointment['hora']} "
                    f"• {appointment['tipo']}", appointment["id"]
                )
        index = self.appointment.findData(old_selection) if old_selection is not None else 0
        self.appointment.setCurrentIndex(index if index >= 0 else 0)
        self.appointment.blockSignals(False)
        self._appointment_changed()

        self.delivered_plan.clear()
        if patient_id is not None:
            for plan in self.plans.list(patient_id):
                if plan["status"] == "Ativo":
                    self.delivered_plan.addItem(
                        f"{plan['nome']} • versão {plan['version_no']}", plan["id"]
                    )
        self._delivery_changed()

    def _appointment_changed(self, *_):
        selected_id = self.appointment.currentData()
        if selected_id is None:
            return
        matches = [appointment for appointment in self.ag.list()
                   if appointment["id"] == selected_id]
        if not matches:
            return
        appointment = matches[0]
        day = QDate.fromString(appointment["data"], "yyyy-MM-dd")
        hour = QTime.fromString(appointment["hora"], "HH:mm")
        if day.isValid():
            self.when.setDate(day)
        if hour.isValid():
            self.time.setTime(hour)
        index = self.kind.findText(appointment["tipo"])
        if index >= 0:
            self.kind.setCurrentIndex(index)

    def _delivery_changed(self, *_):
        self.delivered_plan.setEnabled(self.plan_delivery.currentIndex() == 1)

    def _sync(self):
        index = self.stack.currentIndex()
        self.step_label.setText(f"Etapa {index+1} de {len(CONSULTATION_STEPS)}")
        self.progress.setText(" → ".join(CONSULTATION_STEPS))
        self.back.setEnabled(index > 0 and not self._submitting)
        self.next.setText(
            "Finalizar consulta" if index == len(CONSULTATION_STEPS)-1 else "Avançar"
        )

    def previous(self):
        if self.stack.currentIndex() > 0 and not self._submitting:
            self.stack.setCurrentIndex(self.stack.currentIndex()-1)
            self._sync()

    def advance(self):
        if self._submitting:
            return
        if self.stack.currentIndex() < len(CONSULTATION_STEPS)-1:
            self.stack.setCurrentIndex(self.stack.currentIndex()+1)
            self._sync()
            return
        self.finish_consultation()

    def finish_consultation(self):
        if self._submitting:
            return
        self._submitting = True
        self.next.setEnabled(False)
        try:
            pid = self.patient.currentData()
            if pid is None:
                raise ValueError("Selecione um paciente.")
            delivered = self.plan_delivery.currentIndex() == 1
            cid = complete_guided_consultation(
                database=self.ag.db,
                patient_id=int(pid),
                appointment_id=self.appointment.currentData(),
                idempotency_key=self._completion_key,
                date_value=self.when.date().toString("yyyy-MM-dd"),
                time_value=self.time.time().toString("HH:mm"),
                kind=self.kind.currentText(),
                objective=self.objective.currentText().strip(),
                approach=self.approach.currentText().strip(),
                notes=self.guidance.toPlainText().strip(),
                anamnesis=self.anamnesis.toPlainText().strip(),
                plan_delivered=delivered,
                plan_id=self.delivered_plan.currentData() if delivered else None,
                request_reassessment=self.reassess.isChecked(),
                request_plan_update=self.update_plan.isChecked(),
                return_date=(self.return_date.date().toString("yyyy-MM-dd")
                             if self.schedule_return.isChecked() else None),
                return_time=(self.return_time.time().toString("HH:mm")
                             if self.schedule_return.isChecked() else None),
            )
            self.created_consultation_id = cid
            self.post_finish_focus = (
                "Avaliações" if self.reassess.isChecked()
                else "Plano alimentar" if self.update_plan.isChecked() else None
            )
            self.accept()
        except Exception as error:
            show_error(self, "Não foi possível concluir a consulta", error)
        finally:
            self._submitting = False
            self.next.setEnabled(True)
