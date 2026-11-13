#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KOF97 Mod Studio - Modern Webview Desktop Application.
Implements Design B (Dark Stage) with full two-way communication between
HTML5/CSS3 frontend and Python ROM hacking backend.

All comments, identifiers, and variables strictly follow 100% English specification (Rules.md).
"""

import ctypes
import json
import math
import os
import struct
import subprocess
import sys
import random
import threading
import time
import uuid
import base64
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import webview

# Ensure project root is in sys.path
if getattr(sys, "frozen", False):
    EXE_DIR = Path(sys.executable).resolve().parent
    BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", EXE_DIR))
    if (EXE_DIR / "tools").exists():
        PROJECT_ROOT = EXE_DIR
    elif (EXE_DIR.parent / "tools").exists():
        PROJECT_ROOT = EXE_DIR.parent
    else:
        PROJECT_ROOT = Path.cwd().resolve()
else:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
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


OBSOLETE_THEME_MAP: Dict[str, str] = {
    "black_gold": "imperial_gold",
    "nether_purple": "aurora_mirage",
    "glacial_cyan": "azure_thunder",
    "silver_knight": "paladin_gold",
    "emerald_ghost": "void_shadow",
    "monochrome_ivory": "paladin_gold",
    "solar_flare": "magma_inferno",
}

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.rom_tool import (
    DEFAULT_KOF97_ZIP,
    DEFAULT_OUTPUT_ZIP,
    DEFAULT_SANDBOX_DIR,
    DEFAULT_UNPACK_DIR,
    EXPECTED_SIZES,
    bswap16,
    crc32_hex,
    decode_lspc2,
    encode_lspc2,
    pack_rom_set,
    start_sandbox_kawaks,
    unpack_rom_set,
)

from tools.sprite_compose import (
    SpriteRom,
    official_colors,
    official_header_word,
    render_idle_png,
    slot_labels as compose_slot_labels,
)


def is_custom_theme_id(theme_id: str) -> bool:
    """Return True when the theme id belongs to a user-saved custom palette."""
    return bool(theme_id) and str(theme_id).startswith("custom")



# ============================================================================
# Constant Definitions & Data Models
# ============================================================================

CHARACTER_ROSTER = [
    {"id": 0x00, "name_cn": "\u8349\u8599\u4eac", "name_en": "Kyo Kusanagi"},
    {"id": 0x01, "name_cn": "\u4e8c\u9636\u5802\u7ea2\u4e38", "name_en": "Benimaru Nikaido"},
    {"id": 0x02, "name_cn": "\u5927\u95e8\u4e94\u90ce", "name_en": "Goro Daimon"},
    {"id": 0x03, "name_cn": "\u7279\u745e\u00b7\u4f2f\u52a0\u5fb7", "name_en": "Terry Bogard"},
    {"id": 0x04, "name_cn": "\u5b89\u8fea\u00b7\u4f2f\u52a0\u5fb7", "name_en": "Andy Bogard"},
    {"id": 0x05, "name_cn": "\u4e1c\u4e08", "name_en": "Joe Higashi"},
    {"id": 0x06, "name_cn": "\u5742\u5d0e\u826f", "name_en": "Ryo Sakazaki"},
    {"id": 0x07, "name_cn": "\u7f57\u4f2f\u7279\u00b7\u52a0\u897f\u4e9a", "name_en": "Robert Garcia"},
    {"id": 0x08, "name_cn": "\u5742\u5d0e\u767e\u5408", "name_en": "Yuri Sakazaki"},
    {"id": 0x09, "name_cn": "\u8389\u5b89\u5a1c\u00b7\u54c8\u8fea\u5170", "name_en": "Leona Heidern"},
    {"id": 0x0A, "name_cn": "\u62c9\u5c14\u592b\u00b7\u743c\u65af", "name_en": "Ralf Jones"},
    {"id": 0x0B, "name_cn": "\u514b\u62c9\u514b\u00b7\u65af\u63d0\u5c14", "name_en": "Clark Still"},
    {"id": 0x0C, "name_cn": "\u9ebb\u5bab\u96c5\u5178\u5a1c", "name_en": "Athena Asamiya"},
    {"id": 0x0D, "name_cn": "\u690e\u62f3\u5d07", "name_en": "Sie Kensou"},
    {"id": 0x0E, "name_cn": "\u9547\u5143\u658b", "name_en": "Chin Gentsai"},
    {"id": 0x0F, "name_cn": "\u795e\u4e50\u5343\u9e64", "name_en": "Chizuru Kagura"},
    {"id": 0x10, "name_cn": "\u4e0d\u77e5\u706b\u821e", "name_en": "Mai Shiranui"},
    {"id": 0x11, "name_cn": "\u743c", "name_en": "King"},
    {"id": 0x12, "name_cn": "\u91d1\u5bb6\u85e9", "name_en": "Kim Kaphwan"},
    {"id": 0x13, "name_cn": "\u9648\u56fd\u6c49", "name_en": "Chang Koehan"},
    {"id": 0x14, "name_cn": "\u8521\u5b9d\u5947", "name_en": "Choi Bounge"},
    {"id": 0x15, "name_cn": "\u4e03\u67b7\u793e", "name_en": "Yashiro Nanakase"},
    {"id": 0x16, "name_cn": "\u8c22\u5c14\u7f8e", "name_en": "Shermie"},
    {"id": 0x17, "name_cn": "\u514b\u91cc\u65af", "name_en": "Chris"},
    {"id": 0x18, "name_cn": "\u5c71\u5d0e\u9f99\u4e8c", "name_en": "Ryuji Yamazaki"},
    {"id": 0x19, "name_cn": "\u5e03\u9c81\u00b7\u739b\u4e3d", "name_en": "Blue Mary"},
    {"id": 0x1A, "name_cn": "\u6bd4\u5229\u00b7\u51ef\u6069", "name_en": "Billy Kane"},
    {"id": 0x1B, "name_cn": "\u516b\u795e\u5eb5", "name_en": "Iori Yagami"},
    {"id": 0x1C, "name_cn": "\u77e2\u5439\u771f\u543e", "name_en": "Shingo Yabuki"},
    {"id": 0x1D, "name_cn": "\u66b4\u8d70\u516b\u795e\u5eb5", "name_en": "Orochi Iori"},
    {"id": 0x1E, "name_cn": "\u66b4\u8d70\u8389\u5b89\u5a1c", "name_en": "Orochi Leona"},
    {"id": 0x1F, "name_cn": "\u771f\u4e03\u67b7\u793e", "name_en": "Orochi Yashiro"},
    {"id": 0x20, "name_cn": "\u771f\u8c22\u5c14\u7f8e", "name_en": "Orochi Shermie"},
    {"id": 0x21, "name_cn": "\u771f\u514b\u91cc\u65af", "name_en": "Orochi Chris"},
    {"id": 0x22, "name_cn": "\u5927\u86c7", "name_en": "Orochi"},
    {"id": 0x23, "name_cn": "\u7ecf\u5178\u8349\u8599\u4eac", "name_en": "'94 Kyo"},
]

# Mapping from UI Roster ID (0x00..0x23) to KOF97 Engine tuple:
#   (engine_char_id, alt_form_flag, palette_table_idx)
# Verified against KOF97 P1 ROM routines:
#   - 0x00479A (Palette Loader: engine_cid + (0x0B if alt_flag and engine_cid != 0 else 0))
#   - 0x020834 (Select Screen Alternate Form Check: $2857(A5) bitmask)
#   - 0x0254A2 & 0x015128 (Round Start & Pre-Round Countdown Intro Check: $01D6(A4))
CHAR_ENGINE_MAP: Dict[int, Tuple[int, int, int]] = {
    **{i: (i, 0, i) for i in range(0x1C)},
    0x1C: (0x1F, 0, 0x1F),  # Shingo Yabuki: engine ID 0x1F, normal form, pal table 0x1F (0x08C0)
    0x1D: (0x1C, 0, 0x1C),  # Orochi Iori:   engine ID 0x1C, normal form, pal table 0x1C (0x0800)
    0x1E: (0x1D, 0, 0x1D),  # Orochi Leona:  engine ID 0x1D, normal form, pal table 0x1D (0x0840)
    0x1F: (0x15, 1, 0x20),  # Orochi Yashiro: engine ID 0x15 (Yashiro) + alt_flag=1, pal table 0x20 (0x0900)
    0x20: (0x16, 1, 0x21),  # Orochi Shermie: engine ID 0x16 (Shermie) + alt_flag=1, pal table 0x21 (0x0940)
    0x21: (0x17, 1, 0x22),  # Orochi Chris:   engine ID 0x17 (Chris)   + alt_flag=1, pal table 0x22 (0x0980)
    0x22: (0x1E, 0, 0x1E),  # Orochi:        engine ID 0x1E, normal form, pal table 0x1E (0x0880)
    0x23: (0x00, 1, 0x00),  # '94 Kyo:       engine ID 0x00 (Kyo)     + alt_flag=1, pal table 0x00 (0x0100)
}


def get_char_engine_info(ui_cid: int) -> Tuple[int, int, int]:
    """Return (engine_char_id, alt_form_flag, palette_table_idx) for a UI roster character ID."""
    return CHAR_ENGINE_MAP.get(ui_cid, (ui_cid, 0, ui_cid))

PRESET_THEMES = [
    {
        "id": "classic",
        "name_cn": "\u539f\u7248\u7ecf\u5178",
        "colors": [
            "#FFF7B5", "#F7C584", "#EF945A", "#B55229",
            "#F7F7FF", "#BDBDC5", "#737B84",
            "#DE3A21", "#AD2910", "#7B1908", "#4A0000",
            "#3A3A4A", "#29293A", "#191929", "#000008",
        ],
        "daimon_judogi": ["#FFFFEF", "#EFE6BD", "#CEC59C", "#A59C7B", "#736B4A", "#4A4221"],
        "daimon_headband": "#EF4A21",
        "chang_uniform": ["#FFFFF7", "#EFE6D6", "#BDB5A5", "#847B6B", "#524A3A"],
        "chang_ball": ["#293A7B", "#101942"],
    },
    {
        "id": "crimson_shura",
        "name_cn": "\u8840\u8272\u4fee\u7f57",
        "colors": [
            "#FFF7B5",
            "#F7C584",
            "#EF945A",
            "#B55229",
            "#F7F7FF",
            "#BDBDC5",
            "#737B84",
            "#EF2929",
            "#CE1919",
            "#940808",
            "#4A0000",
            "#4A3A3A",
            "#3A2929",
            "#291919",
            "#000000",
        ],
        "daimon_judogi": ["#FF6B6B", "#EF4444", "#DC2626", "#B91C1C", "#7F1D1D", "#450A0A"],
        "daimon_headband": "#FFFFFF",
        "chang_uniform": ["#FF6B6B", "#EF4444", "#DC2626", "#B91C1C", "#450A0A"],
        "chang_ball": ["#F1F5F9", "#64748B"],
    },
    {
        "id": "azure_thunder",
        "name_cn": "\u82cd\u96f7\u75be\u7535",
        "colors": [
            "#FFF7B5",
            "#F7C584",
            "#EF945A",
            "#B55229",
            "#F7F7FF",
            "#BDBDC5",
            "#737B84",
            "#197BA5",
            "#10638C",
            "#084263",
            "#001929",
            "#3A4242",
            "#293131",
            "#192121",
            "#000000",
        ],
        "daimon_judogi": ["#60A5FA", "#3B82F6", "#2563EB", "#1D4ED8", "#172554", "#080D1A"],
        "daimon_headband": "#FDE047",
        "chang_uniform": ["#60A5FA", "#3B82F6", "#2563EB", "#1D4ED8", "#0F172A"],
        "chang_ball": ["#F8FAFC", "#94A3B8"],
    },
    {
        "id": "paladin_gold",
        "name_cn": "\u5723\u6bbf\u9a91\u58eb",
        "colors": [
            "#FFF7B5",
            "#F7C584",
            "#EF945A",
            "#B55229",
            "#F7F7FF",
            "#BDBDC5",
            "#737B84",
            "#7B6310",
            "#635208",
            "#423100",
            "#191900",
            "#424231",
            "#313121",
            "#212110",
            "#000000",
        ],
        "daimon_judogi": ["#FFFFFF", "#E2E8F0", "#CBD5E1", "#94A3B8", "#64748B", "#334155"],
        "daimon_headband": "#EAB308",
        "chang_uniform": ["#FFFFFF", "#E2E8F0", "#CBD5E1", "#94A3B8", "#475569"],
        "chang_ball": ["#FDE047", "#CA8A04"],
    },
    {
        "id": "void_shadow",
        "name_cn": "\u865a\u7a7a\u5927\u86c7",
        "colors": [
            "#FFF7B5",
            "#F7C584",
            "#EF945A",
            "#B55229",
            "#F7F7FF",
            "#BDBDC5",
            "#737B84",
            "#198463",
            "#086B52",
            "#004A31",
            "#002119",
            "#314242",
            "#213131",
            "#102121",
            "#000000",
        ],
        "daimon_judogi": ["#6EE7B7", "#34D399", "#10B981", "#059669", "#047857", "#022C22"],
        "daimon_headband": "#FDE047",
        "chang_uniform": ["#6EE7B7", "#34D399", "#10B981", "#059669", "#022C22"],
        "chang_ball": ["#E2E8F0", "#64748B"],
    },
    {
        "id": "cyber_neon",
        "name_cn": "\u8d5b\u535a\u9713\u8679",
        "colors": [
            "#FFF7B5",
            "#F7C584",
            "#EF945A",
            "#B55229",
            "#F7F7FF",
            "#BDBDC5",
            "#737B84",
            "#DE214A",
            "#C5193A",
            "#8C0821",
            "#420010",
            "#4A3A3A",
            "#3A2929",
            "#291919",
            "#000000",
        ],
        "daimon_judogi": ["#FB7185", "#F43F5E", "#E11D48", "#BE123C", "#881337", "#4C0519"],
        "daimon_headband": "#22D3EE",
        "chang_uniform": ["#FB7185", "#F43F5E", "#E11D48", "#9F1239", "#4C0519"],
        "chang_ball": ["#38BDF8", "#0284C7"],
    },
    {
        "id": "magma_inferno",
        "name_cn": "\u7194\u5ca9\u5730\u72f1",
        "colors": [
            "#FFF7B5",
            "#F7C584",
            "#EF945A",
            "#B55229",
            "#F7F7FF",
            "#BDBDC5",
            "#737B84",
            "#A54A19",
            "#8C3A10",
            "#5A2908",
            "#291000",
            "#423A3A",
            "#312929",
            "#211919",
            "#000000",
        ],
        "daimon_judogi": ["#FFA040", "#FF7A00", "#EA580C", "#C2410C", "#9A3412", "#4E1402"],
        "daimon_headband": "#EF4444",
        "chang_uniform": ["#FFA040", "#FF7A00", "#EA580C", "#9A3412", "#4E1402"],
        "chang_ball": ["#71717A", "#27272A"],
    },
    {
        "id": "imperial_gold",
        "name_cn": "\u5e1d\u738b\u6218\u5c0a",
        "colors": [
            "#FFF7B5",
            "#F7C584",
            "#EF945A",
            "#B55229",
            "#F7F7FF",
            "#BDBDC5",
            "#737B84",
            "#7B6310",
            "#635208",
            "#423100",
            "#191900",
            "#424231",
            "#313121",
            "#212110",
            "#000000",
        ],
        "daimon_judogi": ["#FFF066", "#FFDE17", "#E5B800", "#B38600", "#7A5700", "#3D2900"],
        "daimon_headband": "#DC2626",
        "chang_uniform": ["#FFF066", "#FFDE17", "#E5B800", "#B38600", "#3D2900"],
        "chang_ball": ["#FDE047", "#854D0E"],
    },
    {
        "id": "sakura_frost",
        "name_cn": "\u6a31\u843d\u5439\u96ea",
        "colors": [
            "#FFF7B5",
            "#F7C584",
            "#EF945A",
            "#B55229",
            "#F7F7FF",
            "#BDBDC5",
            "#737B84",
            "#D6216B",
            "#BD105A",
            "#84083A",
            "#420019",
            "#4A3A42",
            "#3A2931",
            "#291921",
            "#000000",
        ],
        "daimon_judogi": ["#FBCFE8", "#F472B6", "#EC4899", "#BE185D", "#831843", "#460621"],
        "daimon_headband": "#FFFFFF",
        "chang_uniform": ["#FBCFE8", "#F472B6", "#DB2777", "#831843", "#460621"],
        "chang_ball": ["#F8FAFC", "#94A3B8"],
    },
    {
        "id": "aurora_mirage",
        "name_cn": "\u6781\u5149\u5e7b\u5f71",
        "colors": [
            "#FFF7B5",
            "#F7C584",
            "#EF945A",
            "#B55229",
            "#F7F7FF",
            "#BDBDC5",
            "#737B84",
            "#9429FF",
            "#8419DE",
            "#5A08A5",
            "#290052",
            "#423A4A",
            "#31293A",
            "#211929",
            "#000000",
        ],
        "daimon_judogi": ["#C084FC", "#A855F7", "#7E22CE", "#581C87", "#3B0764", "#1F0335"],
        "daimon_headband": "#22D3EE",
        "chang_uniform": ["#C084FC", "#A855F7", "#7E22CE", "#581C87", "#1F0335"],
        "chang_ball": ["#2DD4BF", "#0F766E"],
    },
    {
        "id": "toxic_hazard",
        "name_cn": "\u5267\u6bd2\u9178\u8680",
        "colors": [
            "#FFF7B5",
            "#F7C584",
            "#EF945A",
            "#B55229",
            "#F7F7FF",
            "#BDBDC5",
            "#737B84",
            "#4A7B10",
            "#3A6308",
            "#294200",
            "#101900",
            "#3A4231",
            "#293121",
            "#192110",
            "#000000",
        ],
        "daimon_judogi": ["#BEF264", "#84CC16", "#4D7C0F", "#365314", "#1A2E05", "#0D1702"],
        "daimon_headband": "#FFFFFF",
        "chang_uniform": ["#BEF264", "#84CC16", "#4D7C0F", "#365314", "#1A2E05"],
        "chang_ball": ["#E2E8F0", "#64748B"],
    },
    {
        "id": "abyssal_frost",
        "name_cn": "\u6df1\u6e0a\u5bd2\u51b0",
        "colors": [
            "#FFF7B5",
            "#F7C584",
            "#EF945A",
            "#B55229",
            "#F7F7FF",
            "#BDBDC5",
            "#737B84",
            "#197BA5",
            "#10638C",
            "#084263",
            "#001929",
            "#3A4242",
            "#293131",
            "#192121",
            "#000000",
        ],
        "daimon_judogi": ["#E0F2FE", "#BAE6FD", "#7DD3FC", "#38BDF8", "#0284C7", "#0369A1"],
        "daimon_headband": "#FFFFFF",
        "chang_uniform": ["#E0F2FE", "#BAE6FD", "#38BDF8", "#0284C7", "#0C4A6E"],
        "chang_ball": ["#38BDF8", "#075985"],
    },
    {
        "id": "phoenix_nirvana",
        "name_cn": "\u51e4\u821e\u6d85\u69c3",
        "colors": [
            "#FFF7B5",
            "#F7C584",
            "#EF945A",
            "#B55229",
            "#F7F7FF",
            "#BDBDC5",
            "#737B84",
            "#B54221",
            "#9C3110",
            "#6B2108",
            "#311000",
            "#4A3A3A",
            "#3A2929",
            "#291919",
            "#000000",
        ],
        "daimon_judogi": ["#FED7AA", "#FB923C", "#F97316", "#EA580C", "#C2410C", "#7C2D12"],
        "daimon_headband": "#FDE047",
        "chang_uniform": ["#FED7AA", "#FB923C", "#EA580C", "#C2410C", "#7C2D12"],
        "chang_ball": ["#F59E0B", "#B45309"],
    },
    {
        "id": "emerald_lotus",
        "name_cn": "\u78a7\u7389\u9752\u83b2",
        "colors": [
            "#FFF7B5",
            "#F7C584",
            "#EF945A",
            "#B55229",
            "#F7F7FF",
            "#BDBDC5",
            "#737B84",
            "#198463",
            "#086B52",
            "#004A31",
            "#002119",
            "#314242",
            "#213131",
            "#102121",
            "#000000",
        ],
        "daimon_judogi": ["#D1FAE5", "#A7F3D0", "#6EE7B7", "#10B981", "#059669", "#022C22"],
        "daimon_headband": "#34D399",
        "chang_uniform": ["#D1FAE5", "#A7F3D0", "#34D399", "#059669", "#022C22"],
        "chang_ball": ["#10B981", "#064E3B"],
    },
    {
        "id": "shadow_ninja",
        "name_cn": "\u6697\u591c\u5f71\u5203",
        "colors": [
            "#FFF7B5",
            "#F7C584",
            "#EF945A",
            "#B55229",
            "#F7F7FF",
            "#BDBDC5",
            "#737B84",
            "#5A636B",
            "#4A5252",
            "#31313A",
            "#101919",
            "#3A4242",
            "#293131",
            "#192121",
            "#000000",
        ],
        "daimon_judogi": ["#F1F5F9", "#CBD5E1", "#94A3B8", "#64748B", "#334155", "#0F172A"],
        "daimon_headband": "#EF4444",
        "chang_uniform": ["#F1F5F9", "#CBD5E1", "#64748B", "#334155", "#0F172A"],
        "chang_ball": ["#E2E8F0", "#475569"],
    },
    {
        "id": "sunset_overdrive",
        "name_cn": "\u66ae\u5149\u6d41\u706b",
        "colors": [
            "#FFF7B5",
            "#F7C584",
            "#EF945A",
            "#B55229",
            "#F7F7FF",
            "#BDBDC5",
            "#737B84",
            "#A54A19",
            "#8C3A10",
            "#5A2908",
            "#291000",
            "#423A3A",
            "#312929",
            "#211919",
            "#000000",
        ],
        "daimon_judogi": ["#FED7AA", "#FDBA74", "#FB923C", "#F97316", "#C2410C", "#431407"],
        "daimon_headband": "#DC2626",
        "chang_uniform": ["#FED7AA", "#FB923C", "#F97316", "#C2410C", "#431407"],
        "chang_ball": ["#F59E0B", "#78350F"],
    },
    {
        "id": "amethyst_phantom",
        "name_cn": "\u7d2b\u6676\u9b45\u5f71",
        "colors": [
            "#FFF7B5",
            "#F7C584",
            "#EF945A",
            "#B55229",
            "#F7F7FF",
            "#BDBDC5",
            "#737B84",
            "#9429FF",
            "#7B19E6",
            "#5A08A5",
            "#290052",
            "#423A4A",
            "#31293A",
            "#211929",
            "#000000",
        ],
        "daimon_judogi": ["#F3E8FF", "#D8B4FE", "#C084FC", "#9333EA", "#6B21A8", "#3B0764"],
        "daimon_headband": "#F0ABFC",
        "chang_uniform": ["#F3E8FF", "#D8B4FE", "#A855F7", "#6B21A8", "#3B0764"],
        "chang_ball": ["#C084FC", "#581C87"],
    },
    {
        "id": "ocean_tempest",
        "name_cn": "\u6012\u6d77\u72c2\u6d9b",
        "colors": [
            "#FFF7B5",
            "#F7C584",
            "#EF945A",
            "#B55229",
            "#F7F7FF",
            "#BDBDC5",
            "#737B84",
            "#197BA5",
            "#10638C",
            "#084263",
            "#001929",
            "#3A4242",
            "#293131",
            "#192121",
            "#000000",
        ],
        "daimon_judogi": ["#BAE6FD", "#7DD3FC", "#38BDF8", "#0284C7", "#0369A1", "#082F49"],
        "daimon_headband": "#FFFFFF",
        "chang_uniform": ["#BAE6FD", "#7DD3FC", "#0284C7", "#075985", "#082F49"],
        "chang_ball": ["#0284C7", "#0F172A"],
    },
    {
        "id": "valkyrie_silver",
        "name_cn": "\u767d\u94f6\u88c1\u51b3",
        "colors": [
            "#FFF7B5",
            "#F7C584",
            "#EF945A",
            "#B55229",
            "#F7F7FF",
            "#BDBDC5",
            "#737B84",
            "#5A636B",
            "#4A5252",
            "#31313A",
            "#101919",
            "#3A4242",
            "#293131",
            "#192121",
            "#000000",
        ],
        "daimon_judogi": ["#FFFFFF", "#E2E8F0", "#CBD5E1", "#94A3B8", "#64748B", "#334155"],
        "daimon_headband": "#F59E0B",
        "chang_uniform": ["#FFFFFF", "#E2E8F0", "#CBD5E1", "#94A3B8", "#475569"],
        "chang_ball": ["#F8FAFC", "#64748B"],
    },
    {
        "id": "crimson_dragon",
        "name_cn": "\u8840\u9f99\u7834\u519b",
        "colors": [
            "#FFF7B5",
            "#F7C584",
            "#EF945A",
            "#B55229",
            "#F7F7FF",
            "#BDBDC5",
            "#737B84",
            "#EF2929",
            "#CE1919",
            "#940808",
            "#4A0000",
            "#4A3A3A",
            "#3A2929",
            "#291919",
            "#000000",
        ],
        "daimon_judogi": ["#FCA5A5", "#EF4444", "#DC2626", "#B91C1C", "#7F1D1D", "#450A0A"],
        "daimon_headband": "#FBBF24",
        "chang_uniform": ["#FCA5A5", "#EF4444", "#DC2626", "#7F1D1D", "#450A0A"],
        "chang_ball": ["#991B1B", "#450A0A"],
    },
    {
        "id": "solar_flare",
        "name_cn": "\u65e5\u8037\u98ce\u66b4",
        "colors": [
            "#FFF7B5",
            "#F7C584",
            "#EF945A",
            "#B55229",
            "#F7F7FF",
            "#BDBDC5",
            "#737B84",
            "#7B6310",
            "#635208",
            "#423100",
            "#191900",
            "#424231",
            "#313121",
            "#212110",
            "#000000",
        ],
        "daimon_judogi": ["#FEF08A", "#FDE047", "#FACC15", "#EAB308", "#A16207", "#422006"],
        "daimon_headband": "#DC2626",
        "chang_uniform": ["#FEF08A", "#FACC15", "#EAB308", "#A16207", "#422006"],
        "chang_ball": ["#FDE047", "#854D0E"],
    },
]

DAMAGE_MODES = [
    {
        "id": "god",
        "hook": bytes.fromhex("4eb80300"),
        "cave": bytes.fromhex("4240d16c013a4e75"),
    },
    {
        "id": "eighth",
        "hook": bytes.fromhex("4eb80300"),
        "cave": bytes.fromhex("e648d16c013a4e75"),
    },
    {
        "id": "quarter",
        "hook": bytes.fromhex("4eb80300"),
        "cave": bytes.fromhex("e448d16c013a4e75"),
    },
    {
        "id": "halved",
        "hook": bytes.fromhex("4eb80300"),
        "cave": bytes.fromhex("e248d16c013a4e75"),
    },
    {
        "id": "normal",
        "hook": bytes.fromhex("d16c013a"),
        "cave": bytes.fromhex("ffffffffffffffff"),
    },
    {
        "id": "hell",
        "hook": bytes.fromhex("4eb80300"),
        "cave": bytes.fromhex("e348d16c013a4e75"),
    },
]


def hex_to_lspc2(hex_code: str) -> int:
    """Convert hex string #RRGGBB to 16-bit Neo-Geo LSPC2 word."""
    clean = hex_code.strip().lstrip("#")
    if len(clean) != 6:
        return 0
    try:
        r = int(clean[0:2], 16)
        g = int(clean[2:4], 16)
        b = int(clean[4:6], 16)
        r5 = round(r * 31 / 255)
        g5 = round(g * 31 / 255)
        b5 = round(b * 31 / 255)
        return encode_lspc2(r5, g5, b5, dark=0)
    except ValueError:
        return 0


