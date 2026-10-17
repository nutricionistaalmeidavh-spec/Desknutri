from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import urllib.request
from contextlib import closing
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path

from nutridesktop.core.paths import BACKUP_DIR, UPDATE_DIR
from nutridesktop.data.database import Database, db
from nutridesktop.version import APP_VERSION, RELEASE_CHANNEL
from .app_settings import AppSettings

DEFAULT_RELEASE_API = (
    "https://api.github.com/repos/nutricionistaalmeidavh-spec/Desknutri/releases/latest"
)
LEGACY_MANIFEST_SUFFIX = "/releases/latest/download/version.json"
CHECKSUM_ASSET = "SHA256SUMS.txt"
RESULT_FILE = UPDATE_DIR / "last_update_result.json"
PENDING_FILE = UPDATE_DIR / "pending_update.json"



_INSTALL_HELPER_SCRIPT = r"""
param(
    [Parameter(Mandatory=$true)][int]$ParentPid,
    [Parameter(Mandatory=$true)][string]$Installer,
    [Parameter(Mandatory=$true)][string]$Executable,
    [Parameter(Mandatory=$true)][string]$LogPath
)
$ErrorActionPreference = 'Stop'
try { Wait-Process -Id $ParentPid -ErrorAction SilentlyContinue } catch {}
try {
    $proc = Start-Process -FilePath $Installer -ArgumentList '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-' -Verb RunAs -PassThru -Wait
    if ($proc.ExitCode -ne 0 -and $proc.ExitCode -ne 3010) {
        throw "Instalador terminou com código $($proc.ExitCode)"
    }
    Add-Content -LiteralPath $LogPath -Value "Instalação concluída: $($proc.ExitCode)"
} catch {
    Add-Content -LiteralPath $LogPath -Value "Falha na instalação: $($_.Exception.Message)"
}
# In case of installer error, reopen the previous executable for assisted recovery.
if (Test-Path -LiteralPath $Executable) {
    try { Start-Process -FilePath $Executable } catch {
        Add-Content -LiteralPath $LogPath -Value "Falha ao reabrir: $($_.Exception.Message)"
    }
}
"""

@dataclass(frozen=True)
class UpdateInfo:
    version: str
    channel: str
    installer_url: str
    sha256: str
    notes: str = ""
    mandatory: bool = False
    published_at: str = ""
    release_url: str = ""


def _version_tuple(v: str):
    core = v.lstrip("vV").split("-", 1)[0]
    parts = []
    for value in core.split("."):
        try:
            parts.append(int(value))
        except ValueError:
            parts.append(0)
    return tuple((parts + [0, 0, 0])[:3])


def is_newer(candidate: str, current: str = APP_VERSION) -> bool:
    return _version_tuple(candidate) > _version_tuple(current)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _request(url: str):
    return urllib.request.Request(
        url,
        headers={
            "User-Agent": f"NutriDesk/{APP_VERSION}",
            "Accept": "application/vnd.github+json",
        },
    )


def _read_url(url: str) -> bytes:
    path = Path(url)
    if path.exists():
        return path.read_bytes()
    with urllib.request.urlopen(_request(url), timeout=20) as response:
        return response.read()


def _read_json(url: str) -> dict:
    return json.loads(_read_url(url).decode("utf-8"))


def _asset(release: dict, name: str) -> dict | None:
    for item in release.get("assets") or []:
        if item.get("name") == name:
            return item
    return None


def _checksum_for(text: str, filename: str) -> str | None:
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            continue
        digest, listed = parts
        listed = listed.strip().lstrip("*")
        if listed == filename and len(digest) == 64:
            return digest.lower()
    return None


