from __future__ import annotations

from .auto_update_features import GitHubReleaseUpdateMixin
from .main_window import MainWindow as CoreMainWindow
from .refinement import UiRefinementMixin
from .window_features import AccountFeaturesMixin, OperationalFeaturesMixin


class MainWindow(
    GitHubReleaseUpdateMixin,
    UiRefinementMixin,
    AccountFeaturesMixin,
    OperationalFeaturesMixin,
    CoreMainWindow,
):
    """Janela canônica do NutriDesk.

    O updater simples do GitHub e o refinamento visual vêm antes no MRO e
    delegam comportamento para Conta -> Operacional -> Core. Assim, shell e
    telas evoluem sem duplicar regras clínicas, persistência, licenciamento ou
    serviços.
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
