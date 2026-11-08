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
import os
import struct
import subprocess
import sys
import threading
import time
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
# Ensures clean color blocking, strict luminance ranking, deep dark anchor, and sharp outlines.
CHARACTER_PALETTE_SCHEMA: Dict[int, Dict[str, List[int]]] = {
    0x00: {"skin": [1, 2, 3, 4], "white_trim": [0], "hair": [5, 6], "primary": [7, 8, 9], "dark_anchor": [10, 11, 12, 13], "contour": [14]},
    0x01: {"skin": [0, 1, 2, 3, 4], "white_trim": [5], "dark_anchor": [6, 7, 8, 9], "contour": [10], "accent": [11, 12, 13, 14]},
    0x02: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7, 8, 9, 10], "accent": [11], "white_trim": [12, 13], "contour": [14]},
    0x03: {"skin": [0, 1, 2, 3, 4], "dark_anchor": [5, 6, 7, 8], "primary": [9, 10], "accent": [11, 12], "white_trim": [13], "contour": [14]},
    0x04: {"skin": [0, 1, 2, 3, 4], "white_trim": [5, 6, 7, 8, 9, 11], "accent": [10, 12, 13], "contour": [14]},
    0x05: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7], "accent": [8, 9], "white_trim": [10, 11, 12, 13], "contour": [14]},
    0x06: {"white_trim": [0], "skin": [1, 2, 3, 4, 5], "primary": [6, 7, 8, 9, 10], "contour": [11], "accent": [12, 13, 14]},
    0x07: {"skin": [0, 1, 2, 3, 4], "accent": [5], "primary": [6, 7, 8, 9], "white_trim": [10], "dark_anchor": [11, 12, 13], "contour": [14]},
    0x08: {"accent": [0], "skin": [1, 2, 3, 4, 5], "white_trim": [6, 7, 8, 9, 10], "dark_anchor": [11, 12, 13], "contour": [14]},
    0x09: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7, 8, 9], "dark_anchor": [10], "contour": [11], "accent": [12, 13, 14]},
    0x0A: {"white_trim": [0], "skin": [1, 2, 3, 4, 5], "primary": [6, 7, 8, 9], "dark_anchor": [10, 11, 12, 13], "contour": [14]},
    0x0B: {"white_trim": [0], "skin": [1, 2, 3, 4, 5], "primary": [6, 7, 8, 9], "dark_anchor": [10, 11, 12, 13], "contour": [14]},
    0x0C: {"skin": [0, 1, 2, 3, 4], "accent": [5, 6, 7, 8], "white_trim": [9, 10, 11], "primary": [12, 13, 14]},
    0x0D: {"white_trim": [0], "skin": [1, 2, 3, 4, 5], "primary": [6, 7, 8, 9], "dark_anchor": [10, 11, 12, 13], "contour": [14]},
    0x0E: {"skin": [0, 1, 2, 3, 4], "white_trim": [5, 6, 7, 8, 9], "dark_anchor": [10, 11, 12, 13], "contour": [14]},
    0x0F: {"skin": [0, 1, 2, 3, 4], "white_trim": [5, 6, 7, 8, 9], "primary": [10, 11, 12, 13], "contour": [14]},
    0x10: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7], "white_trim": [8, 9, 10], "dark_anchor": [11, 12], "accent": [13], "contour": [14]},
    0x11: {"primary": [0, 1, 2, 3], "accent": [4, 5], "white_trim": [6, 7, 8, 9], "skin": [10, 11, 12, 13, 14]},
    0x12: {"skin": [0, 1, 2, 3, 4], "white_trim": [5, 6, 7, 8, 9], "primary": [10, 11, 12], "contour": [13], "dark_anchor": [14]},
    0x13: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7, 8, 9], "accent": [10, 11]},
    0x14: {"skin": [0, 1, 2, 3], "primary": [4, 5, 6, 7, 8], "accent": [9, 10], "dark_anchor": [11, 12, 13], "contour": [14]},
    0x15: {"skin": [0, 1, 2, 3, 4], "white_trim": [5, 6, 7, 8, 9], "primary": [10, 11, 12, 13], "contour": [14]},
    0x16: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7, 8, 9], "accent": [10, 11], "contour": [12], "dark_anchor": [13, 14]},
    0x17: {"skin": [0, 1, 2, 3, 4], "white_trim": [5, 6, 7, 8, 9], "primary": [10, 11, 12], "dark_anchor": [13], "contour": [14]},
    0x18: {"skin": [0, 1, 2, 3, 4], "accent": [5, 6, 7], "dark_anchor": [8, 9, 10, 11, 12], "contour": [13], "white_trim": [14]},
    0x19: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7], "accent": [8, 9, 10], "dark_anchor": [11, 12, 13], "contour": [14]},
    0x1A: {"skin": [0, 1, 2, 3, 4], "dark_anchor": [5, 6, 7, 8, 9], "primary": [10, 11, 12, 13], "white_trim": [14]},
    0x1B: {"skin": [0, 1, 2, 3], "white_trim": [4, 5, 6], "accent": [7, 8, 9, 10], "primary": [11, 12, 13], "contour": [14]},
    0x1C: {"white_trim": [0], "skin": [1, 2, 3, 4, 5], "hair": [6], "primary": [7, 8, 9], "dark_anchor": [10, 11, 12, 13], "contour": [14]},
    0x1D: {"skin": [0, 1, 2, 3], "white_trim": [4, 5, 6], "accent": [7, 8, 9, 10], "primary": [11, 12, 13], "contour": [14]},
    0x1E: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7, 8, 9], "dark_anchor": [10], "contour": [11], "accent": [12, 13, 14]},
    0x1F: {"skin": [0, 1, 2, 3, 4], "white_trim": [5, 6, 7, 8, 9], "primary": [10, 11, 12, 13], "contour": [14]},
    0x20: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7, 8, 9], "accent": [10, 11], "contour": [12], "dark_anchor": [13, 14]},
    0x21: {"skin": [0, 1, 2, 3, 4], "white_trim": [5, 6, 7, 8, 9], "primary": [10, 11, 12], "dark_anchor": [13], "contour": [14]},
    0x22: {"skin": [0, 1, 2, 3, 4], "white_trim": [5, 6, 7, 8, 9, 10, 11], "accent": [12, 13, 14]},
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
) -> List[int]:
    """
    Recolor a character with a theme hue while keeping SNK's original shade.

    Each costume slot keeps the luma the sprite was drawn with. Highlights
    preserve that luma and ease saturation when the new hue is darker.
    Dark pigment keeps its saturation and must not get brighter. Skin,
    white cloth, natural hair and outlines stay official. Orochi Iori
    uses normal Iori's shade curve, because the official Orochi ramp is
    a pastel highlight over a crushed shadow.
    """
    _, _, pal_idx = get_char_engine_info(cid)
    base_off = 0x483E + pal_idx * 8
    pal_id = struct.unpack(">H", p1_data[base_off:base_off + 2])[0]
    p2_addr = 0x2CFFF0 + pal_id * 32
    orig_words = list(struct.unpack(">16H", p2_clean[p2_addr : p2_addr + 32])[1:])

    if theme_id == "classic" or theme_id not in THEME_KEYS:
        return orig_words

    primary_h, primary_s, accent_h, accent_s = theme_hsv(theme_id)

    # Orochi Iori's official ramp is the glossy one. Both Iori forms take
    # their shade from normal Iori, then the theme hue is applied.
    source = orig_words
    if cid == 0x1D or pal_idx == 0x1C:
        iori_off = 0x483E + 0x1B * 8
        iori_pid = struct.unpack(">H", p1_data[iori_off:iori_off + 2])[0]
        iori_addr = 0x2CFFF0 + iori_pid * 32
        source = list(struct.unpack(">16H", p2_clean[iori_addr:iori_addr + 32])[1:])

    if cid in (0x1B, 0x1D) or pal_idx in (0x1B, 0x1C):
        res = list(source)
        for idx in (7, 8, 9, 10, 11, 12, 13):
            _paint_slot(res, source, idx, primary_h, primary_s)
        res[14] = 0x0000
        return res

    schema = CHARACTER_PALETTE_SCHEMA.get(cid)
    if not schema:
        return orig_words

    res = list(orig_words)
    # Skin, white cloth and natural hair stay on the official words.
    # Costume groups take the theme hue. Highlights keep luma (saturation
    # eases when the hue is darker). Dark pigment keeps saturation and
    # does not get brighter.
    if "primary" in schema:
        for idx in schema["primary"]:
            _paint_slot(res, orig_words, idx, primary_h, primary_s)
    if "dark_anchor" in schema:
        for idx in schema["dark_anchor"]:
            _paint_slot(res, orig_words, idx, primary_h, primary_s)
    if "accent" in schema:
        for idx in schema["accent"]:
            _paint_slot(res, orig_words, idx, accent_h, accent_s, keep_value=True)
    if "contour" in schema:
        for idx in schema["contour"]:
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


