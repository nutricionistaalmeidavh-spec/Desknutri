"""Gera o instalador gratuito .dmg no próprio macOS (arm64 / x86_64)."""
from __future__ import annotations

import argparse
import hashlib
import time
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from nutridesktop.version import APP_VERSION


def run(*args: str) -> None:
    print(">", *args, flush=True)
    subprocess.run(list(args), check=True, cwd=ROOT)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build do instalador NutriDesk para macOS")
    parser.add_argument("--arch", choices=["arm64", "x86_64"], required=True)
    args = parser.parse_args()

    if platform.system() != "Darwin":
        parser.error("O .app e o .dmg exigem um runner macOS.")
    if platform.machine().lower() != args.arch:
        parser.error(f"Runner {platform.machine()} não corresponde à arquitetura {args.arch}.")

    run(sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "nutridesktop-macos.spec")
    app = ROOT / "dist" / "NutriDesk.app"
    binary = app / "Contents" / "MacOS" / "NutriDesktop"
    plist = app / "Contents" / "Info.plist"
    if not binary.is_file() or not plist.is_file():
        raise SystemExit("O bundle macOS não contém o executável ou Info.plist.")

    run("plutil", "-lint", str(plist))
    run("codesign", "--verify", "--deep", "--strict", str(app))

    # Esta execução não abre janelas: valida o Python, extensões nativas e SQLite.
    with tempfile.TemporaryDirectory(prefix="nutridesk-smoke-") as data:
        import os
        env = dict(os.environ, NUTRIDESKTOP_DATA_DIR=data)
        subprocess.run([str(binary), "--healthcheck"], check=True, cwd=ROOT, env=env)

    release = ROOT / "release"
    release.mkdir(exist_ok=True)
    dmg = release / f"NutriDesk-{APP_VERSION}-macos-{args.arch}.dmg"

    with tempfile.TemporaryDirectory(prefix="nutridesk-dmg-") as staging:
        volume = Path(staging)
        shutil.copytree(app, volume / "NutriDesk.app", symlinks=True)
        (volume / "Applications").symlink_to("/Applications", target_is_directory=True)
        # macOS runners may transiently hold disk image resources (Resource busy).
        for attempt in range(1, 4):
            try:
                run("hdiutil", "create", "-volname", "NutriDesk", "-srcfolder", str(volume),
                    "-ov", "-format", "UDZO", str(dmg))
                break
            except subprocess.CalledProcessError:
                if attempt == 3:
                    raise
                dmg.unlink(missing_ok=True)
                print(f"DMG create attempt {attempt} failed; retrying", flush=True)
                time.sleep(attempt * 8)

    run("hdiutil", "verify", str(dmg))
    print(f"DMG_READY {dmg.name} sha256={sha256(dmg)}", flush=True)


if __name__ == "__main__":
    main()
