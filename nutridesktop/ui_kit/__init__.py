"""Camada visual do NutriDesk baseada no NutriDesk UI Kit."""

from .theme import DEFAULT_THEME, ThemeManager, build_stylesheet, get_theme
from .components import (
    FormGrid,
    FormSection,
    PatientHeader,
    SaveStateLabel,
    StatusBadge,
    TableToolbar,
    TimelineItem,
    UiButton,
    status_tone,
)

__all__ = [
    "DEFAULT_THEME",
    "ThemeManager",
    "build_stylesheet",
    "get_theme",
    "UiButton",
    "StatusBadge",
    "TableToolbar",
    "FormSection",
    "FormGrid",
    "PatientHeader",
    "TimelineItem",
    "SaveStateLabel",
    "status_tone",
]
