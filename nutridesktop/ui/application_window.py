from __future__ import annotations

from .main_window import MainWindow as CoreMainWindow
from .window_features import AccountFeaturesMixin, OperationalFeaturesMixin


class MainWindow(AccountFeaturesMixin, OperationalFeaturesMixin, CoreMainWindow):
    """Janela canônica do NutriDesk.

    A composição preserva a mesma ordem efetiva usada anteriormente por
    V4MainWindow -> P3MainWindow -> MainWindow, mas remove nomes de versão do
    caminho de execução. `main_window.py` continua sendo a base visual oficial;
    recursos operacionais e de conta ficam em mixins neutros.
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
