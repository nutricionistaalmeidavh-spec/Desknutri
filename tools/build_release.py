from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from nutridesktop.version import APP_VERSION


def run(cmd):
    print(">", *map(str, cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_version_contract() -> None:
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").lstrip()
    expected_heading = f"# NutriDesktop {APP_VERSION}"
    if not changelog.startswith(expected_heading):
        raise SystemExit(
            f"CHANGELOG.md precisa iniciar com {expected_heading!r}; "
            "nutridesktop/version.py é a fonte única da versão atual."
        )


def find_iscc():
    candidates = [
        os.environ.get("ISCC"),
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return shutil.which("ISCC.exe") or shutil.which("iscc")


def main():
    parser = argparse.ArgumentParser(
        description="Build reproduzível do instalador NutriDesk para GitHub Releases"
    )
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--installer")
    args = parser.parse_args()

    validate_version_contract()
    run([sys.executable, "-m", "pytest", "-q"])
    run([sys.executable, "-m", "compileall", "-q", "app.py", "nutridesktop"])

    if not args.skip_build:
        if os.name != "nt":
            raise SystemExit("Build do EXE/instalador requer Windows.")
        run([sys.executable, "-m", "PyInstaller", "--clean", "nutridesktop.spec"])
        iscc = find_iscc()
        if not iscc:
            raise SystemExit("Inno Setup ISCC.exe não encontrado")
        run([iscc, f'/DMyAppVersion={APP_VERSION}', "NutriDesktop.iss"])

    installer = (
        Path(args.installer)
        if args.installer
        else ROOT / "installer" / f"NutriDesktop-Setup-{APP_VERSION}.exe"
    )
    if not installer.exists():
        raise SystemExit(f"Instalador ausente: {installer}")

    release = ROOT / "release"
    if release.exists():
        shutil.rmtree(release)
    release.mkdir()

    target = release / installer.name
    shutil.copy2(installer, target)
    (release / "SHA256SUMS.txt").write_text(
        f"{sha256(target)}  {target.name}\n", encoding="utf-8"
    )
    print(f"Release {APP_VERSION} pronta em {release}")


if __name__ == "__main__":
    main()