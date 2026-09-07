from pathlib import Path

from nutridesktop.ui.application_window import MainWindow
from nutridesktop.ui.final_polish import (
    FinalPolishMixin,
    PAGE_TRANSITION_MS,
    SAVE_FEEDBACK_MS,
)
from nutridesktop.version import APP_VERSION


ROOT = Path(__file__).resolve().parents[1]


LEGACY_FILES = [
    "APLICAR_V3_P3.ps1",
    "ROLLBACK_V3_P3.ps1",
    "VERIFICAR_V3_P3.ps1",
    "APLICAR_V4_CONTAS.ps1",
    "ROLLBACK_V4_CONTAS.ps1",
    "VERIFICAR_V4_CONTAS.ps1",
    "README_P3.md",
    "README_V4_1_ACESSO_EMAIL.md",
    "README_V4_CONTAS.md",
    "RELATORIO_VERIFICACAO_P3.md",
    "RELATORIO_VERIFICACAO_V4.md",
    "MATRIZ_P3_29_35.md",
    "MATRIZ_V4_CONTA_LICENCAS.md",
    "MANIFEST_SHA256.txt",
    "config/README_UPDATE_KEY.txt",
]


def test_motion_durations_are_discreet_and_polish_mixin_is_first():
    assert 160 <= PAGE_TRANSITION_MS <= 280
    assert 160 <= SAVE_FEEDBACK_MS <= 280
    assert MainWindow.mro().index(FinalPolishMixin) == 1


def test_version_py_is_current_release_source_of_truth():
    iss = (ROOT / "NutriDesktop.iss").read_text(encoding="utf-8")
    build = (ROOT / "tools" / "build_release.py").read_text(encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").lstrip()
    main_window = (ROOT / "nutridesktop" / "ui" / "main_window.py").read_text(encoding="utf-8")

    assert '#define MyAppVersion "' not in iss
    assert "#error MyAppVersion must be provided" in iss
    assert "f'/DMyAppVersion={APP_VERSION}'" in build
    assert "validate_version_contract()" in build
    assert changelog.startswith(f"# NutriDesktop {APP_VERSION}")
    assert "setWindowTitle(f'NutriDesk {APP_VERSION}')" in main_window


def test_obsolete_p3_v4_delivery_files_are_removed():
    missing = [path for path in LEGACY_FILES if (ROOT / path).exists()]
    assert not missing, f"Arquivos legados ainda presentes: {missing}"


def test_canonical_replacements_for_removed_delivery_scripts_exist():
    expected = [
        "nutridesktop/data/migrations.py",
        "nutridesktop/services/update_service.py",
        "nutridesktop/services/auto_backup.py",
        "nutridesktop/services/account_licensing.py",
        "nutridesktop/ui/auto_update_features.py",
        "license_server/main.py",
        ".github/workflows/verify.yml",
        ".github/workflows/release.yml",
    ]
    assert all((ROOT / path).exists() for path in expected)
