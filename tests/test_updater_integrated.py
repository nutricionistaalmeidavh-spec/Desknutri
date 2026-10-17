from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from nutridesktop.data.database import Database
from nutridesktop.services import update_service as updater
from nutridesktop.services.update_service import UpdateInfo, UpdateService


@pytest.fixture
def service(tmp_path):
    database = Database(tmp_path / "clinica.db")
    with database.connect() as conn:
        conn.execute("CREATE TABLE configuracoes(chave TEXT PRIMARY KEY, valor TEXT)")
        conn.execute(
            "CREATE TABLE app_update_history(id INTEGER PRIMARY KEY, from_version TEXT, "
            "to_version TEXT, status TEXT, manifest_url TEXT, details_json TEXT)"
        )
        conn.execute("CREATE TABLE pacientes(id INTEGER PRIMARY KEY, nome TEXT)")
        conn.execute("INSERT INTO pacientes(nome) VALUES('Paciente preservado')")
    return UpdateService(database)


def info(version="6.5.0"):
    return UpdateInfo(version, "stable", "https://github.com/example/setup.exe", "0" * 64)


def test_backup_before_update_is_consistent_and_keeps_original(service, tmp_path):
    backup = service.backup_before_update(info(), directory=tmp_path / "backups")
    assert backup.exists()
    with sqlite3.connect(backup) as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conn.execute("SELECT nome FROM pacientes").fetchone()[0] == "Paciente preservado"
    with service.db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM pacientes").fetchone()[0] == 1


def test_download_uses_atomic_file_and_sha256(service, tmp_path):
    source = tmp_path / "setup.exe"
    source.write_bytes(b"installer-test-bytes")
    target = tmp_path / "download" / "setup.exe"
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    progresses = []
    service._download(str(source), target, digest, progress=progresses.append)
    assert target.read_bytes() == source.read_bytes()
    assert progresses[-1] == 100
    assert not target.with_suffix(".exe.part").exists()


def test_invalid_download_cannot_be_installed(service, tmp_path):
    source = tmp_path / "source.exe"
    source.write_bytes(b"corrupted")
    target = tmp_path / "download" / "setup.exe"
    with pytest.raises(ValueError, match="SHA-256"):
        service._download(str(source), target, "0" * 64)
    assert not target.exists()
    assert not target.with_suffix(".exe.part").exists()


def test_pending_update_only_completes_on_matching_version(service, tmp_path, monkeypatch):
    pending = tmp_path / "pending.json"
    pending.write_text(json.dumps({
        "from_version": "6.4.0", "to_version": "99.0.0",
        "backup_path": str(tmp_path / "backup.db"),
    }), encoding="utf-8")
    monkeypatch.setattr(updater, "PENDING_FILE", pending)
    monkeypatch.setattr(updater, "RESULT_FILE", tmp_path / "result.json")
    assert service.complete_pending_update() is None
    assert pending.exists()


def test_post_update_healthcheck_records_success(service, tmp_path, monkeypatch):
    pending = tmp_path / "pending.json"
    pending.write_text(json.dumps({
        "from_version": "6.3.0", "to_version": updater.APP_VERSION,
        "backup_path": str(tmp_path / "backup.db"),
    }), encoding="utf-8")
    monkeypatch.setattr(updater, "PENDING_FILE", pending)
    monkeypatch.setattr(updater, "RESULT_FILE", tmp_path / "result.json")
    result = service.complete_pending_update()
    assert result["status"] == "healthy"
    assert not pending.exists()
    assert json.loads((tmp_path / "result.json").read_text(encoding="utf-8"))["status"] == "healthy"


def test_healthcheck_failure_preserves_recovery_marker(service, tmp_path, monkeypatch):
    pending = tmp_path / "pending.json"
    pending.write_text(json.dumps({
        "from_version": "6.3.0", "to_version": updater.APP_VERSION,
        "backup_path": str(tmp_path / "backup.db"),
    }), encoding="utf-8")
    monkeypatch.setattr(updater, "PENDING_FILE", pending)
    monkeypatch.setattr(updater, "RESULT_FILE", tmp_path / "result.json")
    # Simulate a damaged database without corrupting patient fixtures in-place.
    broken = tmp_path / "corrupt.db"
    broken.write_bytes(b"this is not an SQLite database")
    service.db.path = broken
    with pytest.raises(RuntimeError, match="integridade"):
        service.complete_pending_update()
    assert pending.exists()
