from pathlib import Path

from nutridesktop.ui.application_window import MainWindow
from nutridesktop.ui.main_window import MainWindow as CoreMainWindow
from nutridesktop.ui.refinement import UiRefinementMixin
from nutridesktop.ui.window_features import AccountFeaturesMixin, OperationalFeaturesMixin
from nutridesktop.ui_kit.components import StatusBadge, TableToolbar, UiButton, status_tone
from nutridesktop.ui_kit.theme import DEFAULT_THEME, build_stylesheet, get_theme


def test_canonical_window_keeps_behavior_layers_after_ui_refinement():
    mro = MainWindow.__mro__
    assert mro.index(UiRefinementMixin) < mro.index(AccountFeaturesMixin)
    assert mro.index(AccountFeaturesMixin) < mro.index(OperationalFeaturesMixin)
    assert mro.index(OperationalFeaturesMixin) < mro.index(CoreMainWindow)


def test_green_palette_is_preserved_for_default_theme():
    theme = get_theme(DEFAULT_THEME)
    assert theme.bg == "#101B1D"
    assert theme.surface == "#152427"
    assert theme.sidebar_bg == "#0B1719"
    assert theme.accent == "#35BFAF"
    assert theme.accent_hover == "#48D1C0"
    assert theme.active == "#1E5954"


def test_semantic_status_mapping_does_not_change_business_values():
    assert status_tone("Realizada") == "success"
    assert status_tone("Agendada") == "info"
    assert status_tone("Remarcada") == "info"
    assert status_tone("Faltou") == "warning"
    assert status_tone("Cancelada") == "danger"
    assert status_tone("Outro") == "neutral"


def test_stylesheet_exposes_new_component_contracts():
    qss = build_stylesheet(get_theme(DEFAULT_THEME))
    for contract in (
        'QFrame#topbar',
        'QFrame#tableToolbar',
        'QFrame#patientHeader',
        'QFrame#timelineItem',
        'QLabel[badge="true"]',
        'QPushButton[variant="primary"]',
        'QCalendarWidget',
    ):
        assert contract in qss


def test_phase_3_components_are_real_widgets():
    assert issubclass(UiButton, object)
    assert issubclass(StatusBadge, object)
    assert issubclass(TableToolbar, object)


def test_phase_4_to_6_methods_live_in_refinement_layer():
    expected = {
        "patients",
        "agenda",
        "refresh_agenda",
        "recipes",
        "dashboard",
        "run_global_search",
        "focus_global_search",
    }
    assert expected.issubset(set(dir(UiRefinementMixin)))


def test_patient_refinement_is_composed_without_rewriting_core_dialog():
    source = Path("nutridesktop/ui/refined_patient_dialog.py").read_text(encoding="utf-8")
    assert "class RefinedPatientDialog(CorePatientDialog)" in source
    assert "PatientHeader" in source
    assert "TimelineItem" in source


def test_core_business_files_are_not_replaced_by_refinement_imports():
    source = Path("nutridesktop/ui/refinement.py").read_text(encoding="utf-8")
    assert "PatientRepository(" not in source
    assert "AgendaRepository(" not in source
    assert "RecipeRepository(" not in source
    assert "SCHEMA_VERSION" not in source
