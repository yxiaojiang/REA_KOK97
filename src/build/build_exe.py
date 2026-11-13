#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build script to package KOF97 Mod Studio into a standalone Windows executable.
Uses PyInstaller with pywebview and edgechromium dependencies.
"""

import shutil
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.core.paths import PROJECT_ROOT


def build_executable() -> bool:
    """Run PyInstaller to create standalone KOF97ModStudio.exe."""
    entry_script = PROJECT_ROOT / "src" / "studio" / "kof97_webview_app.py"
    html_asset = PROJECT_ROOT / "src" / "studio" / "web" / "index.html"

    if not entry_script.exists():
        print(f"[ERROR] Entry script not found: {entry_script}")
        return False

    if not html_asset.exists():
        print(f"[ERROR] HTML asset not found: {html_asset}")
        return False

    dist_dir = PROJECT_ROOT / "dist"
    build_dir = PROJECT_ROOT / "build_pyinstaller"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=KOF97ModStudio",
        "--onefile",
        "--noconsole",
        "--clean",
        f"--paths={PROJECT_ROOT}",
        f"--add-data={html_asset};src/studio/web",
        "--hidden-import=webview",
        "--hidden-import=webview.platforms.winforms",
        "--hidden-import=webview.platforms.edgechromium",
        "--hidden-import=clr",
        "--hidden-import=pythonnet",
        "--hidden-import=bottle",
        "--hidden-import=proxy_tools",
        "--hidden-import=PIL",
        "--hidden-import=PIL.Image",
        "--hidden-import=PIL.PngImagePlugin",
        "--hidden-import=src.core.paths",
        "--hidden-import=src.core.roster",
        "--hidden-import=src.core.presets",
        "--hidden-import=src.core.config_store",
        "--hidden-import=src.palette.color_utils",
        "--hidden-import=src.palette.costume_painter",
        "--hidden-import=src.palette.portrait_burst",
        "--hidden-import=src.palette.vfx_shader",
        "--hidden-import=src.rom.rom_tool",
        "--hidden-import=src.rom.crom_tool",
        "--hidden-import=src.rom.sprite_compose",
        "--hidden-import=src.rom.p1_patcher",
        "--hidden-import=src.emulator.kawaks_live",
        "--hidden-import=src.studio.bridge_api",
        "--hidden-import=src.studio.legacy_tk_gui",
        f"--distpath={dist_dir}",
        f"--workpath={build_dir}",
        f"--specpath={build_dir}",
        str(entry_script),
    ]

    print("=== Starting PyInstaller Build Pipeline ===")
    print("Command:", " ".join(cmd))
    res = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    if res.returncode != 0:
        print("[ERROR] PyInstaller build failed with code:", res.returncode)
        return False

    built_exe = dist_dir / "KOF97ModStudio.exe"
    if not built_exe.exists():
        print(f"[ERROR] Expected output executable not found: {built_exe}")
        return False

    print(f"[SUCCESS] Standalone executable created: {built_exe} ({built_exe.stat().st_size:,} bytes)")

    root_exe = PROJECT_ROOT / "KOF97ModStudio.exe"
    try:
        shutil.copy2(built_exe, root_exe)
        print(f"[SUCCESS] Copied executable to workspace root: {root_exe}")
    except Exception as exc:
        print(f"[WARN] Could not copy executable to root: {exc}")

    return True


if __name__ == "__main__":
    success = build_executable()
    sys.exit(0 if success else 1)