def hex_to_rgb5(hex_code: str) -> Tuple[int, int, int]:
    """Convert hex string #RRGGBB to (r5, g5, b5) tuple."""
    clean = hex_code.strip().lstrip("#")
    if len(clean) != 6:
        return (0, 0, 0)
    try:
        r = round(int(clean[0:2], 16) * 31 / 255)
        g = round(int(clean[2:4], 16) * 31 / 255)
        b = round(int(clean[4:6], 16) * 31 / 255)
        return (r, g, b)
    except ValueError:
        return (0, 0, 0)



def lspc2_to_hex(w: int) -> str:
    """Convert 16-bit Neo-Geo LSPC2 word to #RRGGBB hex code."""
    r5, g5, b5, _ = decode_lspc2(w)
    r = round(r5 * 255 / 31)
    g = round(g5 * 255 / 31)
    b = round(b5 * 255 / 31)
    return f"#{r:02X}{g:02X}{b:02X}"


THEME_RAMPS: Dict[str, Dict[str, Any]] = {
    "void_shadow": {
        "primary": ["#A7F3D0", "#34D399", "#10B981", "#059669", "#047857", "#064E3B"],
        "accent": ["#E2E8F0", "#94A3B8", "#475569", "#1E293B"],
        "light": ["#ECFDF5", "#D1FAE5"],
        "dark": ["#18181B", "#09090B", "#000000"],
    },
    "cyber_neon": {
        "primary": ["#BAE6FD", "#38BDF8", "#0284C7", "#0369A1", "#075985", "#0C4A6E"],
        "accent": ["#FDA4AF", "#F43F5E", "#E11D48", "#9F1239"],
        "light": ["#F0FDF4", "#E0F2FE"],
        "dark": ["#1E1B4B", "#0F172A", "#030712"],
    },
    "crimson_shura": {
        "primary": ["#FCA5A5", "#EF4444", "#DC2626", "#B91C1C", "#7F1D1D", "#450A0A"],
        "accent": ["#FAFAFA", "#D4D4D4", "#737373", "#262626"],
        "light": ["#FEF2F2", "#FEE2E2"],
        "dark": ["#262626", "#171717", "#000000"],
    },
    "azure_thunder": {
        "primary": ["#93C5FD", "#60A5FA", "#3B82F6", "#1D4ED8", "#1E40AF", "#172554"],
        "accent": ["#E0F2FE", "#7DD3FC", "#0284C7", "#075985"],
        "light": ["#EFF6FF", "#DBEAFE"],
        "dark": ["#0F172A", "#080D1A", "#02040A"],
    },
    "paladin_gold": {
        "primary": ["#FFFFFF", "#E2E8F0", "#CBD5E1", "#94A3B8", "#64748B", "#334155"],
        "accent": ["#FEF08A", "#FACC15", "#CA8A04", "#854D0E"],
        "light": ["#FFFFFF", "#F8FAFC"],
        "dark": ["#1E293B", "#0F172A", "#020617"],
    },
    "toxic_hazard": {
        "primary": ["#D9F99D", "#BEF264", "#84CC16", "#65A30D", "#3F6212", "#1A2E05"],
        "accent": ["#FED7AA", "#FB923C", "#EA580C", "#9A3412"],
        "light": ["#F7FEE7", "#ECFCCB"],
        "dark": ["#334155", "#1E293B", "#0F172A"],
    },
    "sakura_frost": {
        "primary": ["#FBCFE8", "#F472B6", "#EC4899", "#DB2777", "#9D174D", "#500724"],
        "accent": ["#F5D0FE", "#E879F9", "#C026D3", "#701A75"],
        "light": ["#FFF1F2", "#FDF2F8"],
        "dark": ["#2E1065", "#1E0842", "#0D031F"],
    },
    "magma_inferno": {
        "primary": ["#FED7AA", "#FB923C", "#F97316", "#EA580C", "#9A3412", "#431407"],
        "accent": ["#FEF08A", "#FACC15", "#EAB308", "#854D0E"],
        "light": ["#FFF7ED", "#FFEDD5"],
        "dark": ["#27272A", "#18181B", "#09090B"],
    },
    "aurora_mirage": {
        "primary": ["#E9D5FF", "#C084FC", "#A855F7", "#7E22CE", "#581C87", "#2E1065"],
        "accent": ["#99F6E4", "#2DD4BF", "#0D9488", "#115E59"],
        "light": ["#FAF5FF", "#F0FDFA"],
        "dark": ["#1E123F", "#120929", "#070314"],
    },
    "imperial_gold": {
        "primary": ["#FEF08A", "#FACC15", "#EAB308", "#CA8A04", "#854D0E", "#451A03"],
        "accent": ["#FEF3C7", "#FDE68A", "#D97706", "#78350F"],
        "light": ["#FFFBEB", "#FEF3C7"],
        "dark": ["#1C1917", "#0C0A09", "#000000"],
    },
    "abyssal_frost": {
        "primary": ["#E0F2FE", "#BAE6FD", "#7DD3FC", "#38BDF8", "#0284C7", "#0C4A6E"],
        "accent": ["#FFFFFF", "#F1F5F9", "#94A3B8", "#475569"],
        "light": ["#F0F9FF", "#E0F2FE"],
        "dark": ["#0F172A", "#020617", "#000000"],
    },
    "phoenix_nirvana": {
        "primary": ["#FFEDD5", "#FED7AA", "#FB923C", "#EA580C", "#C2410C", "#7C2D12"],
        "accent": ["#FEF08A", "#FACC15", "#EAB308", "#854D0E"],
        "light": ["#FFF7ED", "#FFEDD5"],
        "dark": ["#1C1917", "#0C0A09", "#000000"],
    },
    "emerald_lotus": {
        "primary": ["#D1FAE5", "#A7F3D0", "#6EE7B7", "#34D399", "#059669", "#022C22"],
        "accent": ["#F0FDF4", "#BBF7D0", "#4ADE80", "#15803D"],
        "light": ["#F0FDF4", "#DCFCE7"],
        "dark": ["#111827", "#030712", "#000000"],
    },
    "shadow_ninja": {
        "primary": ["#F8FAFC", "#E2E8F0", "#94A3B8", "#64748B", "#334155", "#0F172A"],
        "accent": ["#EF4444", "#DC2626", "#991B1B", "#450A0A"],
        "light": ["#FFFFFF", "#F8FAFC"],
        "dark": ["#18181B", "#09090B", "#000000"],
    },
    "sunset_overdrive": {
        "primary": ["#FFEDD5", "#FED7AA", "#FB923C", "#F97316", "#C2410C", "#431407"],
        "accent": ["#E0E7FF", "#818CF8", "#4338CA", "#1E1B4B"],
        "light": ["#FFF7ED", "#FFEDD5"],
        "dark": ["#1E1B4B", "#0F0E2A", "#000000"],
    },
    "amethyst_phantom": {
        "primary": ["#F3E8FF", "#D8B4FE", "#C084FC", "#9333EA", "#6B21A8", "#3B0764"],
        "accent": ["#FDF4FF", "#F0ABFC", "#C026D3", "#701A75"],
        "light": ["#FAF5FF", "#F3E8FF"],
        "dark": ["#3B1754", "#220D33", "#11061C"],
    },
    "ocean_tempest": {
        "primary": ["#BAE6FD", "#7DD3FC", "#38BDF8", "#0284C7", "#0369A1", "#082F49"],
        "accent": ["#E0F2FE", "#BAE6FD", "#0284C7", "#075985"],
        "light": ["#F0F9FF", "#E0F2FE"],
        "dark": ["#0F172A", "#020617", "#000000"],
    },
    "valkyrie_silver": {
        "primary": ["#FFFFFF", "#E2E8F0", "#CBD5E1", "#94A3B8", "#64748B", "#334155"],
        "accent": ["#FEF08A", "#FACC15", "#EAB308", "#854D0E"],
        "light": ["#FFFFFF", "#F8FAFC"],
        "dark": ["#334155", "#1E293B", "#0F172A"],
    },
    "crimson_dragon": {
        "primary": ["#FCA5A5", "#EF4444", "#DC2626", "#B91C1C", "#7F1D1D", "#450A0A"],
        "accent": ["#FEF3C7", "#FDE68A", "#D97706", "#78350F"],
        "light": ["#FEF2F2", "#FEE2E2"],
        "dark": ["#1F1313", "#0E0707", "#000000"],
    },
    "solar_flare": {
        "primary": ["#FEF08A", "#FDE047", "#FACC15", "#EAB308", "#A16207", "#422006"],
        "accent": ["#FEE2E2", "#FCA5A5", "#DC2626", "#7F1D1D"],
        "light": ["#FEFCE8", "#FEF9C3"],
        "dark": ["#1C1917", "#0C0A09", "#000000"],
    },
}


