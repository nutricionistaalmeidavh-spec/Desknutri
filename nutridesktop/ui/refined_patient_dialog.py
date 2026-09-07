"""Refino visual do prontuário sem duplicar regras clínicas do PatientDialog."""
from __future__ import annotations

from datetime import date, datetime, timedelta

from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .common import button
from .design_system import Card, StatCard, muted, section_title
from .patient_dialog import PatientDialog as CorePatientDialog
from .view_models import age_label, age_on
from nutridesktop.services.charts import (
    patient_bodyfat_figure,
    patient_circumference_figure,
    patient_composition_figure,
    patient_weight_bmi_figure,
)
from nutridesktop.ui_kit.components import PatientHeader, TimelineItem
from nutridesktop.ui_kit.theme import get_theme


COMPARISON_TABS = (
    ("Composição corporal", "composition"),
    ("Peso e IMC", "weight_bmi"),
    ("Circunferências", "circumference"),
    ("% Gordura", "body_fat"),
)


class ComparisonStatCard(QFrame):
    """Card compacto de primeira → última avaliação, como no layout aprovado."""

    def __init__(
        self,
        label: str,
        first,
        last,
        unit: str = "",
        delta_unit: str | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("comparisonCard")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(3)

        title = QLabel(label)
        title.setObjectName("metricLabel")
        value = QLabel(self._pair(first, last, unit))
        value.setObjectName("comparisonValue")
        delta = QLabel(self._delta(first, last, unit if delta_unit is None else delta_unit))
        delta.setObjectName("comparisonDelta")
        lay.addWidget(title)
        lay.addWidget(value)
        lay.addWidget(delta)

    @staticmethod
    def _pair(first, last, unit):
        if first is None or last is None:
            return "—"
        suffix = f" {unit}" if unit else ""
        return f"{first:.1f}{suffix}  →  {last:.1f}{suffix}"

    @staticmethod
    def _delta(first, last, unit):
        if first is None or last is None:
            return "Sem comparação"
        delta = last - first
        suffix = f" {unit}" if unit else ""
        sign = "+" if delta > 0 else ""
        arrow = "↑" if delta > 0 else "↓" if delta < 0 else "→"
        return f"{arrow} {sign}{delta:.1f}{suffix}"


class PatientEvolutionCard(Card):
    """Comparação longitudinal visual com composição corporal em destaque.

    A visão principal restaura o layout aprovado: massa livre de gordura + massa
    gorda em barras empilhadas, com peso corporal total sobreposto. Os demais
    indicadores ficam em abas e o motor longitudinal legado continua disponível
    separadamente no prontuário.
    """

    def __init__(self, assessments, parent=None):
        super().__init__(parent)
        self.assessments = list(assessments)
        self.canvases = {}

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_box.addWidget(section_title("Evolução"))
        title_box.addWidget(muted("Compare as avaliações registradas do paciente."))
        header.addLayout(title_box, 1)
        header.addWidget(muted(self._range_label()))
        self.body.addLayout(header)

        self._build_comparison_cards()

        self.chart_tabs = QTabWidget(self)
        self.tab_layouts = {}
        for label, key in COMPARISON_TABS:
            page = QWidget()
            lay = QVBoxLayout(page)
            lay.setContentsMargins(0, 6, 0, 0)
            self.tab_layouts[key] = lay
            self.chart_tabs.addTab(page, label)
        self.body.addWidget(self.chart_tabs)

        app = QApplication.instance()
        manager = app.property("theme_manager") if app else None
        if manager is not None and hasattr(manager, "theme_changed"):
            manager.theme_changed.connect(lambda _key: self._render_all())
        self._render_all()

    @staticmethod
    def _value(row, key):
        try:
            return row[key]
        except (KeyError, IndexError, TypeError):
            return None

    def _range_label(self):
        if not self.assessments:
            return "Sem avaliações"
        first = str(self._value(self.assessments[0], "data") or "")
        last = str(self._value(self.assessments[-1], "data") or "")

        def fmt(raw):
            try:
                return datetime.fromisoformat(raw).strftime("%d/%m/%Y")
            except (TypeError, ValueError):
                return raw

        if len(self.assessments) == 1:
            return f"1 avaliação • {fmt(first)}"
        return f"{len(self.assessments)} avaliações • {fmt(first)} → {fmt(last)}"

    def _build_comparison_cards(self):
        if not self.assessments:
            self.body.addWidget(muted("Registre pelo menos uma avaliação para visualizar a evolução."))
            return
        first = self.assessments[0]
        last = self.assessments[-1]
        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)

        specs = (
            ("Peso", "peso", "kg", None),
            ("Massa gorda", "massa_gorda", "kg", None),
            ("Massa livre de gordura", "massa_magra", "kg", None),
            ("% Gordura", "pg_final", "%", "p.p."),
            ("Cintura", "cintura", "cm", None),
        )
        for col, (label, key, unit, delta_unit) in enumerate(specs):
            grid.addWidget(
                ComparisonStatCard(
                    label,
                    self._value(first, key),
                    self._value(last, key),
                    unit,
                    delta_unit,
                    self,
                ),
                0,
                col,
            )
        self.body.addLayout(grid)

    @staticmethod
    def _clear_layout(layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _figure(self, key, tokens):
        if key == "composition":
            return patient_composition_figure(
                self.assessments,
                lean_color=tokens.composition_lean,
                fat_color=tokens.composition_fat,
                total_color=tokens.composition_total,
            )
        if key == "weight_bmi":
            return patient_weight_bmi_figure(
                self.assessments,
                weight_color=tokens.accent,
                bmi_color=tokens.border_strong,
            )
        if key == "circumference":
            return patient_circumference_figure(
                self.assessments,
                waist_color=tokens.accent,
                hip_color=tokens.border_strong,
            )
        return patient_bodyfat_figure(self.assessments, color=tokens.accent)

    def _style_figure(self, fig, tokens):
        fig.patch.set_facecolor(tokens.surface)
        for ax in fig.axes:
            ax.set_facecolor(tokens.surface)
            ax.tick_params(colors=tokens.text_secondary)
            ax.title.set_color(tokens.text)
            ax.yaxis.label.set_color(tokens.text_secondary)
            ax.xaxis.label.set_color(tokens.text_secondary)
            ax.grid(color=tokens.border, alpha=.55)
            for spine in ax.spines.values():
                spine.set_color(tokens.border)
            legend = ax.get_legend()
            if legend:
                for text in legend.get_texts():
                    text.set_color(tokens.text_secondary)
        return fig

    def _render_all(self):
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg

        app = QApplication.instance()
        manager = app.property("theme_manager") if app else None
        tokens = get_theme(getattr(manager, "key", None))
        for _label, key in COMPARISON_TABS:
            layout = self.tab_layouts[key]
            self._clear_layout(layout)
            fig = self._style_figure(self._figure(key, tokens), tokens)
            canvas = FigureCanvasQTAgg(fig)
            canvas.setMinimumHeight(285)
            layout.addWidget(canvas)
            self.canvases[key] = canvas
            canvas.draw_idle()

    @property
    def canvas(self):
        """Compatibilidade com testes/código que esperavam um único canvas."""
        return self.canvases.get("composition")


class RefinedPatientDialog(CorePatientDialog):
    """Aplica PatientHeader e composição premium ao prontuário existente.

    Repositories, cálculos e callbacks continuam pertencendo ao PatientDialog
    original. Esta classe altera apenas composição e apresentação.
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

        self.summary_evolution_card = PatientEvolutionCard(assessments, self)
        lay.addWidget(self.summary_evolution_card)

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

    def evolution_workspace_tab(self):
        """Evolução canônica em barras; o gráfico legado continua acessível."""
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 8, 0, 0)
        lay.setSpacing(12)
        assessments = self.ar.list(self.pid)
        self.evolution_comparison_card = PatientEvolutionCard(assessments, self)
        lay.addWidget(self.evolution_comparison_card)

        actions = QHBoxLayout()
        actions.addStretch()
        actions.addWidget(button("Abrir gráfico longitudinal", self.show_chart, variant="ghost"))
        lay.addLayout(actions)

        history = Card()
        history.body.addWidget(section_title("Histórico clínico"))
        history.body.addWidget(self.timeline_tab())
        lay.addWidget(history)
        return w
