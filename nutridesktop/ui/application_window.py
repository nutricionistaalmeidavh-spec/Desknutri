from __future__ import annotations

from .auto_update_features import GitHubReleaseUpdateMixin
from .final_polish import FinalPolishMixin
from .main_window import MainWindow as CoreMainWindow
from .refinement import UiRefinementMixin
from .window_features import AccountFeaturesMixin, OperationalFeaturesMixin


class MainWindow(
    FinalPolishMixin,
    GitHubReleaseUpdateMixin,
    UiRefinementMixin,
    AccountFeaturesMixin,
    OperationalFeaturesMixin,
    CoreMainWindow,
):
    """Janela canônica do NutriDesk.

    O polish final, updater simples do GitHub e refinamento visual vêm antes no
    MRO e delegam comportamento para Conta -> Operacional -> Core. Assim,
    microinterações e shell evoluem sem duplicar regras clínicas, persistência,
    licenciamento ou serviços.
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