# Disjoint-union semantic slot schema for all 36 characters in KOF97 (0x00..0x23).
# Audited against official A-button palettes. Hair takes the accent hue;
# clothes, pants and shoes take the primary hue. Skin, true white cloth
# and outlines stay official. Cream or midtone cloth is not parked in
# white_trim, so a theme can cover the visible costume.
CHARACTER_PALETTE_SCHEMA: Dict[int, Dict[str, List[int]]] = {
    0x00: {"skin": [1, 2, 3, 4], "white_trim": [0], "hair": [5, 6], "primary": [7, 8, 9], "dark_anchor": [10, 11, 12, 13], "contour": [14]},
    0x01: {"skin": [0, 1, 2, 3, 4], "white_trim": [5], "dark_anchor": [6, 7, 8, 9], "contour": [10], "hair": [11, 12, 13, 14]},
    0x02: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7, 8, 9, 10], "accent": [11], "white_trim": [12, 13], "contour": [14]},
    0x03: {"skin": [0, 1, 2, 3, 4], "dark_anchor": [5, 6, 7, 8], "primary": [9, 10], "accent": [11], "hair": [12], "white_trim": [13], "contour": [14]},
    0x04: {"skin": [0, 1, 2, 3, 4], "white_trim": [5, 11], "primary": [6, 7, 8, 9], "accent": [10], "hair": [12, 13], "contour": [14]},
    0x05: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7], "hair": [8, 9], "dark_anchor": [10, 11, 12], "white_trim": [13], "contour": [14]},
    0x06: {"white_trim": [0], "skin": [1, 2, 3, 4, 5], "primary": [6, 7, 8, 9, 10], "contour": [11], "hair": [12, 13, 14]},
    0x07: {"skin": [0, 1, 2, 3, 4], "accent": [5], "primary": [6, 7, 8, 9, 10], "dark_anchor": [11, 12, 13], "contour": [14]},
    0x08: {"accent": [0], "skin": [1, 2, 3, 4, 5], "white_trim": [6, 7], "primary": [8, 9, 10], "hair": [11, 12, 13], "contour": [14]},
    0x09: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7, 8, 9], "dark_anchor": [10], "contour": [11], "hair": [12, 13, 14]},
    0x0A: {"white_trim": [0], "skin": [1, 2, 3, 4, 5], "primary": [6, 7, 8, 9], "dark_anchor": [10], "hair": [11, 12, 13], "contour": [14]},
    0x0B: {"white_trim": [0], "skin": [1, 2, 3, 4, 5], "primary": [6, 7, 8, 9], "dark_anchor": [10], "hair": [11, 12, 13], "contour": [14]},
    0x0C: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7, 8], "white_trim": [9], "hair": [10, 11, 12, 13, 14]},
    0x0D: {"white_trim": [0], "skin": [1, 2, 3, 4, 5], "primary": [6, 7, 8, 9], "dark_anchor": [10, 11, 12, 13], "contour": [14]},
    0x0E: {"skin": [0, 1, 2, 3, 4], "white_trim": [5], "primary": [6, 7, 8, 9], "dark_anchor": [10, 11, 12, 13], "contour": [14]},
    0x0F: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7, 8, 9, 10, 11, 12], "accent": [13, 14]},
    0x10: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7, 8], "dark_anchor": [9, 10, 11, 12], "accent": [13], "contour": [14]},
    0x11: {"hair": [0, 1, 2, 3], "accent": [4, 5], "primary": [6, 7, 8], "white_trim": [9], "skin": [10, 11, 12, 13, 14]},
    0x12: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7, 8, 9, 14], "hair": [10, 11, 12], "contour": [13]},
    0x13: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7, 8, 9], "accent": [10, 11], "hair": [12, 13, 14]},
    0x14: {"skin": [0, 1, 2, 3], "primary": [4, 5, 6, 7, 8], "accent": [9, 10], "hair": [11, 12, 13], "contour": [14]},
    0x15: {"skin": [0, 1, 2, 3, 4], "white_trim": [5], "primary": [6, 7, 8, 9], "dark_anchor": [10, 11, 12, 13], "contour": [14]},
    0x16: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7, 8, 9], "accent": [10, 11], "contour": [12], "dark_anchor": [13, 14]},
    0x17: {"skin": [0, 1, 2, 3, 4], "white_trim": [5, 6], "hair": [7, 8, 9], "primary": [10, 11, 12], "dark_anchor": [13], "contour": [14]},
    0x18: {"skin": [0, 1, 2, 3, 4], "hair": [5, 6, 7], "primary": [8, 9, 10, 11, 12, 14], "contour": [13]},
    0x19: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7], "hair": [8, 9, 10], "dark_anchor": [11, 12, 13], "contour": [14]},
    0x1A: {"skin": [0, 1, 2, 3, 4], "dark_anchor": [5, 6, 7, 8, 9], "primary": [10, 11, 12, 13, 14]},
    0x1B: {"skin": [0, 1, 2, 3], "white_trim": [4, 5, 6], "hair": [7, 8, 9, 10], "primary": [11, 12, 13], "contour": [14]},
    0x1C: {"white_trim": [0], "skin": [1, 2, 3, 4, 5], "hair": [6], "primary": [7, 8, 9], "dark_anchor": [10, 11, 12, 13], "contour": [14]},
    0x1D: {"skin": [0, 1, 2, 3], "white_trim": [4, 5, 6], "hair": [7, 8, 9, 10], "primary": [11, 12, 13], "contour": [14]},
    0x1E: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7, 8, 9], "dark_anchor": [10], "contour": [11], "hair": [12, 13, 14]},
    0x1F: {"skin": [0, 1, 2, 3, 4], "white_trim": [5], "primary": [6, 7, 8, 9], "dark_anchor": [10, 11, 12, 13], "contour": [14]},
    0x20: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7, 8, 9], "accent": [10, 11], "contour": [12], "hair": [13, 14]},
    0x21: {"skin": [0, 1, 2, 3, 4], "white_trim": [5], "primary": [6, 7, 8, 9], "dark_anchor": [10, 11, 12, 13], "contour": [14]},
    0x22: {"skin": [0, 1, 2, 3, 4], "white_trim": [5], "primary": [6, 7, 8, 9, 10], "contour": [11], "accent": [12, 13, 14]},
    0x23: {"skin": [1, 2, 3, 4], "white_trim": [0], "hair": [5, 6], "primary": [7, 8, 9], "dark_anchor": [10, 11, 12, 13], "contour": [14]},
}


# Identity hues for the 20 skins. Primary dyes the costume; accent dyes
# headbands, ribbons and metal. Silver themes stay below the chroma cutoff
# so they desaturate instead of becoming a vivid tint of gray's hue.
THEME_KEYS: Dict[str, Tuple[str, str]] = {
    "crimson_shura": ("#DC2626", "#F8FAFC"),
    "azure_thunder": ("#0284C7", "#FDE047"),
    "paladin_gold": ("#EAB308", "#DC2626"),
    "void_shadow": ("#10B981", "#FDE047"),
    "cyber_neon": ("#E11D48", "#22D3EE"),
    "magma_inferno": ("#EA580C", "#EF4444"),
    "imperial_gold": ("#EAB308", "#DC2626"),
    "sakura_frost": ("#DB2777", "#F8FAFC"),
    "aurora_mirage": ("#7E22CE", "#22D3EE"),
    "toxic_hazard": ("#65A30D", "#F8FAFC"),
    "abyssal_frost": ("#0284C7", "#F8FAFC"),
    "phoenix_nirvana": ("#FF4500", "#FDE047"),
    "emerald_lotus": ("#059669", "#34D399"),
    "shadow_ninja": ("#94A3B8", "#EF4444"),
    "sunset_overdrive": ("#EA580C", "#DC2626"),
    "amethyst_phantom": ("#A855F7", "#E879F9"),
    "ocean_tempest": ("#0284C7", "#F8FAFC"),
    "valkyrie_silver": ("#CBD5E1", "#F59E0B"),
    "crimson_dragon": ("#DC2626", "#FBBF24"),
    "solar_flare": ("#EAB308", "#DC2626"),
}


def _rgb5_to_hsv(r5: int, g5: int, b5: int) -> Tuple[float, float, float]:
    """Convert Neo-Geo 5-bit RGB to HSV. Hue is degrees, S and V are 0..1."""
    rf, gf, bf = r5 / 31.0, g5 / 31.0, b5 / 31.0
    mx = max(rf, gf, bf)
    mn = min(rf, gf, bf)
    span = mx - mn
    if span <= 1e-8 or mx <= 1e-8:
        hue = 0.0
        sat = 0.0
    else:
        if mx == rf:
            hue = (60.0 * ((gf - bf) / span) + 360.0) % 360.0
        elif mx == gf:
            hue = (60.0 * ((bf - rf) / span) + 120.0) % 360.0
        else:
            hue = (60.0 * ((rf - gf) / span) + 240.0) % 360.0
        sat = span / mx
    return hue, sat, mx


def _hsv_to_rgb_unit(hue: float, sat: float, val: float) -> Tuple[float, float, float]:
    """Convert HSV (hue degrees, S/V 0..1) to linear RGB in 0..1."""
    sat = min(1.0, max(0.0, sat))
    val = min(1.0, max(0.0, val))
    sector = (hue % 360.0) / 60.0
    chroma = val * sat
    mid = chroma * (1.0 - abs((sector % 2.0) - 1.0))
    base = val - chroma
    idx = int(sector) % 6
    if idx == 0:
        rf, gf, bf = chroma, mid, 0.0
    elif idx == 1:
        rf, gf, bf = mid, chroma, 0.0
    elif idx == 2:
        rf, gf, bf = 0.0, chroma, mid
    elif idx == 3:
        rf, gf, bf = 0.0, mid, chroma
    elif idx == 4:
        rf, gf, bf = mid, 0.0, chroma
    else:
        rf, gf, bf = chroma, 0.0, mid
    return rf + base, gf + base, bf + base


def _unit_luma(rf: float, gf: float, bf: float) -> float:
    """Perceived luma of a 0..1 RGB triple."""
    return 0.299 * rf + 0.587 * gf + 0.114 * bf


def _hex_hsv(hex_code: str) -> Tuple[float, float, float]:
    """HSV of a #RRGGBB swatch, quantized the same way as a palette word."""
    r5, g5, b5 = hex_to_rgb5(hex_code)
    return _rgb5_to_hsv(r5, g5, b5)


def theme_hsv(theme_id: str) -> Tuple[float, float, float, float]:
    """Return (primary_hue, primary_sat, accent_hue, accent_sat) for a skin."""
    primary_hex, accent_hex = THEME_KEYS[theme_id]
    ph, ps, _ = _hex_hsv(primary_hex)
    ah, a_sat, _ = _hex_hsv(accent_hex)
    return ph, ps, ah, a_sat


# Mid gray in the same 0..1 luma as _unit_luma. Official Iori red sits
# under this (about 0.41). Brighter saturated cloth is a highlight.
_LIT_CLOTH_LUMA = 0.5


def _v_for_luma(hue: float, sat: float, target_y: float, cap: bool) -> float:
    """
    Pick V so HSV luma lands on target_y.
    cap=True never exceeds target_y (pigment must not grow a highlight).
    """
    def luma_at(val: float) -> float:
        rf, gf, bf = _hsv_to_rgb_unit(hue, sat, val)
        return _unit_luma(rf, gf, bf)

    if cap:
        if luma_at(0.0) >= target_y:
            return 0.0
        if luma_at(1.0) <= target_y:
            return 1.0
        lo, hi = 0.0, 1.0
        for _ in range(20):
            mid = (lo + hi) * 0.5
            if luma_at(mid) <= target_y:
                lo = mid
            else:
                hi = mid
        return lo

    lo, hi = 0.0, 1.0
    for _ in range(20):
        mid = (lo + hi) * 0.5
        if luma_at(mid) < target_y:
            lo = mid
        else:
            hi = mid
    return (lo + hi) * 0.5


def _ease_sat_to_luma(hue: float, sat: float, target_y: float) -> float:
    """
    Drop saturation until value 1 can reach target_y.

    A darker hue is dimmer than yellow at the same saturation and value.
    Lowering saturation mixes in white so a highlight can keep its luma.
    Returns the highest saturation that still reaches target_y, or the
    input saturation when that hue is already bright enough.
    """
    if _unit_luma(*_hsv_to_rgb_unit(hue, sat, 1.0)) + 1e-4 >= target_y:
        return sat
    slo, shi = 0.0, sat
    for _ in range(12):
        mid = (slo + shi) * 0.5
        if _unit_luma(*_hsv_to_rgb_unit(hue, mid, 1.0)) < target_y:
            shi = mid
        else:
            slo = mid
    return slo


def recolor_match_shade(
    r5: int,
    g5: int,
    b5: int,
    hue: float,
    theme_sat: float,
    keep_value: bool = False,
) -> Tuple[int, int, int]:
    """
    Move a palette entry onto a theme hue without inventing a new shade.

    SNK cloth is shaded in the pixel art. A natural recolor keeps that
    entry's luma and only changes hue. Highlights preserve luma: if the
    new hue is darker and cannot reach that luma at the original
    saturation (bright yellow cloth shifted to red), saturation is
    lowered so the highlight stays lit and reads as pink or white cloth
    instead of a dull mid red. Dark saturated pigment (Iori red hair and
    pants) keeps its saturation and is never brighter than the sprite
    shade, so it cannot turn into a pastel highlight. Soft cloth keeps
    its even luma steps, including a light top that stays pale and a
    shadow that stays a color instead of falling to black. Outlines and
    pure white cloth are left alone.
    """
    hue_now, sat, val = _rgb5_to_hsv(r5, g5, b5)
    if val <= 0.06:
        return r5, g5, b5
    if sat <= 0.12 and val >= 0.90:
        return r5, g5, b5

    rf, gf, bf = r5 / 31.0, g5 / 31.0, b5 / 31.0
    target_y = _unit_luma(rf, gf, bf)
    del hue_now

    if theme_sat < 0.22:
        # White accents keep the sprite's value, so a red headband becomes
        # white instead of a mid gray. Silver costumes still match luma below.
        if keep_value:
            use_sat = 0.04 if theme_sat < 0.12 else min(sat, 0.16)
            use_v = val
        else:
            use_sat = _ease_sat_to_luma(hue, min(sat, 0.16), target_y)
            use_v = _v_for_luma(hue, use_sat, target_y, cap=False)
    elif sat >= 0.50:
        # Saturated slots split on perceptual luma.
        # Highlights (brighter than mid gray) keep luma. If the new hue
        # cannot reach it, ease saturation so lit cloth stays bright.
        # Dark pigment keeps saturation and must not get brighter, so
        # Iori red cannot grow a pastel highlight.
        use_sat = sat
        can_reach = (
            _unit_luma(*_hsv_to_rgb_unit(hue, use_sat, 1.0)) + 1e-4 >= target_y
        )
        if target_y > _LIT_CLOTH_LUMA and not can_reach:
            use_sat = _ease_sat_to_luma(hue, use_sat, target_y)
            use_v = _v_for_luma(hue, use_sat, target_y, cap=False)
        else:
            use_v = _v_for_luma(hue, use_sat, target_y, cap=True)
    else:
        # Soft cloth: match luma, hold saturation, ease S only if this hue
        # cannot reach the original brightness (a saturated blue is darker
        # than a saturated yellow at the same value).
        use_sat = _ease_sat_to_luma(hue, sat, target_y)
        use_v = _v_for_luma(hue, use_sat, target_y, cap=False)

    rf, gf, bf = _hsv_to_rgb_unit(hue, use_sat, use_v)
    return (
        min(31, max(0, int(round(rf * 31.0)))),
        min(31, max(0, int(round(gf * 31.0)))),
        min(31, max(0, int(round(bf * 31.0)))),
    )



def _slot_hsv(word: int) -> Tuple[float, float, float, float]:
    """Return hue, saturation, value, and luma for one LSPC2 word."""
    r5, g5, b5, _ = decode_lspc2(word)
    hue, sat, val = _rgb5_to_hsv(r5, g5, b5)
    luma = _unit_luma(r5 / 31.0, g5 / 31.0, b5 / 31.0)
    return hue, sat, val, luma


def _slot_is_inert(word: int) -> bool:
    """True when a painted slot still reads as gray, white, or near-black."""
    _hue, sat, val, _luma = _slot_hsv(word)
    if val <= 0.07:
        return True
    if sat < 0.18:
        return True
    if val < 0.40 and sat < 0.35:
        return True
    # Muddy midtones (a dark blue kimono shifted toward red) still look gray.
    if sat < 0.45 and val < 0.72:
        return True
    return False


def _cluster_slots(source: List[int], indices: List[int]) -> List[List[int]]:
    """Split a costume group where a large luma gap separates two garments."""
    ranked = sorted(indices, key=lambda i: _slot_hsv(source[i])[3])
    clusters: List[List[int]] = [[ranked[0]]]
    for prev, cur in zip(ranked, ranked[1:]):
        if _slot_hsv(source[cur])[3] - _slot_hsv(source[prev])[3] > 0.24:
            clusters.append([cur])
        else:
            clusters[-1].append(cur)
    return clusters


def _cluster_bias(source: List[int], cluster: List[int]) -> str:
    """Choose light, dark, or full theme-ramp coverage for one luma cluster."""
    lumas = [_slot_hsv(source[i])[3] for i in cluster]
    if max(lumas) <= 0.50:
        return "dark"
    if max(lumas) >= 0.80 and (sum(lumas) / float(len(lumas))) >= 0.45:
        return "light"
    return "full"


def _bias_t(unit: float, bias: str) -> float:
    """Map a 0..1 shade rank onto the part of the theme ramp this garment uses."""
    if bias == "light":
        return 0.46 + unit * 0.54
    if bias == "dark":
        return 0.05 + unit * 0.48
    return 0.06 + unit * 0.88


def _ramp_word(theme_id: str, ramp_key: str, unit: float) -> Optional[int]:
    """Sample one theme ramp. 0 is the darkest step, 1 is the lightest."""
    ramp = THEME_RAMPS.get(theme_id, {}).get(ramp_key) or []
    cols = []
    for hx in ramp:
        r5, g5, b5 = hex_to_rgb5(hx)
        luma = _unit_luma(r5 / 31.0, g5 / 31.0, b5 / 31.0)
        cols.append((luma, r5, g5, b5))
    if not cols:
        return None
    cols.sort(key=lambda item: item[0])
    unit = min(1.0, max(0.0, unit))
    if len(cols) == 1:
        _luma, r5, g5, b5 = cols[0]
        return encode_lspc2(r5, g5, b5, dark=0)
    pos = unit * (len(cols) - 1)
    i = int(pos)
    frac = pos - i
    if i >= len(cols) - 1:
        _luma, r5, g5, b5 = cols[-1]
    else:
        _l0, r0, g0, b0 = cols[i]
        _l1, r1, g1, b1 = cols[i + 1]
        r5 = int(round(r0 + (r1 - r0) * frac))
        g5 = int(round(g0 + (g1 - g0) * frac))
        b5 = int(round(b0 + (b1 - b0) * frac))
    return encode_lspc2(
        min(31, max(0, r5)),
        min(31, max(0, g5)),
        min(31, max(0, b5)),
        dark=0,
    )


def _srgb_to_linear(c: float) -> float:
    """sRGB transfer to linear light, 0..1."""
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _linear_to_srgb(c: float) -> float:
    """Linear light to sRGB transfer, 0..1 (input may be out of range)."""
    if c <= 0.0031308:
        return 12.92 * c
    return 1.055 * (c ** (1.0 / 2.4)) - 0.055


def _rgb_unit_to_oklch(rf: float, gf: float, bf: float) -> Tuple[float, float, float]:
    """sRGB 0..1 to OKLCH (L 0..1, chroma, hue degrees)."""
    r, g, b = _srgb_to_linear(rf), _srgb_to_linear(gf), _srgb_to_linear(bf)
    l_ = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1.0 / 3.0)
    m_ = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1.0 / 3.0)
    s_ = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1.0 / 3.0)
    lum = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    a_ax = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    b_ax = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    chroma = (a_ax * a_ax + b_ax * b_ax) ** 0.5
    hue = math.degrees(math.atan2(b_ax, a_ax)) % 360.0
    return lum, chroma, hue


def _oklch_to_linear(lum: float, chroma: float, hue: float) -> Tuple[float, float, float]:
    """OKLCH to linear sRGB (may fall outside 0..1)."""
    a_ax = chroma * math.cos(math.radians(hue))
    b_ax = chroma * math.sin(math.radians(hue))
    l_ = (lum + 0.3963377774 * a_ax + 0.2158037573 * b_ax) ** 3
    m_ = (lum - 0.1055613458 * a_ax - 0.0638541728 * b_ax) ** 3
    s_ = (lum - 0.0894841775 * a_ax - 1.2914855480 * b_ax) ** 3
    r = 4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_
    g = -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_
    b = -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_
    return r, g, b


