"""Refinamento visual das fases 4–6.

A estratégia é de composição: este mixin sobrescreve somente shell e telas
selecionadas, preservando todos os handlers, repositories e serviços da janela
canônica existente.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

from PySide6.QtCore import Qt, QDate, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCalendarWidget,
    QComboBox,
    QDateEdit,
    QFrame,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QStackedWidget,
    QTableWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .common import button, item
from .design_system import Card, EmptyState, StatCard, muted, section_title
from .view_models import NAV_GROUPS, age_label
from nutridesktop.services.pending_actions import collect_pending_actions
from nutridesktop.services.plans import recipe_nutrients
from nutridesktop.ui_kit.components import (
    FormGrid,
    FormSection,
    StatusBadge,
    TableToolbar,
    status_tone,
)
from nutridesktop.version import APP_VERSION


class UiRefinementMixin:
    """Shell e telas refinadas sem alterar contratos funcionais."""

    PAGE_ALIASES = {
        "dashboard": "Dashboard",
        "início": "Dashboard",
        "inicio": "Dashboard",
        "paciente": "Pacientes",
        "pacientes": "Pacientes",
        "agenda": "Agenda",
        "biblioteca": "Biblioteca",
        "alimentos": "Alimentos",
        "receitas": "Receitas",
        "templates": "Templates",
        "protocolos": "Protocolos",
        "crescimento": "Crescimento WHO",
        "who": "Crescimento WHO",
        "materno": "Materno-infantil",
        "conta": "Conta",
        "licença": "Conta",
        "licenca": "Conta",
        "configurações": "Configurações",
        "configuracoes": "Configurações",
        "backup": "Configurações",
    }

    # ------------------------------------------------------------------ shell
    def _build(self):
        root = QWidget()
        root.setObjectName("appRoot")
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        side = QWidget()
        side.setObjectName("sidebar")
        side.setFixedWidth(218)
        sv = QVBoxLayout(side)
        sv.setContentsMargins(13, 16, 13, 12)
        sv.setSpacing(3)

        brand = QLabel("NutriDesk")
        brand.setObjectName("brand")
        sv.addWidget(brand)
        sv.addWidget(button("Nova consulta", self.new_consultation, variant="primary"))
        self.nav = {}
        self.nav_sections = {}
        for section, names in NAV_GROUPS.items():
            label = QLabel(section)
            label.setObjectName("navSection")
            sv.addWidget(label)
            self.nav_sections[section] = label
            for name in names:
                nav_button = button(
                    name,
                    lambda checked=False, page=name: self.show_page(page),
                    variant="ghost",
                )
                if name == "Pacientes":
                    nav_button.setToolTip("Pacientes • Ctrl+P")
                sv.addWidget(nav_button)
                self.nav[name] = nav_button

        sv.addStretch()
        profile = QFrame()
        profile.setObjectName("sidebarProfile")
        profile_layout = QHBoxLayout(profile)
        profile_layout.setContentsMargins(0, 10, 0, 0)
        profile_layout.setSpacing(4)
        profile_layout.addWidget(button("Conta", lambda: self.show_page("Conta"), variant="ghost", compact=True))
        profile_layout.addStretch()
        version = QLabel(f"v{APP_VERSION}")
        version.setObjectName("muted")
        profile_layout.addWidget(version)
        sv.addWidget(profile)
        outer.addWidget(side)

        main = QWidget()
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        topbar = QFrame()
        topbar.setObjectName("topbar")
        topbar_layout = QHBoxLayout(topbar)
        topbar_layout.setContentsMargins(22, 9, 22, 9)
        topbar_layout.setSpacing(10)
        self.topbar_context = QLabel("NutriDesk  /  Dashboard")
        self.topbar_context.setObjectName("topbarContext")
        topbar_layout.addWidget(self.topbar_context)
        topbar_layout.addStretch()
        self.topbar_result = QLabel("")
        self.topbar_result.setObjectName("topbarResult")
        self.topbar_result.setVisible(False)
        topbar_layout.addWidget(self.topbar_result)
        self.global_search = QLineEdit()
        self.global_search.setObjectName("globalSearch")
        self.global_search.setPlaceholderText("Buscar paciente ou tela…   Ctrl+K")
        self.global_search.setClearButtonEnabled(True)
        self.global_search.setMaximumWidth(420)
        self.global_search.returnPressed.connect(self.run_global_search)
        topbar_layout.addWidget(self.global_search, 1)
        topbar_layout.addWidget(button("Conta", lambda: self.show_page("Conta"), variant="ghost", compact=True))
        main_layout.addWidget(topbar)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack, 1)
        outer.addWidget(main, 1)

    def _shortcuts(self):
        self.shortcuts = []
        bindings = [
            ("Ctrl+N", self.new_consultation),
            ("Ctrl+P", lambda: self.show_page("Pacientes")),
            ("Ctrl+K", self.focus_global_search),
        ]
        for sequence, callback in bindings:
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.activated.connect(callback)
            self.shortcuts.append(shortcut)

    def focus_global_search(self):
        if hasattr(self, "global_search"):
            self.global_search.setFocus()
            self.global_search.selectAll()

    def run_global_search(self):
        query = self.global_search.text().strip() if hasattr(self, "global_search") else ""
        if not query:
            return
        normalized = query.casefold()
        direct = self.PAGE_ALIASES.get(normalized)
        if direct:
            self.show_page(direct)
            self._set_search_feedback(f"Abrindo {direct}")
            return

        patients = self.pr.list(query)
        if patients:
            self.show_page("Pacientes")
            if hasattr(self, "patient_search"):
                self.patient_search.setText(query)
                if len(patients) == 1 and self.patient_table.rowCount():
                    self.patient_table.selectRow(0)
            self._set_search_feedback(f"{len(patients)} paciente(s)")
            return

        foods = self.fr.search(query, 20)
        if foods:
            self.show_page("Biblioteca")
            if hasattr(self, "food_search"):
                self.food_search.setText(query)
            self._set_search_feedback(f"{len(foods)} alimento(s)")
            return
        self._set_search_feedback("Nenhum resultado")

    def _set_search_feedback(self, text: str):
        if not hasattr(self, "topbar_result"):
            return
        self.topbar_result.setText(text)
        self.topbar_result.setVisible(True)
        QTimer.singleShot(2800, lambda: self.topbar_result.setVisible(False))

    def show_page(self, name):
        result = super().show_page(name)
        if hasattr(self, "topbar_context"):
            self.topbar_context.setText(f"NutriDesk  /  {name}")
        if hasattr(self, "nav") and name in self.nav:
            self._mark_nav(name)
        return result

    def page(self, title, subtitle=""):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(24, 18, 24, 20)
        v.setSpacing(12)
        heading = QLabel(title)
        heading.setObjectName("pageTitle")
        v.addWidget(heading)
        if subtitle:
            sub = QLabel(subtitle)
            sub.setObjectName("pageSubtitle")
            sub.setWordWrap(True)
            v.addWidget(sub)
        return w, v

    # --------------------------------------------------------------- dashboard
    def dashboard(self):
        w, v = self.page(
            "Dashboard",
            "Agenda, pendências e retornos primeiro; indicadores gerenciais ficam em segundo plano.",
        )
        patient_rows = self.pr.list()
        today = date.today()
        today_s = today.isoformat()
        consults = self.ag.list(today_s, today_s)
        upcoming = self.ag.list(today_s, (today + timedelta(days=7)).isoformat())
        pending_actions = collect_pending_actions(self.pr.db, today)
        objectives = self.ag.objective_distribution()

        stats = QGridLayout()
        stats.setHorizontalSpacing(10)
        values = [
            ("Consultas de hoje", len(consults), "Agenda do dia"),
            ("Pacientes ativos", len(patient_rows), "Prontuários cadastrados"),
            ("Retornos próximos", len([a for a in upcoming if a["data"] > today_s]), "Próximos 7 dias"),
            ("Pendências", len(pending_actions), "Ações que pedem atenção"),
        ]
        for index, data in enumerate(values):
            stats.addWidget(StatCard(*data), 0, index)
        v.addLayout(stats)

        operational = QGridLayout()
        operational.setHorizontalSpacing(12)
        operational.setVerticalSpacing(12)
        operational.setColumnStretch(0, 2)
        operational.setColumnStretch(1, 1)

        agenda_card = Card()
        agenda_head = QHBoxLayout()
        agenda_head.addWidget(section_title("Agenda de hoje"))
        agenda_head.addStretch()
        agenda_head.addWidget(button("Ver agenda", lambda: self.show_page("Agenda"), variant="ghost", compact=True))
        agenda_card.body.addLayout(agenda_head)
        if consults:
            for appointment in consults[:7]:
                row = QWidget()
                layout = QHBoxLayout(row)
                layout.setContentsMargins(0, 3, 0, 3)
                time_label = QLabel(str(appointment["hora"]))
                time_label.setFixedWidth(54)
                patient_label = QLabel(str(appointment["paciente_nome"]))
                layout.addWidget(time_label)
                layout.addWidget(patient_label, 1)
                layout.addWidget(StatusBadge(appointment["status"]))
                agenda_card.body.addWidget(row)
        else:
            agenda_card.body.addWidget(muted("Nenhuma consulta agendada para hoje."))
        operational.addWidget(agenda_card, 0, 0)

        pending_card = Card()
        pending_card.body.addWidget(section_title("Pendências clínicas"))
        if pending_actions:
            for action in pending_actions[:6]:
                title = QLabel(f"{action['patient_name']} • {action['title']}")
                title.setWordWrap(True)
                pending_card.body.addWidget(title)
                if action.get("detail"):
                    pending_card.body.addWidget(muted(action["detail"]))
        else:
            pending_card.body.addWidget(muted("Nenhuma pendência clínica ou operacional identificada."))
        operational.addWidget(pending_card, 0, 1)

        recent_card = Card()
        recent_head = QHBoxLayout()
        recent_head.addWidget(section_title("Pacientes recentes"))
        recent_head.addStretch()
        recent_head.addWidget(button("Ver pacientes", lambda: self.show_page("Pacientes"), variant="ghost", compact=True))
        recent_card.body.addLayout(recent_head)
        recent = patient_rows[:6]
        if recent:
            for patient in recent:
                recent_card.body.addWidget(
                    button(
                        f"{patient['nome']}   •   {age_label(patient['data_nascimento'])}",
                        lambda checked=False, pid=patient["id"]: self._open_patient_id(pid),
                        variant="ghost",
                        compact=True,
                    )
                )
        else:
            recent_card.body.addWidget(muted("Cadastre o primeiro paciente para começar."))
        operational.addWidget(recent_card, 1, 0)

        returns_card = Card()
        returns_card.body.addWidget(section_title("Próximos retornos"))
        returns = [a for a in upcoming if a["data"] > today_s]
        if returns:
            for appointment in returns[:6]:
                display = self._display_date(appointment["data"])
                returns_card.body.addWidget(
                    QLabel(f"{display}  •  {appointment['hora']}  •  {appointment['paciente_nome']}")
                )
        else:
            returns_card.body.addWidget(muted("Nenhum retorno nos próximos 7 dias."))
        operational.addWidget(returns_card, 1, 1)
        v.addLayout(operational)

        insights = QHBoxLayout()
        insights.setSpacing(12)
        distribution = Card()
        distribution.body.addWidget(section_title("Distribuição de objetivos"))
        total = sum(objectives.values())
        if objectives and total:
            for name, count in objectives.items():
                distribution.body.addWidget(QLabel(f"{name}: {(count / total * 100):.0f}% ({count})"))
        else:
            distribution.body.addWidget(muted("Os objetivos aparecerão após as consultas guiadas."))
        adherence = Card()
        adherence.body.addWidget(section_title("Adesão aos planos"))
        adherence.body.addWidget(QLabel("—"))
        adherence.body.addWidget(muted("Sem dados suficientes de acompanhamento para calcular adesão."))
        insights.addWidget(distribution, 1)
        insights.addWidget(adherence, 1)
        v.addLayout(insights)
        v.addStretch()
        return w

    # ---------------------------------------------------------------- patients
    def patients(self):
        w, v = self.page(
            "Pacientes",
            "Prontuário longitudinal, avaliações, planos e evolução em um único workspace.",
        )
        toolbar = TableToolbar("Buscar paciente por nome")
        self.patient_search = toolbar.search
        self.patient_search.textChanged.connect(self.refresh_patients)
        toolbar.add_action(button("Novo paciente", self.new_patient, variant="secondary"))
        toolbar.add_action(button("Nova consulta", self.new_consultation, variant="primary"))
        v.addWidget(toolbar)

        self.patient_table = QTableWidget(0, 5)
        self.patient_table.setHorizontalHeaderLabels(["ID", "Nome", "Sexo", "Nascimento", "Telefone"])
        self.patient_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.patient_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.patient_table.setAlternatingRowColors(True)
        self.patient_table.verticalHeader().setVisible(False)
        header = self.patient_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        for column in (2, 3, 4):
            header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
        self.patient_table.cellDoubleClicked.connect(lambda *_: self.open_patient())
        v.addWidget(self.patient_table, 1)

        self.patient_empty = EmptyState(
            "Nenhum paciente encontrado",
            "Cadastre um novo paciente ou ajuste a busca.",
        )
        v.addWidget(self.patient_empty)
        footer = QHBoxLayout()
        footer.addStretch()
        self.open_patient_button = button(
            "Abrir prontuário",
            self.open_patient,
            variant="secondary",
        )
        self.open_patient_button.setEnabled(False)
        self.patient_table.itemSelectionChanged.connect(
            lambda: self.open_patient_button.setEnabled(self.patient_table.currentRow() >= 0)
        )
        footer.addWidget(self.open_patient_button)
        v.addLayout(footer)
        self.refresh_patients()
        return w

    def refresh_patients(self):
        super().refresh_patients()
        if hasattr(self, "open_patient_button"):
            self.open_patient_button.setEnabled(self.patient_table.currentRow() >= 0)

    def open_patient(self):
        if not hasattr(self, "patient_table"):
            return
        row = self.patient_table.currentRow()
        if row >= 0:
            self._open_patient_id(int(self.patient_table.item(row, 0).text()))
            self.refresh_patients()

    def _open_patient_id(self, patient_id):
        from .refined_patient_dialog import RefinedPatientDialog

        RefinedPatientDialog(int(patient_id), self).exec()

    # ------------------------------------------------------------------ agenda
    def agenda(self):
        w, v = self.page(
            "Agenda",
            "Selecione uma data e acompanhe consultas, retornos e status com filtros compactos.",
        )
        split = QHBoxLayout()
        split.setSpacing(12)
        self.ag_calendar = QCalendarWidget()
        self.ag_calendar.setObjectName("agendaCalendar")
        self.ag_calendar.setGridVisible(False)
        self.ag_calendar.selectionChanged.connect(self._agenda_calendar_changed)
        split.addWidget(self.ag_calendar, 1)

        right = QVBoxLayout()
        right.setSpacing(10)
        filters = QFrame()
        filters.setObjectName("tableToolbar")
        filter_layout = QHBoxLayout(filters)
        filter_layout.setContentsMargins(10, 8, 10, 8)
        filter_layout.setSpacing(8)

        self.ag_start = QDateEdit()
        self.ag_start.setCalendarPopup(True)
        self.ag_start.setDisplayFormat("dd/MM/yyyy")
        self.ag_start.setDate(QDate.currentDate())
        self.ag_end = QDateEdit()
        self.ag_end.setCalendarPopup(True)
        self.ag_end.setDisplayFormat("dd/MM/yyyy")
        self.ag_end.setDate(QDate.currentDate().addDays(30))
        self.ag_status = QComboBox()
        self.ag_status.addItems(["Todos", "Agendada", "Realizada", "Faltou", "Cancelada", "Remarcada"])

        for label_text, control in (
            ("De", self.ag_start),
            ("Até", self.ag_end),
            ("Status", self.ag_status),
        ):
            cell = QWidget()
            cell_layout = QVBoxLayout(cell)
            cell_layout.setContentsMargins(0, 0, 0, 0)
            cell_layout.setSpacing(3)
            label = QLabel(label_text)
            label.setObjectName("fieldLabel")
            cell_layout.addWidget(label)
            cell_layout.addWidget(control)
            filter_layout.addWidget(cell)
        filter_layout.addStretch()
        filter_layout.addWidget(button("Filtrar", self.refresh_agenda, variant="secondary"))
        filter_layout.addWidget(button("Agendar", self.new_appointment, variant="primary"))
        right.addWidget(filters)

        self.ag_table = QTableWidget(0, 7)
        self.ag_table.setHorizontalHeaderLabels(["ID", "Data", "Hora", "Paciente", "Tipo", "Status", "Duração"])
        self.ag_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ag_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.ag_table.setAlternatingRowColors(True)
        self.ag_table.verticalHeader().setVisible(False)
        ag_header = self.ag_table.horizontalHeader()
        ag_header.setSectionResizeMode(QHeaderView.ResizeToContents)
        ag_header.setSectionResizeMode(3, QHeaderView.Stretch)
        right.addWidget(self.ag_table, 1)

        self.agenda_empty = EmptyState(
            "Nenhuma consulta no período",
            "Selecione outra data ou agende uma nova consulta.",
        )
        right.addWidget(self.agenda_empty)
        actions = QHBoxLayout()
        for status in ["Realizada", "Faltou", "Cancelada", "Remarcada"]:
            actions.addWidget(
                button(
                    status,
                    lambda checked=False, current=status: self.set_appointment_status(current),
                    variant="secondary",
                    compact=True,
                    tone=status_tone(status),
                )
            )
        actions.addStretch()
        right.addLayout(actions)
        split.addLayout(right, 3)
        v.addLayout(split, 1)
        self.refresh_agenda()
        return w

    def _agenda_calendar_changed(self):
        chosen = self.ag_calendar.selectedDate()
        if isinstance(self.ag_start, QDateEdit):
            self.ag_start.setDate(chosen)
            self.ag_end.setDate(chosen)
        else:
            value = chosen.toString("yyyy-MM-dd")
            self.ag_start.setText(value)
            self.ag_end.setText(value)
        self.refresh_agenda()

    def refresh_agenda(self):
        if not hasattr(self, "ag_table"):
            return
        start = self._agenda_filter_date(self.ag_start)
        end = self._agenda_filter_date(self.ag_end)
        status = None if self.ag_status.currentText() == "Todos" else self.ag_status.currentText()
        try:
            rows = self.ag.list(start, end, status)
        except Exception:
            return
        self.ag_table.setRowCount(len(rows))
        self.ag_table.setVisible(bool(rows))
        if hasattr(self, "agenda_empty"):
            self.agenda_empty.setVisible(not bool(rows))
        for row_index, appointment in enumerate(rows):
            values = [
                appointment["id"],
                self._display_date(appointment["data"]),
                appointment["hora"],
                appointment["paciente_nome"],
                appointment["tipo"],
                appointment["status"],
                appointment["duracao_min"],
            ]
            for column, value in enumerate(values):
                self.ag_table.setItem(row_index, column, item(value))
            self.ag_table.setCellWidget(row_index, 5, StatusBadge(appointment["status"]))

    @staticmethod
    def _agenda_filter_date(widget) -> str:
        if isinstance(widget, QDateEdit):
            return widget.date().toString("yyyy-MM-dd")
        return widget.text().strip()

    @staticmethod
    def _display_date(value) -> str:
        raw = str(value or "")
        try:
            return datetime.strptime(raw[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError:
            return raw

    # ---------------------------------------------------------------- recipes
    def recipes(self):
        w, v = self.page(
            "Receitas",
            "Cadastre a receita em um workspace compacto e gerencie ingredientes na mesma tela.",
        )
        top = QHBoxLayout()
        top.setSpacing(12)

        data_section = FormSection("Dados da receita", "Informações usadas na biblioteca e nos planos alimentares.")
        form_grid = FormGrid(columns=2)
        self.rec_name = QLineEdit()
        self.rec_name.setPlaceholderText("Nome da receita")
        self.rec_category = QLineEdit()
        self.rec_category.setPlaceholderText("Ex.: lanche, almoço, sobremesa")
        self.rec_tags = QLineEdit()
        self.rec_tags.setPlaceholderText("proteica, rápida, vegetariana…")
        self.rec_serv = QLineEdit("1")
        form_grid.add_field("Nome", self.rec_name)
        form_grid.add_field("Categoria", self.rec_category)
        form_grid.add_field("Tags", self.rec_tags)
        form_grid.add_field("Porções", self.rec_serv)
        data_section.body.addWidget(form_grid)
        top.addWidget(data_section, 1)

        method_section = FormSection("Modo de preparo", "Mantenha as instruções objetivas e reproduzíveis.")
        self.rec_method = QTextEdit()
        self.rec_method.setPlaceholderText("Descreva o modo de preparo")
        self.rec_method.setMinimumHeight(128)
        method_section.body.addWidget(self.rec_method, 1)
        top.addWidget(method_section, 1)
        v.addLayout(top)

        create_row = QHBoxLayout()
        create_row.addStretch()
        create_row.addWidget(button("Criar receita", self.create_recipe, variant="primary"))
        v.addLayout(create_row)

        self.rec_table = QTableWidget(0, 7)
        self.rec_table.setHorizontalHeaderLabels(
            ["ID", "Nome", "Categoria", "Tags", "Porções", "kcal/porção", "Proteína/porção"]
        )
        self.rec_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.rec_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.rec_table.setAlternatingRowColors(True)
        self.rec_table.verticalHeader().setVisible(False)
        rec_header = self.rec_table.horizontalHeader()
        rec_header.setSectionResizeMode(QHeaderView.ResizeToContents)
        rec_header.setSectionResizeMode(1, QHeaderView.Stretch)
        v.addWidget(self.rec_table, 1)

        ingredient_section = FormSection(
            "Ingredientes",
            "Selecione uma receita acima, busque o alimento e informe a quantidade em gramas.",
        )
        ingredient_row = QHBoxLayout()
        self.rec_food = QLineEdit()
        self.rec_food.setPlaceholderText("Buscar ingrediente")
        self.rec_grams = QLineEdit("100")
        self.rec_grams.setMaximumWidth(130)
        ingredient_row.addWidget(self.rec_food, 1)
        ingredient_row.addWidget(self.rec_grams)
        ingredient_row.addWidget(button("Adicionar ingrediente", self.add_recipe_ingredient, variant="secondary"))
        ingredient_section.body.addLayout(ingredient_row)
        v.addWidget(ingredient_section)
        self.refresh_recipes()
        return w

    def refresh_recipes(self):
        if not hasattr(self, "rec_table"):
            return
        rows = self.rr.list()
        self.rec_table.setRowCount(len(rows))
        for row_index, recipe in enumerate(rows):
            nutrients = recipe_nutrients(recipe["id"], self.rr)
            values = [
                recipe["id"],
                recipe["nome"],
                recipe["categoria"] or "",
                recipe["tags"] or "",
                recipe["porcoes"],
                round(nutrients.get("kcal", 0), 1),
                round(nutrients.get("proteina", 0), 1),
            ]
            for column, value in enumerate(values):
                self.rec_table.setItem(row_index, column, item(value))
