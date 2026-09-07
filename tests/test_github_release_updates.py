from pathlib import Path

from nutridesktop.data.database import Database
from nutridesktop.services.update_service import DEFAULT_RELEASE_API, UpdateService
from nutridesktop.ui.application_window import MainWindow
from nutridesktop.ui.auto_update_features import GitHubReleaseUpdateMixin
from nutridesktop.ui.final_polish import FinalPolishMixin
from nutridesktop.ui.refinement import UiRefinementMixin


ROOT = Path(__file__).resolve().parents[1]


def test_default_source_points_to_latest_github_release(tmp_path):
    db = Database(tmp_path / "updates.db")
    db.initialize()
    svc = UpdateService(db)
    assert svc.release_api_url() == DEFAULT_RELEASE_API
    assert DEFAULT_RELEASE_API.endswith("/releases/latest")


def test_legacy_default_manifest_is_migrated_without_schema_change(tmp_path):
    db = Database(tmp_path / "updates.db")
    db.initialize()
    svc = UpdateService(db)
    svc.set_manifest_url(
        "https://github.com/nutricionistaalmeidavh-spec/Desknutri/releases/latest/download/version.json"
    )
    assert svc.release_api_url() == DEFAULT_RELEASE_API


def test_canonical_window_orders_polish_updater_then_refinement():
    mro = MainWindow.mro()
    assert mro.index(FinalPolishMixin) < mro.index(GitHubReleaseUpdateMixin)
    assert mro.index(GitHubReleaseUpdateMixin) < mro.index(UiRefinementMixin)


def test_updater_is_user_confirmed_not_silent():
    src = (ROOT / "nutridesktop" / "ui" / "auto_update_features.py").read_text(encoding="utf-8")
    service = (ROOT / "nutridesktop" / "services" / "update_service.py").read_text(encoding="utf-8")
    assert "QMessageBox.question" in src
    assert "Deseja baixar e abrir o instalador agora?" in src
    assert "/VERYSILENT" not in service
    assert "subprocess.Popen([str(installer)]" in service


def test_release_workflow_needs_no_update_signing_secret():
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    build = (ROOT / "tools" / "build_release.py").read_text(encoding="utf-8")
    assert "UPDATE_SIGNING_PRIVATE_KEY_B64" not in workflow
    assert "private-key" not in build
    assert "version.json" not in build
    assert "SHA256SUMS.txt" in build


def test_packaged_update_public_key_is_no_longer_required():
    assert not (ROOT / "config" / "update_public.pem").exists()