def make_skin_entry(cid: int, theme_id: str, colors: List[str]) -> Dict[str, Any]:
    """Store a skin together with dummy colors derived from its palette."""
    payload = list(colors)
    return {
        "themeId": theme_id,
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

        # Per-character skin store: char_id -> {themeId, colors, preview}
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
                    if t_id not in valid_theme_ids:
                        t_id = "classic"

                    colors = entry.get("colors")
                    if not colors or len(colors) != 15:
                        preset = next((t for t in PRESET_THEMES if t["id"] == t_id), PRESET_THEMES[0])
                        colors = list(preset["colors"])
                    self._character_skins[cid] = make_skin_entry(cid, t_id, colors)

            print(f"[INFO] Successfully loaded configuration from {cfg_path}")
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

    def get_initial_state(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Return the current studio configuration state to frontend."""
        p1_path = self._workdir / "p1_be.bin"
        p2_path = self._workdir / "p2_be.bin"
        has_unpacked = p1_path.exists() and p2_path.exists()
        has_zip = self._output_zip.exists()
        zip_crc = crc32_hex(self._output_zip.read_bytes()) if has_zip else ""

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
        }

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
        """
        char_id = params.get("char_id", self._char_id)
        theme_id = params.get("theme_id", "classic")
        scope = params.get("scope", self._scope)

        p1_path = self._workdir / "p1_be.bin"
        p2_path = self._workdir / "p2_be.bin"
        p1_data = p1_path.read_bytes() if p1_path.exists() else None
        with zipfile.ZipFile(self._source_zip) as z_src:
            p2_clean = bswap16(z_src.read("KOF97_P2.ROM"))
            if p1_data is None:
                p1_data = bswap16(z_src.read("KOF97_P1.ROM"))

        if scope == "ALL":
            for char_info in CHARACTER_ROSTER:
                cid = char_info["id"]
                lspc_words = generate_harmonious_character_palette(cid, theme_id, p1_data, p2_clean)
                self._character_skins[cid] = make_skin_entry(
                    cid, theme_id, [lspc2_to_hex(w) for w in lspc_words]
                )
            async_log(f"\u5df2\u5168\u91cf\u8bbe\u7f6e\u5168\u5458 36 \u89d2\u8272\u76ae\u80a4\u4e3a: \u3010{theme_id}\u3011", "INFO")
        else:
            lspc_words = generate_harmonious_character_palette(char_id, theme_id, p1_data, p2_clean)
            hex_colors = [lspc2_to_hex(w) for w in lspc_words]
            self._character_skins[char_id] = make_skin_entry(
                char_id, theme_id, hex_colors
            )
            char_info = next((c for c in CHARACTER_ROSTER if c["id"] == char_id), None)
            cname = char_info["name_cn"] if char_info else f"0x{char_id:02X}"
            async_log(f"\u5df2\u4fdd\u5b58\u89d2\u8272\u3010{cname}\u3011\u7684\u72ec\u7acb\u76ae\u80a4\u914d\u7f6e: \u3010{theme_id}\u3011", "INFO")

        self._save_config_to_disk()
        return {
            "success": True,
            "character_skins": {str(k): v for k, v in self._character_skins.items()},
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
        Randomize skins for all characters EXCLUDING Iori (0x1B) and Orochi Iori (0x1D).
        Maintains user-defined skin for Iori while giving every other fighter a distinct theme.
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
            # Exclude Iori (0x1B) and Orochi Iori (0x1D) - user defined!
            if cid in (0x1B, 0x1D):
                continue

            chosen_theme = theme_pool[pool_idx % len(theme_pool)]
            pool_idx += 1
            theme_id = chosen_theme["id"]

            lspc_words = generate_harmonious_character_palette(cid, theme_id, p1_data, p2_clean)
            hex_colors = [lspc2_to_hex(w) for w in lspc_words]
            self._character_skins[cid] = make_skin_entry(cid, theme_id, hex_colors)
            randomized_count += 1

        self._save_config_to_disk()
        async_log(f"\u5df2\u4e00\u952e\u968f\u673a\u5176\u4f59 {randomized_count} \u4f4d\u89d2\u8272\u76ae\u80a4\uff01\u516b\u795e(\u66b4\u8d70\u516b\u795e)\u4fdd\u6301\u81ea\u5b9a\u4e49\u3002", "SUCCESS")
        return {
            "success": True,
            "count": randomized_count,
            "character_skins": {str(k): v for k, v in self._character_skins.items()},
        }

    def reset_all_skins(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Reset all 36 characters to their authentic original SNK classic skins.
        """
        p1_path = self._workdir / "p1_be.bin"
        p2_path = self._workdir / "p2_be.bin"
        p1_data = p1_path.read_bytes() if p1_path.exists() else None
        with zipfile.ZipFile(self._source_zip) as z_src:
            p2_clean = bswap16(z_src.read("KOF97_P2.ROM"))
            if p1_data is None:
                p1_data = bswap16(z_src.read("KOF97_P1.ROM"))

        for char_info in CHARACTER_ROSTER:
            cid = char_info["id"]
            lspc_words = generate_harmonious_character_palette(cid, "classic", p1_data, p2_clean)
            hex_colors = [lspc2_to_hex(w) for w in lspc_words]
            self._character_skins[cid] = make_skin_entry(cid, "classic", hex_colors)

        self._save_config_to_disk()
        async_log("\u5df2\u5c06\u5168\u5458 36 \u4f4d\u89d2\u8272\u76ae\u80a4\u5168\u90e8\u91cd\u7f6e\u4e3a\u5b98\u65b9\u539f\u7248\u7ecf\u5178\uff01", "SUCCESS")
        return {
            "success": True,
            "character_skins": {str(k): v for k, v in self._character_skins.items()},
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

            p1_path.write_bytes(p1_data)

            # 3. Apply Palette & Skin for customized characters to p2_be.bin
            async_log("\u6b63\u5728\u5c06\u5b9a\u5236\u89d2\u8272\u7684\u72ec\u7acb\u8c03\u8272\u677f\u65b9\u6848\u5199\u5165 p2_be.bin...", "INFO")

            # Load clean baseline p2 bytes to ensure untouched characters remain 100% pristine
            with zipfile.ZipFile(self._source_zip) as z_src:
                p2_clean = bswap16(z_src.read("KOF97_P2.ROM"))
            p2_data = bytearray(p2_clean)

            customized_count = 0

            for char_info in CHARACTER_ROSTER:
                cid = char_info["id"]
                skin_entry = self._character_skins.get(cid)
                if not skin_entry:
                    continue

                theme_id = skin_entry.get("themeId", "classic")
                # CRITICAL FIX 1: Absolutely do not modify uncustomized characters!
                if theme_id == "classic":
                    continue

                customized_count += 1
                cname = char_info["name_cn"]

                # Generate tailored, luminance-preserving harmonious palette
                lspc_words = generate_harmonious_character_palette(cid, theme_id, p1_data, p2_clean)
                lspc_bytes = struct.pack(">15H", *lspc_words)

                # Generate luminous harmonic burst flash palette for MAX Mode (sub-palette +3)
                burst_words = generate_burst_character_palette(cid, theme_id, lspc_words)
                burst_bytes = struct.pack(">15H", *burst_words)

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
                    p2_addr_base = 0x2CFFF0 + pal_id * 32
                    p2_data[p2_addr_base + 2 : p2_addr_base + 32] = lspc_bytes
                    p2_addr_burst = 0x2CFFF0 + (pal_id + 3) * 32
                    p2_data[p2_addr_burst + 2 : p2_addr_burst + 32] = burst_bytes

                # Character select screen and HUD avatar synchronization
                if self._sync_avatar:
                    sync_character_portraits(cid, theme_id, base_pid, lspc_words, p2_data, p2_clean)

                async_log(f"  [P2] \u5df2\u4e3a\u3010{cname}\u3011\u6ce8\u5165\u5b9a\u5236\u76ae\u80a4: \u3010{theme_id}\u3011(\u5df2\u914d\u7f6e\u57fa\u7840\u6001\u4e0e MAX \u7206\u6c14\u9ad8\u80fd\u6001\u8c03\u8272\u677f)", "INFO")

            async_log(f"  [P2] \u8c03\u8272\u677f\u6ce8\u5165\u5b8c\u6210\uff01\u5171\u5b9a\u5236 {customized_count} \u4f4d\u89d2\u8272\uff0c\u5176\u4f59\u89d2\u8272\u4fdd\u6301\u5b98\u65b9\u539f\u7248", "SUCCESS")
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

    def apply_skin_live(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Dynamically inject character palette directly into running WinKawaks process memory.
        Instantly overwrites on-screen Palette RAM (0x007126B0) and loaded P2 ROM memory buffer (0x00712660 + 0x100000).
        """
        params = params or {}
        cid = params.get("char_id", self._char_id)
        theme_id = params.get("theme_id", "classic")
        scope = params.get("scope", self._scope)

        # 1. Update internal state and persist to disk
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

                if t_id == "classic":
                    orig_p2_addr = 0x2CFFF0 + base_pid * 32
                    lspc_words = [struct.unpack(">H", p2_clean[orig_p2_addr + i * 2 : orig_p2_addr + i * 2 + 2])[0] for i in range(1, 16)]
                    burst_words = lspc_words
                else:
                    lspc_words = generate_harmonious_character_palette(target_cid, t_id, p1_data, p2_clean)
                    burst_words = generate_burst_character_palette(target_cid, t_id, lspc_words)

                # Prepare Little-Endian packed words for WinKawaks RAM
                lspc_bytes_le = bytearray()
                for w in lspc_words:
                    lspc_bytes_le += struct.pack("<H", w)

                burst_bytes_le = bytearray()
                for w in burst_words:
                    burst_bytes_le += struct.pack("<H", w)

                # A. Overwrite all 4 button slots (A, B, C, D) in loaded P2 ROM memory
                for btn_idx in range(4):
                    btn_off = base_off + btn_idx * 2
                    pal_id = struct.unpack(">H", p1_data[btn_off:btn_off + 2])[0]
                    # Normal skin (pal_id + 0)
                    btn_addr = p2_base + 0x2CFFF0 + pal_id * 32 + 2
                    k32.WriteProcessMemory(h_proc, ctypes.c_void_p(btn_addr), bytes(lspc_bytes_le), 30, ctypes.byref(written))
                    # MAX Mode Burst skin (pal_id + 3)
                    burst_addr = p2_base + 0x2CFFF0 + (pal_id + 3) * 32 + 2
                    k32.WriteProcessMemory(h_proc, ctypes.c_void_p(burst_addr), bytes(burst_bytes_le), 30, ctypes.byref(written))

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

                injected_total += 1

            char_info = next((c for c in CHARACTER_ROSTER if c["id"] == cid), None)
            cname = char_info["name_cn"] if char_info else f"0x{cid:02X}"
            target_desc = f"\u3010{cname}\u3011" if scope == "SINGLE" else f"\u5168\u5458 {injected_total} \u4f4d\u89d2\u8272"
            async_log(f"[\u5b9e\u65f6\u70ed\u66f4\u65b0] \u76ae\u80a4\u3010{theme_id}\u3011\u5df2\u6210\u529f\u5b9e\u65f6\u6ce8\u5165\u8fd0\u884c\u4e2d\u7684\u6e38\u620f (PID={pid}, {target_desc})\uff01\u753b\u9762\u5df2\u5373\u65f6\u53d8\u8272\uff01", "SUCCESS")
            return {
                "success": True,
                "running": True,
                "message": f"[\u5b9e\u65f6\u70ed\u66f4\u65b0] \u76ae\u80a4\u5df2\u5b9e\u65f6\u70ed\u66f4\u65b0\u5230\u6e38\u620f\u4e2d\uff01{target_desc}\u753b\u9762\u5df2\u5373\u523b\u53d8\u8272\uff01"
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
