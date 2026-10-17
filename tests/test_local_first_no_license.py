"""Contracts for an offline-first NutriDesk without commercial activation."""
from pathlib import Path
from nutridesktop.data.database import Database
from nutridesktop.services.security_settings import SecuritySettings
from nutridesktop.ui.application_window import MainWindow
from nutridesktop.ui.view_models import NAV_GROUPS
from nutridesktop.version import APP_VERSION, SCHEMA_VERSION

ROOT = Path(__file__).resolve().parents[1]

def source(path):
    return (ROOT / path).read_text(encoding="utf-8")

def test_no_startup_license_requirement():
    entry = source("app.py")
    for fragment in ("_ensure_license", "AccountLicenseService", "licensing.current", "AccountActivationDialog"):
        assert fragment not in entry
    assert "win=MainWindow();win.show();return app.exec()" in entry

def test_no_account_gate_in_window_or_navigation():
    runtime = source("nutridesktop/ui/application_window.py")
    shell = source("nutridesktop/ui/refinement.py")
    assert "AccountFeaturesMixin" not in runtime
    assert 'button("Conta"' not in shell
    assert "Conta" not in MainWindow.NAV
    assert "Conta" not in sum(NAV_GROUPS.values(), [])

def test_distribution_defaults_are_local_first():
    for path in ("nutridesktop/core/config.py", "config/commercial.example.json"):
        assert "license_server_url" not in source(path)
        assert "appdeploy.ai" not in source(path)

def test_optional_pin_remains_available(tmp_path):
    database = Database(tmp_path / "clinical.sqlite")
    database.initialize()
    security = SecuritySettings(database)
    assert security.get()["pin_hash"] is None
    security.set_pin("1234")
    assert security.verify("1234")
    assert not security.verify("0000")

def test_local_first_survives_schema_upgrade():
    assert tuple(int(segment) for segment in APP_VERSION.split(".")) >= (6, 5, 1)
    assert SCHEMA_VERSION == 14
