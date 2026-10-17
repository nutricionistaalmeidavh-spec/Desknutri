from pathlib import Path

from nutridesktop.ui.application_window import MainWindow
from nutridesktop.ui.main_window import MainWindow as CoreMainWindow
from nutridesktop.ui.window_features import OperationalFeaturesMixin


def test_canonical_window_preserves_local_operational_runtime():
    mro = MainWindow.__mro__
    assert mro.index(OperationalFeaturesMixin) < mro.index(CoreMainWindow)
    assert all(base.__name__ != "AccountFeaturesMixin" for base in mro)


def test_canonical_window_keeps_backup_and_portability_without_license_controls():
    expected = {"updates_page", "exports_page", "support_page", "save_backup_policy"}
    assert expected.issubset(set(dir(MainWindow)))
    for obsolete in ("account_page", "open_account_activation", "refresh_account", "unlink_account"):
        assert not hasattr(MainWindow, obsolete)


def test_entrypoint_no_longer_depends_on_accounts_or_versioned_windows():
    source = Path("app.py").read_text(encoding="utf-8")
    assert "from nutridesktop.ui.application_window import MainWindow" in source
    assert "v4_main_window" not in source
    assert "p3_main_window" not in source
    assert "_ensure_license" not in source
    assert "AccountActivationDialog" not in source
    assert "account_licensing" not in source
    assert "if row and row['pin_hash']:" in source
