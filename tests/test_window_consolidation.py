from pathlib import Path

from nutridesktop.ui.application_window import MainWindow
from nutridesktop.ui.main_window import MainWindow as CoreMainWindow
from nutridesktop.ui.window_features import AccountFeaturesMixin, OperationalFeaturesMixin


def test_canonical_window_preserves_previous_runtime_order():
    mro = MainWindow.__mro__
    assert mro.index(AccountFeaturesMixin) < mro.index(OperationalFeaturesMixin)
    assert mro.index(OperationalFeaturesMixin) < mro.index(CoreMainWindow)


def test_canonical_window_exposes_p3_and_v4_capabilities():
    expected = {
        "updates_page",
        "exports_page",
        "support_page",
        "save_backup_policy",
        "account_page",
        "open_account_activation",
        "refresh_account",
        "change_account_password",
        "unlink_account",
    }
    assert expected.issubset(set(dir(MainWindow)))


def test_entrypoint_no_longer_depends_on_versioned_window_classes():
    source = Path("app.py").read_text(encoding="utf-8")
    assert "from nutridesktop.ui.application_window import MainWindow" in source
    assert "v4_main_window" not in source
    assert "p3_main_window" not in source