class UpdateService:
    # Mantemos a chave histórica de configuração para não criar migração de schema.
    SOURCE_KEY = "p3.update_manifest_url"
    MANIFEST_KEY = SOURCE_KEY
    AUTO_KEY = "p3.update_auto"
    CHANNEL_KEY = "p3.update_channel"

    def __init__(self, database: Database = db):
        self.db = database
        self.settings = AppSettings(database)

    def release_api_url(self) -> str:
        saved = (self.settings.get(self.SOURCE_KEY, "") or "").strip()
        if not saved or saved.endswith(LEGACY_MANIFEST_SUFFIX):
            return DEFAULT_RELEASE_API
        return saved

    # Aliases preservados para chamadas legadas da UI/P3.
    def manifest_url(self) -> str:
        return self.release_api_url()

    def set_manifest_url(self, url):
        self.settings.set(self.SOURCE_KEY, (url or "").strip())

    def auto_check(self) -> bool:
        return bool(self.settings.get(self.AUTO_KEY, True))

    def set_auto_check(self, value):
        self.settings.set(self.AUTO_KEY, bool(value))

    def channel(self) -> str:
        return self.settings.get(self.CHANNEL_KEY, RELEASE_CHANNEL) or RELEASE_CHANNEL

    def set_channel(self, value):
        # GitHub /releases/latest representa o canal estável. Mantemos a API por compatibilidade.
        self.settings.set(self.CHANNEL_KEY, "stable")

    def check(self, url=None) -> UpdateInfo | None:
        source = (url or self.release_api_url()).strip()
        if not source:
            return None
        if source.endswith(LEGACY_MANIFEST_SUFFIX):
            source = DEFAULT_RELEASE_API

        release = _read_json(source)
        if release.get("draft") or release.get("prerelease"):
            return None

        version = str(release.get("tag_name") or release.get("name") or "").lstrip("vV")
        if not version or not is_newer(version):
            return None

        installer_name = f"NutriDesktop-Setup-{version}.exe"
        installer = _asset(release, installer_name)
        checksums = _asset(release, CHECKSUM_ASSET)
        if not installer:
            raise ValueError(f"Release {version} não contém {installer_name}")
        if not checksums:
            raise ValueError(f"Release {version} não contém {CHECKSUM_ASSET}")

        checksum_text = _read_url(checksums["browser_download_url"]).decode("utf-8")
        digest = _checksum_for(checksum_text, installer_name)
        if not digest:
            raise ValueError(f"Checksum de {installer_name} não encontrado em {CHECKSUM_ASSET}")

        return UpdateInfo(
            version=version,
            channel="stable",
            installer_url=installer["browser_download_url"],
            sha256=digest,
            notes=release.get("body") or "",
            published_at=release.get("published_at") or "",
            release_url=release.get("html_url") or "",
        )

    def _download(self, url: str, dest: Path, expected: str, progress=None):
        """Download in chunks; publish EXE only after SHA-256 verification."""
        dest.parent.mkdir(parents=True, exist_ok=True)
        partial = dest.with_name(dest.name + ".part")
        partial.unlink(missing_ok=True)
        source = Path(url)
        response = source.open("rb") if source.is_file() else urllib.request.urlopen(_request(url), timeout=30)
        digest = hashlib.sha256()
        downloaded = 0
        try:
            with response, partial.open("wb") as target:
                size = int(getattr(response, "headers", {}).get("Content-Length", 0) or 0)
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    target.write(chunk)
                    digest.update(chunk)
                    downloaded += len(chunk)
                    if progress and size:
                        progress(min(99, int(downloaded * 100 / size)))
            if digest.hexdigest().lower() != expected.lower():
                raise ValueError("SHA-256 do instalador não confere com a Release do GitHub")
            os.replace(partial, dest)
            if progress:
                progress(100)
            return dest
        except Exception:
            partial.unlink(missing_ok=True)
            raise

    def backup_before_update(self, info: UpdateInfo, directory: Path = BACKUP_DIR) -> Path:
        """Consistent SQLite snapshot including the WAL; original data is untouched."""
        directory.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
        backup = directory / f"nutridesk-preupdate-{APP_VERSION}-to-{info.version}-{stamp}.db"
        try:
            with closing(self.db.connect()) as original, closing(sqlite3.connect(backup)) as target:
                original.backup(target)
            with closing(sqlite3.connect(backup)) as verify:
                if verify.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise RuntimeError("Backup clínico falhou na verificação de integridade")
            return backup
        except Exception:
            backup.unlink(missing_ok=True)
            raise

    def stage(self, info: UpdateInfo, progress=None):
        installer = self._download(
            info.installer_url,
            UPDATE_DIR / f"NutriDesktop-Setup-{info.version}.exe",
            info.sha256,
            progress=progress,
        )
        backup = self.backup_before_update(info)
        return installer, backup

    def launch_staged(self, info: UpdateInfo, installer: Path, rollback_installer=None):
        if os.name != "nt":
            raise RuntimeError("A instalação integrada está disponível no Windows.")
        installer = Path(installer)
        if not installer.is_file() or sha256_file(installer).lower() != info.sha256.lower():
            raise RuntimeError("Instalador ausente ou alterado após a validação SHA-256.")
        backup = Path(rollback_installer) if rollback_installer else None
        if not backup or not backup.is_file():
            raise RuntimeError("Backup clínico pré-atualização não encontrado. Operação cancelada.")
        if not getattr(sys, "frozen", False):
            raise RuntimeError("Instalação integrada disponível apenas no executável empacotado.")

        script = UPDATE_DIR / "install-update.ps1"
        script.write_text(_INSTALL_HELPER_SCRIPT, encoding="utf-8-sig")
        PENDING_FILE.write_text(json.dumps({
            "from_version": APP_VERSION,
            "to_version": info.version,
            "backup_path": str(backup),
            "installer": str(installer),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }, ensure_ascii=False), encoding="utf-8")
        try:
            subprocess.Popen(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden",
                 "-ExecutionPolicy", "Bypass", "-File", str(script),
                 "-ParentPid", str(os.getpid()), "-Installer", str(installer),
                 "-Executable", sys.executable, "-LogPath", str(UPDATE_DIR / "install-update.log")],
                close_fds=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW,
            )
        except Exception:
            PENDING_FILE.unlink(missing_ok=True)
            raise
        self._record_history(APP_VERSION, info.version, "installer_started", info.release_url)
        return True

    def complete_pending_update(self):
        """On the next launch, confirm target version and clinic database integrity."""
        if not PENDING_FILE.is_file():
            return None
        data = json.loads(PENDING_FILE.read_text(encoding="utf-8"))
        if data.get("to_version") != APP_VERSION:
            return None
        with closing(self.db.connect()) as conn:
            if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError(
                    "Falha na integridade do banco após atualizar. "
                    f"Preserve os dados e utilize o backup: {data.get('backup_path')}"
                )
        result = {
            "status": "healthy",
            "from_version": data.get("from_version"),
            "to_version": APP_VERSION,
            "backup_path": data.get("backup_path"),
        }
        RESULT_FILE.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
        self._record_history(data.get("from_version") or "", APP_VERSION,
                             "healthy", "Verificação SQLite pós-instalação concluída")
        PENDING_FILE.unlink(missing_ok=True)
        return result

    def _record_history(self, from_version: str, to_version: str, status: str, details: str = ""):
        with self.db.transaction() as c:
            c.execute(
                "INSERT INTO app_update_history(from_version,to_version,status,manifest_url,details_json) VALUES(?,?,?,?,?)",
                (
                    from_version,
                    to_version,
                    status,
                    self.release_api_url(),
                    json.dumps({"details": details}, ensure_ascii=False),
                ),
            )

    def record_result(self):
        # Compatibilidade com updates P3 antigos que possam ter deixado resultado pendente.
        if not RESULT_FILE.exists():
            return None
        try:
            data = json.loads(RESULT_FILE.read_text(encoding="utf-8-sig"))
        except Exception:
            return None
        self._record_history(
            data.get("from_version") or "",
            data.get("to_version") or "",
            data.get("status") or "legacy",
            data.get("details") or "",
        )
        RESULT_FILE.unlink(missing_ok=True)
        return data

    def history(self, limit=20):
        with self.db.connect() as c:
            return c.execute(
                "SELECT * FROM app_update_history ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
