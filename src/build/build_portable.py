#!/usr/bin/env python3
"""Assemble a self-contained portable release from the onedir build."""

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]


def assemble(destination: Path, source_roms: Path) -> Path:
    """Copy explicit runtime assets and generate the configured mod in isolation."""
    destination = destination.resolve()
    if destination.exists():
        raise FileExistsError(f"Use a new destination: {destination}")
    bundle = ROOT / "dist" / "KOF97ModStudio"
    required = [bundle / "KOF97ModStudio.exe", bundle / "_internal",
                ROOT / "mod_studio_config.json", ROOT / "sandbox" / "WinKawaks.exe"]
    required += [source_roms / name for name in ("kof97.ZIP", "neogeo.zip")]
    for path in required:
        if not path.exists():
            raise FileNotFoundError(path)
    destination.mkdir(parents=True)
    shutil.copytree(bundle / "_internal", destination / "_internal")
    for name in ("studio.exe", "KOF97GameLauncher.exe"):
        shutil.copy2(bundle / "KOF97ModStudio.exe", destination / name)
    shutil.copy2(ROOT / "mod_studio_config.json", destination)
    (destination / "portable-package.json").write_text(
        json.dumps({"format": 1, "created": datetime.now().isoformat(),
                    "rom_source": "roms", "mod_rom": "output/roms/kof97pls.zip"}, indent=2),
        encoding="utf-8")
    roms = destination / "roms"
    roms.mkdir()
    for name in ("kof97.ZIP", "neogeo.zip"):
        with zipfile.ZipFile(source_roms / name) as archive:
            bad = archive.testzip()
            if bad:
                raise ValueError(f"Invalid ROM archive member: {bad}")
        shutil.copy2(source_roms / name, roms / name)
    sandbox = destination / "sandbox"
    sandbox.mkdir()
    for name in ("WinKawaks.exe", "WinKawaks.rom", "kailleraclient.dll",
                 "defaultkeysCPS.ini", "defaultkeysMVS.ini"):
        shutil.copy2(ROOT / "sandbox" / name, sandbox / name)
    for name in ("ini", "saves", "eeprom", "capture", "sshots", "recinput",
                 "lang", "tracklst", "cheats", "blend"):
        (sandbox / name).mkdir()
    for name in ("kof97.ini", "kof97pls.ini"):
        shutil.copy2(ROOT / "sandbox" / "ini" / name, sandbox / "ini" / name)
    settings = (ROOT / "sandbox" / "WinKawaks.ini").read_bytes().decode("latin-1")
    for index in range(1, 6):
        value = r"..\output\roms" if index == 1 else r"..\roms"
        settings = re.sub(rf"(?m)^RomPath{index}=.*$",
                          lambda match: f"RomPath{index}={value}\r", settings)
    (sandbox / "WinKawaks.ini").write_bytes(settings.encode("latin-1"))
    notices = destination / "ThirdParty"
    notices.mkdir()
    for name in ("faq.txt", "whatsnew.txt", "ROMCHANGES.TXT"):
        path = source_roms.parent / name
        if path.is_file():
            shutil.copy2(path, notices / name)
    result = subprocess.run([str(destination / "studio.exe"), "--check-package"],
                            cwd=str(destination.parent), timeout=180)
    report = json.loads((destination / "package-check.json").read_text(encoding="utf-8"))
    if result.returncode or not report.get("success"):
        raise RuntimeError(f"Frozen package check failed: {report}")
    if Path(report["root"]).resolve() != destination or Path(report["source"]).resolve() != roms:
        raise RuntimeError(f"Package escaped its portable root: {report}")
    print(f"[PASS] Frozen repack and sprite preview: {destination}")
    return destination


def archive_release(destination: Path) -> Path:
    """Write hashes and a ZIP containing one top-level portable directory."""
    hashes = []
    for path in sorted(destination.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            hashes.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(destination).as_posix()}")
    (destination / "SHA256SUMS.txt").write_text("\n".join(hashes) + "\n", encoding="utf-8")
    return Path(shutil.make_archive(str(destination), "zip", destination.parent, destination.name))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path,
                        default=ROOT / "dist" / ("KOF97-Portable-" + datetime.now().strftime("%Y%m%d-%H%M%S")))
    parser.add_argument("--source-roms", type=Path,
                        default=Path(r"C:\Program Files (x86)\KOF97\roms"))
    args = parser.parse_args()
    destination = assemble(args.destination, args.source_roms)
    shutil.copy2(ROOT / "Docs" / "Portable-Readme.txt", destination / "README.txt")
    print(f"[SUCCESS] {archive_release(destination)}")


if __name__ == "__main__":
    main()
