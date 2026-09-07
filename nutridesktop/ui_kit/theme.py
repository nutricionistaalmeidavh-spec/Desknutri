"""Tokens e gerenciamento de tema do NutriDesk UI Kit.

A identidade canônica do produto é a interface clínica clara em vinho/rosé.
O tema escuro continua disponível como alternativa, sem interferir nas regras
clínicas ou na persistência de dados.
"""
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QObject, QSettings, Signal


DEFAULT_THEME = "premium-rose-healthcare"
LEGACY_DEFAULT_THEME = "professional-data-clinic"
THEME_SETTING_KEY = "ui/theme"
THEME_VISUAL_GENERATION_KEY = "ui/theme_visual_generation"
THEME_VISUAL_GENERATION = 2


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
    composition_lean: str
    composition_fat: str
    composition_total: str
    radius_sm: int = 8
    radius_md: int = 14


THEMES = {
    "premium-rose-healthcare": ThemeTokens(
        key="premium-rose-healthcare",
        label="Clínico rosé",
        bg="#FBF8F9",
        surface="#FFFFFF",
        surface_alt="#FCF2F6",
        surface_elevated="#FFFFFF",
        sidebar_bg="#FFFCFD",
        topbar_bg="#FFFFFF",
        text="#2D272A",
        text_secondary="#62585D",
        text_muted="#92878C",
        border="#EEDDE5",
        border_strong="#DDBFCD",
        accent="#A84770",
        accent_hover="#91385F",
        accent_contrast="#FFFFFF",
        active="#A84770",
        active_text="#FFFFFF",
        hover="#F7E9EF",
        success="#3F9B68",
        success_soft="#EAF6EE",
        warning="#C58A24",
        warning_soft="#FFF3D9",
        danger="#B74D5C",
        danger_soft="#FBE7EB",
        info="#4E72AD",
        info_soft="#EAF0F9",
        composition_lean="#9A7895",
        composition_fat="#F3C35B",
        composition_total="#263746",
    ),
    "professional-data-clinic": ThemeTokens(
        key="professional-data-clinic",
        label="Profissional escuro",
        bg="#101B1D",
        surface="#152427",
        surface_alt="#1A2D30",
        surface_elevated="#20383A",
        sidebar_bg="#0B1719",
        topbar_bg="#152427",
        text="#F1F7F5",
        text_secondary="#B8CBC7",
        text_muted="#8BA19C",
        border="#294346",
        border_strong="#3A5B5B",
        accent="#35BFAF",
        accent_hover="#48D1C0",
        accent_contrast="#08201E",
        active="#1E5954",
        active_text="#F5FFFD",
        hover="#213B3D",
        success="#65D39B",
        success_soft="#183C30",
        warning="#F3BB5C",
        warning_soft="#4A3820",
        danger="#F28A86",
        danger_soft="#482527",
        info="#78B8FF",
        info_soft="#1E3854",
        composition_lean="#A98AA5",
        composition_fat="#F3BB5C",
        composition_total="#E7F3F0",
    ),
    "premium-soft-healthcare": ThemeTokens(
        key="premium-soft-healthcare",
        label="Clínico verde (legado)",
        bg="#F4F8F7",
        surface="#FFFFFF",
        surface_alt="#EDF5F3",
        surface_elevated="#FFFFFF",
        sidebar_bg="#0F4C48",
        topbar_bg="#FFFFFF",
        text="#18302E",
        text_secondary="#55706C",
        text_muted="#738883",
        border="#D6E5E1",
        border_strong="#B8D1CB",
        accent="#0F8074",
        accent_hover="#0C6A61",
        accent_contrast="#FFFFFF",
        active="#D9F0EB",
        active_text="#0B514A",
        hover="#E6F2EF",
        success="#18794E",
        success_soft="#DCF4E7",
        warning="#A96400",
        warning_soft="#FFF0D4",
        danger="#B53B3B",
        danger_soft="#FDE3E1",
        info="#1E63B6",
        info_soft="#E1EFFF",
        composition_lean="#8B7992",
        composition_fat="#EAB95C",
        composition_total="#18302E",
    ),
}


def get_theme(key: str | None = None) -> ThemeTokens:
    return THEMES.get(key or DEFAULT_THEME, THEMES[DEFAULT_THEME])


