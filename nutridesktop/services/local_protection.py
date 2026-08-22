from __future__ import annotations
import os
import subprocess
from pathlib import Path

from nutridesktop.core.paths import DATA_DIR, DB_PATH


class LocalProtectionService:
    """Optional transparent at-rest protection using Windows EFS/NTFS.

    EFS is intentionally optional because availability depends on the Windows
    edition, filesystem and organization policy. Failure never silently falls
    back to an unverified "encrypted" state.
    """

    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = Path(data_dir)

    @staticmethod
    def supported() -> bool:
        return os.name == "nt"

    def _run(self, *args: str) -> str:
        if not self.supported():
            raise RuntimeError("Criptografia EFS está disponível apenas no Windows com NTFS/EFS habilitado.")
        proc = subprocess.run(
            ["cipher", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            check=False,
        )
        text = (proc.stdout or "") + "\n" + (proc.stderr or "")
        if proc.returncode != 0:
            raise RuntimeError(f"Windows EFS não pôde concluir a operação (código {proc.returncode}).\n{text.strip()}")
        return text.strip()

    def enable(self) -> str:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        # /S applies recursively; marking the directory encrypted also makes
        # subsequently created patient files inherit EFS protection.
        return self._run("/E", f"/S:{self.data_dir}")

    def disable(self) -> str:
        return self._run("/D", f"/S:{self.data_dir}")

    def status(self) -> str:
        target = DB_PATH if Path(DB_PATH).exists() else self.data_dir
        return self._run("/C", str(target))
