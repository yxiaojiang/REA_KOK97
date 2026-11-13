#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PyWebView RPC Bridge API coordinating studio state, ROM patching, and live injection."""

import base64
import os
import random
import struct
import subprocess
import sys
import threading
import uuid
import zipfile
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import webview

import src.core.paths as _paths
from src.core.config_store import load_studio_config, save_studio_config
from src.core.presets import PRESET_THEMES, VFX_PRESET_MAP, VFX_PRESETS, is_custom_theme_id
from src.core.roster import CHARACTER_PALETTE_SCHEMA, CHARACTER_ROSTER, get_char_engine_info
from src.emulator.kawaks_live import find_kawaks_pid, inject_live_palettes_to_kawaks
from src.palette.color_utils import hex_to_lspc2, lspc2_to_hex
from src.palette.costume_painter import (
    generate_harmonious_character_palette,
    make_skin_entry,
)
from src.palette.portrait_burst import (
    generate_burst_character_palette,
    sync_character_portraits,
)
from src.palette.vfx_shader import (
    apply_vfx_palettes_to_p2,
    build_character_vfx_map,
    generate_vfx_preview_ramp,
)
from src.rom.p1_patcher import (
    apply_combat_and_unlock_patches_to_p1,
    apply_hit_effect_vfx_to_p1,
)
from src.rom.rom_tool import (
    DEFAULT_KOF97_ZIP,
    DEFAULT_OUTPUT_ZIP,
    DEFAULT_SANDBOX_DIR,
    DEFAULT_UNPACK_DIR,
    EXPECTED_SIZES,
    bswap16,
    crc32_hex,
    pack_rom_set,
    start_sandbox_kawaks,
    unpack_rom_set,
)
from src.rom.sprite_compose import (
    SpriteRom,
    official_colors,
    official_header_word,
    render_idle_png,
    slot_labels as compose_slot_labels,
)

# ============================================================================
# Thread-Safe Asynchronous Logging Helper (Prevents PyWebView Deadlock)
# ============================================================================

_APP_WINDOW: Optional[webview.Window] = None


def set_app_window(win: webview.Window) -> None:
    """Store the global window handle for safe asynchronous log dispatch."""
    global _APP_WINDOW
    _APP_WINDOW = win


def async_log(message: str, level: str = "INFO") -> None:
    """Dispatch a live log message in a separate thread without blocking the RPC loop."""
    import json

    try:
        print(f"[{level}] {message}")
    except UnicodeEncodeError:
        enc = getattr(sys.stdout, "encoding", "utf-8") or "utf-8"
        safe_msg = message.encode(enc, errors="replace").decode(enc)
        print(f"[{level}] {safe_msg}")

    def _worker() -> None:
        if _APP_WINDOW:
            try:
                safe_msg = json.dumps(message)
                safe_level = json.dumps(level)
                js_code = f"if(window.onBackendLog){{window.onBackendLog({safe_msg}, {safe_level});}}"
                _APP_WINDOW.evaluate_js(js_code)
            except Exception:
                pass

    threading.Thread(target=_worker, daemon=True).start()


# ============================================================================
# Pure PyWebView Bridge API Implementation
# ============================================================================