def build_stylesheet(t: ThemeTokens) -> str:
    """QSS global com contratos semânticos para telas novas e legadas."""
    return f"""
* {{ font-family: 'Segoe UI', 'Inter', Arial, sans-serif; font-size: 13px; color: {t.text}; }}
QMainWindow, QDialog, QWidget#appRoot {{ background: {t.bg}; }}

/* Shell */
QWidget#sidebar {{ background: {t.sidebar_bg}; border-right: 1px solid {t.border}; }}
QLabel#brand {{ color: {t.accent}; font-size: 23px; font-weight: 800; padding: 5px 4px 13px; }}
QLabel#navSection {{ color: {t.text_muted}; font-size: 10px; font-weight: 700; padding: 13px 7px 4px; letter-spacing: 1px; }}
QFrame#topbar {{ background: {t.topbar_bg}; border-bottom: 1px solid {t.border}; }}
QLabel#topbarContext {{ color: {t.text_secondary}; font-size: 12px; font-weight: 650; }}
QLabel#topbarResult {{ color: {t.text_muted}; font-size: 11px; }}
QFrame#sidebarProfile {{ background: transparent; border-top: 1px solid {t.border}; }}
QLineEdit#globalSearch {{ background: {t.surface}; min-height: 20px; }}

/* Buttons */
QPushButton {{ background: transparent; border: 1px solid transparent; border-radius: {t.radius_sm}px; padding: 8px 12px; color: {t.text}; }}
QPushButton:hover {{ background: {t.hover}; }}
QPushButton:focus {{ border-color: {t.accent}; }}
QPushButton:disabled {{ color: {t.text_muted}; background: transparent; border-color: {t.border}; }}
QPushButton[compact="true"] {{ padding: 5px 9px; }}
QPushButton[variant="primary"], QPushButton[primary="true"] {{ background: {t.accent}; color: {t.accent_contrast}; border-color: {t.accent}; font-weight: 700; text-align: center; }}
QPushButton[variant="primary"]:hover, QPushButton[primary="true"]:hover {{ background: {t.accent_hover}; border-color: {t.accent_hover}; }}
QPushButton[variant="secondary"] {{ background: {t.surface}; color: {t.text}; border-color: {t.border}; }}
QPushButton[variant="secondary"]:hover {{ background: {t.hover}; border-color: {t.border_strong}; }}
QPushButton[variant="ghost"] {{ background: transparent; color: {t.text_secondary}; border-color: transparent; }}
QPushButton[variant="ghost"]:hover {{ background: {t.hover}; color: {t.text}; }}
QPushButton[variant="danger"] {{ background: {t.danger_soft}; color: {t.danger}; border-color: {t.danger}; font-weight: 700; }}
QPushButton[tone="success"] {{ background: {t.success_soft}; color: {t.success}; border-color: {t.success}; }}
QPushButton[tone="warning"] {{ background: {t.warning_soft}; color: {t.warning}; border-color: {t.warning}; }}
QPushButton[tone="danger"] {{ background: {t.danger_soft}; color: {t.danger}; border-color: {t.danger}; }}
QPushButton[tone="info"] {{ background: {t.info_soft}; color: {t.info}; border-color: {t.info}; }}
QWidget#sidebar QPushButton {{ color: {t.text_secondary}; text-align: left; padding: 9px 11px; background: transparent; border-color: transparent; }}
QWidget#sidebar QPushButton:hover {{ color: {t.text}; background: {t.hover}; }}
QWidget#sidebar QPushButton[active="true"] {{ color: {t.active_text}; background: {t.active}; font-weight: 700; }}
QWidget#sidebar QPushButton[variant="primary"], QWidget#sidebar QPushButton[primary="true"] {{ background: {t.accent}; color: {t.accent_contrast}; border-color: {t.accent}; font-weight: 700; text-align: center; }}
QWidget#sidebar QPushButton[variant="primary"]:hover, QWidget#sidebar QPushButton[primary="true"]:hover {{ background: {t.accent_hover}; color: {t.accent_contrast}; border-color: {t.accent_hover}; }}

/* Inputs e formulários */
QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {{ background: {t.surface}; border: 1px solid {t.border}; border-radius: {t.radius_sm}px; padding: 8px 10px; selection-background-color: {t.active}; }}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{ border: 1px solid {t.accent}; }}
QComboBox QAbstractItemView {{ background: {t.surface_elevated}; border: 1px solid {t.border}; selection-background-color: {t.active}; }}
QLabel#fieldLabel {{ color: {t.text_secondary}; font-size: 12px; font-weight: 650; }}
QFrame#formSection {{ background: {t.surface}; border: 1px solid {t.border}; border-radius: {t.radius_md}px; }}
QFrame#tableToolbar {{ background: {t.surface_alt}; border: 1px solid {t.border}; border-radius: {t.radius_md}px; }}

/* Dados */
QTableWidget, QTableView {{ background: {t.surface}; alternate-background-color: {t.surface_alt}; border: 1px solid {t.border}; border-radius: {t.radius_md}px; gridline-color: transparent; selection-background-color: {t.active}; }}
QHeaderView::section {{ background: {t.surface_alt}; color: {t.text_secondary}; border: 0; border-bottom: 1px solid {t.border}; padding: 9px 10px; font-weight: 700; }}
QTableWidget::item {{ border-bottom: 1px solid {t.border}; padding: 7px 10px; }}
QTableWidget::item:hover, QTableView::item:hover {{ background: {t.hover}; }}
QTableWidget::item:selected, QTableView::item:selected {{ background: {t.active}; color: {t.active_text}; }}

/* Cards e tipografia */
QFrame#card {{ background: {t.surface}; border: 1px solid {t.border}; border-radius: {t.radius_md}px; }}
QFrame#softCard {{ background: {t.surface_alt}; border: 1px solid {t.border}; border-radius: {t.radius_md}px; }}
QFrame#comparisonCard {{ background: {t.surface}; border: 1px solid {t.border}; border-radius: 10px; }}
QLabel#pageTitle {{ font-size: 25px; font-weight: 800; color: {t.text}; }}
QLabel#pageSubtitle, QLabel#muted {{ color: {t.text_muted}; }}
QLabel#metricLabel {{ color: {t.text_secondary}; font-weight: 600; }}
QLabel#metricValue {{ color: {t.text}; font-size: 24px; font-weight: 800; }}
QLabel#comparisonValue {{ color: {t.text}; font-size: 15px; font-weight: 800; }}
QLabel#comparisonDelta {{ color: {t.success}; font-size: 12px; font-weight: 700; }}
QLabel#sectionTitle {{ color: {t.text}; font-size: 15px; font-weight: 750; }}

/* Prontuário */
QFrame#patientHeader {{ background: {t.surface}; border: 1px solid {t.border}; border-radius: {t.radius_md}px; }}
QLabel#patientName {{ color: {t.text}; font-size: 22px; font-weight: 800; }}
QLabel#patientNext {{ color: {t.accent}; font-size: 12px; font-weight: 650; }}
QFrame#timelineItem {{ background: transparent; border-bottom: 1px solid {t.border}; }}
QLabel#timelineMarker {{ color: {t.accent}; font-size: 11px; }}
QLabel#timelineDate {{ color: {t.text_muted}; font-size: 11px; }}
QLabel#timelineTitle {{ color: {t.text}; font-weight: 650; }}

/* Badges e feedback */
QLabel[badge="true"] {{ border-radius: 7px; padding: 4px 8px; font-size: 11px; font-weight: 700; }}
QLabel[badge="true"][tone="success"] {{ background: {t.success_soft}; color: {t.success}; }}
QLabel[badge="true"][tone="warning"] {{ background: {t.warning_soft}; color: {t.warning}; }}
QLabel[badge="true"][tone="danger"] {{ background: {t.danger_soft}; color: {t.danger}; }}
QLabel[badge="true"][tone="info"] {{ background: {t.info_soft}; color: {t.info}; }}
QLabel[badge="true"][tone="neutral"] {{ background: {t.surface_alt}; color: {t.text_secondary}; }}
QLabel#saveState[saveState="saved"] {{ color: {t.success}; }}
QLabel#saveState[saveState="saving"] {{ color: {t.warning}; }}
QLabel#saveState[saveState="error"] {{ color: {t.danger}; }}

/* Agenda */
QCalendarWidget {{ background: {t.surface}; border: 1px solid {t.border}; border-radius: {t.radius_md}px; }}
QCalendarWidget QWidget#qt_calendar_navigationbar {{ background: {t.surface_alt}; }}
QCalendarWidget QToolButton {{ background: transparent; color: {t.text}; border: 0; padding: 7px; font-weight: 650; }}
QCalendarWidget QToolButton:hover {{ background: {t.hover}; }}
QCalendarWidget QMenu {{ background: {t.surface_elevated}; color: {t.text}; }}
QCalendarWidget QAbstractItemView {{ background: {t.surface}; color: {t.text}; selection-background-color: {t.active}; selection-color: {t.active_text}; outline: 0; }}

/* Tabs, scroll e tooltip */
QTabWidget::pane {{ border: 0; background: transparent; }}
QTabBar::tab {{ color: {t.text_muted}; padding: 10px 14px; margin-right: 4px; border-bottom: 2px solid transparent; }}
QTabBar::tab:hover {{ color: {t.text}; background: {t.hover}; }}
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
        stored = self.settings.value(THEME_SETTING_KEY, None)
        try:
            generation = int(self.settings.value(THEME_VISUAL_GENERATION_KEY, 0) or 0)
        except (TypeError, ValueError):
            generation = 0

        # A 6.1–6.3 gravava o tema escuro como padrão. Na primeira execução da
        # geração visual 2, esse antigo padrão é migrado para a identidade rosé.
        # Temas alternativos explicitamente diferentes continuam preservados.
        if generation < THEME_VISUAL_GENERATION and (stored is None or str(stored) == LEGACY_DEFAULT_THEME):
            self._key = DEFAULT_THEME
            self.settings.setValue(THEME_SETTING_KEY, DEFAULT_THEME)
        else:
            self._key = str(stored or DEFAULT_THEME)
        if generation < THEME_VISUAL_GENERATION:
            self.settings.setValue(THEME_VISUAL_GENERATION_KEY, THEME_VISUAL_GENERATION)

    @property
    def key(self) -> str:
        return self._key if self._key in THEMES else DEFAULT_THEME

    def apply(self, key: str | None = None, *, persist: bool = True) -> str:
        chosen = key if key in THEMES else self.key
        self._key = chosen
        if persist:
            self.settings.setValue(THEME_SETTING_KEY, chosen)
            self.settings.setValue(THEME_VISUAL_GENERATION_KEY, THEME_VISUAL_GENERATION)
        self.app.setStyleSheet(build_stylesheet(get_theme(chosen)))
        self.theme_changed.emit(chosen)
        return chosen
