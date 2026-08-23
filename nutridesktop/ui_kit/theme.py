"""Tokens e gerenciamento de tema do NutriDesk UI Kit.

O tema escuro profissional é o padrão do produto. A alternativa clara fica
disponível nas Configurações sem misturar regras clínicas com aparência.
"""
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QObject, QSettings, Signal


DEFAULT_THEME = "professional-data-clinic"
THEME_SETTING_KEY = "ui/theme"


@dataclass(frozen=True)
class ThemeTokens:
    key: str
    label: str
    bg: str
    surface: str
    surface_alt: str
    surface_elevated: str
    sidebar_bg: str
    topbar_bg: str
    text: str
    text_secondary: str
    text_muted: str
    border: str
    border_strong: str
    accent: str
    accent_hover: str
    accent_contrast: str
    active: str
    active_text: str
    hover: str
    success: str
    success_soft: str
    warning: str
    warning_soft: str
    danger: str
    danger_soft: str
    info: str
    info_soft: str
    radius_sm: int = 8
    radius_md: int = 14


THEMES = {
    "professional-data-clinic": ThemeTokens(
        key="professional-data-clinic", label="Profissional escuro",
        bg="#101B1D", surface="#152427", surface_alt="#1A2D30", surface_elevated="#20383A",
        sidebar_bg="#0B1719", topbar_bg="#152427", text="#F1F7F5", text_secondary="#B8CBC7",
        text_muted="#8BA19C", border="#294346", border_strong="#3A5B5B", accent="#35BFAF",
        accent_hover="#48D1C0", accent_contrast="#08201E", active="#1E5954", active_text="#F5FFFD",
        hover="#213B3D", success="#65D39B", success_soft="#183C30", warning="#F3BB5C",
        warning_soft="#4A3820", danger="#F28A86", danger_soft="#482527", info="#78B8FF", info_soft="#1E3854",
    ),
    "premium-soft-healthcare": ThemeTokens(
        key="premium-soft-healthcare", label="Clínico claro",
        bg="#F4F8F7", surface="#FFFFFF", surface_alt="#EDF5F3", surface_elevated="#FFFFFF",
        sidebar_bg="#0F4C48", topbar_bg="#FFFFFF", text="#18302E", text_secondary="#55706C",
        text_muted="#738883", border="#D6E5E1", border_strong="#B8D1CB", accent="#0F8074",
        accent_hover="#0C6A61", accent_contrast="#FFFFFF", active="#D9F0EB", active_text="#0B514A",
        hover="#E6F2EF", success="#18794E", success_soft="#DCF4E7", warning="#A96400",
        warning_soft="#FFF0D4", danger="#B53B3B", danger_soft="#FDE3E1", info="#1E63B6", info_soft="#E1EFFF",
    ),
}


def get_theme(key: str | None = None) -> ThemeTokens:
    return THEMES.get(key or DEFAULT_THEME, THEMES[DEFAULT_THEME])


def build_stylesheet(t: ThemeTokens) -> str:
    """QSS global, com contratos semânticos para telas novas e legadas."""
    return f"""
* {{ font-family: 'Segoe UI', 'Inter', Arial, sans-serif; font-size: 13px; color: {t.text}; }}
QMainWindow, QDialog, QWidget#appRoot {{ background: {t.bg}; }}
QWidget#sidebar {{ background: {t.sidebar_bg}; border-right: 1px solid {t.border}; }}
QLabel#brand {{ color: {t.text}; font-size: 23px; font-weight: 800; padding: 5px 4px 15px; }}
QLabel#navSection {{ color: {t.text_muted}; font-size: 10px; font-weight: 700; padding: 14px 7px 4px; letter-spacing: 1px; }}
QPushButton {{ background: transparent; border: 1px solid transparent; border-radius: {t.radius_sm}px; padding: 8px 12px; color: {t.text}; }}
QPushButton:hover {{ background: {t.hover}; }}
QWidget#sidebar QPushButton {{ color: {t.text_secondary}; text-align: left; padding: 10px 12px; }}
QWidget#sidebar QPushButton:hover {{ color: {t.text}; background: {t.hover}; }}
QWidget#sidebar QPushButton[active="true"] {{ color: {t.active_text}; background: {t.active}; font-weight: 700; }}
QPushButton[primary="true"] {{ background: {t.accent}; color: {t.accent_contrast}; border-color: {t.accent}; font-weight: 700; text-align: center; }}
QPushButton[primary="true"]:hover {{ background: {t.accent_hover}; border-color: {t.accent_hover}; }}
QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {{ background: {t.surface}; border: 1px solid {t.border}; border-radius: {t.radius_sm}px; padding: 8px 10px; }}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus {{ border: 1px solid {t.accent}; }}
QComboBox QAbstractItemView {{ background: {t.surface_elevated}; border: 1px solid {t.border}; selection-background-color: {t.active}; }}
QTableWidget, QTableView {{ background: {t.surface}; alternate-background-color: {t.surface_alt}; border: 1px solid {t.border}; border-radius: {t.radius_md}px; gridline-color: transparent; selection-background-color: {t.active}; }}
QHeaderView::section {{ background: {t.surface_alt}; color: {t.text_secondary}; border: 0; border-bottom: 1px solid {t.border}; padding: 10px; font-weight: 700; }}
QTableWidget::item {{ border-bottom: 1px solid {t.border}; padding: 7px 10px; }}
QFrame#card {{ background: {t.surface}; border: 1px solid {t.border}; border-radius: {t.radius_md}px; }}
QFrame#softCard {{ background: {t.surface_alt}; border: 1px solid {t.border}; border-radius: {t.radius_md}px; }}
QLabel#pageTitle {{ font-size: 27px; font-weight: 800; color: {t.text}; }}
QLabel#pageSubtitle, QLabel#muted {{ color: {t.text_muted}; }}
QLabel#metricLabel {{ color: {t.text_secondary}; font-weight: 600; }}
QLabel#metricValue {{ color: {t.text}; font-size: 25px; font-weight: 800; }}
QLabel#sectionTitle {{ color: {t.text}; font-size: 15px; font-weight: 750; }}
QTabWidget::pane {{ border: 0; background: transparent; }}
QTabBar::tab {{ color: {t.text_muted}; padding: 10px 14px; margin-right: 4px; border-bottom: 2px solid transparent; }}
QTabBar::tab:selected {{ color: {t.accent}; border-bottom-color: {t.accent}; font-weight: 700; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {t.border_strong}; min-height: 24px; border-radius: 5px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QToolTip {{ background: {t.surface_elevated}; color: {t.text}; border: 1px solid {t.border_strong}; padding: 6px 8px; border-radius: 6px; }}
"""


class ThemeManager(QObject):
    theme_changed = Signal(str)

    def __init__(self, app, settings: QSettings | None = None):
        super().__init__()
        self.app = app
        self.settings = settings or QSettings("NutriDesk", "NutriDesk")
        self._key = str(self.settings.value(THEME_SETTING_KEY, DEFAULT_THEME))

    @property
    def key(self) -> str:
        return self._key if self._key in THEMES else DEFAULT_THEME

    def apply(self, key: str | None = None, *, persist: bool = True) -> str:
        chosen = key if key in THEMES else self.key
        self._key = chosen
        if persist:
            self.settings.setValue(THEME_SETTING_KEY, chosen)
        self.app.setStyleSheet(build_stylesheet(get_theme(chosen)))
        self.theme_changed.emit(chosen)
        return chosen
