#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KOF97 Mod Studio - Modern Webview Desktop Application.
Implements Design B (Dark Stage) with full two-way communication between
HTML5/CSS3 frontend and Python ROM hacking backend.

All comments, identifiers, and variables strictly follow 100% English specification (Rules.md).
"""

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
    {"id": 0x00, "name_cn": "草薙京", "name_en": "Kyo Kusanagi"},
    {"id": 0x01, "name_cn": "二阶堂红丸", "name_en": "Benimaru Nikaido"},
    {"id": 0x02, "name_cn": "大门五郎", "name_en": "Goro Daimon"},
    {"id": 0x03, "name_cn": "特瑞·伯加德", "name_en": "Terry Bogard"},
    {"id": 0x04, "name_cn": "安迪·伯加德", "name_en": "Andy Bogard"},
    {"id": 0x05, "name_cn": "东丈", "name_en": "Joe Higashi"},
    {"id": 0x06, "name_cn": "坂崎良", "name_en": "Ryo Sakazaki"},
    {"id": 0x07, "name_cn": "罗伯特·加西亚", "name_en": "Robert Garcia"},
    {"id": 0x08, "name_cn": "坂崎百合", "name_en": "Yuri Sakazaki"},
    {"id": 0x09, "name_cn": "莉安娜·哈迪兰", "name_en": "Leona Heidern"},
    {"id": 0x0A, "name_cn": "拉尔夫·琼斯", "name_en": "Ralf Jones"},
    {"id": 0x0B, "name_cn": "克拉克·斯提尔", "name_en": "Clark Still"},
    {"id": 0x0C, "name_cn": "麻宫雅典娜", "name_en": "Athena Asamiya"},
    {"id": 0x0D, "name_cn": "椎拳崇", "name_en": "Sie Kensou"},
    {"id": 0x0E, "name_cn": "镇元斋", "name_en": "Chin Gentsai"},
    {"id": 0x0F, "name_cn": "神乐千鹤", "name_en": "Chizuru Kagura"},
    {"id": 0x10, "name_cn": "不知火舞", "name_en": "Mai Shiranui"},
    {"id": 0x11, "name_cn": "琼", "name_en": "King"},
    {"id": 0x12, "name_cn": "金家藩", "name_en": "Kim Kaphwan"},
    {"id": 0x13, "name_cn": "陈国汉", "name_en": "Chang Koehan"},
    {"id": 0x14, "name_cn": "蔡宝奇", "name_en": "Choi Bounge"},
    {"id": 0x15, "name_cn": "七枷社", "name_en": "Yashiro Nanakase"},
    {"id": 0x16, "name_cn": "谢尔美", "name_en": "Shermie"},
    {"id": 0x17, "name_cn": "克里斯", "name_en": "Chris"},
    {"id": 0x18, "name_cn": "山崎龙二", "name_en": "Ryuji Yamazaki"},
    {"id": 0x19, "name_cn": "布鲁·玛丽", "name_en": "Blue Mary"},
    {"id": 0x1A, "name_cn": "比利·凯恩", "name_en": "Billy Kane"},
    {"id": 0x1B, "name_cn": "八神庵", "name_en": "Iori Yagami"},
    {"id": 0x1C, "name_cn": "矢吹真吾", "name_en": "Shingo Yabuki"},
    {"id": 0x1D, "name_cn": "暴走八神庵", "name_en": "Orochi Iori"},
    {"id": 0x1E, "name_cn": "暴走莉安娜", "name_en": "Orochi Leona"},
    {"id": 0x1F, "name_cn": "真七枷社", "name_en": "Orochi Yashiro"},
    {"id": 0x20, "name_cn": "真谢尔美", "name_en": "Orochi Shermie"},
    {"id": 0x21, "name_cn": "真克里斯", "name_en": "Orochi Chris"},
    {"id": 0x22, "name_cn": "大蛇", "name_en": "Orochi"},
    {"id": 0x23, "name_cn": "经典草薙京", "name_en": "'94 Kyo"},
]

PRESET_THEMES = [
    {
        "id": "classic",
        "name_cn": "原版经典",
        "colors": [
            "#FFF7B5", "#F7C584", "#EF945A", "#B55229",
            "#F7F7FF", "#BDBDC5", "#737B84",
            "#DE3A21", "#AD2910", "#7B1908", "#4A0000",
            "#3A3A4A", "#29293A", "#191929", "#000008",
        ],
    },
    {
        "id": "black_gold",
        "name_cn": "奢华黑金",
        "colors": [
            "#FFF7B5", "#F7C584", "#EF945A", "#B55229",
            "#4A4A4A", "#303030", "#181818",
            "#FFDE3A", "#DEAD19", "#A57308", "#634200",
            "#292929", "#1A1A1A", "#101010", "#000000",
        ],
    },
    {
        "id": "nether_purple",
        "name_cn": "幽冥暗紫",
        "colors": [
            "#FFF7B5", "#F7C584", "#EF945A", "#B55229",
            "#E6E0F5", "#B8AED4", "#7B6E9E",
            "#A855F7", "#7E22CE", "#581C87", "#3B0764",
            "#25202E", "#1A1622", "#100D16", "#000000",
        ],
    },
    {
        "id": "glacial_cyan",
        "name_cn": "极地幽蓝",
        "colors": [
            "#FFF7B5", "#F7C584", "#EF945A", "#B55229",
            "#F0F9FF", "#BAE6FD", "#7DD3FC",
            "#38BDF8", "#0284C7", "#0369A1", "#0C4A6E",
            "#1E293B", "#0F172A", "#080D1A", "#000000",
        ],
    },
    {
        "id": "silver_knight",
        "name_cn": "白银骑士",
        "colors": [
            "#FFF7B5", "#F7C584", "#EF945A", "#B55229",
            "#334155", "#1E293B", "#0F172A",
            "#EF4444", "#B91C1C", "#7F1D1D", "#450A0A",
            "#F1F5F9", "#CBD5E1", "#94A3B8", "#475569",
        ],
    },
    {
        "id": "emerald_ghost",
        "name_cn": "翡翠幽灵",
        "colors": [
            "#FFF7B5", "#F7C584", "#EF945A", "#B55229",
            "#ECFDF5", "#A7F3D0", "#6EE7B7",
            "#10B981", "#059669", "#047857", "#064E3B",
            "#14241B", "#0D1913", "#070E0A", "#000000",
        ],
    },
    {
        "id": "monochrome_ivory",
        "name_cn": "纯白誓约",
        "colors": [
            "#FFF7B5", "#F7C584", "#EF945A", "#B55229",
            "#F8FAFC", "#E2E8F0", "#CBD5E1",
            "#334155", "#1E293B", "#0F172A", "#020617",
            "#FFFFFF", "#E2E8F0", "#94A3B8", "#475569",
        ],
    },
    {
        "id": "solar_flare",
        "name_cn": "炽炎烈火",
        "colors": [
            "#FFF7B5", "#F7C584", "#EF945A", "#B55229",
            "#FFEDD5", "#FED7AA", "#FDBA74",
            "#F59E0B", "#D97706", "#B45309", "#78350F",
            "#2E2E38", "#1C1C24", "#101016", "#000000",
        ],
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


THEME_RAMPS: Dict[str, Dict[str, Any]] = {
    "black_gold": {
        "primary": ["#71717A", "#52525B", "#3F3F46", "#27272A", "#18181B", "#09090B"],
        "accent": ["#FFE55C", "#FFD700", "#D4AF37", "#997A15"],
        "light": ["#FFFFFF", "#F4F4F5"],
        "dark": ["#18181B", "#09090B", "#000000"],
    },
    "nether_purple": {
        "primary": ["#D8B4FE", "#C084FC", "#A855F7", "#7E22CE", "#581C87", "#3B0764"],
        "accent": ["#F3E8FF", "#E9D5FF", "#C084FC", "#7E22CE"],
        "light": ["#FAF5FF", "#E9D5FF"],
        "dark": ["#25202E", "#1A1622", "#0F0D16"],
    },
    "glacial_cyan": {
        "primary": ["#BAE6FD", "#7DD3FC", "#38BDF8", "#0284C7", "#0369A1", "#0C4A6E"],
        "accent": ["#E0F2FE", "#BAE6FD", "#38BDF8", "#0284C7"],
        "light": ["#F0F9FF", "#E0F2FE"],
        "dark": ["#1E293B", "#0F172A", "#080D1A"],
    },
    "silver_knight": {
        "primary": ["#F8FAFC", "#E2E8F0", "#CBD5E1", "#94A3B8", "#64748B", "#334155"],
        "accent": ["#F87171", "#EF4444", "#DC2626", "#991B1B"],
        "light": ["#FFFFFF", "#F1F5F9"],
        "dark": ["#1E293B", "#0F172A", "#020617"],
    },
    "emerald_ghost": {
        "primary": ["#A7F3D0", "#6EE7B7", "#10B981", "#059669", "#047857", "#064E3B"],
        "accent": ["#D1FAE5", "#A7F3D0", "#10B981", "#047857"],
        "light": ["#ECFDF5", "#D1FAE5"],
        "dark": ["#14241B", "#0D1913", "#070E0A"],
    },
    "monochrome_ivory": {
        "primary": ["#FFFFFF", "#F8FAFC", "#E2E8F0", "#CBD5E1", "#94A3B8", "#475569"],
        "accent": ["#334155", "#1E293B", "#0F172A", "#020617"],
        "light": ["#FFFFFF", "#F8FAFC"],
        "dark": ["#1E293B", "#0F172A", "#000000"],
    },
    "solar_flare": {
        "primary": ["#FED7AA", "#FDBA74", "#F59E0B", "#D97706", "#B45309", "#78350F"],
        "accent": ["#FEF08A", "#FACC15", "#EAB308", "#CA8A04"],
        "light": ["#FFF7ED", "#FFEDD5"],
        "dark": ["#2E2E38", "#1C1C24", "#101016"],
    },
}


def generate_harmonious_character_palette(
    cid: int,
    theme_id: str,
    p1_data: bytes,
    p2_clean: bytes,
) -> List[int]:
    """
    Generate harmonious 15-word LSPC2 palette for any character and theme.
    Preserves authentic skin tones and 3D luminance hierarchy to guarantee
    clear color blocking, clean shading, and professional aesthetics.
    """
    base_off = 0x483E + cid * 8
    pal_id = struct.unpack(">H", p1_data[base_off:base_off + 2])[0]
    p2_addr = 0x2CFFF0 + pal_id * 32
    orig_words = list(struct.unpack(">16H", p2_clean[p2_addr : p2_addr + 32])[1:])

    if theme_id == "classic":
        return orig_words

    theme = THEME_RAMPS.get(theme_id)
    if not theme:
        return orig_words

    # 1. Iori Yagami (0x1B): Use hand-tuned 4-part semantic preset
    if cid == 0x1B:
        preset = next((t for t in PRESET_THEMES if t["id"] == theme_id), None)
        if preset:
            return [hex_to_lspc2(h) for h in preset["colors"]]

    # 2. Goro Daimon (0x02):
    # W1..W5: Natural muscle skin tones (100% authentic SNK shading)
    # W6..W11: Judogi 6-step gradient ramp
    # W12: Headband accent
    # W13..W14: Light clogs / straps
    # W15: Black belt & outlines
    if cid == 0x02:
        res = list(orig_words[0:5])
        for h in theme["primary"]:
            res.append(encode_lspc2(*hex_to_rgb5(h)))
        res.append(encode_lspc2(*hex_to_rgb5(theme["accent"][1])))
        res.append(orig_words[12])
        res.append(orig_words[13])
        res.append(0x0000)
        return res

    # 3. Chang Koehan (0x13):
    # W1..W5: Natural face and body skin tones
    # W6..W10: Prison uniform 5-step gradient ramp
    # W11..W12: Iron ball & heavy chains
    # W13..W15: Natural dark beard & leather straps
    if cid == 0x13:
        res = list(orig_words[0:5])
        for h in theme["primary"][:5]:
            res.append(encode_lspc2(*hex_to_rgb5(h)))
        if theme_id == "black_gold":
            res.append(encode_lspc2(*hex_to_rgb5(theme["accent"][0])))
            res.append(encode_lspc2(*hex_to_rgb5(theme["accent"][2])))
        else:
            res.append(encode_lspc2(*hex_to_rgb5(theme["primary"][1])))
            res.append(encode_lspc2(*hex_to_rgb5(theme["primary"][4])))
        res.extend(orig_words[12:15])
        return res

    # 4. Universal character synthesis:
    # Preserve skin tones, keep dark outlines and white details,
    # map non-skin garment words to theme primary ramp preserving relative luminance.
    res = list(orig_words)
    non_skin_indices = []
    for i in range(15):
        w = orig_words[i]
        r, g, b, _ = decode_lspc2(w)
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        is_skin = (r >= g >= b and r >= 10 and r - b >= 3)
        if not is_skin and lum > 2 and not (lum >= 29 and abs(r - g) <= 2 and abs(g - b) <= 2):
            non_skin_indices.append((i, lum))

    non_skin_indices.sort(key=lambda x: x[1], reverse=True)
    n_ramp = len(theme["primary"])
    for rank, (idx, _) in enumerate(non_skin_indices):
        ramp_idx = min(round(rank * (n_ramp - 1) / max(1, len(non_skin_indices) - 1)), n_ramp - 1)
        hex_c = theme["primary"][ramp_idx]
        res[idx] = encode_lspc2(*hex_to_rgb5(hex_c))

    return res


def sync_character_portraits(
    cid: int,
    theme_id: str,
    base_pid: int,
    lspc_words: List[int],
    p2_data: bytearray,
    p2_clean: bytes,
) -> None:
    """
    Synchronize character select screen portrait and in-game HUD avatar palettes.
    In KOF97, portrait palettes reside at base_pid + 13, 14, 15.
    """
    if cid == 0x1B:
        # Iori Yagami: Avatar & Portrait Palettes
        c_high = lspc_words[7]
        c_mid = lspc_words[8]
        c_shad = lspc_words[9]
        c_deep = lspc_words[10]

        p2_data[0x2DF990 + 16: 0x2DF990 + 18] = struct.pack(">H", c_high)
        p2_data[0x2DF990 + 20: 0x2DF990 + 22] = struct.pack(">H", c_mid)
        p2_data[0x2DF990 + 22: 0x2DF990 + 24] = struct.pack(">H", c_shad)
        p2_data[0x2DF990 + 30: 0x2DF990 + 32] = struct.pack(">H", c_deep)

        p2_data[0x2DF9B0 + 14: 0x2DF9B0 + 16] = struct.pack(">H", c_high)
        p2_data[0x2DF9B0 + 16: 0x2DF9B0 + 18] = struct.pack(">H", c_mid)
        p2_data[0x2DF9B0 + 18: 0x2DF9B0 + 20] = struct.pack(">H", c_shad)

        p2_data[0x2DF9D0 + 12: 0x2DF9D0 + 14] = struct.pack(">H", c_high)
        p2_data[0x2DF9D0 + 14: 0x2DF9D0 + 16] = struct.pack(">H", c_mid)
        p2_data[0x2DF9D0 + 16: 0x2DF9D0 + 18] = struct.pack(">H", c_shad)
        p2_data[0x2DF9D0 + 28: 0x2DF9D0 + 30] = struct.pack(">H", c_high)

    elif cid == 0x02:
        # Goro Daimon: Judogi words in 0x2D3190 (397), 0x2D31B0 (398), 0x2D31D0 (399)
        judogi_bytes = struct.pack(">4H", *lspc_words[5:9])
        p2_data[0x2D3190 + 12: 0x2D3190 + 20] = judogi_bytes
        p2_data[0x2D31D0 + 12: 0x2D31D0 + 20] = judogi_bytes
        p2_data[0x2D31B0 + 14: 0x2D31B0 + 22] = judogi_bytes

    elif cid == 0x13:
        # Chang Koehan: Uniform words in 0x2DB990 (1485), 0x2DB9B0 (1486), 0x2DB9D0 (1487)
        u_bytes = struct.pack(">4H", *lspc_words[5:9])
        p2_data[0x2DB990 + 12: 0x2DB990 + 20] = u_bytes
        p2_data[0x2DB9B0 + 20: 0x2DB9B0 + 26] = struct.pack(">3H", *lspc_words[7:10])
        p2_data[0x2DB9D0 + 12: 0x2DB9D0 + 18] = struct.pack(">3H", *lspc_words[5:8])

    else:
        # Universal portrait update for select screen portrait (base_pid + 14)
        sel_pid = base_pid + 14
        sel_addr = 0x2CFFF0 + sel_pid * 32
        p_words = list(struct.unpack(">16H", p2_clean[sel_addr : sel_addr + 32]))
        for i in range(1, 16):
            orig_w = p_words[i]
            r, g, b, _ = decode_lspc2(orig_w)
            is_skin = (r >= g >= b and r >= 10 and r - b >= 3)
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            if not is_skin and 2 < lum < 28:
                p_words[i] = lspc_words[i - 1]
        p2_data[sel_addr : sel_addr + 32] = struct.pack(">16H", *p_words)


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
    print(f"[{level}] {message}")

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

        # Per-character skin store: char_id -> {"themeId": str, "colors": List[str]}
        self._character_skins: Dict[int, Dict[str, Any]] = {}
        classic_colors = list(PRESET_THEMES[0]["colors"])
        for char in CHARACTER_ROSTER:
            self._character_skins[char["id"]] = {
                "themeId": "classic",
                "colors": list(classic_colors),
            }

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
        async_log(f"选定目标角色: 【{cname}】 (ID=0x{char_id:02X})", "INFO")
        return {"success": True}

    def set_character_skin(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set skin for a single character or bulk set for all characters.
        Maintains independent per-character entries!
        """
        char_id = params.get("char_id", self._char_id)
        theme_id = params.get("theme_id", "classic")
        scope = params.get("scope", self._scope)
        custom_colors = params.get("colors")

        if not custom_colors or not isinstance(custom_colors, list):
            preset = next((t for t in PRESET_THEMES if t["id"] == theme_id), PRESET_THEMES[0])
            custom_colors = list(preset["colors"])

        if scope == "ALL":
            for cid in self._character_skins:
                self._character_skins[cid] = {
                    "themeId": theme_id,
                    "colors": list(custom_colors),
                }
            async_log(f"已全量设置全员 36 角色皮肤为: 【{theme_id}】", "INFO")
        else:
            self._character_skins[char_id] = {
                "themeId": theme_id,
                "colors": list(custom_colors),
            }
            char_info = next((c for c in CHARACTER_ROSTER if c["id"] == char_id), None)
            cname = char_info["name_cn"] if char_info else f"0x{char_id:02X}"
            async_log(f"已保存角色【{cname}】的独立皮肤配置: 【{theme_id}】", "INFO")

        return {"success": True}

    def update_scope(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update target application scope ('SINGLE' or 'ALL')."""
        self._scope = params.get("scope", "SINGLE")
        mode_str = "全员 36 位角色" if self._scope == "ALL" else "当前选定角色"
        async_log(f"应用范围已切换为: 【{mode_str}】", "INFO")
        return {"success": True}

    def update_combat_rule(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update guard crush or stun immunity."""
        rule = params.get("rule")
        val = bool(params.get("value", True))
        if rule == "guard":
            self._guard = val
            async_log(f"免破防机制已{'启用 (锁死 103 点)' if val else '关闭 (恢复原版扣减)'}", "INFO")
        elif rule == "stun":
            self._stun = val
            async_log(f"免眩晕机制已{'启用 (锁死 103 点)' if val else '关闭 (恢复原版扣减)'}", "INFO")
        return {"success": True}

    def update_damage_mode(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update damage multiplier option."""
        self._damage_mode = params.get("mode_id", "halved")
        async_log(f"受创伤害倍率已设置为: 【{self._damage_mode}】", "INFO")
        return {"success": True}

    def update_sync_avatar(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update whether portrait and HUD avatar should be synced."""
        self._sync_avatar = bool(params.get("sync", True))
        async_log(f"立绘与 HUD 小头像同步已{'开启' if self._sync_avatar else '关闭'}", "INFO")
        return {"success": True}

    def save_skin(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Save all characters skin configurations to memory state."""
        modded_count = sum(1 for cid, s in self._character_skins.items() if s.get("themeId") != "classic")
        async_log(f"全员 36 位角色配置已保存！当前共有 {modded_count} 位角色启用了定制配色方案。", "SUCCESS")
        return {"success": True, "msg": f"全员配置已保存 (定制角色: {modded_count} 位)"}

    # ------------------------------------------------------------------------
    # ROM Packaging Pipeline
    # ------------------------------------------------------------------------

    def pack_rom(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute property patching, per-character palette modification, and ROM packaging.
        Writes all customized character palettes to their respective ROM slots.
        """
        if not self._build_lock.acquire(blocking=False):
            return {"success": False, "error": "打包流水线正在运行中，请稍候"}

        try:
            async_log("=== 开始执行【打包Rom】全量流水线 ===", "INFO")

            # 1. Ensure unpacked files exist
            p1_path = self._workdir / "p1_be.bin"
            p2_path = self._workdir / "p2_be.bin"
            s1_path = self._workdir / "s1.bin"

            if not (p1_path.exists() and p2_path.exists() and s1_path.exists()):
                async_log("解包缓存不完整，正在从原生 ROM 自动解包...", "INFO")
                unpack_rom_set(self._source_zip, self._workdir)
                async_log("原生 ROM 解包完成。", "SUCCESS")

            p1_data = bytearray(p1_path.read_bytes())
            p2_data = bytearray(p2_path.read_bytes())

            if len(p1_data) != EXPECTED_SIZES["p1"]:
                raise ValueError(f"Invalid p1_be.bin size: {len(p1_data)}")
            if len(p2_data) != EXPECTED_SIZES["p2"]:
                raise ValueError(f"Invalid p2_be.bin size: {len(p2_data)}")

            # 2. Apply Combat & Defense Patches to p1_be.bin
            async_log("正在注入 68000 战斗与防御属性 Patch...", "INFO")

            # Guard Crush
            if self._guard:
                p1_data[0x01397E:0x013982] = bytes.fromhex("4e714e71")
                async_log("  [P1] 免破防: 0x01397E -> NOP; NOP (锁死 103 点)", "INFO")
            else:
                p1_data[0x01397E:0x013982] = bytes.fromhex("916c013e")
                async_log("  [P1] 恢复原版破防计算机制", "INFO")

            # Dizzy / Stun
            if self._stun:
                p1_data[0x0139A4:0x0139A8] = bytes.fromhex("4e714e71")
                async_log("  [P1] 免眩晕: 0x0139A4 -> NOP; NOP (锁死 103 点)", "INFO")
            else:
                p1_data[0x0139A4:0x0139A8] = bytes.fromhex("916c0146")
                async_log("  [P1] 恢复原版眩晕计算机制", "INFO")

            # Damage Multiplier Hook (Code Cave 0x000300)
            selected_mode = next((m for m in DAMAGE_MODES if m["id"] == self._damage_mode), DAMAGE_MODES[3])
            if self._damage_mode == "normal":
                p1_data[0x01394A:0x01394E] = selected_mode["hook"]
                p1_data[0x000300:0x000308] = bytes.fromhex("ffffffffffffffff")
                async_log("  [P1] 恢复 100% 原始受创伤害", "INFO")
            else:
                p1_data[0x01394A:0x01394E] = selected_mode["hook"]
                p1_data[0x000300:0x000308] = selected_mode["cave"]
                async_log(f"  [P1] 注入 Code Cave 伤害 Hook (模式: {self._damage_mode})", "INFO")

            p1_path.write_bytes(p1_data)

            # 3. Apply Palette & Skin for customized characters to p2_be.bin
            async_log("正在将定制角色的独立调色板方案写入 p2_be.bin...", "INFO")

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

                base_off = 0x483E + cid * 8
                base_pid = struct.unpack(">H", p1_data[base_off:base_off + 2])[0]

                # CRITICAL FIX 2: Only modify Button 0 (A) and Button 1 (B)!
                # Button 2 (C) and Button 3 (D) remain 100% original SNK colors for CPU / 2P enemies!
                for btn_idx in (0, 1):
                    btn_off = base_off + btn_idx * 2
                    pal_id = struct.unpack(">H", p1_data[btn_off:btn_off + 2])[0]
                    p2_addr = 0x2CFFF0 + pal_id * 32
                    p2_data[p2_addr + 2: p2_addr + 32] = lspc_bytes

                # CRITICAL FIX 3: Character select screen and HUD avatar synchronization!
                if self._sync_avatar:
                    sync_character_portraits(cid, theme_id, base_pid, lspc_words, p2_data, p2_clean)

                async_log(f"  [P2] 已为【{cname}】注入定制皮肤: 【{theme_id}】(仅覆盖 1P A/B 键，保留 CPU 敌人 C/D 键)", "INFO")

            async_log(f"  [P2] 调色板注入完成！共定制 {customized_count} 位角色，其余角色保持官方原版", "SUCCESS")
            p2_path.write_bytes(p2_data)

            # 4. Pack into kof97pls.zip with bswap16
            async_log("正在执行 bswap16 硬件字节序交换并重新压缩打包...", "INFO")
            pack_rom_set(self._workdir, self._output_zip)
            zip_crc = crc32_hex(self._output_zip.read_bytes())

            async_log("=== 打包流水线执行完毕！===", "SUCCESS")
            async_log(f"交付成果物: {self._output_zip.name} (CRC32: {zip_crc})", "SUCCESS")

            return {"success": True, "crc32": zip_crc}

        except Exception as exc:
            async_log(f"打包流水线异常中断: {exc}", "ERROR")
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
                    async_log("未检测到 output/roms/kof97pls.zip，正在自动触发打包...", "WARN")
                    res = self.pack_rom()
                    if not res.get("success"):
                        async_log("自动打包失败，启动中止。", "ERROR")
                        return

                exe_path = self._sandbox_dir / "WinKawaks.exe"
                if not exe_path.exists():
                    raise FileNotFoundError(f"未找到模拟器主程序: {exe_path}")

                async_log(f"正在启动沙盒模拟器 WinKawaks (挂载 RomPath1={self._output_zip.parent})...", "INFO")
                proc = start_sandbox_kawaks(self._sandbox_dir, rom_name="kof97pls", enable_bg_input=False)
                async_log(f"WinKawaks 模拟器已成功启动！(PID={proc.pid})，已施加内存反遮蔽 Patch！", "SUCCESS")
            except Exception as exc:
                async_log(f"启动模拟器失败: {exc}", "ERROR")

        threading.Thread(target=_launch, daemon=True).start()
        return {"success": True, "pid": 0}

    # ------------------------------------------------------------------------
    # Maintenance Actions
    # ------------------------------------------------------------------------

    def unpack_rom(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Trigger background unpack of native kof97.ZIP."""
        def _task() -> None:
            try:
                async_log("正在从原生 ROM 重新解包...", "INFO")
                rep = unpack_rom_set(self._source_zip, self._workdir)
                async_log(f"解包成功！共解包 {len(rep)} 个核心 ROM 镜像至 {self._workdir}", "SUCCESS")
            except Exception as exc:
                async_log(f"解包失败: {exc}", "ERROR")

        threading.Thread(target=_task, daemon=True).start()
        return {"success": True}

    def restore_baseline(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Trigger background restore of official baseline ROM."""
        def _task() -> None:
            try:
                async_log("正在构建官方原版风云再起基线包...", "INFO")
                # Reset all character skins to classic
                classic_colors = list(PRESET_THEMES[0]["colors"])
                for cid in self._character_skins:
                    self._character_skins[cid] = {
                        "themeId": "classic",
                        "colors": list(classic_colors),
                    }
                unpack_rom_set(self._source_zip, self._workdir)
                pack_rom_set(self._workdir, self._output_zip)
                async_log(f"基线包重置完成: {self._output_zip}，全员皮肤已恢复 SNK 原生默认", "SUCCESS")
            except Exception as exc:
                async_log(f"还原基线包失败: {exc}", "ERROR")

        threading.Thread(target=_task, daemon=True).start()
        return {"success": True}

    def run_self_test(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Trigger background execution of rom_tool self-test."""
        def _task() -> None:
            try:
                async_log("正在执行全局工具链自检 (bswap16 / LSPC2 / 瓦片测试)...", "INFO")
                script_path = PROJECT_ROOT / "tools" / "rom_tool.py"
                cmd = [sys.executable, str(script_path), "self-test"]
                res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
                if res.returncode == 0:
                    for line in res.stdout.strip().splitlines():
                        if line.strip():
                            async_log(line.strip(), "INFO")
                    async_log("[PASS] 全局自检 100% 通过！", "SUCCESS")
                else:
                    async_log(res.stderr.strip(), "ERROR")
            except Exception as exc:
                async_log(f"自检执行异常: {exc}", "ERROR")

        threading.Thread(target=_task, daemon=True).start()
        return {"success": True}

    def open_output_dir(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Open output roms directory in Windows File Explorer."""
        out_dir = self._output_zip.parent
        out_dir.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(str(out_dir))
            async_log(f"已打开输出目录: {out_dir}", "SUCCESS")
            return {"success": True}
        except Exception as exc:
            async_log(f"打开输出目录失败: {exc}", "ERROR")
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
        title="拳皇97 逆向魔改工作台 (KOF97 Mod Studio)",
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
