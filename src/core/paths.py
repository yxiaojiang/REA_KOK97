#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Filesystem path resolution for source and PyInstaller-frozen execution."""

import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    EXE_DIR = Path(sys.executable).resolve().parent
    BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", EXE_DIR))
    if (EXE_DIR / "src").exists() or (EXE_DIR / "sandbox").exists():
        PROJECT_ROOT = EXE_DIR
    elif (EXE_DIR.parent / "src").exists() or (EXE_DIR.parent / "sandbox").exists():
        PROJECT_ROOT = EXE_DIR.parent
    else:
        PROJECT_ROOT = Path.cwd().resolve()
else:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    BUNDLE_DIR = PROJECT_ROOT
    EXE_DIR = PROJECT_ROOT

CONFIG_FILE_NAME = "mod_studio_config.json"


def get_config_path() -> Path:
    """Return the filesystem path for the persisted JSON config file."""
    if getattr(sys, "frozen", False):
        exe_cfg = EXE_DIR / CONFIG_FILE_NAME
        proj_cfg = PROJECT_ROOT / CONFIG_FILE_NAME
        if not exe_cfg.exists() and proj_cfg.exists():
            return proj_cfg
        return exe_cfg
    return PROJECT_ROOT / CONFIG_FILE_NAME


def resolve_web_index_html() -> Path:
    """Locate the web frontend index.html across bundled and source layouts."""
    candidates = [
        BUNDLE_DIR / "src" / "studio" / "web" / "index.html",
        BUNDLE_DIR / "web" / "index.html",
        PROJECT_ROOT / "src" / "studio" / "web" / "index.html",
        PROJECT_ROOT / "web" / "index.html",
    ]
    html_file = next((p for p in candidates if p.exists()), None)
    if not html_file:
        raise FileNotFoundError(
            f"Web interface index.html not found in {[str(p) for p in candidates]}"
        )
    return html_file