def _oklch_word(lum: float, chroma: float, hue: float) -> int:
    """Encode an OKLCH color as LSPC2, lowering chroma until it fits sRGB."""
    lum = min(1.0, max(0.0, lum))
    lo, hi = 0.0, max(0.0, chroma)
    rgb = _oklch_to_linear(lum, hi, hue)
    if min(rgb) < 0.0 or max(rgb) > 1.0:
        for _ in range(18):
            mid = (lo + hi) * 0.5
            test = _oklch_to_linear(lum, mid, hue)
            if min(test) < 0.0 or max(test) > 1.0:
                hi = mid
            else:
                lo = mid
        rgb = _oklch_to_linear(lum, lo, hue)
    out = []
    for comp in rgb:
        unit = _linear_to_srgb(min(1.0, max(0.0, comp)))
        out.append(min(31, max(0, int(round(unit * 31.0)))))
    return encode_lspc2(out[0], out[1], out[2], dark=0)


# Peak OKLCH chroma of official SNK alternate costumes. Measured on the
# Chizuru and Yamazaki B/C/D palettes: pale garments sit near 0.04-0.07,
# dark suits near 0.07-0.13. Tailwind ramps run up to 0.20, which reads as
# neon on 15-color pixel art, so the cover painter caps chroma here.
_CLOTH_CHROMA_PEAK = {"light": 0.105, "full": 0.11, "dark": 0.13}


def _cloth_chroma_cap(lum: float, bias: str) -> float:
    """Chroma ceiling for one cloth shade: highest at mid L, low at the ends."""
    bell = 1.0 - ((lum - 0.5) / 0.55) ** 2
    bell = min(1.0, max(0.15, bell))
    return _CLOTH_CHROMA_PEAK.get(bias, 0.10) * bell


def _natural_cloth_word(
    theme_id: str,
    ramp_key: str,
    ramp_t: float,
    src_word: int,
    bias: str,
    key_hex: Optional[str] = None,
    lift_neutral: bool = False,
) -> Optional[int]:
    """
    Dye one cloth or hair shade the way SNK built alternate costumes.

    The sprite's own OKLCH lightness is kept, so a white top stays a pale
    tint, a black suit stays a deep tone, and the contrast between garments
    survives. Hue comes from the theme ramp at that rank, so each skin keeps
    its identity. Chroma is the ramp's chroma, capped to the official
    alt-costume range. A slot the artist drew vivid (Iori's red hair, Mai's
    red dress) may keep up to its own chroma. When a vivid slot is turned
    near-neutral (a red headband on a white theme), lightness is lifted
    toward a gray of the same HSV value, so it reads as white, not dull gray.
    key_hex, when given, replaces the ramp sample as hue and chroma source
    (the theme's identity color from THEME_KEYS, used for vivid garments).
    """
    if key_hex is not None:
        kr, kg, kb = hex_to_rgb5(key_hex)
        _kl, ramp_c, ramp_h = _rgb_unit_to_oklch(kr / 31.0, kg / 31.0, kb / 31.0)
    else:
        ramp_word = _ramp_word(theme_id, ramp_key, ramp_t)
        if ramp_word is None:
            return None
        rr, rg, rb, _ = decode_lspc2(ramp_word)
        _rl, ramp_c, ramp_h = _rgb_unit_to_oklch(rr / 31.0, rg / 31.0, rb / 31.0)
    sr, sg, sb, _ = decode_lspc2(src_word)
    src_l, src_c, _sh = _rgb_unit_to_oklch(sr / 31.0, sg / 31.0, sb / 31.0)
    # Keep the drawn lightness. Very dark shades get a small lift so the
    # dye can still be seen against the black outline.
    lum = src_l if src_l >= 0.16 else 0.16 + (src_l - 0.16) * 0.5
    if bias == "light":
        # Pure white cannot carry any hue. Settle pale cloth a touch lower
        # so the top step still shows the dye, like SNK's cream Chizuru.
        lum = min(lum, 0.97) - 0.02 * lum
    ceiling = max(_cloth_chroma_cap(lum, bias), min(src_c, 0.20))
    chroma = min(ramp_c, ceiling)
    if lift_neutral and src_c > 0.08 and chroma < src_c:
        loss = (src_c - chroma) / src_c
        src_val = max(sr, sg, sb) / 31.0
        gray_l, _gc, _gh = _rgb_unit_to_oklch(src_val, src_val, src_val)
        if gray_l > lum:
            lum += (gray_l - lum) * loss * 0.6
    return _oklch_word(lum, chroma, ramp_h)


def _paint_ramp_cluster(
    res: List[int],
    source: List[int],
    cluster: List[int],
    theme_id: str,
    ramp_key: str,
    keep_shine: bool,
    lift_neutral: bool = False,
) -> None:
    """
    Dye one garment cluster with the theme hue, keeping its own shading.

    keep_shine marks a garment the artist drew in color. Its pure white
    slots are specular shine and stay, and its hue comes from the theme's
    identity color (THEME_KEYS). A gray, white, or black garment
    (keep_shine False) tints every slot and takes hue from the theme ramp.
    """
    bias = _cluster_bias(source, cluster)
    key_hex: Optional[str] = None
    if keep_shine and theme_id in THEME_KEYS:
        key_hex = THEME_KEYS[theme_id][0 if ramp_key == "primary" else 1]
    ordered = sorted(cluster, key=lambda i: _slot_hsv(source[i])[3])
    count = len(ordered)
    for rank, idx in enumerate(ordered):
        _hue, sat, val, _luma = _slot_hsv(source[idx])
        if val <= 0.06:
            continue
        if keep_shine and sat <= 0.12 and val >= 0.90:
            res[idx] = source[idx]
            continue
        unit = 0.5 if count == 1 else rank / float(count - 1)
        word = _natural_cloth_word(
            theme_id, ramp_key, _bias_t(unit, bias), source[idx], bias, key_hex, lift_neutral
        )
        if word is not None:
            res[idx] = word


# Schema group -> theme ramp. Clothes, pants and shoes take the primary
# ramp; hair, headbands and belts take the accent ramp.
_NATURAL_GROUPS = (
    ("primary", "primary"),
    ("dark_anchor", "primary"),
    ("hair", "accent"),
    ("accent", "accent"),
)


def _paint_costume_natural(
    res: List[int],
    source: List[int],
    schema: Dict[str, List[int]],
    theme_id: str,
) -> None:
    """
    Dye every costume group of one fighter with the natural cloth painter.

    Each group is split into garments by luma gaps, then each garment keeps
    its own lightness ladder. Skin, white trim and contour are not touched.
    """
    for group, ramp_key in _NATURAL_GROUPS:
        indices = [i for i in schema.get(group, []) if 0 <= i < len(res)]
        if not indices:
            continue
        for cluster in _cluster_slots(source, indices):
            inert = [i for i in cluster if _slot_is_inert(source[i])]
            keep_shine = len(inert) / float(len(cluster)) < 0.55
            # Only headbands, belts and ribbons get the white lift. Hair and
            # cloth never grow brighter than the drawn shade.
            _paint_ramp_cluster(
                res, source, cluster, theme_id, ramp_key, keep_shine,
                lift_neutral=(group == "accent"),
            )


def _paint_slot(
    res: List[int],
    source: List[int],
    idx: int,
    hue: float,
    theme_sat: float,
    keep_value: bool = False,
) -> None:
    """Recolor one palette word from source, keeping its shade."""
    r5, g5, b5, _ = decode_lspc2(source[idx])
    nr, ng, nb = recolor_match_shade(r5, g5, b5, hue, theme_sat, keep_value)
    if (nr, ng, nb) == (r5, g5, b5):
        res[idx] = source[idx]
    else:
        res[idx] = encode_lspc2(nr, ng, nb, dark=0)


def generate_harmonious_character_palette(
    cid: int,
    theme_id: str,
    p1_data: bytes,
    p2_clean: bytes,
    btn_idx: int = 0,
) -> List[int]:
    """
    Recolor one button palette with a theme hue while keeping SNK's shade.

    Each costume slot keeps the luma the sprite was drawn with. Highlights
    preserve that luma and ease saturation when the new hue is darker.
    Dark pigment keeps its saturation and must not get brighter. Skin,
    true white trim and outlines stay official. Hair takes the accent
    hue, and clothes, pants and shoes take the primary hue. A costume
    that stays gray, white, or black is then laid across that theme's
    existing light-to-dark ramp, in the original shade order. btn_idx
    0..3 reads that button's own 15 colors, so a second costume is not
    replaced by the A-button result. Orochi Iori uses normal Iori's
    shade curve for the same button.
    """
    _, _, pal_idx = get_char_engine_info(cid)
    base_off = 0x483E + pal_idx * 8
    if btn_idx < 0 or btn_idx > 3:
        btn_idx = 0
    pal_id = struct.unpack(">H", p1_data[base_off + btn_idx * 2:base_off + btn_idx * 2 + 2])[0]
    p2_addr = 0x2CFFF0 + pal_id * 32
    orig_words = list(struct.unpack(">16H", p2_clean[p2_addr : p2_addr + 32])[1:])

    if theme_id == "classic" or theme_id not in THEME_KEYS:
        return orig_words

    # Orochi Iori's official ramp is the glossy one. Both Iori forms take
    # their shade from normal Iori, then the theme hue is applied.
    source = orig_words
    if cid == 0x1D or pal_idx == 0x1C:
        iori_off = 0x483E + 0x1B * 8
        iori_pid = struct.unpack(">H", p1_data[iori_off + btn_idx * 2:iori_off + btn_idx * 2 + 2])[0]
        iori_addr = 0x2CFFF0 + iori_pid * 32
        source = list(struct.unpack(">16H", p2_clean[iori_addr:iori_addr + 32])[1:])

    schema = CHARACTER_PALETTE_SCHEMA.get(cid)
    if not schema:
        return orig_words

    res = list(orig_words)
    # Skin, true white cloth and outlines stay official. Every costume
    # group goes through the natural cloth painter (see ProjectMemory
    # section 13): keep each slot's OKLCH lightness, take the hue from the
    # theme ramp, cap chroma to SNK's alt-costume range. Painted slots read
    # their shade from source, so Orochi Iori keeps official skin while
    # using normal Iori's costume curve.
    if theme_id in THEME_RAMPS:
        _paint_costume_natural(res, source, schema, theme_id)
    else:
        primary_h, primary_s, accent_h, accent_s = theme_hsv(theme_id)
        for idx in schema.get("primary", []) + schema.get("dark_anchor", []):
            _paint_slot(res, source, idx, primary_h, primary_s)
        for idx in schema.get("accent", []):
            _paint_slot(res, source, idx, accent_h, accent_s, keep_value=True)
        for idx in schema.get("hair", []):
            _paint_slot(res, source, idx, accent_h, accent_s)
    for idx in schema.get("contour", []):
        res[idx] = 0x0000
    return res


def _hex_luma(hex_code: str) -> float:
    """Perceptual luma of a #RRGGBB color in 0..1."""
    clean = hex_code.strip().lstrip("#")
    if len(clean) != 6:
        return 0.0
    try:
        rf = int(clean[0:2], 16) / 255.0
        gf = int(clean[2:4], 16) / 255.0
        bf = int(clean[4:6], 16) / 255.0
    except ValueError:
        return 0.0
    return _unit_luma(rf, gf, bf)


