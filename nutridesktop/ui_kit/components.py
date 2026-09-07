"""Componentes canônicos do NutriDesk UI Kit para PySide6.

Os componentes desta camada são puramente visuais. Eles não conhecem banco,
repositories ou regras clínicas e podem ser usados pelas telas sem alterar seus
contratos de dados.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


BUTTON_VARIANTS = {"primary", "secondary", "ghost", "danger"}
STATUS_TONES = {"success", "warning", "danger", "info", "neutral"}


def status_tone(status: str | None) -> str:
    """Converte estados funcionais em tons semânticos, sem mudar o valor salvo."""
    normalized = (status or "").strip().casefold()
    if normalized in {"realizada", "concluída", "concluida", "ativo", "ok", "salvo"}:
        return "success"
    if normalized in {"agendada", "remarcada", "pendente", "salvando"}:
        return "info" if normalized in {"agendada", "remarcada"} else "warning"
    if normalized in {"faltou", "atrasada", "atenção", "atencao"}:
        return "warning"
    if normalized in {"cancelada", "erro", "bloqueado", "inativo"}:
        return "danger"
    return "neutral"


class UiButton(QPushButton):
    """Botão com hierarquia visual explícita e compatibilidade com `primary`."""

    def __init__(
        self,
        text: str,
        callback=None,
        *,
        variant: str = "secondary",
        compact: bool = False,
        tone: str | None = None,
        parent=None,
    ):
        super().__init__(text, parent)
        variant = variant if variant in BUTTON_VARIANTS else "secondary"
        self.setCursor(Qt.PointingHandCursor)
        self.setProperty("variant", variant)
        self.setProperty("primary", variant == "primary")
        self.setProperty("compact", bool(compact))
        if tone in STATUS_TONES:
            self.setProperty("tone", tone)
        if callback:
            self.clicked.connect(callback)


class StatusBadge(QLabel):
    """Badge compacto para status clínicos e operacionais."""

    def __init__(self, text: str, tone: str | None = None, parent=None):
        super().__init__(str(text), parent)
        self.setAlignment(Qt.AlignCenter)
        self.setProperty("badge", True)
        self.setProperty("tone", tone if tone in STATUS_TONES else status_tone(text))
        self.setMinimumWidth(76)


class TableToolbar(QFrame):
    """Toolbar consistente: busca/filtro à esquerda e ações à direita."""

    def __init__(self, placeholder: str = "Buscar…", parent=None):
        super().__init__(parent)
        self.setObjectName("tableToolbar")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)
        self.search = QLineEdit()
        self.search.setObjectName("toolbarSearch")
        self.search.setPlaceholderText(placeholder)
        self.search.setClearButtonEnabled(True)
        layout.addWidget(self.search, 1)
        self.actions = QHBoxLayout()
        self.actions.setContentsMargins(0, 0, 0, 0)
        self.actions.setSpacing(6)
        layout.addLayout(self.actions)

    def add_action(self, widget: QWidget) -> QWidget:
        self.actions.addWidget(widget)
        return widget


class FormSection(QFrame):
    """Seção de formulário que reduz formulários longos de uma única coluna."""

    def __init__(self, title: str, description: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("formSection")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(16, 14, 16, 14)
        self.body.setSpacing(10)
        title_label = QLabel(title)
        title_label.setObjectName("sectionTitle")
        self.body.addWidget(title_label)
        if description:
            desc = QLabel(description)
            desc.setObjectName("muted")
            desc.setWordWrap(True)
            self.body.addWidget(desc)


class FormGrid(QWidget):
    """Grid de campos com 2 ou 3 colunas, mantendo labels junto aos controles."""

    def __init__(self, columns: int = 2, parent=None):
        super().__init__(parent)
        self.columns = 3 if columns == 3 else 2
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(12)
        self.grid.setVerticalSpacing(10)
        self._index = 0
        for col in range(self.columns):
            self.grid.setColumnStretch(col, 1)

    def add_field(self, label: str, widget: QWidget, *, span: int = 1) -> QWidget:
        span = max(1, min(int(span), self.columns))
        row = self._index // self.columns
        col = self._index % self.columns
        if col + span > self.columns:
            row += 1
            col = 0
            self._index = row * self.columns
        cell = QWidget()
        lay = QVBoxLayout(cell)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(5)
        lab = QLabel(label)
        lab.setObjectName("fieldLabel")
        lay.addWidget(lab)
        lay.addWidget(widget)
        self.grid.addWidget(cell, row, col, 1, span)
        self._index += span
        return widget


class PatientHeader(QFrame):
    """Cabeçalho persistente do prontuário com contexto e ações principais."""

    def __init__(self, on_new_consultation=None, on_edit=None, parent=None):
        super().__init__(parent)
        self.setObjectName("patientHeader")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        info = QVBoxLayout()
        info.setSpacing(2)
        self.name_label = QLabel("Paciente")
        self.name_label.setObjectName("patientName")
        self.meta_label = QLabel("")
        self.meta_label.setObjectName("muted")
        self.next_label = QLabel("")
        self.next_label.setObjectName("patientNext")
        info.addWidget(self.name_label)
        info.addWidget(self.meta_label)
        info.addWidget(self.next_label)
        layout.addLayout(info, 1)
        if on_edit:
            layout.addWidget(UiButton("Editar", on_edit, variant="ghost", compact=True))
        if on_new_consultation:
            layout.addWidget(UiButton("Nova consulta", on_new_consultation, variant="primary"))

    def set_patient(self, name: str, meta: str = "", next_text: str = ""):
        self.name_label.setText(name or "Paciente")
        self.meta_label.setText(meta)
        self.next_label.setText(next_text)
        self.next_label.setVisible(bool(next_text))


class TimelineItem(QFrame):
    """Item de timeline com data, título e detalhe opcional."""

    def __init__(self, event_date: str, title: str, detail: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("timelineItem")
        row = QHBoxLayout(self)
        row.setContentsMargins(10, 8, 10, 8)
        row.setSpacing(10)
        marker = QLabel("●")
        marker.setObjectName("timelineMarker")
        marker.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        marker.setFixedWidth(14)
        row.addWidget(marker)
        body = QVBoxLayout()
        body.setSpacing(2)
        date_label = QLabel(event_date or "")
        date_label.setObjectName("timelineDate")
        title_label = QLabel(title or "Registro clínico")
        title_label.setObjectName("timelineTitle")
        body.addWidget(date_label)
        body.addWidget(title_label)
        if detail:
            detail_label = QLabel(detail)
            detail_label.setObjectName("muted")
            detail_label.setWordWrap(True)
            body.addWidget(detail_label)
        row.addLayout(body, 1)


class SaveStateLabel(QLabel):
    """Feedback não intrusivo para operações de salvar."""

    def __init__(self, text: str = "", state: str = "neutral", parent=None):
        super().__init__(text, parent)
        self.setProperty("saveState", state)
        self.setObjectName("saveState")

    def set_state(self, text: str, state: str):
        self.setText(text)
        self.setProperty("saveState", state)
        self.style().unpolish(self)
        self.style().polish(self)
