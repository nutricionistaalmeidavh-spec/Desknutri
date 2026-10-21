"""Regressões reais relatadas por Marcelo na versão 6.5.5: campos invisíveis e datas cortadas."""
from __future__ import annotations

from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication, QScrollArea, QWidget

from nutridesktop.data.database import db
from nutridesktop.data.repositories import PatientRepository
from nutridesktop.ui.refined_patient_dialog import RefinedPatientDialog
from nutridesktop.ui_kit.theme import get_theme, build_stylesheet, DEFAULT_THEME, THEMES


def test_patient_forms_have_painted_light_background_not_native_dark(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    previous = app.styleSheet()
    app.setStyleSheet(build_stylesheet(get_theme(DEFAULT_THEME)))
    monkeypatch.setattr(db, "path", tmp_path / "patient-ui-contrast.db")
    db.initialize()
    pid = PatientRepository().create("Paciente QA Marcelo", "F", "1995-06-12")
    dialog = RefinedPatientDialog(pid)
    dialog.resize(860, 550)
    dialog.show()
    try:
        for index in (1, 2):
            dialog.tabs.setCurrentIndex(index)
            app.processEvents()
            area = dialog.tabs.widget(index)
            assert isinstance(area, QScrollArea)
            content = area.widget()
            assert content.objectName() == "patientWorkspaceContent"
            assert content.autoFillBackground(), "Fundo do formulário deve ser pintado em todas as plataformas"
            # A paleta precisa ser explicitamente controlada pelo tema, não pelo modo escuro do Windows.
            expected = get_theme(DEFAULT_THEME).bg.lower()
            assert content.palette().color(QPalette.Window).name().lower() == expected
    finally:
        dialog.close()
        app.setStyleSheet(previous)


def test_patient_evolution_date_labels_fit_available_chart_height(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(db, "path", tmp_path / "patient-chart-dates.db")
    db.initialize()
    pid = PatientRepository().create("Paciente QA Gráfico", "F", "1995-06-12")
    from nutridesktop.data.repositories import AssessmentRepository
    ar = AssessmentRepository()
    for d, weight in [("2026-06-19", 82.4), ("2026-08-13", 79.8), ("2026-10-03", 77.1)]:
        ar.create(pid, {"data": d, "peso": weight, "altura_cm": 168,
                        "massa_magra": 56.5, "massa_gorda": weight - 56.5,
                        "pg_final": 31.5, "cintura": 92.0})
    dialog = RefinedPatientDialog(pid)
    dialog.resize(860, 550)
    dialog.show()
    try:
        dialog.tabs.setCurrentIndex(4)
        app.processEvents()
        card = dialog.evolution_comparison_card
        assert card.chart_tabs.minimumHeight() >= 400, "Gráfico deve ter espaço mínimo mesmo no notebook"
        for canvas in card.canvases.values():
            assert canvas.minimumHeight() >= 340
            canvas.draw()
            fig = canvas.figure
            renderer = fig.canvas.get_renderer()
            for axis in fig.axes:
                for label in axis.get_xticklabels():
                    if label.get_visible() and label.get_text():
                        bbox = label.get_window_extent(renderer)
                        assert bbox.y0 >= 6, f"Data cortada em {bbox} dentro de {fig.bbox}"
                        assert bbox.y1 <= fig.bbox.y1 - 6
    finally:
        dialog.close()


def test_patient_workspace_background_defined_in_all_themes():
    for theme in THEMES.values():
        stylesheet = build_stylesheet(theme)
        assert f"QWidget#patientWorkspaceContent {{ background: {theme.bg}; }}" in stylesheet
        assert f"QWidget#patientWorkspaceViewport {{ background: {theme.bg}; }}" in stylesheet
