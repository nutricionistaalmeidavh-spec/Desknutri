from __future__ import annotations

from .main_window import MainWindow as CoreMainWindow
from .refinement import UiRefinementMixin
from .window_features import AccountFeaturesMixin, OperationalFeaturesMixin


class MainWindow(UiRefinementMixin, AccountFeaturesMixin, OperationalFeaturesMixin, CoreMainWindow):
    """Janela canônica do NutriDesk.

    A camada de refinamento visual vem primeiro no MRO e delega comportamento
    para Conta -> Operacional -> Core. Assim, shell e telas podem evoluir sem
    duplicar regras clínicas, persistência, licenciamento ou serviços.
    """

    NAV = [
        "Dashboard",
        "Pacientes",
        "Agenda",
        "Biblioteca",
        "Conta",
        "Atualizações",
        "Exportações",
        "Suporte",
        "Configurações",
    ]