class KOF97BridgeApi:
    """Exposes Python backend RPC methods to the HTML/JavaScript UI layer."""

    def __init__(self, config_path: Optional[Path] = None) -> None:
        self._build_lock = threading.Lock()
        self._config_path: Optional[Path] = (
            Path(config_path) if config_path is not None else None
        )

        # Workspace paths
        self._workdir = DEFAULT_UNPACK_DIR
        self._output_zip = DEFAULT_OUTPUT_ZIP
        self._source_zip = DEFAULT_KOF97_ZIP
        self._sandbox_dir = DEFAULT_SANDBOX_DIR

        # Current application state
        self._char_id = 0x1B  # Default: Iori Yagami (0x1B)
        self._scope = "SINGLE"  # "SINGLE" or "ALL"
        self._guard = True
        self._stun = True
        self._damage_mode = "halved"
        self._sync_avatar = True
        self._infinite_power = True
        self._dizzy_duration = 5.0

        # Running emulator handle & P2 Base cache
        self._running_proc: Optional[subprocess.Popen] = None
        self._cached_p2_base: Optional[int] = None
        self._cached_p2_pid: Optional[int] = None

        # Per-character skin store: char_id -> {themeId, vfxTheme, colors, preview}
        self._sprite_rom = None
        self._custom_skins = []
        self._last_vfx_ram_sigs: Dict[int, bytes] = {}

        self._character_skins: Dict[int, Dict[str, Any]] = {}
        classic_colors = list(PRESET_THEMES[0]["colors"])
        for char in CHARACTER_ROSTER:
            self._character_skins[char["id"]] = make_skin_entry(
                char["id"], "classic", classic_colors
            )

        # Load persisted settings from disk if available
        self._load_config_from_disk()

    # ------------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------------

    def _resolve_config_path(self) -> Path:
        """Resolve config path supporting explicit injection and module monkeypatching."""
        if self._config_path is not None:
            return self._config_path
        for mod_name in ("src.studio.kof97_webview_app", "kof97_webview_app"):
            mod = sys.modules.get(mod_name)
            fn = getattr(mod, "get_config_path", None) if mod is not None else None
            if callable(fn) and fn is not _paths.get_config_path:
                return Path(fn())
        return _paths.get_config_path()

    def _load_config_from_disk(self) -> bool:
        """Load persisted configuration from JSON file."""
        cfg_path = self._resolve_config_path()
        parsed = load_studio_config(cfg_path, skin_entry_factory=make_skin_entry)
        if parsed is None:
            return False

        if "active_char_id" in parsed:
            self._char_id = parsed["active_char_id"]
        if "scope" in parsed:
            self._scope = parsed["scope"]
        if "guard" in parsed:
            self._guard = parsed["guard"]
        if "stun" in parsed:
            self._stun = parsed["stun"]
        if "damage_mode" in parsed:
            self._damage_mode = parsed["damage_mode"]
        if "sync_avatar" in parsed:
            self._sync_avatar = parsed["sync_avatar"]
        if "infinite_power" in parsed:
            self._infinite_power = parsed["infinite_power"]
        if "dizzy_duration" in parsed:
            self._dizzy_duration = parsed["dizzy_duration"]

        self._character_skins.update(parsed.get("character_skins", {}))
        self._custom_skins = list(parsed.get("custom_skins", []))
        return True

    def _save_config_to_disk(self) -> bool:
        """Persist current application state to JSON config file."""
        config_data = {
            "version": 1,
            "active_char_id": self._char_id,
            "scope": self._scope,
            "guard": self._guard,
            "stun": self._stun,
            "infinite_power": self._infinite_power,
            "dizzy_duration": self._dizzy_duration,
            "damage_mode": self._damage_mode,
            "sync_avatar": self._sync_avatar,
            "character_skins": {
                str(cid): skin for cid, skin in self._character_skins.items()
            },
            "custom_skins": list(self._custom_skins),
        }
        return save_studio_config(
            self._resolve_config_path(),
            config_data,
            project_root=_paths.PROJECT_ROOT,
            exe_dir=_paths.EXE_DIR,
            config_file_name=_paths.CONFIG_FILE_NAME,
        )

    # ------------------------------------------------------------------------
    # State synchronization
    # ------------------------------------------------------------------------

    def _load_p1_p2_baseline(self) -> Tuple[bytes, bytes]:
        """Load Big-Endian P1 data (from workdir or source zip) and clean P2 data."""
        p1_path = self._workdir / "p1_be.bin"
        p1_data = p1_path.read_bytes() if p1_path.exists() else None
        with zipfile.ZipFile(self._source_zip) as z_src:
            p2_clean = bswap16(z_src.read("KOF97_P2.ROM"))
            if p1_data is None:
                p1_data = bswap16(z_src.read("KOF97_P1.ROM"))
        return p1_data, p2_clean

    def _build_vfx_previews(self) -> Dict[str, Any]:
        """Build 6-step luminous ramp previews per character based on current vfxTheme."""
        out: Dict[str, Any] = {}
        for char in CHARACTER_ROSTER:
            cid = char["id"]
            skin_entry = self._character_skins.get(cid, {})
            vid = skin_entry.get("vfxTheme", "classic")
            out[str(cid)] = generate_vfx_preview_ramp(vid, skin_entry)
        return out

    def get_initial_state(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Return the current studio configuration state to frontend."""
        p1_path = self._workdir / "p1_be.bin"
        p2_path = self._workdir / "p2_be.bin"
        has_unpacked = p1_path.exists() and p2_path.exists()
        has_zip = self._output_zip.exists()
        zip_crc = crc32_hex(self._output_zip.read_bytes()) if has_zip else ""

        vfx_support: Dict[str, bool] = {str(ch["id"]): True for ch in CHARACTER_ROSTER}
        try:
            p1_data, p2_clean = self._load_p1_p2_baseline()
            vmap = build_character_vfx_map(p1_data, p2_clean)
            vfx_support = {str(cid): bool(info.get("has_vfx")) for cid, info in vmap.items()}
        except Exception:
            pass

        return {
            "char_id": self._char_id,
            "scope": self._scope,
            "guard": self._guard,
            "stun": self._stun,
            "infinite_power": self._infinite_power,
            "dizzy_duration": self._dizzy_duration,
            "damage_mode": self._damage_mode,
            "sync_avatar": self._sync_avatar,
            "character_skins": self._character_skins,
            "has_unpacked": has_unpacked,
            "has_zip": has_zip,
            "zip_crc32": zip_crc,
            "custom_skins": list(self._custom_skins),
            "vfx_presets": VFX_PRESETS,
            "vfx_support": vfx_support,
            "vfx_previews": self._build_vfx_previews(),
        }

    def _lspc_words_for_skin(
        self, cid: int, skin_entry: Dict[str, Any], p1_data: bytes, p2_clean: bytes
    ) -> tuple:
        """Return (theme_id, 15 LSPC2 words) for packing or live injection."""
        theme_id = skin_entry.get("themeId", "classic") if skin_entry else "classic"
        if is_custom_theme_id(theme_id):
            colors = (skin_entry or {}).get("colors") or []
            if isinstance(colors, list) and len(colors) == 15:
                return theme_id, [hex_to_lspc2(c) for c in colors]
            theme_id = "classic"
        if theme_id == "classic":
            _, _, pal_idx = get_char_engine_info(cid)
            base_off = 0x483E + pal_idx * 8
            base_pid = struct.unpack(">H", p1_data[base_off : base_off + 2])[0]
            orig_p2_addr = 0x2CFFF0 + base_pid * 32
            lspc_words = [
                struct.unpack(">H", p2_clean[orig_p2_addr + i * 2 : orig_p2_addr + i * 2 + 2])[0]
                for i in range(1, 16)
            ]
            return theme_id, lspc_words
        lspc_words = generate_harmonious_character_palette(cid, theme_id, p1_data, p2_clean)
        return theme_id, lspc_words

    def _get_sprite_rom(self) -> SpriteRom:
        """Load and cache official P/C ROM data for idle previews."""
        if self._sprite_rom is None:
            rom = SpriteRom(Path(self._source_zip))
            rom.load()
            self._sprite_rom = rom
        return self._sprite_rom

    def get_idle_preview(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Render an ACT 00 standing sprite recolored with 15 gameplay colors."""
        params = params or {}
        cid = int(params.get("char_id", self._char_id))
        engine_cid, _alt, pal_idx = get_char_engine_info(cid)
        schema = CHARACTER_PALETTE_SCHEMA.get(cid, {})
        labels = compose_slot_labels(schema)
        official = []
        try:
            rom = self._get_sprite_rom()
            official = official_colors(rom.p1, rom.p2, pal_idx)
            header = official_header_word(rom.p1, rom.p2, pal_idx)
            raw = params.get("colors")
            if isinstance(raw, list) and len(raw) == 15:
                colors15 = [str(c) for c in raw]
            else:
                colors15 = official
            png = render_idle_png(rom, engine_cid, colors15, frame_i=0, scale=4, header_word=header)
            if not png:
                return {
                    "success": False,
                    "error": "idle frame not available",
                    "labels": labels,
                    "official_colors": official,
                    "png_base64": "",
                }
            return {
                "success": True,
                "png_base64": base64.b64encode(png).decode("ascii"),
                "labels": labels,
                "official_colors": official,
            }
        except Exception as exc:
            return {
                "success": False,
                "error": str(exc),
                "labels": labels,
                "official_colors": official,
                "png_base64": "",
            }

    def save_custom_skin(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Save or update a named 15-color custom skin for one character."""
        params = params or {}
        try:
            cid = int(params.get("char_id", self._char_id))
        except (TypeError, ValueError):
            return {"success": False, "error": "invalid character"}
        colors = params.get("colors")
        if not isinstance(colors, list) or len(colors) != 15:
            return {"success": False, "error": "need 15 colors"}
        name = str(params.get("name") or "\u81ea\u5b9a\u4e49\u76ae\u80a4").strip() or "\u81ea\u5b9a\u4e49\u76ae\u80a4"
        sid = str(params.get("id") or "").strip()
        entry = {"id": sid, "name": name, "cid": cid, "colors": [str(c) for c in colors]}
        if sid:
            found = False
            for i, item in enumerate(self._custom_skins):
                if item.get("id") == sid:
                    self._custom_skins[i] = entry
                    found = True
                    break
            if not found:
                self._custom_skins.append(entry)
        else:
            sid = "cs_%02x_%s" % (cid, uuid.uuid4().hex[:8])
            entry["id"] = sid
            self._custom_skins.append(entry)
        self._save_config_to_disk()
        async_log(f"\u5df2\u4fdd\u5b58\u81ea\u5b9a\u4e49\u76ae\u80a4\u3010{name}\u3011", "SUCCESS")
        return {"success": True, "id": sid, "custom_skins": list(self._custom_skins)}

    def delete_custom_skin(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Remove one saved custom skin by id."""
        params = params or {}
        sid = str(params.get("id") or "").strip()
        if not sid:
            return {"success": False, "error": "missing id"}
        self._custom_skins = [s for s in self._custom_skins if s.get("id") != sid]
        self._save_config_to_disk()
        return {"success": True, "custom_skins": list(self._custom_skins)}

    def update_active_character(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update active character selection."""
        char_id = params.get("char_id", 0x1B)
        self._char_id = char_id
        char_info = next((c for c in CHARACTER_ROSTER if c["id"] == char_id), None)
        cname = char_info["name_cn"] if char_info else f"0x{char_id:02X}"
        async_log(f"\u9009\u5b9a\u76ee\u6807\u89d2\u8272: \u3010{cname}\u3011 (ID=0x{char_id:02X})", "INFO")
        self._save_config_to_disk()
        return {"success": True}

    def set_character_skin(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set skin for a single character or bulk set for all characters."""
        char_id = params.get("char_id", self._char_id)
        theme_id = params.get("theme_id", "classic")
        scope = params.get("scope", self._scope)
        raw_colors = params.get("colors")
        stored_colors = list(raw_colors) if isinstance(raw_colors, list) and len(raw_colors) == 15 else None
        use_stored = bool(params.get("use_stored_colors")) or is_custom_theme_id(theme_id)
        explicit_vfx = params.get("vfx_theme")
        if explicit_vfx is not None and str(explicit_vfx) not in VFX_PRESET_MAP:
            explicit_vfx = None

        p1_data, p2_clean = self._load_p1_p2_baseline()

        if use_stored and stored_colors:
            cur_vfx = str(explicit_vfx) if explicit_vfx else str(self._character_skins.get(char_id, {}).get("vfxTheme", "classic"))
            self._character_skins[char_id] = make_skin_entry(char_id, theme_id, stored_colors, vfx_theme=cur_vfx)
            char_info = next((c for c in CHARACTER_ROSTER if c["id"] == char_id), None)
            cname = char_info["name_cn"] if char_info else f"0x{char_id:02X}"
            async_log(f"\u5df2\u4fdd\u5b58\u89d2\u8272\u3010{cname}\u3011\u7684\u81ea\u5b9a\u4e49\u76ae\u80a4: \u3010{theme_id}\u3011", "INFO")
        elif scope == "ALL":
            for char_info in CHARACTER_ROSTER:
                cid = char_info["id"]
                cur_vfx = str(explicit_vfx) if explicit_vfx else str(self._character_skins.get(cid, {}).get("vfxTheme", "classic"))
                lspc_words = generate_harmonious_character_palette(cid, theme_id, p1_data, p2_clean)
                self._character_skins[cid] = make_skin_entry(
                    cid, theme_id, [lspc2_to_hex(w) for w in lspc_words], vfx_theme=cur_vfx
                )
            async_log(f"\u5df2\u5168\u91cf\u8bbe\u7f6e\u5168\u5458 36 \u89d2\u8272\u76ae\u80a4\u4e3a: \u3010{theme_id}\u3011", "INFO")
        else:
            cur_vfx = str(explicit_vfx) if explicit_vfx else str(self._character_skins.get(char_id, {}).get("vfxTheme", "classic"))
            lspc_words = generate_harmonious_character_palette(char_id, theme_id, p1_data, p2_clean)
            hex_colors = [lspc2_to_hex(w) for w in lspc_words]
            self._character_skins[char_id] = make_skin_entry(
                char_id, theme_id, hex_colors, vfx_theme=cur_vfx
            )
            char_info = next((c for c in CHARACTER_ROSTER if c["id"] == char_id), None)
            cname = char_info["name_cn"] if char_info else f"0x{char_id:02X}"
            async_log(f"\u5df2\u4fdd\u5b58\u89d2\u8272\u3010{cname}\u3011\u7684\u72ec\u7acb\u76ae\u80a4\u914d\u7f6e: \u3010{theme_id}\u3011", "INFO")

        self._save_config_to_disk()
        return {
            "success": True,
            "character_skins": {str(k): v for k, v in self._character_skins.items()},
            "custom_skins": list(self._custom_skins),
            "vfx_previews": self._build_vfx_previews(),
        }

    def set_character_vfx(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set skill/VFX palette theme for one character or all 36 characters."""
        params = params or {}
        try:
            char_id = int(params.get("char_id", self._char_id))
        except (TypeError, ValueError):
            char_id = self._char_id
        vfx_theme = str(params.get("vfx_theme") or "classic")
        if vfx_theme not in VFX_PRESET_MAP:
            return {"success": False, "error": f"Unknown VFX theme: {vfx_theme}"}
        scope = params.get("scope", self._scope)

        target_cids = [ch["id"] for ch in CHARACTER_ROSTER] if scope == "ALL" else [char_id]
        for cid in target_cids:
            entry = self._character_skins.get(cid)
            if not entry:
                entry = make_skin_entry(cid, "classic", list(PRESET_THEMES[0]["colors"]), vfx_theme=vfx_theme)
                self._character_skins[cid] = entry
            else:
                entry["vfxTheme"] = vfx_theme

        preset_info = VFX_PRESET_MAP[vfx_theme]
        vname = preset_info["name_cn"]
        if scope == "ALL":
            async_log(f"\u5df2\u5168\u91cf\u8bbe\u7f6e\u5168\u5458 36 \u89d2\u8272\u6280\u80fd\u7279\u6548\u914d\u8272\u4e3a: \u3010{vname}\u3011", "INFO")
        else:
            char_info = next((c for c in CHARACTER_ROSTER if c["id"] == char_id), None)
            cname = char_info["name_cn"] if char_info else f"0x{char_id:02X}"
            async_log(f"\u5df2\u8bbe\u7f6e\u89d2\u8272\u3010{cname}\u3011\u7684\u6280\u80fd\u7279\u6548\u914d\u8272\u4e3a: \u3010{vname}\u3011", "INFO")

        self._save_config_to_disk()
        return {
            "success": True,
            "character_skins": {str(k): v for k, v in self._character_skins.items()},
            "vfx_previews": self._build_vfx_previews(),
        }

    def update_scope(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update target application scope ('SINGLE' or 'ALL')."""
        self._scope = params.get("scope", "SINGLE")
        mode_str = "\u5168\u5458 36 \u4f4d\u89d2\u8272" if self._scope == "ALL" else "\u5f53\u524d\u9009\u5b9a\u89d2\u8272"
        async_log(f"\u5e94\u7528\u8303\u56f4\u5df2\u5207\u6362\u4e3a: \u3010{mode_str}\u3011", "INFO")
        self._save_config_to_disk()
        return {"success": True}

    def update_combat_rule(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update guard crush or stun immunity."""
        rule = params.get("rule")
        val = bool(params.get("value", True))
        if rule == "guard":
            self._guard = val
            status = "\u542f\u7528 (\u9501\u6b7b 103 \u70b9)" if val else "\u5173\u95ed (\u6062\u590d\u539f\u7248\u6263\u51cf)"
            async_log(f"\u514d\u7834\u9632\u673a\u5236\u5df2{status}", "INFO")
        elif rule == "stun":
            self._stun = val
            status = "\u542f\u7528 (\u9501\u6b7b 103 \u70b9)" if val else "\u5173\u95ed (\u6062\u590d\u539f\u7248\u6263\u51cf)"
            async_log(f"\u514d\u7729\u6655\u673a\u5236\u5df2{status}", "INFO")
        self._save_config_to_disk()
        return {"success": True}

    def update_damage_mode(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update damage multiplier option."""
        self._damage_mode = params.get("mode_id", "halved")
        async_log(f"\u53d7\u521b\u4f24\u5bb3\u500d\u7387\u5df2\u8bbe\u7f6e\u4e3a: \u3010{self._damage_mode}\u3011", "INFO")
        self._save_config_to_disk()
        return {"success": True}

    def update_sync_avatar(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update whether portrait and HUD avatar should be synced."""
        self._sync_avatar = bool(params.get("sync", True))
        state = "\u5f00\u542f" if self._sync_avatar else "\u5173\u95ed"
        async_log(f"\u7acb\u7ed8\u4e0e HUD \u5c0f\u5934\u50cf\u540c\u6b65\u5df2{state}", "INFO")
        self._save_config_to_disk()
        return {"success": True}

    def update_infinite_power(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update infinite power / super meter setting."""
        self._infinite_power = bool(params.get("value", True))
        state = (
            "\u542f\u7528 (\u521d\u59cb3\u6c14+\u6ee1\u80fd\u91cf\u69fd\uff0c\u8d85\u5fc5\u6740/MAX\u7206\u6c14\u96f6\u6d88\u8017)"
            if self._infinite_power
            else "\u5173\u95ed (\u6062\u590d\u539f\u7248\u80fd\u91cf\u6263\u51cf)"
        )
        async_log(f"\u65e0\u9650\u80fd\u91cf\u673a\u5236\u5df2{state}", "INFO")
        self._save_config_to_disk()
        return {"success": True}

    def update_dizzy_duration(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update stun/dizzy duration in seconds."""
        try:
            val = float(params.get("value", 5.0))
            self._dizzy_duration = max(0.5, min(30.0, val))
        except (ValueError, TypeError):
            self._dizzy_duration = 5.0
        async_log(f"\u7729\u6655\u6301\u7eed\u65f6\u95f4\u5df2\u8bbe\u7f6e\u4e3a: \u3010{self._dizzy_duration:.1f} \u79d2\u3011", "INFO")
        self._save_config_to_disk()
        return {"success": True}

    def randomize_other_skins(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Assign a preset skin to every roster character."""
        available_themes = [t for t in PRESET_THEMES if t["id"] != "classic"]
        if not available_themes:
            return {"success": False, "error": "No custom themes available"}

        p1_data, p2_clean = self._load_p1_p2_baseline()

        randomized_count = 0
        theme_pool = list(available_themes)
        random.shuffle(theme_pool)
        pool_idx = 0

        for char_info in CHARACTER_ROSTER:
            cid = char_info["id"]
            chosen_theme = theme_pool[pool_idx % len(theme_pool)]
            pool_idx += 1
            theme_id = chosen_theme["id"]

            cur_vfx = str(self._character_skins.get(cid, {}).get("vfxTheme", "classic"))
            lspc_words = generate_harmonious_character_palette(cid, theme_id, p1_data, p2_clean)
            hex_colors = [lspc2_to_hex(w) for w in lspc_words]
            self._character_skins[cid] = make_skin_entry(cid, theme_id, hex_colors, vfx_theme=cur_vfx)
            randomized_count += 1

        self._save_config_to_disk()
        async_log(f"\u5df2\u4e3a\u5168\u90e8 {randomized_count} \u4f4d\u89d2\u8272\u968f\u673a\u5206\u914d\u76ae\u80a4\u3002", "SUCCESS")
        return {
            "success": True,
            "count": randomized_count,
            "character_skins": {str(k): v for k, v in self._character_skins.items()},
            "vfx_previews": self._build_vfx_previews(),
        }

    def reset_all_skins(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Reset all 36 characters to their authentic original SNK classic skins and VFX."""
        p1_data, p2_clean = self._load_p1_p2_baseline()

        for char_info in CHARACTER_ROSTER:
            cid = char_info["id"]
            lspc_words = generate_harmonious_character_palette(cid, "classic", p1_data, p2_clean)
            hex_colors = [lspc2_to_hex(w) for w in lspc_words]
            self._character_skins[cid] = make_skin_entry(cid, "classic", hex_colors, vfx_theme="classic")

        self._save_config_to_disk()
        async_log("\u5df2\u5c06\u5168\u5458 36 \u4f4d\u89d2\u8272\u76ae\u80a4\u4e0e\u6280\u80fd\u7279\u6548\u5168\u90e8\u91cd\u7f6e\u4e3a\u5b98\u65b9\u539f\u7248\u7ecf\u5178\uff01", "SUCCESS")
        return {
            "success": True,
            "character_skins": {str(k): v for k, v in self._character_skins.items()},
            "vfx_previews": self._build_vfx_previews(),
        }

    def save_skin(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Save all characters skin configurations and combat settings to disk."""
        ok = self._save_config_to_disk()
        modded_count = sum(1 for _cid, s in self._character_skins.items() if s.get("themeId") != "classic")
        cfg_name = self._resolve_config_path().name
        if ok:
            async_log(
                f"\u5168\u5458\u914d\u7f6e\u4e0e\u6218\u6597\u8bbe\u7f6e\u5df2\u6210\u529f\u6301\u4e45\u5316\u4fdd\u5b58\u81f3\u672c\u5730 ({cfg_name})\uff01\u5171 {modded_count} \u4f4d\u89d2\u8272\u542f\u7528\u5b9a\u5236\u76ae\u80a4\u3002",
                "SUCCESS",
            )
            return {"success": True, "msg": f"\u5168\u5458\u914d\u7f6e\u5df2\u4fdd\u5b58\u81f3 {cfg_name} (\u5b9a\u5236\u89d2\u8272: {modded_count} \u4f4d)"}
        else:
            async_log("\u4fdd\u5b58\u914d\u7f6e\u6587\u4ef6\u5931\u8d25\uff0c\u8bf7\u68c0\u67e5\u78c1\u76d8\u5199\u5165\u6743\u9650\uff01", "ERROR")
            return {"success": False, "error": "\u4fdd\u5b58\u5931\u8d25"}

    # ------------------------------------------------------------------------
    # ROM Packaging Pipeline
    # ------------------------------------------------------------------------

    def pack_rom(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute property patching, per-character palette modification, and ROM packaging."""
        if not self._build_lock.acquire(blocking=False):
            return {"success": False, "error": "\u6253\u5305\u6d41\u6c34\u7ebf\u6b63\u5728\u8fd0\u884c\u4e2d\uff0c\u8bf7\u7a0d\u5019"}

        try:
            async_log("=== \u5f00\u59cb\u6267\u884c\u3010\u6253\u5305Rom\u3011\u5168\u91cf\u6d41\u6c34\u7ebf ===", "INFO")

            # 1. Ensure unpacked files exist
            p1_path = self._workdir / "p1_be.bin"
            p2_path = self._workdir / "p2_be.bin"
            s1_path = self._workdir / "s1.bin"

            if not (p1_path.exists() and p2_path.exists() and s1_path.exists()):
                async_log("\u89e3\u5305\u7f13\u5b58\u4e0d\u5b8c\u6574\uff0c\u6b63\u5728\u4ece\u539f\u751f ROM \u81ea\u52a8\u89e3\u5305...", "INFO")
                unpack_rom_set(self._source_zip, self._workdir)
                async_log("\u539f\u751f ROM \u89e3\u5305\u5b8c\u6210\u3002", "SUCCESS")

            p1_data = bytearray(p1_path.read_bytes())
            p2_data = bytearray(p2_path.read_bytes())

            if len(p1_data) != EXPECTED_SIZES["p1"]:
                raise ValueError(f"Invalid p1_be.bin size: {len(p1_data)}")
            if len(p2_data) != EXPECTED_SIZES["p2"]:
                raise ValueError(f"Invalid p2_be.bin size: {len(p2_data)}")

            # 2. Apply Combat & Defense Patches to p1_be.bin
            apply_combat_and_unlock_patches_to_p1(
                p1_data,
                guard=self._guard,
                stun=self._stun,
                dizzy_duration=self._dizzy_duration,
                infinite_power=self._infinite_power,
                damage_mode=self._damage_mode,
                log_fn=async_log,
            )

            # Load clean baseline p2 bytes for both P1 hit-effect VFX hooks and P2 palette builds
            with zipfile.ZipFile(self._source_zip) as z_src:
                p2_clean = bswap16(z_src.read("KOF97_P2.ROM"))

            hit_vfx_patch = apply_hit_effect_vfx_to_p1(p1_data, self._character_skins, p2_clean)
            if hit_vfx_patch:
                async_log(
                    f"  [P1-VFX] \u5df2\u6ce8\u5165 68000 \u53d7\u51fb\u71c3\u70e7/\u611f\u7535/\u706b\u82b1\u52a8\u6001\u540c\u6b65 Hook "
                    f"(0x0F0000, {hit_vfx_patch['theme_count']} \u79cd\u7279\u6548\u4e3b\u9898 / {hit_vfx_patch['char_slots']} \u89d2\u8272\u69fd\uff0c\u4fdd\u7559 P2 0x0000..0x00FF \u539f\u7248)",
                    "INFO",
                )
            else:
                async_log("  [P1-VFX] \u5df2\u6062\u590d\u539f\u7248\u53d7\u51fb\u71c3\u70e7/\u706b\u82b1\u673a\u5236", "INFO")

            p1_path.write_bytes(p1_data)

            # 3. Apply Palette & Skin for customized characters to p2_be.bin
            async_log("\u6b63\u5728\u5c06\u5b9a\u5236\u89d2\u8272\u7684\u72ec\u7acb\u8c03\u8272\u677f\u65b9\u6848\u5199\u5165 p2_be.bin...", "INFO")

            p2_data = bytearray(p2_clean)

            customized_count = 0
            vfx_char_count = 0
            vfx_slot_total = 0

            for char_info in CHARACTER_ROSTER:
                cid = char_info["id"]
                skin_entry = self._character_skins.get(cid)
                if not skin_entry:
                    continue

                theme_id = skin_entry.get("themeId", "classic")
                vfx_theme = skin_entry.get("vfxTheme", "classic")
                if theme_id == "classic" and vfx_theme == "classic":
                    continue

                cname = char_info["name_cn"]

                if theme_id != "classic":
                    customized_count += 1

                    _tid, lspc_words = self._lspc_words_for_skin(cid, skin_entry, p1_data, p2_clean)

                    _, _, pal_idx = get_char_engine_info(cid)
                    base_off = 0x483E + pal_idx * 8
                    base_pid = struct.unpack(">H", p1_data[base_off : base_off + 2])[0]

                    for btn_idx in range(4):
                        btn_off = base_off + btn_idx * 2
                        pal_id = struct.unpack(">H", p1_data[btn_off : btn_off + 2])[0]
                        if is_custom_theme_id(theme_id):
                            btn_words = lspc_words
                        else:
                            btn_words = generate_harmonious_character_palette(
                                cid, theme_id, p1_data, p2_clean, btn_idx
                            )
                        btn_bytes = struct.pack(">15H", *btn_words)
                        burst_words = generate_burst_character_palette(cid, theme_id, btn_words)
                        burst_bytes = struct.pack(">15H", *burst_words)
                        p2_addr_base = 0x2CFFF0 + pal_id * 32
                        p2_data[p2_addr_base + 2 : p2_addr_base + 32] = btn_bytes
                        p2_addr_burst = 0x2CFFF0 + (pal_id + 3) * 32
                        p2_data[p2_addr_burst + 2 : p2_addr_burst + 32] = burst_bytes

                    if self._sync_avatar:
                        sync_character_portraits(cid, theme_id, base_pid, lspc_words, p2_data, p2_clean)

                    async_log(
                        f"  [P2] \u5df2\u4e3a\u3010{cname}\u3011\u6ce8\u5165\u5b9a\u5236\u76ae\u80a4: \u3010{theme_id}\u3011(\u5df2\u914d\u7f6e\u57fa\u7840\u6001\u4e0e MAX \u7206\u6c14\u9ad8\u80fd\u6001\u8c03\u8272\u677f)",
                        "INFO",
                    )

                if vfx_theme != "classic":
                    v_written = apply_vfx_palettes_to_p2(cid, vfx_theme, skin_entry, p1_data, p2_data, p2_clean)
                    if v_written > 0:
                        vfx_char_count += 1
                        vfx_slot_total += v_written
                        vname = VFX_PRESET_MAP.get(vfx_theme, {}).get("name_cn", vfx_theme)
                        async_log(f"  [P2-VFX] \u5df2\u4e3a\u3010{cname}\u3011\u6ce8\u5165\u6280\u80fd\u7279\u6548: \u3010{vname}\u3011({v_written} \u4e2a\u7279\u6548\u69fd)", "INFO")

            async_log(
                f"  [P2] \u8c03\u8272\u677f\u6ce8\u5165\u5b8c\u6210\uff01\u5b9a\u5236\u76ae\u80a4 {customized_count} \u4f4d\u89d2\u8272\uff0c\u5b9a\u5236\u7279\u6548 {vfx_char_count} \u4f4d\u89d2\u8272 ({vfx_slot_total} \u69fd)\uff0c\u5176\u4f59\u4fdd\u6301\u5b98\u65b9\u539f\u7248",
                "SUCCESS",
            )
            p2_path.write_bytes(p2_data)

            # 4. Pack into kof97pls.zip with bswap16
            async_log("\u6b63\u5728\u6267\u884c bswap16 \u786c\u4ef6\u5b57\u8282\u5e8f\u4ea4\u6362\u5e76\u91cd\u65b0\u538b\u7f29\u6253\u5305...", "INFO")
            pack_rom_set(self._workdir, self._output_zip)
            zip_crc = crc32_hex(self._output_zip.read_bytes())

            async_log("=== \u6253\u5305\u6d41\u6c34\u7ebf\u6267\u884c\u5b8c\u6bd5\uff01===", "SUCCESS")
            async_log(f"\u4ea4\u4ed8\u6210\u679c\u7269: {self._output_zip.name} (CRC32: {zip_crc})", "SUCCESS")

            return {"success": True, "crc32": zip_crc}

        except Exception as exc:
            async_log(f"\u6253\u5305\u6d41\u6c34\u7ebf\u5f02\u5e38\u4e2d\u65ad: {exc}", "ERROR")
            return {"success": False, "error": str(exc)}

        finally:
            self._build_lock.release()

    # ------------------------------------------------------------------------
    # Start Game Launcher & Live Memory Injection
    # ------------------------------------------------------------------------

    def start_game(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Launch WinKawaks with custom ROM in background thread."""
        def _launch() -> None:
            try:
                if not self._output_zip.exists():
                    async_log("\u672a\u68c0\u6d4b\u5230 output/roms/kof97pls.zip\uff0c\u6b63\u5728\u81ea\u52a8\u89e6\u53d1\u6253\u5305...", "WARN")
                    res = self.pack_rom()
                    if not res.get("success"):
                        async_log("\u81ea\u52a8\u6253\u5305\u5931\u8d25\uff0c\u542f\u52a8\u4e2d\u6b62\u3002", "ERROR")
                        return

                exe_path = self._sandbox_dir / "WinKawaks.exe"
                if not exe_path.exists():
                    raise FileNotFoundError(f"\u672a\u627e\u5230\u6a21\u62df\u5668\u4e3b\u7a0b\u5e8f: {exe_path}")

                async_log(f"\u6b63\u5728\u542f\u52a8\u6c99\u76d2\u6a21\u62df\u5668 WinKawaks (\u6302\u8f7d RomPath1={self._output_zip.parent})...", "INFO")
                proc = start_sandbox_kawaks(self._sandbox_dir, rom_name="kof97pls", enable_bg_input=False)
                self._running_proc = proc
                self._cached_p2_base = None
                self._cached_p2_pid = None
                async_log(f"WinKawaks \u6a21\u62df\u5668\u5df2\u6210\u529f\u542f\u52a8\uff01(PID={proc.pid})\uff0c\u5df2\u65bd\u52a0\u5185\u5b58\u53cd\u906e\u853d Patch\uff01", "SUCCESS")
            except Exception as exc:
                async_log(f"\u542f\u52a8\u6a21\u62df\u5668\u5931\u8d25: {exc}", "ERROR")

        threading.Thread(target=_launch, daemon=True).start()
        return {"success": True, "pid": 0}

    def _find_kawaks_pid(self) -> Optional[int]:
        """Locate running WinKawaks process PID."""
        if self._running_proc is not None and self._running_proc.poll() is not None:
            self._running_proc = None
        return find_kawaks_pid(self._running_proc)

    def get_emulator_status(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Check whether WinKawaks emulator is currently active in process tree."""
        try:
            pid = self._find_kawaks_pid()
            return {"running": pid is not None, "pid": pid or 0}
        except Exception as exc:
            return {"running": False, "pid": 0, "error": str(exc)}

    def apply_vfx_live(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Persist VFX preset selection and hot-inject into running WinKawaks if active."""
        merged = dict(params or {})
        merged["vfx_only"] = True
        return self.apply_skin_live(merged)

    def apply_skin_live(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Persist skin/VFX settings and hot-inject into running WinKawaks memory."""
        params = params or {}
        cid = params.get("char_id", self._char_id)
        vfx_only = bool(params.get("vfx_only"))
        theme_id = params.get("theme_id", "classic")
        scope = params.get("scope", self._scope)

        # 1. Update internal state and persist to disk
        if vfx_only:
            self.set_character_vfx(params)
        else:
            self.set_character_skin(params)

        # 2. Check if WinKawaks is running
        pid = self._find_kawaks_pid()
        if not pid:
            return {
                "success": True,
                "running": False,
                "message": "\u914d\u7f6e\u5df2\u4fdd\u5b58\uff01\u5f53\u524d\u6a21\u62df\u5668\u672a\u5728\u8fd0\u884c\uff0c\u70b9\u51fb\u300c\u5f00\u59cb\u6e38\u620f\u300d\u6216\u300c\u6253\u5305ROM\u300d\u5373\u53ef\u751f\u6548\u3002",
            }

        # 3. Read p1 and clean p2 baseline
        p1_path = self._workdir / "p1_be.bin"
        if not p1_path.exists():
            return {"success": False, "running": True, "message": "\u5de5\u4f5c\u533a\u7f3a\u5c11 p1_be.bin"}
        p1_data = p1_path.read_bytes()

        with zipfile.ZipFile(self._source_zip) as z_src:
            p2_clean = bswap16(z_src.read("KOF97_P2.ROM"))

        return inject_live_palettes_to_kawaks(
            pid=pid,
            char_id=cid,
            vfx_only=vfx_only,
            theme_id=theme_id,
            scope=scope,
            params=params,
            character_skins=self._character_skins,
            sync_avatar=self._sync_avatar,
            p1_data=p1_data,
            p2_clean=p2_clean,
            last_vfx_ram_sigs=self._last_vfx_ram_sigs,
            lspc_words_fn=self._lspc_words_for_skin,
            log_fn=async_log,
        )

    # ------------------------------------------------------------------------
    # Maintenance Actions
    # ------------------------------------------------------------------------

    def unpack_rom(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Trigger background unpack of native kof97.ZIP."""
        def _task() -> None:
            try:
                async_log("\u6b63\u5728\u4ece\u539f\u751f ROM \u91cd\u65b0\u89e3\u5305...", "INFO")
                rep = unpack_rom_set(self._source_zip, self._workdir)
                async_log(f"\u89e3\u5305\u6210\u529f\uff01\u5171\u89e3\u5305 {len(rep)} \u4e2a\u6838\u5fc3 ROM \u955c\u50cf\u81f3 {self._workdir}", "SUCCESS")
            except Exception as exc:
                async_log(f"\u89e3\u5305\u5931\u8d25: {exc}", "ERROR")

        threading.Thread(target=_task, daemon=True).start()
        return {"success": True}

    def restore_baseline(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Trigger background restore of official baseline ROM."""
        def _task() -> None:
            try:
                async_log("\u6b63\u5728\u6784\u5efa\u5b98\u65b9\u539f\u7248\u98ce\u4e91\u518d\u8d77\u57fa\u7ebf\u5305...", "INFO")
                classic_colors = list(PRESET_THEMES[0]["colors"])
                for cid in self._character_skins:
                    self._character_skins[cid] = make_skin_entry(
                        cid, "classic", classic_colors
                    )
                self._save_config_to_disk()
                unpack_rom_set(self._source_zip, self._workdir)
                pack_rom_set(self._workdir, self._output_zip)
                async_log(f"\u57fa\u7ebf\u5305\u91cd\u7f6e\u5b8c\u6210: {self._output_zip}\uff0c\u5168\u5458\u76ae\u80a4\u5df2\u6062\u590d SNK \u539f\u751f\u9ed8\u8ba4", "SUCCESS")
            except Exception as exc:
                async_log(f"\u8fd8\u539f\u57fa\u7ebf\u5305\u5931\u8d25: {exc}", "ERROR")

        threading.Thread(target=_task, daemon=True).start()
        return {"success": True}

    def run_self_test(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Trigger background execution of rom_tool self-test."""
        def _task() -> None:
            try:
                async_log("\u6b63\u5728\u6267\u884c\u5168\u5c40\u5de5\u5177\u94fe\u81ea\u68c0 (bswap16 / LSPC2 / \u74e6\u7247\u6d4b\u8bd5)...", "INFO")
                script_path = _paths.PROJECT_ROOT / "src" / "rom" / "rom_tool.py"
                cmd = [sys.executable, str(script_path), "self-test"]
                res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(_paths.PROJECT_ROOT))
                if res.returncode == 0:
                    for line in res.stdout.strip().splitlines():
                        if line.strip():
                            async_log(line.strip(), "INFO")
                    async_log("[PASS] \u5168\u5c40\u81ea\u68c0 100% \u901a\u8fc7\uff01", "SUCCESS")
                else:
                    async_log(res.stderr.strip(), "ERROR")
            except Exception as exc:
                async_log(f"\u81ea\u68c0\u6267\u884c\u5f02\u5e38: {exc}", "ERROR")

        threading.Thread(target=_task, daemon=True).start()
        return {"success": True}

    def open_output_dir(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Open output roms directory in Windows File Explorer."""
        out_dir = self._output_zip.parent
        out_dir.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(str(out_dir))
            async_log(f"\u5df2\u6253\u5f00\u8f93\u51fa\u76ee\u5f55: {out_dir}", "SUCCESS")
            return {"success": True}
        except Exception as exc:
            async_log(f"\u6253\u5f00\u8f93\u51fa\u76ee\u5f55\u5931\u8d25: {exc}", "ERROR")
            return {"success": False, "error": str(exc)}
