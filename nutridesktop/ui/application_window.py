from __future__ import annotations

from .auto_update_features import SignedAutoUpdateMixin
from .main_window import MainWindow as CoreMainWindow
from .refinement import UiRefinementMixin
from .window_features import AccountFeaturesMixin, OperationalFeaturesMixin


class MainWindow(
    SignedAutoUpdateMixin,
    UiRefinementMixin,
    AccountFeaturesMixin,
    OperationalFeaturesMixin,
    CoreMainWindow,
):
    """Janela canônica do NutriDesk.

    Atualização assinada e refinamento visual vêm antes no MRO e delegam
    comportamento para Conta -> Operacional -> Core. Assim, shell e telas
    evoluem sem duplicar regras clínicas, persistência, licenciamento ou
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