def figure_preview_colors(cid: int, colors: List[str]) -> Dict[str, str]:
    """Map a character's 15 gameplay palette colors onto the stage dummy."""
    fallback = {
        "coat": "#3A3A4A",
        "shirt": "#F7F7FF",
        "hair": "#DE3A21",
        "pants": "#AD2910",
        "shoes": "#191929",
    }
    if not colors or len(colors) < 15:
        return dict(fallback)

    def take(idxs: List[int], pick: str = "mid"):
        vals: List[str] = []
        for i in idxs:
            if 0 <= i < len(colors):
                hx = colors[i]
                if isinstance(hx, str) and len(hx) == 7 and hx.upper() not in ("#000000", "#000008"):
                    vals.append(hx)
        if not vals:
            return None
        ordered = sorted(vals, key=_hex_luma)
        if pick == "light":
            return ordered[-1]
        if pick == "dark":
            return ordered[0]
        return ordered[len(ordered) // 2]

    if cid in (0x1B, 0x1D):
        return {
            "hair": colors[7],
            "pants": colors[8],
            "shirt": colors[4],
            "coat": colors[11],
            "shoes": colors[13],
        }

    schema = CHARACTER_PALETTE_SCHEMA.get(cid, {})
    hair = (
        take(schema.get("hair", []), "mid")
        or take(schema.get("accent", []), "mid")
        or take(schema.get("primary", []), "light")
    )
    coat = (
        take(schema.get("dark_anchor", []), "dark")
        or take(schema.get("primary", []), "dark")
    )
    shirt = take(schema.get("white_trim", []), "light")
    pants = (
        take(schema.get("primary", []), "mid")
        or take(schema.get("dark_anchor", []), "light")
        or take(schema.get("accent", []), "mid")
    )
    shoes = (
        take(schema.get("dark_anchor", []), "dark")
        or take(schema.get("contour", []), "dark")
    )
    return {
        "hair": hair or fallback["hair"],
        "coat": coat or fallback["coat"],
        "shirt": shirt or fallback["shirt"],
        "pants": pants or fallback["pants"],
        "shoes": shoes or fallback["shoes"],
    }


def make_skin_entry(
    cid: int,
    theme_id: str,
    colors: List[str],
    vfx_theme: str = "classic",
) -> Dict[str, Any]:
    """Store a skin together with dummy colors and VFX theme selection."""
    payload = list(colors)
    return {
        "themeId": theme_id,
        "vfxTheme": vfx_theme or "classic",
        "colors": payload,
        "preview": figure_preview_colors(cid, payload),
    }


def generate_burst_character_palette(
    cid: int,
    theme_id: str,
    base_words: List[int],
) -> List[int]:
    """
    Generate luminous burst flash palette variant for MAX mode (ABC burst).
    In KOF97, MAX mode burst alternates between Button A/B palette and Button C/D palette.
    By populating Button C/D with this luminous harmonic variant, the character pulses
    with radiant energy matching the custom skin, completely eliminating original skin flicker.
    """
    burst_words = []
    for w in base_words:
        r5, g5, b5, dark = decode_lspc2(w)
        # Check if color is part of skin tone
        is_skin = (r5 >= g5 >= b5 and r5 >= 10 and r5 - b5 >= 3)
        # Keep dark outlines dark so silhouette remains razor sharp
        is_dark_outline = (r5 <= 1 and g5 <= 1 and b5 <= 1)

        if is_dark_outline:
            burst_words.append(w)
        elif is_skin:
            # Subtle skin highlight (+2 steps)
            nr = min(31, r5 + 2)
            ng = min(31, g5 + 2)
            nb = min(31, b5 + 1)
            burst_words.append(encode_lspc2(nr, ng, nb, dark=0))
        else:
            # Radiant highlight for hair and garments (+30% luminance + 4)
            nr = min(31, round(r5 * 1.30 + 4))
            ng = min(31, round(g5 * 1.30 + 4))
            nb = min(31, round(b5 * 1.30 + 4))
            burst_words.append(encode_lspc2(nr, ng, nb, dark=0))

    return burst_words


def sync_character_portraits(
    cid: int,
    theme_id: str,
    base_pid: int,
    lspc_words: List[int],
    p2_data: bytearray,
    p2_clean: bytes,
) -> None:
    """
    Synchronize character select screen portraits, victory/win screen portraits,
    and in-game HUD avatar palettes across all 4 button slots (A, B, C, D).
    In KOF97:
      base_pid + 13 + btn*16 = Big Victory/Ending Portrait (e.g. Iori big bust on win screen)
      base_pid + 14 + btn*16 = Member Select / Result Screen Portrait (e.g. Chang & Daimon on win screen)
      base_pid + 15 + btn*16 = HUD Top Life Bar Avatar
    """
    if theme_id == "classic":
        # Restore all 4 slots from clean P2 ROM baseline
        for btn_idx in range(4):
            for slot_off in (13, 14, 15):
                pal_id = base_pid + slot_off + btn_idx * 16
                addr = 0x2CFFF0 + pal_id * 32
                p2_data[addr:addr + 32] = p2_clean[addr:addr + 32]
        return

    # 1. Iori Yagami (0x1B) & Orochi Iori (0x1D UI / 0x1C Engine)
    if cid in (0x1B, 0x1D):
        c_high = lspc_words[7]
        c_mid = lspc_words[8]
        c_shad = lspc_words[9]
        c_deep = lspc_words[10]
        c_shirt = lspc_words[4]
        c_coat = lspc_words[11]
        c_coat_dark = lspc_words[13]

        target_base = 0x07C0 if cid == 0x1B else 0x0800
        for btn_idx in range(4):
            b0 = 0x2CFFF0 + (target_base + 13 + btn_idx * 16) * 32
            b1 = 0x2CFFF0 + (target_base + 14 + btn_idx * 16) * 32
            b2 = 0x2CFFF0 + (target_base + 15 + btn_idx * 16) * 32

            # Big Victory Portrait (b0): Words 5..7 shirt, 8/10/11 hair, 13..15 coat
            p2_data[b0 + 10: b0 + 16] = struct.pack(">3H", c_shirt, c_shirt, c_shirt)
            p2_data[b0 + 16: b0 + 18] = struct.pack(">H", c_high)
            p2_data[b0 + 20: b0 + 22] = struct.pack(">H", c_mid)
            p2_data[b0 + 22: b0 + 24] = struct.pack(">H", c_shad)
            p2_data[b0 + 26: b0 + 28] = struct.pack(">H", c_shirt)
            p2_data[b0 + 28: b0 + 32] = struct.pack(">2H", c_coat, c_coat_dark)

            # Mid / Result Screen Portrait (b1): Word 6 shirt, 7..9 hair, 12..13 coat, 14 hair highlight
            p2_data[b1 + 12: b1 + 14] = struct.pack(">H", c_shirt)
            p2_data[b1 + 14: b1 + 16] = struct.pack(">H", c_high)
            p2_data[b1 + 16: b1 + 18] = struct.pack(">H", c_mid)
            p2_data[b1 + 18: b1 + 20] = struct.pack(">H", c_shad)
            p2_data[b1 + 24: b1 + 28] = struct.pack(">2H", c_coat, c_coat_dark)
            p2_data[b1 + 28: b1 + 30] = struct.pack(">H", c_high)

            # HUD Small Avatar (b2): Words 6..8 hair, 14 hair highlight
            p2_data[b2 + 12: b2 + 14] = struct.pack(">H", c_high)
            p2_data[b2 + 14: b2 + 16] = struct.pack(">H", c_mid)
            p2_data[b2 + 16: b2 + 18] = struct.pack(">H", c_shad)
            p2_data[b2 + 28: b2 + 30] = struct.pack(">H", c_high)

    # 2. Goro Daimon (0x02)
    elif cid == 0x02:
        judogi_words = lspc_words[5:10]
        headband_word = lspc_words[11]
        for btn_idx in range(4):
            b0 = 0x2CFFF0 + (0x0180 + 13 + btn_idx * 16) * 32
            b1 = 0x2CFFF0 + (0x0180 + 14 + btn_idx * 16) * 32
            b2 = 0x2CFFF0 + (0x0180 + 15 + btn_idx * 16) * 32

            # Big portrait: Words 6..10 judogi, Word 12 headband
            p2_data[b0 + 12: b0 + 22] = struct.pack(">5H", *judogi_words)
            p2_data[b0 + 24: b0 + 26] = struct.pack(">H", headband_word)

            # Result screen / select screen portrait: Words 7..11 judogi, Words 12..13 headband
            p2_data[b1 + 14: b1 + 24] = struct.pack(">5H", *judogi_words)
            p2_data[b1 + 24: b1 + 28] = struct.pack(">2H", headband_word, headband_word)

            # HUD avatar: Words 6..9 judogi
            p2_data[b2 + 12: b2 + 20] = struct.pack(">4H", *judogi_words[:4])

    # 3. Chang Koehan (0x13)
    elif cid == 0x13:
        u_words = lspc_words[5:9]
        for btn_idx in range(4):
            b0 = 0x2CFFF0 + (0x05C0 + 13 + btn_idx * 16) * 32
            b1 = 0x2CFFF0 + (0x05C0 + 14 + btn_idx * 16) * 32
            b2 = 0x2CFFF0 + (0x05C0 + 15 + btn_idx * 16) * 32

            # Big portrait: Words 6..9 uniform
            p2_data[b0 + 12: b0 + 20] = struct.pack(">4H", *u_words)

            # Result screen / select screen portrait: Words 6..9 uniform (fixes yellow prison uniform on win screen!)
            p2_data[b1 + 12: b1 + 20] = struct.pack(">4H", *u_words)

            # HUD avatar: Words 6..8 uniform
            p2_data[b2 + 12: b2 + 18] = struct.pack(">3H", *u_words[:3])

    # 4. Universal portraits keep the artwork's own shade and only take the hue.
    else:
        if theme_id not in THEME_KEYS:
            return
        primary_h, primary_s, _, _ = theme_hsv(theme_id)
        for btn_idx in range(4):
            for slot_off in (13, 14, 15):
                pal_id = base_pid + slot_off + btn_idx * 16
                addr = 0x2CFFF0 + pal_id * 32
                p_words = list(struct.unpack(">16H", p2_clean[addr:addr + 32]))
                for i in range(1, 16):
                    r, g, b, _ = decode_lspc2(p_words[i])
                    is_skin = (r >= g >= b and r >= 10 and r - b >= 3)
                    if is_skin:
                        continue
                    nr, ng, nb = recolor_match_shade(r, g, b, primary_h, primary_s)
                    if (nr, ng, nb) != (r, g, b):
                        p_words[i] = encode_lspc2(nr, ng, nb, dark=0)
                p2_data[addr:addr + 32] = struct.pack(">16H", *p_words)


# ============================================================================
# Skill / VFX Palette Recoloring Engine (TASK-STUDIO-019)
# Completely decoupled from the frozen costume OKLCH painter.
# Uses P1 0x004956 table lookup (never linear formula) and P1 0x00483E sub-slots.
# ============================================================================

VFX_PRESETS: List[Dict[str, str]] = [
    {
        "id": "classic",
        "name_cn": "\u539f\u7248\u7279\u6548",
        "badge": "SNK\u539f\u8272",
        "inner": "#FFFFFF",
        "outer": "#FF8C1A",
    },
    {
        "id": "sync_skin",
        "name_cn": "\u8ddf\u968f\u76ae\u80a4\u4e3b\u8272",
        "badge": "\u81ea\u52a8\u540c\u6b65",
        "inner": "#F8FAFC",
        "outer": "#38BDF8",
    },
    {
        "id": "cangyan_blue",
        "name_cn": "\u82cd\u708e\u84dd",
        "badge": "\u7535\u5149\u84dd\u7130",
        "inner": "#D8F8FF",
        "outer": "#008CFF",
    },
    {
        "id": "mingyan_purple",
        "name_cn": "\u51a5\u708e\u7d2b",
        "badge": "\u5927\u86c7\u7d2b\u7130",
        "inner": "#F6DCFF",
        "outer": "#9D2BFF",
    },
    {
        "id": "holy_gold",
        "name_cn": "\u5723\u8000\u91d1",
        "badge": "\u70bd\u9633\u91d1\u8f89",
        "inner": "#FFFDE0",
        "outer": "#FFB300",
    },
    {
        "id": "jade_venom",
        "name_cn": "\u7fe1\u7fe0\u6bd2\u706b",
        "badge": "\u8367\u5149\u7fe0\u7130",
        "inner": "#E4FFD8",
        "outer": "#00E65B",
    },
    {
        "id": "crimson_flame",
        "name_cn": "\u8d64\u7130\u7ea2",
        "badge": "\u72c2\u708e\u7eef\u7ea2",
        "inner": "#FFE4D4",
        "outer": "#FF1F2D",
    },
    {
        "id": "aurora_cyan",
        "name_cn": "\u6781\u5149\u9752",
        "badge": "\u51b0\u6676\u9752\u5149",
        "inner": "#E6FFFF",
        "outer": "#00F0D8",
    },
    {
        "id": "sakura_plasma",
        "name_cn": "\u6a31\u9b45\u7c89\u7130",
        "badge": "\u9713\u8679\u7c89\u7130",
        "inner": "#FFE8F6",
        "outer": "#FF2B9A",
    },
    {
        "id": "void_ember",
        "name_cn": "\u865a\u7a7a\u6697\u7130",
        "badge": "\u5e7d\u84dd\u6697\u7d2b",
        "inner": "#E4DAFF",
        "outer": "#4B3BFF",
    },
]

VFX_PRESET_MAP: Dict[str, Dict[str, str]] = {p["id"]: p for p in VFX_PRESETS}

# Hardware sentinel / mask padding words embedded inside KOF97 VFX palette blocks:
# 0x0000 (0,0,0), 0x4553 (11,10,6), 0x305C (0,11,25), 0x304E (0,9,29),
# 0x20F0 (0,31,0), 0x4F00 (31,0,0), 0x4497 (9,18,14).
VFX_SENTINEL_WORDS = frozenset({0x0000, 0x4553, 0x305C, 0x304E, 0x20F0, 0x4F00, 0x4497})
VFX_SUBSLOT_OFFSETS: Tuple[int, ...] = (1, 2, 4, 5, 7, 8, 10, 11)
_VFX_MAP_CACHE: Dict[Tuple[int, int], Dict[int, Dict[str, Any]]] = {}


def _read_p2_slot_words15(p2_data: bytes, pal_id: int) -> List[int]:
    """Read color indices 1..15 (Big-Endian LSPC2 words) from a P2 palette slot."""
    off = 0x2CFFF0 + pal_id * 32
    return list(struct.unpack(">15H", p2_data[off + 2 : off + 32]))


def scan_character_vfx_slots(
    cid: int,
    p1_data: bytes,
    p2_clean: bytes,
) -> Dict[str, Any]:
    """
    Scan and whitelist clean VFX palette slots for one roster character.
    Reads P1 0x004956 directly (handling the 0x15..0x1A interleaving) and filters
    out solid placeholders, dark shadow silhouettes, and button-variant body flashes.
    """
    _, _, pal_idx = get_char_engine_info(cid)

    # 1. Read VFX base ID from P1 0x004956 (35 word entries: 0x00..0x22)
    vfx_base_off = 0x4956 + pal_idx * 2
    vfx_base_pid = struct.unpack(">H", p1_data[vfx_base_off : vfx_base_off + 2])[0]

    # 2. Scan vfx_base + 0..15 for real luminous projectile / flame / spark palettes
    vfx_slots: List[int] = []
    vfx_signatures: set = set()
    for s in range(16):
        pid = vfx_base_pid + s
        words = _read_p2_slot_words15(p2_clean, pid)
        active_words = [w for w in words if w not in VFX_SENTINEL_WORDS]
        if len(set(active_words)) < 2:
            continue
        has_energy = any(
            max(r, g, b) >= 16 and (r, g, b) != (31, 31, 31)
            for r, g, b, _ in (decode_lspc2(w) for w in active_words)
        )
        if not has_energy:
            continue
        vfx_slots.append(pid)
        vfx_signatures.add(tuple(words))

    # 3. Scan character button sub-slots in P1 0x00483E that hold pure uniform VFX
    btn_base_off = 0x483E + pal_idx * 8
    btn_pids = [
        struct.unpack(">H", p1_data[btn_base_off + b * 2 : btn_base_off + b * 2 + 2])[0]
        for b in range(4)
    ]
    char_sub_offsets: List[int] = []
    char_sub_slots: List[int] = []

    for sub in VFX_SUBSLOT_OFFSETS:
        banks = [tuple(_read_p2_slot_words15(p2_clean, bp + sub)) for bp in btn_pids]
        if len(set(banks)) != 1:
            # Differs per button -> character body/costume flash, never recolor as VFX
            continue
        words_tup = banks[0]
        active_words = [w for w in words_tup if w not in VFX_SENTINEL_WORDS]
        if len(set(active_words)) < 2:
            continue

        decoded = [decode_lspc2(w)[:3] for w in active_words]
        matches_vfx_bank = words_tup in vfx_signatures
        has_white_core = any(r == 31 and g >= 30 and b >= 27 for r, g, b in decoded)
        is_slash_spark = decoded[0][0] >= 30 and decoded[0][1] >= 30 and decoded[0][2] >= 28
        is_pure_flame = len(decoded) >= 5 and all(r >= 28 and r >= b + 4 for r, g, b in decoded)
        if matches_vfx_bank or has_white_core or is_slash_spark or is_pure_flame:
            char_sub_offsets.append(sub)
            for bp in btn_pids:
                char_sub_slots.append(bp + sub)

    return {
        "cid": cid,
        "pal_idx": pal_idx,
        "vfx_base_pid": vfx_base_pid,
        "btn_pids": btn_pids,
        "vfx_slots": vfx_slots,
        "char_sub_offsets": char_sub_offsets,
        "char_sub_slots": char_sub_slots,
        "all_slots": vfx_slots + char_sub_slots,
        "has_vfx": bool(vfx_slots or char_sub_slots),
    }


def build_character_vfx_map(p1_data: bytes, p2_clean: bytes) -> Dict[int, Dict[str, Any]]:
    """Build and cache the 36-character VFX palette slot map from P1 and clean P2."""
    cache_key = (len(p1_data), hash(bytes(p1_data[0x4956:0x499C])))
    cached = _VFX_MAP_CACHE.get(cache_key)
    if cached is not None:
        return cached
    result = {
        ch["id"]: scan_character_vfx_slots(ch["id"], p1_data, p2_clean)
        for ch in CHARACTER_ROSTER
    }
    _VFX_MAP_CACHE[cache_key] = result
    return result


def _oklch_gamut_word(lum: float, chroma: float, hue: float) -> int:
    """
    Encode (L, C, H) into a 16-bit LSPC2 word while binary-searching chroma inside
    the sRGB gamut so neon hues (cyan, yellow, blue, magenta) never clip-shift.
    """
    lum = min(0.99, max(0.08, lum))
    chroma = max(0.0, chroma)
    hi = chroma
    r, g, b = _oklch_to_linear(lum, hi, hue)
    if min(r, g, b) < 0.0 or max(r, g, b) > 1.0:
        lo = 0.0
        for _ in range(12):
            mid = 0.5 * (lo + hi)
            mr, mg, mb = _oklch_to_linear(lum, mid, hue)
            if min(mr, mg, mb) >= 0.0 and max(mr, mg, mb) <= 1.0:
                lo = mid
            else:
                hi = mid
        chroma = lo
    return _oklch_word(lum, chroma, hue)


def _hex_to_oklch(hex_code: str) -> Tuple[float, float, float]:
    """Convert #RRGGBB hex string into OKLCH (L, C, H)."""
    h = str(hex_code or "#FFFFFF").lstrip("#")
    if len(h) != 6:
        return 0.75, 0.18, 220.0
    rf = int(h[0:2], 16) / 255.0
    gf = int(h[2:4], 16) / 255.0
    bf = int(h[4:6], 16) / 255.0
    return _rgb_unit_to_oklch(rf, gf, bf)


def _lerp_hue(h0: float, h1: float, t: float) -> float:
    """Interpolate two OKLCH hue angles along the shortest arc."""
    delta = ((h1 - h0 + 540.0) % 360.0) - 180.0
    return (h0 + delta * min(1.0, max(0.0, t))) % 360.0


def _dominant_palette_accent(colors: List[str]) -> Tuple[str, str]:
    """Extract a vivid inner/outer hex pair from a 15-color character palette."""
    best_hex = "#38BDF8"
    best_c = -1.0
    best_l = 0.65
    for hx in colors or []:
        lum, chm, _hue = _hex_to_oklch(hx)
        if chm > best_c and lum >= 0.35:
            best_c = chm
            best_l = lum
            best_hex = hx
    if best_c < 0.05:
        return "#F8FAFC", "#38BDF8"
    # Build bright core shifted slightly warmer/brighter and vivid outer hue
    lum, chm, hue = _hex_to_oklch(best_hex)
    inner_word = _oklch_gamut_word(min(0.95, max(0.88, lum + 0.22)), min(0.10, chm * 0.55), hue)
    outer_word = _oklch_gamut_word(min(0.76, max(0.58, best_l)), max(0.20, min(0.26, chm * 1.35)), hue)
    return lspc2_to_hex(inner_word), lspc2_to_hex(outer_word)


def resolve_vfx_hues(
    vfx_theme_id: str,
    skin_entry: Optional[Dict[str, Any]] = None,
    cid: Optional[int] = None,
    p1_data: Optional[bytes] = None,
    p2_clean: Optional[bytes] = None,
) -> Optional[Tuple[str, str]]:
    """
    Resolve (inner_hex, outer_hex) for a VFX preset. Returns None for 'classic'.
    Supports 'sync_skin' by reading THEME_KEYS, custom skin colors, or clean ROM clothes.
    """
    vid = str(vfx_theme_id or "classic")
    if vid == "classic":
        return None
    if vid == "sync_skin":
        entry = skin_entry or {}
        skin_tid = str(entry.get("themeId", "classic"))
        if skin_tid in THEME_KEYS:
            primary_hex, accent_hex = THEME_KEYS[skin_tid]
            return primary_hex, accent_hex
        colors = entry.get("colors")
        if isinstance(colors, list) and len(colors) == 15 and skin_tid != "classic":
            return _dominant_palette_accent(colors)
        if cid is not None and p1_data is not None and p2_clean is not None:
            _, _, pal_idx = get_char_engine_info(cid)
            off = 0x483E + pal_idx * 8
            base_pid = struct.unpack(">H", p1_data[off : off + 2])[0]
            clean_hexes = [lspc2_to_hex(w) for w in _read_p2_slot_words15(p2_clean, base_pid)]
            return _dominant_palette_accent(clean_hexes)
        return "#F8FAFC", "#38BDF8"

    preset = VFX_PRESET_MAP.get(vid)
    if preset:
        return preset["inner"], preset["outer"]
    return None


def recolor_vfx_palette(
    words15: List[int],
    inner_hex: str,
    outer_hex: str,
) -> List[int]:
    """
    Independent luminous gradient shader for VFX palettes.
    - Preserves sentinel mask/padding words verbatim.
    - Keeps pure white (31,31,31) and high-luminance core near-white incandescent.
    - Drives mid/high tiers to vivid neon chroma (up to ~0.24 OKLCH, gamut-safe)
      with smooth inner-to-outer dual-hue progression.
    """
    _li, c_in, h_in = _hex_to_oklch(inner_hex)
    _lo, c_out, h_out = _hex_to_oklch(outer_hex)
    inner_is_neutral = c_in < 0.03
    outer_is_neutral = c_out < 0.03
    if inner_is_neutral and not outer_is_neutral:
        h_in = h_out
    elif outer_is_neutral and not inner_is_neutral:
        h_out = h_in

    non_white_ls: List[float] = []
    for w in words15:
        if w in VFX_SENTINEL_WORDS:
            continue
        r5, g5, b5, _ = decode_lspc2(w)
        if r5 >= 31 and g5 >= 31 and b5 >= 31:
            continue
        sl, _, _ = _rgb_unit_to_oklch(r5 / 31.0, g5 / 31.0, b5 / 31.0)
        non_white_ls.append(sl)
    min_act_l = min(non_white_ls) if non_white_ls else 0.4
    max_act_l = max(non_white_ls) if non_white_ls else 0.9
    pale_source_only = len(non_white_ls) >= 2 and min_act_l > 0.62

    out_words: List[int] = []
    for w in words15:
        if w in VFX_SENTINEL_WORDS:
            out_words.append(w)
            continue
        r5, g5, b5, _dark = decode_lspc2(w)
        if r5 >= 31 and g5 >= 31 and b5 >= 31:
            out_words.append(0x7FFF)
            continue

        src_l, _src_c, _src_h = _rgb_unit_to_oklch(r5 / 31.0, g5 / 31.0, b5 / 31.0)
        # Progress from bright flame core (0.0) toward outer aura tail (1.0)
        grad_t = min(1.0, max(0.0, (0.94 - src_l) / 0.30))
        target_h = _lerp_hue(h_in, h_out, grad_t)

        if src_l >= 0.90:
            # Incandescent flame heart: bright, crisp, light inner glow tint
            target_l = max(src_l, 0.91)
            target_c = min(0.11, max(0.025, (0.985 - src_l) * 1.15))
        elif pale_source_only:
            # Pale cyan/pink sources lack dark steps; stretch midtones to saturated neon
            sub_max = min(0.899, max_act_l)
            rank_t = min(1.0, max(0.0, (sub_max - src_l) / max(0.04, sub_max - min_act_l)))
            target_l = min(0.87, max(0.54, 0.87 - 0.32 * rank_t))
            target_c = max(0.17, min(0.25, 0.16 + 0.08 * rank_t))
        elif src_l >= 0.45:
            # Neon mid/high energy body: preserve brightness hierarchy, lift chroma
            target_l = min(0.89, max(src_l, 0.48))
            peak_c = max(0.18, min(0.25, max(c_out, 0.21)))
            # Gentle peak in the middle luminous band (0.58..0.82)
            band = 1.0 - 0.18 * abs(src_l - 0.68) / 0.25
            target_c = max(0.17, min(0.25, peak_c * band))
        else:
            # Dark outer ember / trail outline: crisp dark tone with rich tint
            target_l = max(0.16, src_l * 0.96)
            target_c = min(0.21, max(0.06, src_l * 0.42))

        out_words.append(_oklch_gamut_word(target_l, target_c, target_h))

    return out_words


def generate_vfx_preview_ramp(
    vfx_theme_id: str,
    skin_entry: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """Generate a 6-step luminous preview hex ramp for UI glow badges."""
    pair = resolve_vfx_hues(vfx_theme_id, skin_entry)
    if not pair:
        pair = ("#FFFFFF", "#FF8C1A")
    sample_words = [
        encode_lspc2(31, 31, 31),
        encode_lspc2(31, 31, 24),
        encode_lspc2(31, 28, 17),
        encode_lspc2(31, 21, 6),
        encode_lspc2(26, 13, 1),
        encode_lspc2(14, 5, 0),
    ]
    recolored = recolor_vfx_palette(sample_words, pair[0], pair[1])
    return [lspc2_to_hex(w) for w in recolored]


def apply_vfx_palettes_to_p2(
    cid: int,
    vfx_theme_id: str,
    skin_entry: Optional[Dict[str, Any]],
    p1_data: bytes,
    p2_data: bytearray,
    p2_clean: bytes,
) -> int:
    """
    Patch whitelisted VFX palette slots (P1 0x004956 + pure-VFX 0x00483E sub-slots)
    into P2 ROM buffer for one character. Returns count of P2 slots written.
    """
    pair = resolve_vfx_hues(vfx_theme_id, skin_entry, cid=cid, p1_data=p1_data, p2_clean=p2_clean)
    if pair is None:
        return 0
    vfx_map = build_character_vfx_map(p1_data, p2_clean)
    info = vfx_map.get(cid)
    if not info or not info.get("has_vfx"):
        return 0

    inner_hex, outer_hex = pair
    written_slots = 0
    for pid in info["all_slots"]:
        if pid <= 0x00FF:
            # Never touch public UI / system palettes 0x0000..0x00FF
            continue
        clean_words = _read_p2_slot_words15(p2_clean, pid)
        new_words = recolor_vfx_palette(clean_words, inner_hex, outer_hex)
        p2_addr = 0x2CFFF0 + pid * 32
        p2_data[p2_addr + 2 : p2_addr + 32] = struct.pack(">15H", *new_words)
        written_slots += 1
    return written_slots


# ============================================================================
# P1 68000 Hit-Effect & Victim Elemental Burn/Shock VFX Hook System
# Keeps P2 public palettes 0x0000..0x00FF and 0x17B0..0x17DF 100% official
# while dynamically switching Palette RAM slots (0xF8/0xF9/0xFA and 0x51..0x6A)
# to match the attacking fighter's customized VFX theme on every hit/burn.
# ============================================================================

VFX_HIT_EFFECT_CAVE_BASE = 0x0F0000
VFX_HIT_EFFECT_CAVE_SIZE = 0x10000
VFX_THEME_ENTRY_STRIDE = 0x620
VFX_RAM_F8_OWNER = 0x6E00
VFX_RAM_F9_OWNER = 0x6E02
VFX_RAM_FA_OWNER = 0x6E04
VFX_RAM_EL_OWNER = 0x6E06
VFX_RAM_IM_OWNER = 0x6E08

VFX_HIT_EFFECT_DARK_MASKS = frozenset({0x0010, 0x1210})
VFX_SMOKE_SPLIT_SLOTS = frozenset({0x0058, 0x005F})

# Ordered common effect groups stored per custom theme (+0x000..+0x21F, 17 * 32B)
VFX_COMMON_EFFECT_GROUPS: Tuple[Tuple[int, int, int, int, int, int, Tuple[int, ...]], ...] = (
    # (cache_off, common_off, cnt_m1, burn_pal_id, custom_burn_off, classic_burn_ptr, slot_ids)
    (VFX_RAM_F8_OWNER, 0x0000, 3, 0x00F8, 0x0220, 0x002FF5F0, (0x0057, 0x0058, 0x0059, 0x0061)),
    (VFX_RAM_F9_OWNER, 0x0080, 3, 0x00F9, 0x0420, 0x002FF7F0, (0x005B, 0x005F, 0x0067, 0x0068)),
    (VFX_RAM_EL_OWNER, 0x0100, 3, 0x0000, 0x0000, 0x00000000, (0x0052, 0x0062, 0x0053, 0x0054)),
    (VFX_RAM_IM_OWNER, 0x0180, 4, 0x0000, 0x0000, 0x00000000, (0x0051, 0x0055, 0x0054, 0x0064, 0x006A)),
    (VFX_RAM_FA_OWNER, 0x0000, 0xFFFF, 0x00FA, 0x0000, 0x002FF9F0, ()),
)

# Exact 6-byte P1 hook sites and their clean official machine code bytes
VFX_HIT_HOOK_ORIGINALS: Tuple[Tuple[str, int, bytes, str], ...] = (
    ("match_init_hook", 0x0251C4, bytes.fromhex("3b7cffff040c"), "match_init_hook"),
    ("f8_ptr_hook", 0x0041AE, bytes.fromhex("41f9002ff5f0"), "f8_ptr_hook"),
    ("f9_ptr_hook", 0x0041E6, bytes.fromhex("41f9002ff7f0"), "f9_ptr_hook"),
    ("fa_ptr_hook", 0x004254, bytes.fromhex("41f9002ff9f0"), "fa_ptr_hook"),
    ("impact_0", 0x012E64, bytes.fromhex("247b102c3212"), "on_impact_hook"),
    ("fire_0", 0x012F18, bytes.fromhex("197c00f8003a"), "on_fire_burn_hook"),
    ("fire_1", 0x012F8C, bytes.fromhex("197c00f8003a"), "on_fire_burn_hook"),
    ("fire_2", 0x013108, bytes.fromhex("197c00f8003a"), "on_fire_burn_hook"),
    ("fire_3", 0x013174, bytes.fromhex("197c00f8003a"), "on_fire_burn_hook"),
    ("purple_0", 0x012F9E, bytes.fromhex("197c00f9003a"), "on_purple_burn_hook"),
    ("purple_1", 0x01314E, bytes.fromhex("197c00f9003a"), "on_purple_burn_hook"),
    ("purple_2", 0x01316C, bytes.fromhex("197c00f9003a"), "on_purple_burn_hook"),
    ("elec_0", 0x012F42, bytes.fromhex("002c000200e3"), "on_elec_shock_hook"),
    ("elec_1", 0x013184, bytes.fromhex("002c000200e3"), "on_elec_shock_hook"),
    ("elec_2", 0x03376E, bytes.fromhex("002c000200e3"), "on_elec_shock_hook"),
    ("fa_flash", 0x01317C, bytes.fromhex("197c00fa003a"), "on_fa_flash_hook"),
)


def _recolor_hit_effect_slot(
    pal_id: int,
    p2_clean: bytes,
    inner_hex: str,
    outer_hex: str,
) -> List[int]:
    """
    Recolor a single common effect or cyclic victim burn slot while keeping
    neutral grey smoke in split slots (0x0058/0x005F) and dark outline sentinels intact.
    """
    clean_words = _read_p2_slot_words15(p2_clean, pal_id)
    mask_positions = {
        idx: w for idx, w in enumerate(clean_words) if w in VFX_HIT_EFFECT_DARK_MASKS
    }
    if pal_id in VFX_SMOKE_SPLIT_SLOTS:
        smoke_head = list(clean_words[:9])
        flame_tail = recolor_vfx_palette(clean_words[9:15], inner_hex, outer_hex)
        out_words = smoke_head + flame_tail
    else:
        out_words = recolor_vfx_palette(clean_words, inner_hex, outer_hex)
    for idx, orig_w in mask_positions.items():
        out_words[idx] = orig_w
    return out_words


class _M68kCodeCaveBuilder:
    """Minimal relocatable Motorola 68000 assembler for P1 code caves."""

    def __init__(self, base: int) -> None:
        self.base = base
        self.buf = bytearray()
        self.labels: Dict[str, int] = {}
        self.fixups: List[Tuple[int, str, str]] = []

    @property
    def pc(self) -> int:
        return self.base + len(self.buf)

    def label(self, name: str) -> None:
        if name in self.labels:
            raise ValueError(f"Duplicate 68k label: {name}")
        self.labels[name] = self.pc

    def w(self, *words: int) -> None:
        for val in words:
            self.buf += struct.pack(">H", val & 0xFFFF)

    def l(self, *longs: int) -> None:
        for val in longs:
            self.buf += struct.pack(">I", val & 0xFFFFFFFF)

    def b_branch(self, op_hi: int, target: str) -> None:
        self.w(op_hi)
        self.fixups.append((len(self.buf), "wrel", target))
        self.w(0)

    def dbra(self, dreg: int, target: str) -> None:
        self.w(0x51C8 | (dreg & 7))
        self.fixups.append((len(self.buf), "wrel", target))
        self.w(0)

    def ref_abs32(self, opcode_word: int, target: str) -> None:
        self.w(opcode_word)
        self.fixups.append((len(self.buf), "abs32", target))
        self.l(0)

    def finalize(self) -> bytes:
        for pos, kind, target in self.fixups:
            taddr = self.labels[target]
            if kind == "wrel":
                disp = taddr - (self.base + pos)
                if not (-32768 <= disp <= 32767):
                    raise ValueError(f"Branch displacement out of range for {target}: {disp}")
                self.buf[pos : pos + 2] = struct.pack(">h", disp)
            elif kind == "abs32":
                self.buf[pos : pos + 4] = struct.pack(">I", taddr)
        return bytes(self.buf)


def build_hit_effect_vfx_p1_patch(
    character_skins: Dict[int, Dict[str, Any]],
    p1_data: bytes,
    p2_clean: bytes,
) -> Optional[Dict[str, Any]]:
    """
    Build the P1 0x0F0000 code cave and deduplicated theme tables for dynamic
    on-hit elemental burn/shock/spark palette switching. Returns None if every
    character uses the classic VFX theme.
    """
    vfx_map = build_character_vfx_map(p1_data, p2_clean)
    char_slot_table = [0xFFFF] * 36
    pair_to_idx: Dict[Tuple[str, str], int] = {}
    unique_pairs: List[Tuple[str, str]] = []
    orochi_pair: Optional[Tuple[str, str]] = None

    for char_info in CHARACTER_ROSTER:
        cid = int(char_info["id"])
        skin_entry = character_skins.get(cid)
        if not skin_entry:
            continue
        vfx_theme = skin_entry.get("vfxTheme", "classic")
        if vfx_theme == "classic":
            continue
        pair = resolve_vfx_hues(
            vfx_theme, skin_entry, cid=cid, p1_data=p1_data, p2_clean=p2_clean
        )
        if pair is None:
            continue
        cinfo = vfx_map.get(cid)
        if not cinfo or not cinfo.get("has_vfx"):
            continue
        eid, alt_flag, pal_idx = get_char_engine_info(cid)
        runtime_slot = 35 if (eid == 0 and alt_flag != 0) else pal_idx
        if pair not in pair_to_idx:
            pair_to_idx[pair] = len(unique_pairs)
            unique_pairs.append(pair)
        char_slot_table[runtime_slot] = pair_to_idx[pair]
        if runtime_slot == 30:
            orochi_pair = pair

    if not unique_pairs:
        return None

    asm = _M68kCodeCaveBuilder(VFX_HIT_EFFECT_CAVE_BASE)

    # 1. match_init_hook: execute replaced insn & reset owner caches to 0xFFFE
    asm.label("match_init_hook")
    asm.w(0x3B7C, 0xFFFF, 0x040C)
    asm.w(0x2B7C, 0xFFFE, 0xFFFE, VFX_RAM_F8_OWNER)
    asm.w(0x2B7C, 0xFFFE, 0xFFFE, VFX_RAM_FA_OWNER)
    asm.w(0x3B7C, 0xFFFE, VFX_RAM_IM_OWNER)
    asm.w(0x4E75)

    # 2. f8_ptr_hook / f9_ptr_hook / fa_ptr_hook (returns table ptr in a0, preserves d0)
    for hook_name, cache_reg, burn_off, classic_addr in (
        ("f8_ptr_hook", VFX_RAM_F8_OWNER, 0x0220, 0x002FF5F0),
        ("f9_ptr_hook", VFX_RAM_F9_OWNER, 0x0420, 0x002FF7F0),
    ):
        classic_lbl = f"{hook_name}_classic"
        asm.label(hook_name)
        asm.w(0x2F00)
        asm.w(0x302D, cache_reg)
        asm.b_branch(0x6B00, classic_lbl)
        asm.w(0xC0FC, VFX_THEME_ENTRY_STRIDE)
        asm.ref_abs32(0x41F9, "theme_entries")
        asm.w(0xD1C0)  # adda.l d0, a0 (avoid sign-extending products >= 0x8000)
        asm.w(0xD0FC, burn_off)
        asm.w(0x201F, 0x4E75)
        asm.label(classic_lbl)
        asm.w(0x41F9, (classic_addr >> 16) & 0xFFFF, classic_addr & 0xFFFF)
        asm.w(0x201F, 0x4E75)

    asm.label("fa_ptr_hook")
    asm.w(0x4A6D, VFX_RAM_FA_OWNER)
    asm.b_branch(0x6B00, "fa_ptr_hook_classic")
    asm.ref_abs32(0x41F9, "fa_custom_table")
    asm.w(0x4E75)
    asm.label("fa_ptr_hook_classic")
    asm.w(0x41F9, 0x002F, 0xF9F0)
    asm.w(0x4E75)

    # 3. Entry stubs for hit/effect hooks
    asm.label("on_fire_burn_hook")
    asm.w(0x197C, 0x00F8, 0x003A)
    asm.w(0x48E7, 0xF0F0)
    asm.w(0x7600)
    asm.b_branch(0x6000, "update_effect_group")

    asm.label("on_purple_burn_hook")
    asm.w(0x197C, 0x00F9, 0x003A)
    asm.w(0x48E7, 0xF0F0)
    asm.w(0x7601)
    asm.b_branch(0x6000, "update_effect_group")

    asm.label("on_elec_shock_hook")
    asm.w(0x002C, 0x0002, 0x00E3)
    asm.w(0x48E7, 0xF0F0)
    asm.w(0x7602)
    asm.b_branch(0x6000, "update_effect_group")

    asm.label("on_impact_hook")
    asm.w(0x45F9, 0x0001, 0x2E92)
    asm.w(0x2472, 0x1000)
    asm.w(0x3212)
    asm.w(0x48E7, 0xF0F0)
    asm.w(0x7603)
    asm.b_branch(0x6000, "update_effect_group")

    asm.label("on_fa_flash_hook")
    asm.w(0x197C, 0x00FA, 0x003A)
    asm.w(0x48E7, 0xF0F0)
    asm.w(0x7604)

    # 4. Shared group updater: a4 = victim, d3.w = group_idx (0..4)
    asm.label("update_effect_group")
    asm.w(0x206C, 0x00B6)               # movea.l $b6(a4), a0 (attacker fighter)
    asm.w(0x2008)                       # move.l a0, d0
    asm.b_branch(0x6700, "atk_classic")
    asm.w(0x7000)
    asm.w(0x1028, 0x0070)               # move.b $70(a0), d0
    asm.w(0x0C00, 0x001F)
    asm.b_branch(0x6200, "atk_classic")
    asm.w(0x4A28, 0x01D6)               # tst.b $1d6(a0)
    asm.b_branch(0x6700, "got_slot")
    asm.w(0x4A00)
    asm.b_branch(0x6600, "alt_non_kyo")
    asm.w(0x7023)                       # 94 Kyo -> runtime slot 35
    asm.b_branch(0x6000, "got_slot")
    asm.label("alt_non_kyo")
    asm.w(0x0600, 0x000B)
    asm.w(0x0C00, 0x0023)
    asm.b_branch(0x6200, "atk_classic")
    asm.label("got_slot")
    asm.w(0xD040)                       # add.w d0, d0
    asm.ref_abs32(0x41F9, "char_theme_idx")
    asm.w(0x3030, 0x0000)               # move.w (a0, d0.w), d0
    asm.b_branch(0x6000, "have_theme")
    asm.label("atk_classic")
    asm.w(0x303C, 0xFFFF)

    asm.label("have_theme")
    asm.w(0xE94B)                       # lsl.w #4, d3
    asm.ref_abs32(0x47F9, "group_descs")
    asm.w(0xD6C3)                       # adda.w d3, a3 (d3 is 0..64)
    asm.w(0x3413)                       # move.w (a3), d2 (cache_off)
    asm.w(0x3235, 0x2000)               # move.w (a5, d2.w), d1 (prev_owner)
    asm.w(0xB041)
    asm.b_branch(0x6700, "done_exit")
    asm.w(0x3B80, 0x2000)               # move.w d0, (a5, d2.w)

    asm.w(0x4A40)
    asm.b_branch(0x6B00, "switch_classic")

    # Custom theme path (d0 >= 0)
    asm.w(0xC0FC, VFX_THEME_ENTRY_STRIDE)
    asm.ref_abs32(0x45F9, "theme_entries")
    asm.w(0xD5C0)                       # adda.l d0, a2
    asm.w(0x240A)                       # move.l a2, d2 (save ThemeEntry base)
    asm.w(0x322B, 0x0004)               # common_cnt_m1
    asm.b_branch(0x6B00, "custom_burn")
    asm.w(0x2042)                       # movea.l d2, a0
    asm.w(0xD0EB, 0x0002)               # adda.w 2(a3), a0
    asm.b_branch(0x6100, "push_n_records")
    asm.label("custom_burn")
    asm.w(0x2042)                       # reload ThemeEntry base BEFORE clobbering d2.w
    asm.w(0x342B, 0x0006)               # burn_pal_id
    asm.b_branch(0x6700, "done_exit")
    asm.w(0x0C42, 0x00FA)
    asm.b_branch(0x6600, "custom_burn_off")
    asm.ref_abs32(0x41F9, "fa_custom_table")
    asm.b_branch(0x6000, "call_push_burn")
    asm.label("custom_burn_off")
    asm.w(0xD0EB, 0x0008)               # adda.w 8(a3), a0
    asm.label("call_push_burn")
    asm.b_branch(0x6100, "push_burn_slot")
    asm.b_branch(0x6000, "done_exit")

    # Classic restore path (d0 == 0xFFFF)
    asm.label("switch_classic")
    asm.w(0x4A41)
    asm.b_branch(0x6B00, "done_exit")   # 0xFFFE/0xFFFF -> RAM already clean
    asm.w(0x322B, 0x0004)
    asm.b_branch(0x6B00, "classic_burn")
    asm.ref_abs32(0x41F9, "classic_common")
    asm.w(0xD0EB, 0x0002)
    asm.b_branch(0x6100, "push_n_records")
    asm.label("classic_burn")
    asm.w(0x342B, 0x0006)
    asm.b_branch(0x6700, "done_exit")
    asm.w(0x206B, 0x000C)
    asm.b_branch(0x6100, "push_burn_slot")

    asm.label("done_exit")
    asm.w(0x4CDF, 0x0F0F)
    asm.w(0x4E75)

    # Helper: push_n_records (a0 = [pal_id.w, 15 words] * (d1+1))
    asm.label("push_n_records")
    asm.w(0x246D, 0x5924)
    asm.w(0x43ED, 0x5B30)
    asm.label("pn_loop")
    asm.w(0xB5C9)
    asm.b_branch(0x6400, "pn_done")
    asm.w(0x34D8, 0x34D8)
    for _ in range(7):
        asm.w(0x24D8)
    asm.dbra(1, "pn_loop")
    asm.label("pn_done")
    asm.w(0x34BC, 0xFFFF)
    asm.w(0x2B4A, 0x5924)
    asm.w(0x4E75)

    # Helper: push_burn_slot (a0 = 32B LSPC record, d2.w = target pal_id 00F8/00F9/00FA)
    asm.label("push_burn_slot")
    asm.w(0x246D, 0x5924)
    asm.w(0x43ED, 0x5B30)
    asm.w(0xB5C9)
    asm.b_branch(0x6400, "pb_done")
    asm.w(0x5488, 0x34C2, 0x34D8)
    for _ in range(7):
        asm.w(0x24D8)
    asm.w(0x34BC, 0xFFFF)
    asm.w(0x2B4A, 0x5924)
    asm.label("pb_done")
    asm.w(0x4E75)

    if len(asm.buf) % 2:
        asm.buf.append(0)

    # 5. Data tables
    asm.label("char_theme_idx")
    for tid in char_slot_table:
        asm.w(tid)

    asm.label("group_descs")
    for cache_off, common_off, cnt_m1, burn_id, custom_burn_off, classic_ptr, _ in VFX_COMMON_EFFECT_GROUPS:
        asm.w(cache_off, common_off, cnt_m1, burn_id, custom_burn_off, 0)
        asm.l(classic_ptr)

    asm.label("classic_common")
    for _, _, _, _, _, _, slot_ids in VFX_COMMON_EFFECT_GROUPS[:4]:
        for pid in slot_ids:
            clean_w = _read_p2_slot_words15(p2_clean, pid)
            asm.w(pid, *clean_w)

    asm.label("fa_custom_table")
    for frame in range(16):
        src_pid = 0x17D0 + frame
        if orochi_pair is not None:
            words15 = _recolor_hit_effect_slot(src_pid, p2_clean, orochi_pair[0], orochi_pair[1])
        else:
            words15 = _read_p2_slot_words15(p2_clean, src_pid)
        asm.w(src_pid, *words15)

    asm.label("theme_entries")
    for inner_hex, outer_hex in unique_pairs:
        # +0x000..+0x21F: 17 common hit/flame/shock/spark records (32B each)
        for _, _, _, _, _, _, slot_ids in VFX_COMMON_EFFECT_GROUPS[:4]:
            for pid in slot_ids:
                words15 = _recolor_hit_effect_slot(pid, p2_clean, inner_hex, outer_hex)
                asm.w(pid, *words15)
        # +0x220..+0x41F: 0xF8 16 cyclic burn frames (0x17B0..0x17BF)
        for frame in range(16):
            src_pid = 0x17B0 + frame
            words15 = (
                [0] * 15
                if frame == 15
                else _recolor_hit_effect_slot(src_pid, p2_clean, inner_hex, outer_hex)
            )
            asm.w(src_pid, *words15)
        # +0x420..+0x61F: 0xF9 16 cyclic purple-burn frames (0x17C0..0x17CF)
        for frame in range(16):
            src_pid = 0x17C0 + frame
            words15 = (
                [0] * 15
                if frame == 15
                else _recolor_hit_effect_slot(src_pid, p2_clean, inner_hex, outer_hex)
            )
            asm.w(src_pid, *words15)

    blob = asm.finalize()
    if len(blob) > VFX_HIT_EFFECT_CAVE_SIZE:
        raise ValueError(f"Hit-effect VFX code cave exceeds 64KB limit: {len(blob)} bytes")

    return {
        "blob": blob,
        "hooks": dict(asm.labels),
        "theme_count": len(unique_pairs),
        "char_slots": sum(1 for v in char_slot_table if v != 0xFFFF),
    }


def restore_hit_effect_vfx_p1(p1_data: bytearray) -> None:
    """Restore all 16 P1 hit-effect hook sites and clear 0x0F0000..0x0FFFFF to 0xFF."""
    for _name, off, orig_bytes, _lbl in VFX_HIT_HOOK_ORIGINALS:
        p1_data[off : off + 6] = orig_bytes
    p1_data[VFX_HIT_EFFECT_CAVE_BASE : VFX_HIT_EFFECT_CAVE_BASE + VFX_HIT_EFFECT_CAVE_SIZE] = (
        bytes([0xFF] * VFX_HIT_EFFECT_CAVE_SIZE)
    )


def apply_hit_effect_vfx_to_p1(
    p1_data: bytearray,
    character_skins: Dict[int, Dict[str, Any]],
    p2_clean: bytes,
) -> Optional[Dict[str, Any]]:
    """
    Inject dynamic P1 on-hit elemental burn/shock/flame code cave when any character
    has custom VFX enabled, or restore pristine official bytes if all are classic.
    """
    restore_hit_effect_vfx_p1(p1_data)
    patch = build_hit_effect_vfx_p1_patch(character_skins, p1_data, p2_clean)
    if patch is None:
        return None
    blob = patch["blob"]
    p1_data[VFX_HIT_EFFECT_CAVE_BASE : VFX_HIT_EFFECT_CAVE_BASE + len(blob)] = blob
    hooks = patch["hooks"]
    for _name, off, _orig, target_lbl in VFX_HIT_HOOK_ORIGINALS:
        target_addr = hooks[target_lbl]
        p1_data[off : off + 6] = struct.pack(">HI", 0x4EB9, target_addr)
    return patch


# ============================================================================
# Asynchronous Thread-Safe Frontend Logging (Decoupled from RPC loop)
# ============================================================================

_APP_WINDOW: Optional[webview.Window] = None


def set_app_window(win: webview.Window) -> None:
    """Store the global window handle for safe asynchronous log dispatch."""
    global _APP_WINDOW
    _APP_WINDOW = win


def async_log(message: str, level: str = "INFO") -> None:
    """
    Dispatch a live log message in a separate thread.
    Never blocks or deadlocks the pywebview RPC message loop!
    """
    try:
        print(f"[{level}] {message}")
    except UnicodeEncodeError:
        safe_msg = message.encode(getattr(sys.stdout, "encoding", "utf-8") or "utf-8", errors="replace").decode(getattr(sys.stdout, "encoding", "utf-8") or "utf-8")
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
# All internal state fields are prefixed with '_' so pywebview reflection
# will NEVER attempt to inspect COM/native window controls!
# ============================================================================

class KOF97BridgeApi:
    """
    Exposes clean Python backend functions to the HTML/JavaScript UI layer.
    Pure RPC methods only. All state attributes are private ('_').
    """

    def __init__(self) -> None:
        self._build_lock = threading.Lock()

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

    def _load_config_from_disk(self) -> bool:
        """Load persisted configuration from JSON file."""
        cfg_path = get_config_path()
        if not cfg_path.exists():
            return False

        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "active_char_id" in data:
                self._char_id = int(data["active_char_id"])
            if "scope" in data:
                self._scope = str(data["scope"])
            if "guard" in data:
                self._guard = bool(data["guard"])
            if "stun" in data:
                self._stun = bool(data["stun"])
            if "damage_mode" in data:
                mode = str(data["damage_mode"])
                if any(m["id"] == mode for m in DAMAGE_MODES):
                    self._damage_mode = mode
            if "sync_avatar" in data:
                self._sync_avatar = bool(data["sync_avatar"])
            if "infinite_power" in data:
                self._infinite_power = bool(data["infinite_power"])
            if "dizzy_duration" in data:
                try:
                    self._dizzy_duration = float(data["dizzy_duration"])
                except (ValueError, TypeError):
                    self._dizzy_duration = 5.0

            valid_theme_ids = {t["id"] for t in PRESET_THEMES}
            saved_skins = data.get("character_skins", {})
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
                    self._character_skins[cid] = make_skin_entry(cid, t_id, colors, vfx_theme=v_id)

            print(f"[INFO] Successfully loaded configuration from {cfg_path}")

            raw_customs = data.get("custom_skins", [])
            customs = []
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
                    name = str(item.get("name") or "自定义皮肤").strip() or "自定义皮肤"
                    if not sid:
                        continue
                    customs.append({
                        "id": sid,
                        "name": name,
                        "cid": cid,
                        "colors": [str(c) for c in colors],
                    })
            self._custom_skins = customs
            return True
        except Exception as exc:
            print(f"[WARN] Failed to read configuration from {cfg_path}: {exc}")
            return False

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
                str(cid): skin
                for cid, skin in self._character_skins.items()
            },
            "custom_skins": list(self._custom_skins),
            "last_saved": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        cfg_path = get_config_path()
        try:
            tmp_path = cfg_path.with_suffix(".tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            tmp_path.replace(cfg_path)

            if getattr(sys, "frozen", False) and PROJECT_ROOT != EXE_DIR and PROJECT_ROOT.exists():
                try:
                    with open(PROJECT_ROOT / CONFIG_FILE_NAME, "w", encoding="utf-8") as f:
                        json.dump(config_data, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
            return True
        except Exception as exc:
            print(f"[ERROR] Failed to save configuration to {cfg_path}: {exc}")
            return False

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

    def _build_vfx_previews(self) -> Dict[str, List[str]]:
        """Build 6-step luminous ramp previews per character based on current vfxTheme."""
        out: Dict[str, List[str]] = {}
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


    def _lspc_words_for_skin(self, cid: int, skin_entry: Dict[str, Any], p1_data: bytes, p2_clean: bytes) -> tuple:
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
            base_pid = struct.unpack(">H", p1_data[base_off:base_off + 2])[0]
            orig_p2_addr = 0x2CFFF0 + base_pid * 32
            lspc_words = [
                struct.unpack(">H", p2_clean[orig_p2_addr + i * 2: orig_p2_addr + i * 2 + 2])[0]
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
        """
        Set skin for a single character or bulk set for all characters.
        Maintains independent per-character entries with computed hex colors!
        Custom palettes keep the 15 colors the user stored and skip the theme generator.
        """
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
            async_log(f"\u514d\u7834\u9632\u673a\u5236\u5df2{'\u542f\u7528 (\u9501\u6b7b 103 \u70b9)' if val else '\u5173\u95ed (\u6062\u590d\u539f\u7248\u6263\u51cf)'}", "INFO")
        elif rule == "stun":
            self._stun = val
            async_log(f"\u514d\u7729\u6655\u673a\u5236\u5df2{'\u542f\u7528 (\u9501\u6b7b 103 \u70b9)' if val else '\u5173\u95ed (\u6062\u590d\u539f\u7248\u6263\u51cf)'}", "INFO")
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
        async_log(f"\u7acb\u7ed8\u4e0e HUD \u5c0f\u5934\u50cf\u540c\u6b65\u5df2{'\u5f00\u542f' if self._sync_avatar else '\u5173\u95ed'}", "INFO")
        self._save_config_to_disk()
        return {"success": True}

    def update_infinite_power(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update infinite power / super meter setting."""
        self._infinite_power = bool(params.get("value", True))
        async_log(f"\u65e0\u9650\u80fd\u91cf\u673a\u5236\u5df2{'\u542f\u7528 (\u521d\u59cb3\u6c14+\u6ee1\u80fd\u91cf\u69fd\uff0c\u8d85\u5fc5\u6740/MAX\u7206\u6c14\u96f6\u6d88\u8017)' if self._infinite_power else '\u5173\u95ed (\u6062\u590d\u539f\u7248\u80fd\u91cf\u6263\u51cf)'}", "INFO")
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
        """
        Assign a preset skin to every roster character, including Iori.
        """
        import random
        available_themes = [t for t in PRESET_THEMES if t["id"] != "classic"]
        if not available_themes:
            return {"success": False, "error": "No custom themes available"}

        p1_path = self._workdir / "p1_be.bin"
        p2_path = self._workdir / "p2_be.bin"
        p1_data = p1_path.read_bytes() if p1_path.exists() else None
        with zipfile.ZipFile(self._source_zip) as z_src:
            p2_clean = bswap16(z_src.read("KOF97_P2.ROM"))
            if p1_data is None:
                p1_data = bswap16(z_src.read("KOF97_P1.ROM"))

        randomized_count = 0
        # Shuffle pool to minimize duplicate consecutive themes
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
        """
        Reset all 36 characters to their authentic original SNK classic skins and VFX.
        """
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
        modded_count = sum(1 for cid, s in self._character_skins.items() if s.get("themeId") != "classic")
        cfg_name = get_config_path().name
        if ok:
            async_log(f"\u5168\u5458\u914d\u7f6e\u4e0e\u6218\u6597\u8bbe\u7f6e\u5df2\u6210\u529f\u6301\u4e45\u5316\u4fdd\u5b58\u81f3\u672c\u5730 ({cfg_name})\uff01\u5171 {modded_count} \u4f4d\u89d2\u8272\u542f\u7528\u5b9a\u5236\u76ae\u80a4\u3002", "SUCCESS")
            return {"success": True, "msg": f"\u5168\u5458\u914d\u7f6e\u5df2\u4fdd\u5b58\u81f3 {cfg_name} (\u5b9a\u5236\u89d2\u8272: {modded_count} \u4f4d)"}
        else:
            async_log("\u4fdd\u5b58\u914d\u7f6e\u6587\u4ef6\u5931\u8d25\uff0c\u8bf7\u68c0\u67e5\u78c1\u76d8\u5199\u5165\u6743\u9650\uff01", "ERROR")
            return {"success": False, "error": "\u4fdd\u5b58\u5931\u8d25"}

    # ------------------------------------------------------------------------
    # ROM Packaging Pipeline
    # ------------------------------------------------------------------------

    def pack_rom(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute property patching, per-character palette modification, and ROM packaging.
        Writes all customized character palettes to their respective ROM slots.
        """
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
            async_log("\u6b63\u5728\u6ce8\u5165 68000 \u6218\u6597\u4e0e\u9632\u5fa1\u5c5e\u6027 Patch...", "INFO")

            # Guard Crush
            if self._guard:
                p1_data[0x01397E:0x013982] = bytes.fromhex("4e714e71")
                async_log("  [P1] \u514d\u7834\u9632: 0x01397E -> NOP; NOP (\u9501\u6b7b 103 \u70b9)", "INFO")
            else:
                p1_data[0x01397E:0x013982] = bytes.fromhex("916c013e")
                async_log("  [P1] \u6062\u590d\u539f\u7248\u7834\u9632\u8ba1\u7b97\u673a\u5236", "INFO")

            # Dizzy / Stun Immunity
            if self._stun:
                p1_data[0x0139A4:0x0139A8] = bytes.fromhex("4e714e71")
                async_log("  [P1] \u514d\u7729\u6655: 0x0139A4 -> NOP; NOP (\u9501\u6b7b 103 \u70b9)", "INFO")
            else:
                p1_data[0x0139A4:0x0139A8] = bytes.fromhex("916c0146")
                async_log("  [P1] \u6062\u590d\u539f\u7248\u7729\u6655\u8ba1\u7b97\u673a\u5236", "INFO")

            # Dizzy / Stun Duration Timer (frames at 60Hz)
            dizzy_frames = max(1, min(1800, round(self._dizzy_duration * 60)))
            dizzy_frame_bytes = struct.pack(">H", dizzy_frames)
            p1_data[0x0167D4:0x0167D6] = dizzy_frame_bytes
            p1_data[0x018210:0x018212] = dizzy_frame_bytes
            p1_data[0x01E80A:0x01E80C] = dizzy_frame_bytes
            p1_data[0x01E81A:0x01E81C] = dizzy_frame_bytes
            async_log(f"  [P1] \u7729\u6655\u6301\u7eed\u65f6\u95f4: \u5df2\u6ce8\u5165 {self._dizzy_duration:.1f} \u79d2 ({dizzy_frames} \u5e27)", "INFO")

            # Infinite Super Meter / Power Option
            if self._infinite_power:
                # Hook match start round setup: 0x025160 -> JSR $0320.W (4EB8 0320)
                p1_data[0x025160:0x025164] = bytes.fromhex("4eb80320")
                # Code Cave 0x000320: JSR $31F4.W; MOVE.B #3, $01E3(A4); MOVE.B #$80, $01E8(A4); RTS
                p1_data[0x000320:0x000332] = bytes.fromhex("4eb831f4197c000301e3197c008001e84e75")
                # NOP power stock deductions across super moves and MAX burst
                p1_data[0x01117C:0x011180] = bytes.fromhex("4e714e71")
                p1_data[0x018206:0x01820A] = bytes.fromhex("4e714e71")
                p1_data[0x01E7EC:0x01E7F0] = bytes.fromhex("4e714e71")
                p1_data[0x01E7F8:0x01E7FC] = bytes.fromhex("4e714e71")
                async_log("  [P1] \u65e0\u9650\u80fd\u91cf: \u5df2\u542f\u7528 (\u521d\u59cb3\u6c14+\u6ee1\u80fd\u91cf\u69fd\uff0c\u8d85\u5fc5\u6740/MAX\u7206\u6c14\u96f6\u6d88\u8017)", "INFO")
            else:
                p1_data[0x025160:0x025164] = bytes.fromhex("4eb831f4")
                p1_data[0x000320:0x000332] = bytes([0xFF] * 18)
                p1_data[0x01117C:0x011180] = bytes.fromhex("532c01e3")
                p1_data[0x018206:0x01820A] = bytes.fromhex("532c01e3")
                p1_data[0x01E7EC:0x01E7F0] = bytes.fromhex("532c01e3")
                p1_data[0x01E7F8:0x01E7FC] = bytes.fromhex("532c01e3")
                async_log("  [P1] \u6062\u590d\u539f\u7248\u80fd\u91cf\u6263\u51cf\u673a\u5236", "INFO")

            # Damage Multiplier Hook (Code Cave 0x000300)
            selected_mode = next((m for m in DAMAGE_MODES if m["id"] == self._damage_mode), DAMAGE_MODES[3])
            if self._damage_mode == "normal":
                p1_data[0x01394A:0x01394E] = selected_mode["hook"]
                p1_data[0x000300:0x000308] = bytes.fromhex("ffffffffffffffff")
                async_log("  [P1] \u6062\u590d 100% \u539f\u59cb\u53d7\u521b\u4f24\u5bb3", "INFO")
            else:
                p1_data[0x01394A:0x01394E] = selected_mode["hook"]
                p1_data[0x000300:0x000308] = selected_mode["cave"]
                async_log(f"  [P1] \u6ce8\u5165 Code Cave \u4f24\u5bb3 Hook (\u6a21\u5f0f: {self._damage_mode})", "INFO")

            # Clean / restore all character select / spawn hooks to 100% pristine original SNK code
            p1_data[0x01FE54:0x01FE5A] = bytes.fromhex("1c830fa80010")
            p1_data[0x021F1E:0x021F22] = bytes.fromhex("422d2784")
            p1_data[0x025178:0x02517C] = bytes.fromhex("41ed2847")
            p1_data[0x011FDC:0x011FE0] = bytes.fromhex("61000212")
            p1_data[0x0868A0:0x0868A4] = bytes.fromhex("4eb878c0")
            p1_data[0x022334:0x02234C] = bytes.fromhex("1b6d284b27ed1b6d284c27ee1b6d284d27ef1b6d285727f0")
            p1_data[0x000350:0x000450] = bytes([0xFF] * 256)

            # Unlock all hidden characters directly on character select screen
            # 1. 0x009976: Set $6c34(a5) = 0x1F (move.b #$1f, $6c34(a5); NOP)
            p1_data[0x009976:0x00997E] = bytes.fromhex("4e711b7c001f6c34")
            # 2. 0x01F7C8: Guarantee $6c34(a5) = 0x1F is always set during character select
            p1_data[0x01F7C8:0x01F7CA] = bytes.fromhex("4e71")
            # 3. Add Orochi (0x1E) into Row 3 Col 4 of all 8 select screen grid tables
            for orochi_off in [0x0A9499, 0x0A94C6, 0x0A94F3, 0x0A9520, 0x0A954D, 0x0A957A, 0x0A95A7, 0x0A95D4]:
                p1_data[orochi_off] = 0x1E
            async_log("  [P1] \u5df2\u5168\u9762\u89e3\u9501\u9009\u4eba\u754c\u9762\u9690\u85cf\u4eba\u7269 (\u66b4\u8d70\u516b\u795e\u3001\u66b4\u8d70\u8389\u5b89\u5a1c\u3001\u771f\u5927\u86c7\u961f\u4e09\u4eba\u7ec4\u3001\u5927\u86c7\u53ca\u7ecf\u5178\u8349\u8599\u4eac)", "INFO")

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
                # CRITICAL FIX 1: Absolutely do not modify uncustomized characters!
                if theme_id == "classic" and vfx_theme == "classic":
                    continue

                cname = char_info["name_cn"]

                if theme_id != "classic":
                    customized_count += 1

                    # Button A feeds portraits. Preset themes rebuild each button
                    # from that button's own official colors.
                    _tid, lspc_words = self._lspc_words_for_skin(cid, skin_entry, p1_data, p2_clean)

                    _, _, pal_idx = get_char_engine_info(cid)
                    base_off = 0x483E + pal_idx * 8
                    base_pid = struct.unpack(">H", p1_data[base_off:base_off + 2])[0]

                    # Write both Base Skin (pal_id + 0) and MAX Mode Burst Flash (pal_id + 3)
                    # across all 4 color buttons (A, B, C, D) in 0x483E!
                    # In KOF97, 0x0144E2 executes 'ADD.B #3, $30(A4)' on alternate frames during MAX Mode,
                    # switching the character sprite palette from (pal_id + 0) to (pal_id + 3).
                    for btn_idx in range(4):
                        btn_off = base_off + btn_idx * 2
                        pal_id = struct.unpack(">H", p1_data[btn_off:btn_off + 2])[0]
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

                    # Character select screen and HUD avatar synchronization
                    if self._sync_avatar:
                        sync_character_portraits(cid, theme_id, base_pid, lspc_words, p2_data, p2_clean)

                    async_log(f"  [P2] \u5df2\u4e3a\u3010{cname}\u3011\u6ce8\u5165\u5b9a\u5236\u76ae\u80a4: \u3010{theme_id}\u3011(\u5df2\u914d\u7f6e\u57fa\u7840\u6001\u4e0e MAX \u7206\u6c14\u9ad8\u80fd\u6001\u8c03\u8272\u677f)", "INFO")

                if vfx_theme != "classic":
                    v_written = apply_vfx_palettes_to_p2(cid, vfx_theme, skin_entry, p1_data, p2_data, p2_clean)
                    if v_written > 0:
                        vfx_char_count += 1
                        vfx_slot_total += v_written
                        vname = VFX_PRESET_MAP.get(vfx_theme, {}).get("name_cn", vfx_theme)
                        async_log(f"  [P2-VFX] \u5df2\u4e3a\u3010{cname}\u3011\u6ce8\u5165\u6280\u80fd\u7279\u6548: \u3010{vname}\u3011({v_written} \u4e2a\u7279\u6548\u69fd)", "INFO")

            async_log(f"  [P2] \u8c03\u8272\u677f\u6ce8\u5165\u5b8c\u6210\uff01\u5b9a\u5236\u76ae\u80a4 {customized_count} \u4f4d\u89d2\u8272\uff0c\u5b9a\u5236\u7279\u6548 {vfx_char_count} \u4f4d\u89d2\u8272 ({vfx_slot_total} \u69fd)\uff0c\u5176\u4f59\u4fdd\u6301\u5b98\u65b9\u539f\u7248", "SUCCESS")
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
    # Start Game Launcher
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
        """Locate running WinKawaks process PID with robust multi-layered detection."""
        try:
            if self._running_proc is not None:
                if self._running_proc.poll() is None:
                    return int(self._running_proc.pid)
                self._running_proc = None

            u32 = ctypes.WinDLL("user32")
            found_pid: Optional[int] = None

            def _enum_cb(hwnd: int, _lparam: int) -> bool:
                nonlocal found_pid
                pid = ctypes.c_ulong()
                u32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                buf = ctypes.create_unicode_buffer(256)
                u32.GetWindowTextW(hwnd, buf, 256)
                title = buf.value.lower()
                if "winkawaks" in title or "kawaks" in title:
                    found_pid = int(pid.value)
                    return False
                return True

            WNDENUM = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
            u32.EnumWindows(WNDENUM(_enum_cb), 0)
            if found_pid is not None:
                return found_pid

            # Fallback to tasklist query
            cmd = ['tasklist', '/FI', 'IMAGENAME eq WinKawaks.exe', '/FO', 'CSV', '/NH']
            out = subprocess.check_output(cmd, creationflags=0x08000000).decode("latin1", errors="ignore")
            for line in out.strip().splitlines():
                parts = [p.strip('"' + ' ') for p in line.split('","')]
                if len(parts) >= 2 and "winkawaks" in parts[0].lower():
                    try:
                        return int(parts[1])
                    except ValueError:
                        pass
        except Exception:
            pass
        return None

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
        """
        Dynamically inject character and VFX palettes directly into running WinKawaks memory.
        Instantly overwrites on-screen Palette RAM (0x007126B0) and loaded P2 ROM memory buffer (0x00712660 + 0x100000).
        """
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
                "message": "\u914d\u7f6e\u5df2\u4fdd\u5b58\uff01\u5f53\u524d\u6a21\u62df\u5668\u672a\u5728\u8fd0\u884c\uff0c\u70b9\u51fb\u300c\u5f00\u59cb\u6e38\u620f\u300d\u6216\u300c\u6253\u5305ROM\u300d\u5373\u53ef\u751f\u6548\u3002"
            }

        # 3. Read p1 and clean p2 baseline
        p1_path = self._workdir / "p1_be.bin"
        if not p1_path.exists():
            return {"success": False, "running": True, "message": "\u5de5\u4f5c\u533a\u7f3a\u5c11 p1_be.bin"}
        p1_data = p1_path.read_bytes()

        with zipfile.ZipFile(self._source_zip) as z_src:
            p2_clean = bswap16(z_src.read("KOF97_P2.ROM"))

        # 4. Open process handle
        k32 = ctypes.WinDLL("kernel32")
        PROCESS_ALL = 0x001F0FFF
        h_proc = k32.OpenProcess(PROCESS_ALL, False, pid)
        if not h_proc:
            return {"success": False, "running": True, "message": f"\u65e0\u6cd5\u6302\u8f7d\u6a21\u62df\u5668\u8fdb\u7a0b (PID={pid})"}

        try:
            read = ctypes.c_size_t(0)
            written = ctypes.c_size_t(0)
            ptr_buf = ctypes.create_string_buffer(4)

            # Read WinKawaks 1.48 Core Pointers
            k32.ReadProcessMemory(h_proc, ctypes.c_void_p(0x00712660), ptr_buf, 4, ctypes.byref(read))
            prom_va = struct.unpack("<I", ptr_buf.raw)[0]

            k32.ReadProcessMemory(h_proc, ctypes.c_void_p(0x007126B0), ptr_buf, 4, ctypes.byref(read))
            pal_ram_va = struct.unpack("<I", ptr_buf.raw)[0]

            k32.ReadProcessMemory(h_proc, ctypes.c_void_p(0x00712688), ptr_buf, 4, ctypes.byref(read))
            work_ram_va = struct.unpack("<I", ptr_buf.raw)[0]

            if prom_va == 0 or pal_ram_va == 0:
                return {
                    "success": False,
                    "running": True,
                    "message": "\u6a21\u62df\u5668\u5c1a\u5728\u52a0\u8f7d\u6e38\u620f\u4e2d\uff0c\u8bf7\u7a0d\u5019\u518d\u70b9\u51fb\u5b9e\u65f6\u5e94\u7528\u76ae\u80a4"
                }

            p2_base = prom_va + 0x100000

            # Read current active 8KB Palette RAM to scan existing slots
            pal_ram_buf = ctypes.create_string_buffer(8192)
            k32.ReadProcessMemory(h_proc, ctypes.c_void_p(pal_ram_va), pal_ram_buf, 8192, ctypes.byref(read))
            pal_ram_bytes = bytearray(pal_ram_buf.raw)

            # Read 1P Active Palette Index from Work RAM (0x108130 -> WorkRAM + 0x8130)
            p1_active_slot = -1
            if work_ram_va != 0:
                slot_buf = ctypes.create_string_buffer(1)
                k32.ReadProcessMemory(h_proc, ctypes.c_void_p(work_ram_va + 0x8130), slot_buf, 1, ctypes.byref(read))
                p1_active_slot = slot_buf.raw[0]

            target_cids = [c["id"] for c in CHARACTER_ROSTER] if scope == "ALL" else [cid]
            injected_total = 0

            for target_cid in target_cids:
                skin_entry = self._character_skins.get(target_cid, {})
                t_id = skin_entry.get("themeId", "classic")
                engine_cid, _, pal_idx = get_char_engine_info(target_cid)
                base_off = 0x483E + pal_idx * 8
                base_pid = struct.unpack(">H", p1_data[base_off:base_off + 2])[0]

                _tid, lspc_words = self._lspc_words_for_skin(target_cid, skin_entry, p1_data, p2_clean)
                if _tid == "classic":
                    burst_words = lspc_words
                else:
                    burst_words = generate_burst_character_palette(target_cid, _tid, lspc_words)

                # Prepare Little-Endian packed words for WinKawaks RAM
                lspc_bytes_le = bytearray()
                for w in lspc_words:
                    lspc_bytes_le += struct.pack("<H", w)

                burst_bytes_le = bytearray()
                for w in burst_words:
                    burst_bytes_le += struct.pack("<H", w)

                # A. Overwrite all 4 button slots (A, B, C, D) in loaded P2 ROM memory.
                # Each button is recolored from its own official palette.
                for btn_idx in range(4):
                    btn_off = base_off + btn_idx * 2
                    pal_id = struct.unpack(">H", p1_data[btn_off:btn_off + 2])[0]
                    if is_custom_theme_id(t_id) or t_id == "classic":
                        btn_words = lspc_words
                        btn_burst = burst_words
                    else:
                        btn_words = generate_harmonious_character_palette(
                            target_cid, t_id, p1_data, p2_clean, btn_idx
                        )
                        btn_burst = generate_burst_character_palette(target_cid, t_id, btn_words)
                    btn_le = bytearray()
                    for w in btn_words:
                        btn_le += struct.pack("<H", w)
                    burst_le = bytearray()
                    for w in btn_burst:
                        burst_le += struct.pack("<H", w)
                    btn_addr = p2_base + 0x2CFFF0 + pal_id * 32 + 2
                    k32.WriteProcessMemory(h_proc, ctypes.c_void_p(btn_addr), bytes(btn_le), 30, ctypes.byref(written))
                    burst_addr = p2_base + 0x2CFFF0 + (pal_id + 3) * 32 + 2
                    k32.WriteProcessMemory(h_proc, ctypes.c_void_p(burst_addr), bytes(burst_le), 30, ctypes.byref(written))

                # B. Synchronize all portrait and avatar palettes in P2 ROM
                if self._sync_avatar:
                    p2_temp = bytearray(p2_clean)
                    sync_character_portraits(target_cid, t_id, base_pid, lspc_words, p2_temp, p2_clean)
                    for btn_idx in range(4):
                        for slot_off in (13, 14, 15):
                            port_pal = base_pid + slot_off + btn_idx * 16
                            port_addr = 0x2CFFF0 + port_pal * 32
                            port_words_be = [struct.unpack(">H", p2_temp[port_addr + i * 2 : port_addr + i * 2 + 2])[0] for i in range(16)]
                            port_bytes_le = bytearray()
                            for pw in port_words_be:
                                port_bytes_le += struct.pack("<H", pw)
                            k32.WriteProcessMemory(h_proc, ctypes.c_void_p(p2_base + port_addr), bytes(port_bytes_le), 32, ctypes.byref(written))

                # C. Instant On-Screen Hot-Update (8KB Palette RAM)
                # 1. Directly overwrite 1P Active Slot if matched
                if p1_active_slot != -1 and p1_active_slot < 256:
                    target_va = pal_ram_va + p1_active_slot * 32 + 2
                    k32.WriteProcessMemory(h_proc, ctypes.c_void_p(target_va), bytes(lspc_bytes_le), 30, ctypes.byref(written))
                    # Also write +3 for MAX burst
                    if p1_active_slot + 3 < 256:
                        target_burst_va = pal_ram_va + (p1_active_slot + 3) * 32 + 2
                        k32.WriteProcessMemory(h_proc, ctypes.c_void_p(target_burst_va), bytes(burst_bytes_le), 30, ctypes.byref(written))

                # 2. Scan entire Palette RAM (all 256 slots) for matching character signature
                # Read baseline skin signature (words 1..4 in LE) to match and replace
                clean_addr = 0x2CFFF0 + base_pid * 32 + 2
                clean_sig = bytearray()
                for i in range(4):
                    cw = struct.unpack(">H", p2_clean[clean_addr + i*2 : clean_addr + i*2 + 2])[0]
                    clean_sig += struct.pack("<H", cw)

                for slot_idx in range(256):
                    slot_data = pal_ram_bytes[slot_idx * 32 + 2 : slot_idx * 32 + 10]
                    if slot_data == clean_sig or slot_idx == p1_active_slot:
                        va = pal_ram_va + slot_idx * 32 + 2
                        k32.WriteProcessMemory(h_proc, ctypes.c_void_p(va), bytes(lspc_bytes_le), 30, ctypes.byref(written))

                # D. VFX Palette Hot-Update (P2 ROM + Active Palette RAM)
                vfx_info = build_character_vfx_map(p1_data, p2_clean).get(target_cid)
                vfx_theme = skin_entry.get("vfxTheme", "classic")
                if vfx_info and vfx_info.get("has_vfx"):
                    vpair = resolve_vfx_hues(
                        vfx_theme, skin_entry, cid=target_cid, p1_data=p1_data, p2_clean=p2_clean
                    )
                    for v_pid in vfx_info["all_slots"]:
                        if v_pid <= 0x00FF:
                            continue
                        clean_v = _read_p2_slot_words15(p2_clean, v_pid)
                        new_v = clean_v if vpair is None else recolor_vfx_palette(clean_v, vpair[0], vpair[1])
                        v_le = struct.pack("<15H", *new_v)
                        v_addr = p2_base + 0x2CFFF0 + v_pid * 32 + 2
                        k32.WriteProcessMemory(h_proc, ctypes.c_void_p(v_addr), v_le, 30, ctypes.byref(written))

                        clean_vsig = struct.pack("<4H", *clean_v[:4])
                        prev_vsig = self._last_vfx_ram_sigs.get(v_pid)
                        for slot_idx in range(16, 256):
                            slot_data = pal_ram_bytes[slot_idx * 32 + 2 : slot_idx * 32 + 10]
                            if slot_data == clean_vsig or (prev_vsig and slot_data == prev_vsig):
                                va = pal_ram_va + slot_idx * 32 + 2
                                k32.WriteProcessMemory(h_proc, ctypes.c_void_p(va), v_le, 30, ctypes.byref(written))
                        if vpair is None:
                            self._last_vfx_ram_sigs.pop(v_pid, None)
                        else:
                            self._last_vfx_ram_sigs[v_pid] = v_le[:8]

                    if p1_active_slot != -1 and p1_active_slot < 256:
                        btn0_pid = vfx_info["btn_pids"][0]
                        for sub in vfx_info["char_sub_offsets"]:
                            if p1_active_slot + sub < 256:
                                clean_sub = _read_p2_slot_words15(p2_clean, btn0_pid + sub)
                                new_sub = clean_sub if vpair is None else recolor_vfx_palette(clean_sub, vpair[0], vpair[1])
                                sub_va = pal_ram_va + (p1_active_slot + sub) * 32 + 2
                                k32.WriteProcessMemory(
                                    h_proc, ctypes.c_void_p(sub_va), struct.pack("<15H", *new_sub), 30, ctypes.byref(written)
                                )

                    # Hot-update common battle effect slots in live Palette RAM only (never P2 ROM)
                    seen_eff_slots: set = set()
                    for _cache_off, _c_off, _cnt_m1, _b_id, _cb_off, _cl_ptr, slot_ids in VFX_COMMON_EFFECT_GROUPS[:4]:
                        for eff_pid in slot_ids:
                            if eff_pid in seen_eff_slots or eff_pid >= 256:
                                continue
                            seen_eff_slots.add(eff_pid)
                            eff_words = (
                                _read_p2_slot_words15(p2_clean, eff_pid)
                                if vpair is None
                                else _recolor_hit_effect_slot(eff_pid, p2_clean, vpair[0], vpair[1])
                            )
                            eff_va = pal_ram_va + eff_pid * 32 + 2
                            k32.WriteProcessMemory(
                                h_proc, ctypes.c_void_p(eff_va), struct.pack("<15H", *eff_words), 30, ctypes.byref(written)
                            )

                injected_total += 1

            char_info = next((c for c in CHARACTER_ROSTER if c["id"] == cid), None)
            cname = char_info["name_cn"] if char_info else f"0x{cid:02X}"
            target_desc = f"\u3010{cname}\u3011" if scope == "SINGLE" else f"\u5168\u5458 {injected_total} \u4f4d\u89d2\u8272"
            applied_name = (
                VFX_PRESET_MAP.get(str(params.get("vfx_theme") or "classic"), {}).get("name_cn", "VFX")
                if vfx_only
                else theme_id
            )
            async_log(f"[\u5b9e\u65f6\u70ed\u66f4\u65b0] {'\u7279\u6548' if vfx_only else '\u76ae\u80a4'}\u3010{applied_name}\u3011\u5df2\u6210\u529f\u5b9e\u65f6\u6ce8\u5165\u8fd0\u884c\u4e2d\u7684\u6e38\u620f (PID={pid}, {target_desc})\uff01\u753b\u9762\u5df2\u5373\u65f6\u53d8\u8272\uff01", "SUCCESS")
            return {
                "success": True,
                "running": True,
                "message": f"[\u5b9e\u65f6\u70ed\u66f4\u65b0] {'\u6280\u80fd\u7279\u6548' if vfx_only else '\u76ae\u80a4'}\u5df2\u5b9e\u65f6\u70ed\u66f4\u65b0\u5230\u6e38\u620f\u4e2d\uff01{target_desc}\u753b\u9762\u5df2\u5373\u523b\u53d8\u8272\uff01"
            }
        except Exception as exc:
            async_log(f"\u5b9e\u65f6\u70ed\u66f4\u65b0\u5931\u8d25: {exc}", "ERROR")
            return {"success": False, "running": True, "message": str(exc)}
        finally:
            k32.CloseHandle(h_proc)

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
                # Reset all character skins to classic
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
                script_path = PROJECT_ROOT / "tools" / "rom_tool.py"
                cmd = [sys.executable, str(script_path), "self-test"]
                res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
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


# ============================================================================
# Main Entry Point
# ============================================================================

def main() -> None:
    """Launch the PyWebView Desktop GUI Application."""
    api = KOF97BridgeApi()

    # Determine HTML path
    candidates = [
        BUNDLE_DIR / "tools" / "web" / "index.html",
        BUNDLE_DIR / "web" / "index.html",
        PROJECT_ROOT / "tools" / "web" / "index.html",
        PROJECT_ROOT / "web" / "index.html",
    ]
    html_file = next((p for p in candidates if p.exists()), None)
    if not html_file:
        raise FileNotFoundError(f"Web interface index.html not found in {[str(p) for p in candidates]}")

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
