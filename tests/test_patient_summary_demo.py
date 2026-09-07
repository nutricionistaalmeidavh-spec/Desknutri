import inspect
from pathlib import Path

from PySide6.QtWidgets import QApplication, QComboBox

from nutridesktop.data.database import Database
from nutridesktop.data.repositories import AssessmentRepository, PatientRepository
from nutridesktop.data.seed import DEMO_PATIENT_SEED_KEY, seed_demo_patient
from nutridesktop.ui.refined_patient_dialog import PatientEvolutionCard, RefinedPatientDialog


ROOT = Path(__file__).resolve().parents[1]


def ensure_app():
    return QApplication.instance() or QApplication([])


def test_demo_patient_is_seeded_once_only_in_empty_database(tmp_path):
    db = Database(tmp_path / "demo.db")
    db.initialize()
    pid = seed_demo_patient(db)
    assert pid is not None

    patients = PatientRepository(db).list()
    assert len(patients) == 1
    assert patients[0]["nome"] == "Mariana Souza • Demonstração"
    assert "fictícia" in patients[0]["observacoes"]

    assessments = AssessmentRepository(db).list(pid)
    assert len(assessments) == 3
    assert [row["peso"] for row in assessments] == [82.4, 79.8, 77.1]
    assert all(row["imc"] is not None for row in assessments)
    assert all(row["pg_final"] is not None for row in assessments)
    assert all(row["cintura"] is not None for row in assessments)

    assert seed_demo_patient(db) is None
    assert len(PatientRepository(db).list()) == 1
    with db.connect() as c:
        value = c.execute(
            "SELECT valor FROM configuracoes WHERE chave=?", (DEMO_PATIENT_SEED_KEY,)
        ).fetchone()[0]
    assert value == "1"


def test_demo_seed_does_not_touch_existing_patients(tmp_path):
    db = Database(tmp_path / "existing.db")
    db.initialize()
    repo = PatientRepository(db)
    repo.create("Paciente existente", "F", "1990-01-01")

    assert seed_demo_patient(db) is None
    rows = repo.list()
    assert len(rows) == 1
    assert rows[0]["nome"] == "Paciente existente"


def test_patient_evolution_card_reuses_existing_chart_engine(tmp_path):
    ensure_app()
    db = Database(tmp_path / "chart.db")
    db.initialize()
    pid = seed_demo_patient(db)
    assessments = AssessmentRepository(db).list(pid)

    card = PatientEvolutionCard(assessments)
    combo = card.findChild(QComboBox)
    assert combo is not None
    assert combo.currentData() == "peso"
    assert combo.count() >= 4
    assert card.canvas is not None
    ax = card.canvas.figure.axes[0]
    assert "Peso" in ax.get_title()
    assert len(ax.lines) == 1
    assert len(ax.lines[0].get_ydata()) == 3
    card.deleteLater()


def test_summary_and_startup_are_wired_to_new_behavior():
    summary_source = inspect.getsource(RefinedPatientDialog.summary_tab)
    assert "PatientEvolutionCard(assessments" in summary_source
    app_source = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "seed_demo_patient()" in app_source
