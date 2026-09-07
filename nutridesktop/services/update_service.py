from __future__ import annotations

import hashlib
import json
import os
import subprocess
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from nutridesktop.core.paths import UPDATE_DIR
from nutridesktop.data.database import Database, db
from nutridesktop.version import APP_VERSION, RELEASE_CHANNEL
from .app_settings import AppSettings

DEFAULT_RELEASE_API = (
    "https://api.github.com/repos/nutricionistaalmeidavh-spec/Desknutri/releases/latest"
)
LEGACY_MANIFEST_SUFFIX = "/releases/latest/download/version.json"
CHECKSUM_ASSET = "SHA256SUMS.txt"
RESULT_FILE = UPDATE_DIR / "last_update_result.json"


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

    def _download(self, url: str, dest: Path, expected: str):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(_read_url(url))
        actual = sha256_file(dest)
        if actual.lower() != expected.lower():
            dest.unlink(missing_ok=True)
            raise ValueError("SHA-256 do instalador não confere com a Release do GitHub")
        return dest

    def stage(self, info: UpdateInfo):
        installer = self._download(
            info.installer_url,
            UPDATE_DIR / f"NutriDesktop-Setup-{info.version}.exe",
            info.sha256,
        )
        # Segundo item mantido para compatibilidade com a chamada P3 anterior.
        return installer, None

    def launch_staged(self, info: UpdateInfo, installer: Path, rollback_installer=None):
        if os.name != "nt":
            raise RuntimeError("O instalador automático está disponível no Windows.")
        # Instalação propositalmente interativa: o usuário controla e confirma o processo.
        subprocess.Popen([str(installer)], close_fds=True)
        self._record_history(APP_VERSION, info.version, "installer_started", info.release_url)
        return True

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
