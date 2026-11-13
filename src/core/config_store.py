#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""JSON configuration persistence for KOF97 Mod Studio."""

import json
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from src.core.presets import (
    DAMAGE_MODES,
    OBSOLETE_THEME_MAP,
    PRESET_THEMES,
    VFX_PRESET_MAP,
    is_custom_theme_id,
)
from src.core.roster import CHARACTER_ROSTER


def load_studio_config(
    cfg_path: Path,
    skin_entry_factory: Optional[Callable[[int, str, List[str], str], Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    """Load persisted studio configuration from JSON file, returning parsed fields or None."""
    if not cfg_path.exists():
        return None

    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        out: Dict[str, Any] = {}
        if "active_char_id" in data:
            out["active_char_id"] = int(data["active_char_id"])
        if "scope" in data:
            out["scope"] = str(data["scope"])
        if "guard" in data:
            out["guard"] = bool(data["guard"])
        if "stun" in data:
            out["stun"] = bool(data["stun"])
        if "damage_mode" in data:
            mode = str(data["damage_mode"])
            if any(m["id"] == mode for m in DAMAGE_MODES):
                out["damage_mode"] = mode
        if "sync_avatar" in data:
            out["sync_avatar"] = bool(data["sync_avatar"])
        if "infinite_power" in data:
            out["infinite_power"] = bool(data["infinite_power"])
        if "dizzy_duration" in data:
            try:
                out["dizzy_duration"] = float(data["dizzy_duration"])
            except (ValueError, TypeError):
                out["dizzy_duration"] = 5.0

        valid_theme_ids = {t["id"] for t in PRESET_THEMES}
        saved_skins = data.get("character_skins", {})
        parsed_skins: Dict[int, Dict[str, Any]] = {}
        for char in CHARACTER_ROSTER:
            cid = char["id"]
            cid_str = str(cid)
            if cid_str in saved_skins:
                entry = saved_skins[cid_str]
                t_id = entry.get("themeId", "classic")
                if t_id in OBSOLETE_THEME_MAP:
                    t_id = OBSOLETE_THEME_MAP[t_id]
                if t_id not in valid_theme_ids and not is_custom_theme_id(t_id):
                    t_id = "classic"

                colors = entry.get("colors")
                if not colors or len(colors) != 15:
                    preset = next((t for t in PRESET_THEMES if t["id"] == t_id), PRESET_THEMES[0])
                    colors = list(preset["colors"])
                v_id = str(entry.get("vfxTheme", "classic"))
                if v_id not in VFX_PRESET_MAP:
                    v_id = "classic"
                if skin_entry_factory is not None:
                    parsed_skins[cid] = skin_entry_factory(cid, t_id, list(colors), v_id)
                else:
                    parsed_skins[cid] = {
                        "themeId": t_id,
                        "vfxTheme": v_id or "classic",
                        "colors": list(colors),
                    }
        out["character_skins"] = parsed_skins

        raw_customs = data.get("custom_skins", [])
        customs: List[Dict[str, Any]] = []
        if isinstance(raw_customs, list):
            for item in raw_customs:
                if not isinstance(item, dict):
                    continue
                colors = item.get("colors")
                if not isinstance(colors, list) or len(colors) != 15:
                    continue
                try:
                    cid = int(item.get("cid"))
                except (TypeError, ValueError):
                    continue
                sid = str(item.get("id") or "").strip()
                name = str(item.get("name") or "\u81ea\u5b9a\u4e49\u76ae\u80a4").strip() or "\u81ea\u5b9a\u4e49\u76ae\u80a4"
                if not sid:
                    continue
                customs.append({
                    "id": sid,
                    "name": name,
                    "cid": cid,
                    "colors": [str(c) for c in colors],
                })
        out["custom_skins"] = customs

        print(f"[INFO] Successfully loaded configuration from {cfg_path}")
        return out
    except Exception as exc:
        print(f"[WARN] Failed to read configuration from {cfg_path}: {exc}")
        return None


def save_studio_config(
    cfg_path: Path,
    payload: Dict[str, Any],
    project_root: Optional[Path] = None,
    exe_dir: Optional[Path] = None,
    config_file_name: str = "mod_studio_config.json",
) -> bool:
    """Persist studio configuration dictionary atomically to JSON on disk."""
    config_data = dict(payload)
    config_data.setdefault("version", 1)
    config_data["last_saved"] = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        tmp_path = cfg_path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        tmp_path.replace(cfg_path)

        if (
            getattr(sys, "frozen", False)
            and project_root is not None
            and exe_dir is not None
            and project_root != exe_dir
            and project_root.exists()
        ):
            try:
                with open(project_root / config_file_name, "w", encoding="utf-8") as f:
                    json.dump(config_data, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
        return True
    except Exception as exc:
        print(f"[ERROR] Failed to save configuration to {cfg_path}: {exc}")
        return False
