"""Contratos multiplataforma do instalador macOS e atualizações."""
from pathlib import Path
import hashlib
import json

import pytest

from nutridesktop.core import paths
from nutridesktop.services import update_service as updater
from nutridesktop.services.update_service import UpdateInfo, UpdateService, installer_filename
from nutridesktop.data.database import Database


def test_installer_filename_uses_native_package_for_each_platform():
    assert installer_filename("6.5.2", system="Windows") == "NutriDesktop-Setup-6.5.2.exe"
    assert installer_filename("6.5.2", system="Darwin", architecture="arm64") == "NutriDesk-6.5.2-macos-arm64.dmg"
    assert installer_filename("6.5.2", system="Darwin", architecture="x86_64") == "NutriDesk-6.5.2-macos-x86_64.dmg"
    with pytest.raises(RuntimeError, match="arquitetura"):
        installer_filename("6.5.2", system="Darwin", architecture="mips")
    with pytest.raises(RuntimeError, match="suportado"):
        installer_filename("6.5.2", system="Linux")


def test_macos_uses_application_support_and_respects_existing_local_data(tmp_path, monkeypatch):
    monkeypatch.delenv("NUTRIDESKTOP_DATA_DIR", raising=False)
    monkeypatch.setattr(paths.sys, "platform", "darwin")
    monkeypatch.setattr(paths.Path, "home", classmethod(lambda cls: tmp_path))
    native = tmp_path / "Library" / "Application Support" / "NutriDesktop"
    assert paths.app_data_dir() == native

    previous = tmp_path / ".local" / "share" / "NutriDesktop"
    previous.mkdir(parents=True)
    (previous / "nutridesktop.db").write_bytes(b"previous-clinical-db")
    assert paths.app_data_dir() == previous

    override = tmp_path / "custom"
    monkeypatch.setenv("NUTRIDESKTOP_DATA_DIR", str(override))
    assert paths.app_data_dir() == override


def test_macos_update_checks_exact_architecture_and_checksum(tmp_path, monkeypatch):
    database = Database(tmp_path / "db.sqlite")
    database.initialize()
    svc = UpdateService(database)
    monkeypatch.setattr(updater.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(updater.platform, "machine", lambda: "arm64")
    name = "NutriDesk-99.1.0-macos-arm64.dmg"
    digest = hashlib.sha256(b"test-dmg").hexdigest()
    checksum = tmp_path / "checksums.txt"
    checksum.write_text(f"{digest}  {name}\n", encoding="utf-8")

    monkeypatch.setattr(updater, "_read_json", lambda _: {
        "tag_name": "v99.1.0",
        "draft": False,
        "prerelease": False,
        "assets": [
            {"name": name, "browser_download_url": "https://example.invalid/" + name},
            {"name": updater.CHECKSUM_ASSET, "browser_download_url": str(checksum)},
            {"name": "NutriDesktop-Setup-99.1.0.exe", "browser_download_url": "https://example.invalid/windows.exe"},
        ],
    })
    info = svc.check()
    assert info.installer_url.endswith(name)
    assert info.sha256 == digest

    monkeypatch.setattr(updater.platform, "machine", lambda: "x86_64")
    with pytest.raises(ValueError, match="x86_64"):
        svc.check()


def test_mac_dmg_opens_after_backup_and_keeps_app_running(tmp_path, monkeypatch):
    database = Database(tmp_path / "db.sqlite")
    database.initialize()
    svc = UpdateService(database)
    monkeypatch.setattr(updater.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(updater.sys, "frozen", True, raising=False)
    pending = tmp_path / "pending.json"
    monkeypatch.setattr(updater, "PENDING_FILE", pending)
    called = []
    monkeypatch.setattr(updater.subprocess, "Popen", lambda command, **_: called.append(command))
    monkeypatch.setattr(updater.platform, "machine", lambda: "arm64")
    dmg = tmp_path / "NutriDesk-99.1.0-macos-arm64.dmg"
    dmg.write_bytes(b"test-dmg")
    backup = tmp_path / "clinical.db"
    backup.write_bytes(b"backup")
    info = UpdateInfo("99.1.0", "stable", str(dmg), hashlib.sha256(dmg.read_bytes()).hexdigest())
    assert svc.launch_staged(info, dmg, backup)
    assert called == [["open", str(dmg)]]
    assert json.loads(pending.read_text(encoding="utf-8"))["backup_path"] == str(backup)


def test_macos_build_files_are_present():
    root = Path(__file__).resolve().parents[1]
    assert (root / "nutridesktop-macos.spec").is_file()
    assert (root / "tools" / "build_macos.py").is_file()
    workflow = (root / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert "macos-15-intel" in workflow
    assert "macos-15" in workflow
    assert "SHA256SUMS.txt" in workflow
