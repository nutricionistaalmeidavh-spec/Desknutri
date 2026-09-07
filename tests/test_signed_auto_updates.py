from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from nutridesktop.data.database import Database
from nutridesktop.services.update_service import DEFAULT_MANIFEST_URL, UpdateService
from nutridesktop.ui.application_window import MainWindow
from nutridesktop.ui.auto_update_features import SignedAutoUpdateMixin


ROOT = Path(__file__).resolve().parents[1]


def test_default_manifest_points_to_latest_github_release(tmp_path):
    db = Database(tmp_path / "updates.db")
    db.initialize()
    svc = UpdateService(db)
    assert svc.manifest_url() == DEFAULT_MANIFEST_URL
    assert DEFAULT_MANIFEST_URL.endswith("/releases/latest/download/version.json")


def test_auto_install_defaults_to_enabled_and_is_configurable(tmp_path):
    db = Database(tmp_path / "updates.db")
    db.initialize()
    svc = UpdateService(db)
    assert svc.auto_install() is True
    svc.set_auto_install(False)
    assert svc.auto_install() is False


def test_packaged_public_update_key_is_ed25519():
    key_path = ROOT / "config" / "update_public.pem"
    assert key_path.exists()
    key = serialization.load_pem_public_key(key_path.read_bytes())
    assert isinstance(key, Ed25519PublicKey)


def test_canonical_window_uses_signed_auto_update_mixin_first():
    mro = MainWindow.mro()
    assert SignedAutoUpdateMixin in mro
    assert mro.index(SignedAutoUpdateMixin) < mro.index(MainWindow.__bases__[1])


def test_release_workflow_requires_signing_secret():
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert "UPDATE_SIGNING_PRIVATE_KEY_B64" in workflow
    assert "Release automática recusada" in workflow
    assert "--allow-unsigned" not in workflow
