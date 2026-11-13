#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KOF97 Mod Studio - PyWebView Entrypoint and Compatibility Facade.
Orchestrates the HTML frontend and re-exports the stable 38-symbol API surface.
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import webview

from src.core.paths import CONFIG_FILE_NAME, get_config_path, resolve_web_index_html
from src.core.presets import (
    DAMAGE_MODES,
    PRESET_THEMES,
    THEME_KEYS,
    THEME_RAMPS,
    VFX_PRESET_MAP,
    VFX_PRESETS,
)
from src.core.roster import (
    CHAR_ENGINE_MAP,
    CHARACTER_PALETTE_SCHEMA,
    CHARACTER_ROSTER,
    get_char_engine_info,
)
from src.palette.color_utils import (
    _hex_hsv,
    _rgb5_to_hsv,
    _rgb_unit_to_oklch,
    _unit_luma,
    decode_lspc2,
    encode_lspc2,
    hex_to_lspc2,
    hex_to_rgb5,
    lspc2_to_hex,
    recolor_match_shade,
)
from src.palette.costume_painter import generate_harmonious_character_palette
from src.palette.portrait_burst import (
    generate_burst_character_palette,
    sync_character_portraits,
)
from src.palette.vfx_shader import (
    VFX_SENTINEL_WORDS,
    _read_p2_slot_words15,
    build_character_vfx_map,
    recolor_vfx_palette,
)
from src.rom.p1_patcher import (
    VFX_HIT_EFFECT_CAVE_BASE,
    VFX_HIT_EFFECT_CAVE_SIZE,
    VFX_HIT_HOOK_ORIGINALS,
    VFX_THEME_ENTRY_STRIDE,
    build_hit_effect_vfx_p1_patch,
)
from src.rom.rom_tool import bswap16
from src.studio.bridge_api import KOF97BridgeApi, set_app_window

__all__ = [
    "CONFIG_FILE_NAME",
    "get_config_path",
    "resolve_web_index_html",
    "CHARACTER_ROSTER",
    "CHAR_ENGINE_MAP",
    "get_char_engine_info",
    "CHARACTER_PALETTE_SCHEMA",
    "PRESET_THEMES",
    "DAMAGE_MODES",
    "THEME_RAMPS",
    "THEME_KEYS",
    "VFX_PRESETS",
    "VFX_PRESET_MAP",
    "bswap16",
    "decode_lspc2",
    "encode_lspc2",
    "hex_to_lspc2",
    "hex_to_rgb5",
    "lspc2_to_hex",
    "_rgb5_to_hsv",
    "_unit_luma",
    "_hex_hsv",
    "_rgb_unit_to_oklch",
    "recolor_match_shade",
    "generate_harmonious_character_palette",
    "generate_burst_character_palette",
    "sync_character_portraits",
    "VFX_SENTINEL_WORDS",
    "_read_p2_slot_words15",
    "build_character_vfx_map",
    "recolor_vfx_palette",
    "VFX_HIT_EFFECT_CAVE_BASE",
    "VFX_HIT_EFFECT_CAVE_SIZE",
    "VFX_THEME_ENTRY_STRIDE",
    "VFX_HIT_HOOK_ORIGINALS",
    "build_hit_effect_vfx_p1_patch",
    "KOF97BridgeApi",
    "main",
]


def main() -> None:
    """Launch the PyWebView Desktop GUI Application."""
    api = KOF97BridgeApi()
    html_file = resolve_web_index_html()

    window = webview.create_window(
        title="\u62f3\u768797 \u9006\u5411\u9b54\u6539\u5de5\u4f5c\u53f0 (KOF97 Mod Studio)",
        url=str(html_file.resolve()),
        js_api=api,
        width=1280,
        height=780,
        min_size=(1140, 680),
        background_color="#0A0B0E",
    )
    set_app_window(window)

    webview.start(gui="edgechromium", debug=False)


if __name__ == "__main__":
    main()
