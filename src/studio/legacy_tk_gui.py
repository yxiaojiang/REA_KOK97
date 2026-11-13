#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KOF97 Mod Studio - Interactive Desktop GUI for KOF97 ROM Hacking.
Allows real-time property customization, 10 built-in color schemes,
custom palette creation, global character application, ROM packing,
and sandbox emulator launching.

All comments and variables in this file follow 100% English specification (Rules.md).
"""

import colorsys
import os
import random
import struct
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import tkinter as tk
from tkinter import colorchooser, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.rom.rom_tool import (
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

# 8 Curated Harmonious Preset Color Schemes
# All schemes strictly preserve original natural skin (Words 1..4)
# Upper body (Coat & Inner Shirt) and Lower body (Pants & Hair) use coherent color families
PRESET_THEMES = [
    {
        "id": "classic",
        "name_cn": "原版经典 (Original 1997)",
        "category": "官方原版",
        "desc": "SNK 官方原版正统：深渊紫黑风衣 + 纯白内衬 + 经典血月绯红发色与长裤",
        "upper_desc": "紫黑风衣 + 纯白内衬",
        "lower_desc": "经典血月绯红 (发色/长裤)",
        "upper_colors": ["#3A3A4A", "#29293A", "#191929", "#F7F7FF"],
        "lower_colors": ["#DE3A21", "#AD2910", "#7B1908", "#4A0000"],
        "coat_color": "#3A3A4A",
        "shirt_color": "#F7F7FF",
        "hair_color": "#DE3A21",
        "pants_color": "#AD2910",
        "shoes_color": "#191929",
        "colors": [
            "#FFF7B5", "#F7C584", "#EF945A", "#B55229",  # Skin (4) - 100% SNK Default
            "#F7F7FF", "#BDBDC5", "#737B84",              # Shirt (3) - Upper Body Inner
            "#DE3A21", "#AD2910", "#7B1908", "#4A0000",  # Pants/Hair (4) - Lower Body & Hair
            "#3A3A4A", "#29293A", "#191929", "#000008",  # Coat/Outline (4) - Upper Body Outer
        ],
    },
    {
        "id": "black_gold",
        "name_cn": "奢华黑金 (Obsidian & Gold)",
        "category": "经典奢华",
        "desc": "黑曜石极夜纯黑风衣 + 炭黑真丝内衬 + 璨金流光发色与金质长裤",
        "upper_desc": "极夜黑风衣 + 炭黑衬衫",
        "lower_desc": "璨金流光 (金色发丝/金质长裤)",
        "upper_colors": ["#292929", "#1A1A1A", "#101010", "#4A4A4A"],
        "lower_colors": ["#FFDE3A", "#DEAD19", "#A57308", "#634200"],
        "coat_color": "#212129",
        "shirt_color": "#3A3A3A",
        "hair_color": "#FFDE3A",
        "pants_color": "#DEAD19",
        "shoes_color": "#101010",
        "colors": [
            "#FFF7B5", "#F7C584", "#EF945A", "#B55229",  # Skin (4) - 100% Default
            "#4A4A4A", "#303030", "#181818",              # Shirt (3) - Charcoal Upper
            "#FFDE3A", "#DEAD19", "#A57308", "#634200",  # Hair/Pants (4) - Gold Lower
            "#292929", "#1A1A1A", "#101010", "#000000",  # Coat (4) - Obsidian Upper
        ],
    },
    {
        "id": "nether_purple",
        "name_cn": "幽冥暗紫 (Nether Royal Violet)",
        "category": "神秘魅影",
        "desc": "虚空幽黑战衣 + 浅灰紫真丝内衬 + 皇家紫罗兰发色与暗紫长裤",
        "upper_desc": "虚空幽黑 + 浅灰紫",
        "lower_desc": "皇家紫罗兰 (幻紫发色/暗紫长裤)",
        "upper_colors": ["#25202E", "#1A1622", "#100D16", "#E6E0F5"],
        "lower_colors": ["#A855F7", "#7E22CE", "#581C87", "#3B0764"],
        "coat_color": "#25202E",
        "shirt_color": "#E6E0F5",
        "hair_color": "#A855F7",
        "pants_color": "#7E22CE",
        "shoes_color": "#100D16",
        "colors": [
            "#FFF7B5", "#F7C584", "#EF945A", "#B55229",  # Skin (4) - Default
            "#E6E0F5", "#B8AED4", "#7B6E9E",              # Shirt (3) - Lavender
            "#A855F7", "#7E22CE", "#581C87", "#3B0764",  # Hair/Pants (4) - Royal Violet
            "#25202E", "#1A1622", "#100D16", "#000000",  # Coat (4) - Midnight Violet
        ],
    },
    {
        "id": "glacial_cyan",
        "name_cn": "极地幽蓝 (Glacial Navy & Cyan)",
        "category": "极寒素雅",
        "desc": "深渊藏青大衣 + 冰霜浅蓝衬衫 + 极光钻青发丝与冰蓝长裤",
        "upper_desc": "深渊藏青 + 冰霜浅蓝",
        "lower_desc": "极光钻青 (冰蓝发丝/极光长裤)",
        "upper_colors": ["#1E293B", "#0F172A", "#080D1A", "#F0F9FF"],
        "lower_colors": ["#38BDF8", "#0284C7", "#0369A1", "#0C4A6E"],
        "coat_color": "#1E293B",
        "shirt_color": "#F0F9FF",
        "hair_color": "#38BDF8",
        "pants_color": "#0284C7",
        "shoes_color": "#080D1A",
        "colors": [
            "#FFF7B5", "#F7C584", "#EF945A", "#B55229",  # Skin (4) - Default
            "#F0F9FF", "#BAE6FD", "#7DD3FC",              # Shirt (3) - Frost White
            "#38BDF8", "#0284C7", "#0369A1", "#0C4A6E",  # Hair/Pants (4) - Arctic Cyan
            "#1E293B", "#0F172A", "#080D1A", "#000000",  # Coat (4) - Marine Navy
        ],
    },
    {
        "id": "silver_knight",
        "name_cn": "白银骑士 (Silver & Crimson)",
        "category": "贵族骑士",
        "desc": "高贵白银风衣 + 铁灰内衬 + 猩红血月发丝与鲜红战袍长裤",
        "upper_desc": "高贵白银 + 铁灰内衬",
        "lower_desc": "猩红血月 (纯红发丝/猩红长裤)",
        "upper_colors": ["#F1F5F9", "#CBD5E1", "#94A3B8", "#334155"],
        "lower_colors": ["#EF4444", "#B91C1C", "#7F1D1D", "#450A0A"],
        "coat_color": "#CBD5E1",
        "shirt_color": "#334155",
        "hair_color": "#EF4444",
        "pants_color": "#B91C1C",
        "shoes_color": "#1E293B",
        "colors": [
            "#FFF7B5", "#F7C584", "#EF945A", "#B55229",  # Skin (4) - Default
            "#334155", "#1E293B", "#0F172A",              # Shirt (3) - Slate Grey
            "#EF4444", "#B91C1C", "#7F1D1D", "#450A0A",  # Hair/Pants (4) - Blood Crimson
            "#F1F5F9", "#CBD5E1", "#94A3B8", "#475569",  # Coat (4) - Silver/Platinum
        ],
    },
    {
        "id": "emerald_ghost",
        "name_cn": "翡翠幽灵 (Emerald & Forest)",
        "category": "自然森灵",
        "desc": "暗夜森绿风衣 + 薄荷淡绿衬衫 + 碧玉荧光发色与青玉长裤",
        "upper_desc": "暗夜森绿 + 薄荷淡绿",
        "lower_desc": "碧玉荧光 (翡翠绿发/青玉长裤)",
        "upper_colors": ["#14241B", "#0D1913", "#070E0A", "#ECFDF5"],
        "lower_colors": ["#10B981", "#059669", "#047857", "#064E3B"],
        "coat_color": "#14241B",
        "shirt_color": "#ECFDF5",
        "hair_color": "#10B981",
        "pants_color": "#059669",
        "shoes_color": "#070E0A",
        "colors": [
            "#FFF7B5", "#F7C584", "#EF945A", "#B55229",  # Skin (4) - Default
            "#ECFDF5", "#A7F3D0", "#6EE7B7",              # Shirt (3) - Pale Mint
            "#10B981", "#059669", "#047857", "#064E3B",  # Hair/Pants (4) - Emerald Jade
            "#14241B", "#0D1913", "#070E0A", "#000000",  # Coat (4) - Forest Moss
        ],
    },
    {
        "id": "monochrome_ivory",
        "name_cn": "纯白誓约 (Ivory & Obsidian)",
        "category": "极简黑白",
        "desc": "极简纯白风衣 + 浅灰真丝内衬 + 极夜石墨黑发色与纯黑长裤",
        "upper_desc": "极简纯白 + 浅灰内衬",
        "lower_desc": "极夜石墨黑 (黑曜石发/纯黑长裤)",
        "upper_colors": ["#FFFFFF", "#E2E8F0", "#94A3B8", "#F8FAFC"],
        "lower_colors": ["#334155", "#1E293B", "#0F172A", "#020617"],
        "coat_color": "#E2E8F0",
        "shirt_color": "#FFFFFF",
        "hair_color": "#334155",
        "pants_color": "#1E293B",
        "shoes_color": "#020617",
        "colors": [
            "#FFF7B5", "#F7C584", "#EF945A", "#B55229",  # Skin (4) - Default
            "#F8FAFC", "#E2E8F0", "#CBD5E1",              # Shirt (3) - Silk Ivory
            "#334155", "#1E293B", "#0F172A", "#020617",  # Hair/Pants (4) - Pitch Black
            "#FFFFFF", "#E2E8F0", "#94A3B8", "#475569",  # Coat (4) - Clean White
        ],
    },
    {
        "id": "solar_flare",
        "name_cn": "炽炎烈火 (Solar Amber & Charcoal)",
        "category": "热烈赤金",
        "desc": "玄武岩炭灰风衣 + 炽炎淡橙衬衣 + 烈阳赤金发色与金橙长裤",
        "upper_desc": "玄武岩炭灰 + 炽炎淡橙",
        "lower_desc": "烈阳赤金 (烈日金橙发/赤金长裤)",
        "upper_colors": ["#2E2E38", "#1C1C24", "#101016", "#FFEDD5"],
        "lower_colors": ["#F59E0B", "#D97706", "#B45309", "#78350F"],
        "coat_color": "#2E2E38",
        "shirt_color": "#FFEDD5",
        "hair_color": "#F59E0B",
        "pants_color": "#D97706",
        "shoes_color": "#101016",
        "colors": [
            "#FFF7B5", "#F7C584", "#EF945A", "#B55229",  # Skin (4) - Default
            "#FFEDD5", "#FDBA74", "#FB923C",              # Shirt (3) - Ember Orange
            "#F59E0B", "#D97706", "#B45309", "#78350F",  # Hair/Pants (4) - Solar Amber
            "#2E2E38", "#1C1C24", "#101016", "#000000",  # Coat (4) - Anthracite Charcoal
        ],
    },
]

# Color slot metadata for 15 sprite colors (Words 1 to 15)
SLOT_METADATA = [
    {"slot": 1, "group": "面部肤色", "name": "肤色高光", "hint": "面部/肌肉高光"},
    {"slot": 2, "group": "面部肤色", "name": "肤色主色", "hint": "面部/胸膛主肤色"},
    {"slot": 3, "group": "面部肤色", "name": "肤色阴影", "hint": "面部/肌肉阴影"},
    {"slot": 4, "group": "面部肤色", "name": "肤色深影", "hint": "轮廓极深阴影"},
    {"slot": 5, "group": "内衬饰品", "name": "内衬高光", "hint": "衬衣/手套高光"},
    {"slot": 6, "group": "内衬饰品", "name": "内衬主色", "hint": "衬衣/手套主色"},
    {"slot": 7, "group": "内衬饰品", "name": "内衬阴影", "hint": "内衬极深阴影"},
    {"slot": 8, "group": "主服发色", "name": "发色高光", "hint": "头发/主服/武器高光"},
    {"slot": 9, "group": "主服发色", "name": "发色主色", "hint": "头发/主服/武器主色"},
    {"slot": 10, "group": "主服发色", "name": "发色阴影", "hint": "发色/主服阴影"},
    {"slot": 11, "group": "主服发色", "name": "发色深底", "hint": "发色/主服深轮廓"},
    {"slot": 12, "group": "外套战甲", "name": "外套反光", "hint": "风衣/大身折角反光"},
    {"slot": 13, "group": "外套战甲", "name": "外套主色", "hint": "风衣/战袍大身主色"},
    {"slot": 14, "group": "外套战甲", "name": "外套褶皱", "hint": "风衣褶皱深阴影"},
    {"slot": 15, "group": "外套战甲", "name": "轮廓勾边", "hint": "大身外部纯黑勾边"},
]

# All 36 characters in KOF 97
CHARACTER_ROSTER = [
    {"id": 0x00, "name_cn": "草薙京 (Kyo)", "name_en": "Kyo Kusanagi"},
    {"id": 0x01, "name_cn": "二阶堂红丸 (Benimaru)", "name_en": "Benimaru Nikaido"},
    {"id": 0x02, "name_cn": "大门五郎 (Daimon)", "name_en": "Goro Daimon"},
    {"id": 0x03, "name_cn": "特瑞·伯加德 (Terry)", "name_en": "Terry Bogard"},
    {"id": 0x04, "name_cn": "安迪·伯加德 (Andy)", "name_en": "Andy Bogard"},
    {"id": 0x05, "name_cn": "东丈 (Joe)", "name_en": "Joe Higashi"},
    {"id": 0x06, "name_cn": "坂崎良 (Ryo)", "name_en": "Ryo Sakazaki"},
    {"id": 0x07, "name_cn": "罗伯特·加西亚 (Robert)", "name_en": "Robert Garcia"},
    {"id": 0x08, "name_cn": "坂崎百合 (Yuri)", "name_en": "Yuri Sakazaki"},
    {"id": 0x09, "name_cn": "莉安娜·哈迪兰 (Leona)", "name_en": "Leona Heidern"},
    {"id": 0x0A, "name_cn": "拉尔夫·琼斯 (Ralf)", "name_en": "Ralf Jones"},
    {"id": 0x0B, "name_cn": "克拉克·斯提尔 (Clark)", "name_en": "Clark Still"},
    {"id": 0x0C, "name_cn": "麻宫雅典娜 (Athena)", "name_en": "Athena Asamiya"},
    {"id": 0x0D, "name_cn": "椎拳崇 (Kensou)", "name_en": "Sie Kensou"},
    {"id": 0x0E, "name_cn": "镇元斋 (Chin)", "name_en": "Chin Gentsai"},
    {"id": 0x0F, "name_cn": "神乐千鹤 (Chizuru)", "name_en": "Chizuru Kagura"},
    {"id": 0x10, "name_cn": "不知火舞 (Mai)", "name_en": "Mai Shiranui"},
    {"id": 0x11, "name_cn": "琼 (King)", "name_en": "King"},
    {"id": 0x12, "name_cn": "金家藩 (Kim)", "name_en": "Kim Kaphwan"},
    {"id": 0x13, "name_cn": "陈国汉 (Chang)", "name_en": "Chang Koehan"},
    {"id": 0x14, "name_cn": "蔡宝奇 (Choi)", "name_en": "Choi Bounge"},
    {"id": 0x15, "name_cn": "七枷社 (Yashiro)", "name_en": "Yashiro Nanakase"},
    {"id": 0x16, "name_cn": "谢尔美 (Shermie)", "name_en": "Shermie"},
    {"id": 0x17, "name_cn": "克里斯 (Chris)", "name_en": "Chris"},
    {"id": 0x18, "name_cn": "山崎龙二 (Yamazaki)", "name_en": "Ryuji Yamazaki"},
    {"id": 0x19, "name_cn": "布鲁·玛丽 (Blue Mary)", "name_en": "Blue Mary"},
    {"id": 0x1A, "name_cn": "比利·凯恩 (Billy)", "name_en": "Billy Kane"},
    {"id": 0x1B, "name_cn": "八神庵 (Iori)", "name_en": "Iori Yagami"},
    {"id": 0x1C, "name_cn": "矢吹真吾 (Shingo)", "name_en": "Shingo Yabuki"},
    {"id": 0x1D, "name_cn": "暴走八神庵 (Orochi Iori)", "name_en": "Orochi Iori"},
    {"id": 0x1E, "name_cn": "暴走莉安娜 (Orochi Leona)", "name_en": "Orochi Leona"},
    {"id": 0x1F, "name_cn": "真七枷社 (Orochi Yashiro)", "name_en": "Orochi Yashiro"},
    {"id": 0x20, "name_cn": "真谢尔美 (Orochi Shermie)", "name_en": "Orochi Shermie"},
    {"id": 0x21, "name_cn": "真克里斯 (Orochi Chris)", "name_en": "Orochi Chris"},
    {"id": 0x22, "name_cn": "大蛇 (Orochi)", "name_en": "Orochi"},
    {"id": 0x23, "name_cn": "经典草薙京 ('94 Kyo)", "name_en": "'94 Kyo"},
]

# Damage multiplier options (Motorola 68000 Code Cave hook at 0x000300)
DAMAGE_MODES = [
    {
        "id": "halved",
        "name_cn": "受创减半 (50% 伤害 / 双倍生命 - 推荐)",
        "desc": "掉血除以2，格斗手感极佳，容错率倍增",
        "hook": bytes.fromhex("4eb80300"),
        "cave": bytes.fromhex("e248d16c013a4e75"),
    },
    {
        "id": "quarter",
        "name_cn": "受创 1/4 (25% 伤害 / 四倍生命)",
        "desc": "掉血除以4，耐打度极高",
        "hook": bytes.fromhex("4eb80300"),
        "cave": bytes.fromhex("e448d16c013a4e75"),
    },
    {
        "id": "eighth",
        "name_cn": "受创 1/8 (12.5% 伤害 / 八倍生命)",
        "desc": "掉血除以8，肉盾坦克级别",
        "hook": bytes.fromhex("4eb80300"),
        "cave": bytes.fromhex("e648d16c013a4e75"),
    },
    {
        "id": "normal",
        "name_cn": "正常伤害 (100% 原始受创)",
        "desc": "保持原版掉血速度，无任何修改",
        "hook": bytes.fromhex("d16c013a"),
        "cave": bytes.fromhex("ffffffffffffffff"),
    },
    {
        "id": "hell",
        "name_cn": "受创翻倍 (200% 伤害 / 地狱模式)",
        "desc": "受到伤害翻倍，两连招即可暴毙",
        "hook": bytes.fromhex("4eb80300"),
        "cave": bytes.fromhex("e348d16c013a4e75"),
    },
    {
        "id": "god",
        "name_cn": "完全无敌 (0% 伤害 / 锁血神模式)",
        "desc": "掉血量直接清零，受击绝不减血",
        "hook": bytes.fromhex("4eb80300"),
        "cave": bytes.fromhex("4240d16c013a4e75"),
    },
]


# ============================================================================
# Color & Palette Conversion Utilities
# ============================================================================

def hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    """Convert #RRGGBB hex string to (r, g, b) tuple 0..255."""
    clean = hex_code.strip().lstrip("#")
    if len(clean) != 6:
        return 0, 0, 0
    try:
        r = int(clean[0:2], 16)
        g = int(clean[2:4], 16)
        b = int(clean[4:6], 16)
        return r, g, b
    except ValueError:
        return 0, 0, 0


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert (r, g, b) tuple 0..255 to #RRGGBB hex string."""
    r = max(0, min(255, int(r)))
    g = max(0, min(255, int(g)))
    b = max(0, min(255, int(b)))
    return f"#{r:02X}{g:02X}{b:02X}"


def hex_to_lspc2(hex_code: str) -> int:
    """Convert #RRGGBB hex string to 16-bit Neo-Geo LSPC2-A2 word."""
    r, g, b = hex_to_rgb(hex_code)
    r5 = round(r * 31 / 255)
    g5 = round(g * 31 / 255)
    b5 = round(b * 31 / 255)
    return encode_lspc2(r5, g5, b5, dark=0)


def lspc2_to_hex(word: int) -> str:
    """Convert 16-bit Neo-Geo LSPC2-A2 word to #RRGGBB hex string."""
    r5, g5, b5, _ = decode_lspc2(word)
    r = round(r5 * 255 / 31)
    g = round(g5 * 255 / 31)
    b = round(b5 * 255 / 31)
    return rgb_to_hex(r, g, b)


def get_contrasting_text_color(hex_code: str) -> str:
    """Determine whether black or white text is more legible on hex_code."""
    r, g, b = hex_to_rgb(hex_code)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#000000" if luminance > 0.55 else "#FFFFFF"


# ============================================================================
# Reusable Scrollable Frame Component
# ============================================================================

class ScrollableFrame(ttk.Frame):
    """
    A vertically scrollable frame that ensures components never get cut off
    when font size is doubled, providing smooth mouse wheel interaction.
    """

    def __init__(self, parent: tk.Widget, bg_color: str = "#21262D", *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        self.canvas = tk.Canvas(self, bg=bg_color, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.content = ttk.Frame(self.canvas, style="Card.TFrame")

        self.content.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_window = self.canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<Enter>", lambda _: self.canvas.bind_all("<MouseWheel>", self._on_mousewheel))
        self.canvas.bind("<Leave>", lambda _: self.canvas.unbind_all("<MouseWheel>"))

    def _on_canvas_configure(self, event: tk.Event) -> None:
        """Keep inner frame width matched to the canvas viewport width."""
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event: tk.Event) -> None:
        """Handle vertical mousewheel scroll on Windows."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


# ============================================================================
# Main Studio GUI Application
# ============================================================================

class KOF97ModStudioGUI(tk.Tk):
    """
    Main Tkinter application window for KOF97 ROM Modding Studio.
    """

    def __init__(self) -> None:
        super().__init__()

        # High DPI awareness for Windows
        self._enable_high_dpi()

        # Dynamic window size configuration for 2x enlarged font scale
        self.title("拳皇97 (KOF 97) 逆向魔改工作台 - KOF97 Mod Studio")
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        win_w = min(1480, max(1200, int(screen_w * 0.94)))
        win_h = min(820, max(680, int(screen_h * 0.88)))
        pos_x = max(0, (screen_w - win_w) // 2)
        pos_y = max(0, (screen_h - win_h) // 2 - 15)
        self.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")
        self.minsize(1150, 680)

        # Workspace paths
        self.workdir = DEFAULT_UNPACK_DIR
        self.output_zip = DEFAULT_OUTPUT_ZIP
        self.source_zip = DEFAULT_KOF97_ZIP
        self.sandbox_dir = DEFAULT_SANDBOX_DIR

        # State variables
        self.current_theme_id = tk.StringVar(value="classic")
        self.target_mode = tk.StringVar(value="SINGLE")  # Default to SINGLE character modification
        self.selected_char_id = tk.IntVar(value=0x1B)  # Default: Iori Yagami (0x1B)
        self.apply_all_buttons = tk.BooleanVar(value=True)
        self.sync_avatar_portraits = tk.BooleanVar(value=True)

        # Combat & defense properties
        self.opt_guard_crush = tk.BooleanVar(value=True)
        self.opt_dizzy_stun = tk.BooleanVar(value=True)
        self.opt_damage_mode = tk.StringVar(value="halved")

        # 15 Custom color variables (#RRGGBB)
        self.slot_hex_vars: List[tk.StringVar] = []
        for c in PRESET_THEMES[0]["colors"]:
            self.slot_hex_vars.append(tk.StringVar(value=c))

        # Color preview buttons
        self.slot_buttons: List[tk.Button] = []
        self.slot_lspc_labels: List[tk.Label] = []
        self.preview_rects: List[int] = []

        # Lock for async operations
        self.build_lock = threading.Lock()

        # Build UI layout: top banner, bottom action bar, console logger, and middle notebook
        self._apply_dark_theme_styles()
        self._create_header_banner()
        self._create_bottom_action_bar()
        self._create_console_logger()
        self._create_main_notebook()

        # Initial status refresh
        self.after(100, self._initial_health_check)

    def _enable_high_dpi(self) -> None:
        """Enable DPI awareness on Windows to prevent blurriness."""
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                import ctypes
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

    def _apply_dark_theme_styles(self) -> None:
        """Configure ttk modern dark arcade styling with 2x enlarged fonts."""
        self.configure(bg="#16181D")
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Global option database for Combobox and popup menus
        self.option_add("*TCombobox*Listbox.font", ("Microsoft YaHei UI", 15))
        self.option_add("*Font", ("Microsoft YaHei UI", 15))

        # Configure style colors with doubled font scale (base 15~16pt)
        style.configure(".", background="#16181D", foreground="#E6EDF3", font=("Microsoft YaHei UI", 15))
        style.configure("TFrame", background="#16181D")
        style.configure("Card.TFrame", background="#21262D", relief="solid", borderwidth=1)
        style.configure("TLabel", background="#16181D", foreground="#E6EDF3", font=("Microsoft YaHei UI", 15))
        style.configure("Card.TLabel", background="#21262D", foreground="#E6EDF3", font=("Microsoft YaHei UI", 15))
        style.configure("Muted.TLabel", foreground="#8B949E", font=("Microsoft YaHei UI", 13))
        style.configure("CardMuted.TLabel", background="#21262D", foreground="#8B949E", font=("Microsoft YaHei UI", 13))

        style.configure("TNotebook", background="#16181D", tabmargins=[4, 6, 4, 0])
        style.configure("TNotebook.Tab", background="#21262D", foreground="#8B949E", padding=[22, 8], font=("Microsoft YaHei UI", 16, "bold"))
        style.map("TNotebook.Tab",
                  background=[("selected", "#30363D"), ("active", "#282E38")],
                  foreground=[("selected", "#58A6FF"), ("active", "#C9D1D9")])

        style.configure("TCheckbutton", background="#21262D", foreground="#E6EDF3", font=("Microsoft YaHei UI", 15))
        style.map("TCheckbutton", background=[("active", "#21262D")])
        style.configure("TRadiobutton", background="#21262D", foreground="#E6EDF3", font=("Microsoft YaHei UI", 15))
        style.map("TRadiobutton", background=[("active", "#21262D")])

        style.configure("TCombobox", fieldbackground="#16181D", background="#30363D", foreground="#E6EDF3", arrowcolor="#58A6FF", font=("Microsoft YaHei UI", 15))
        style.map("TCombobox", fieldbackground=[("readonly", "#16181D")], foreground=[("readonly", "#E6EDF3")])

    def _create_header_banner(self) -> None:
        """Create top banner with project title and status indicator."""
        banner = tk.Frame(self, bg="#0D1117", padx=20, pady=8)
        banner.pack(fill="x", side="top")

        left_box = tk.Frame(banner, bg="#0D1117")
        left_box.pack(side="left", fill="y")

        lbl_title = tk.Label(
            left_box,
            text="拳皇97 (KOF 97) 逆向魔改工作台",
            font=("Microsoft YaHei UI", 20, "bold"),
            bg="#0D1117",
            fg="#58A6FF",
        )
        lbl_title.pack(anchor="w")

        lbl_sub = tk.Label(
            left_box,
            text="ROM 核心参数实时修改 · 10套内置炫彩皮肤 · 全员调色板定制 · 一键打包 · 沙盒秒启",
            font=("Microsoft YaHei UI", 13),
            bg="#0D1117",
            fg="#8B949E",
        )
        lbl_sub.pack(anchor="w", pady=(2, 0))

        right_box = tk.Frame(banner, bg="#0D1117")
        right_box.pack(side="right", fill="y")

        self.lbl_status_badge = tk.Label(
            right_box,
            text="正在检测 ROM 状态...",
            font=("Microsoft YaHei UI", 14, "bold"),
            bg="#21262D",
            fg="#F0883E",
            padx=14,
            pady=6,
            relief="groove",
        )
        self.lbl_status_badge.pack(side="right", pady=4)

    def _create_main_notebook(self) -> None:
        """Create 3-tab notebook for Palettes, Combat, and Engine."""
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=4)

        # Tab 1: Skin & Palette Studio
        self.tab_palette = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_palette, text="  🎨 皮肤与调色板定制  ")
        self._build_palette_tab(self.tab_palette)

        # Tab 2: Combat & Defense Properties
        self.tab_combat = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_combat, text="  ⚔️ 战斗与防御属性  ")
        self._build_combat_tab(self.tab_combat)

        # Tab 3: Engine Environment & Diagnostics
        self.tab_engine = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_engine, text="  ⚙️ 工程环境与诊断  ")
        self._build_engine_tab(self.tab_engine)

    # ------------------------------------------------------------------------
    # Tab 1: Clean Stylized Skin Studio with Center Preview
    # ------------------------------------------------------------------------
    def _build_palette_tab(self, parent: ttk.Frame) -> None:
        """Construct Tab 1: Clean, Stylized Character Skin Studio with Center Preview."""
        container = ttk.Frame(parent)
        container.pack(fill="both", expand=True, padx=6, pady=6)

        # 1. Left Column: Target & Actions & Combat Defenses (~310px)
        left_scroll = ScrollableFrame(container, bg_color="#21262D", width=310, style="Card.TFrame")
        left_scroll.pack(side="left", fill="both", padx=(0, 6))
        left_scroll.pack_propagate(False)
        left_pane = left_scroll.content

        lbl_target_title = ttk.Label(left_pane, text="1. 目标角色与范围", style="Card.TLabel", font=("Microsoft YaHei UI", 16, "bold"))
        lbl_target_title.pack(anchor="w", padx=8, pady=(8, 4))

        self.cbo_character = ttk.Combobox(
            left_pane,
            values=[f"{c['name_cn']} (0x{c['id']:02X})" for c in CHARACTER_ROSTER],
            state="readonly",
            font=("Microsoft YaHei UI", 14),
        )
        self.cbo_character.current(27)  # Iori Yagami
        self.cbo_character.pack(fill="x", padx=8, pady=(0, 6))
        self.cbo_character.bind("<<ComboboxSelected>>", self._on_character_changed)

        rb_single = ttk.Radiobutton(
            left_pane,
            text="👤 仅应用在当前选定角色 (推荐)",
            variable=self.target_mode,
            value="SINGLE",
            command=self._on_target_mode_changed,
        )
        rb_single.pack(anchor="w", padx=8, pady=2)

        rb_all = ttk.Radiobutton(
            left_pane,
            text="🌟 批量应用在全员 36 位角色",
            variable=self.target_mode,
            value="ALL",
            command=self._on_target_mode_changed,
        )
        rb_all.pack(anchor="w", padx=8, pady=2)

        ttk.Separator(left_pane, orient="horizontal").pack(fill="x", padx=8, pady=8)

        lbl_act_title = ttk.Label(left_pane, text="2. 核心控制操作", style="Card.TLabel", font=("Microsoft YaHei UI", 16, "bold"))
        lbl_act_title.pack(anchor="w", padx=8, pady=(0, 4))

        btn_save = tk.Button(
            left_pane,
            text="💾 保存当前皮肤至 ROM",
            bg="#1F6FEB",
            fg="#FFFFFF",
            activebackground="#388BFD",
            activeforeground="#FFFFFF",
            relief="flat",
            font=("Microsoft YaHei UI", 13, "bold"),
            pady=7,
            command=self._on_click_pack_rom,
        )
        btn_save.pack(fill="x", padx=8, pady=3)

        btn_restore = tk.Button(
            left_pane,
            text="🔄 恢复全员原版皮肤",
            bg="#D29922",
            fg="#16181D",
            activebackground="#E3B341",
            activeforeground="#000000",
            relief="flat",
            font=("Microsoft YaHei UI", 13, "bold"),
            pady=6,
            command=self._restore_all_default_rom_skins,
        )
        btn_restore.pack(fill="x", padx=8, pady=3)

        btn_launch = tk.Button(
            left_pane,
            text="🚀 启动 WinKawaks 实机对战",
            bg="#238636",
            fg="#FFFFFF",
            activebackground="#2EA043",
            activeforeground="#FFFFFF",
            relief="flat",
            font=("Microsoft YaHei UI", 13, "bold"),
            pady=6,
            command=self._on_click_start_game,
        )
        btn_launch.pack(fill="x", padx=8, pady=3)

        ttk.Separator(left_pane, orient="horizontal").pack(fill="x", padx=8, pady=8)

        lbl_combat_title = ttk.Label(left_pane, text="3. 战斗机制加护", style="Card.TLabel", font=("Microsoft YaHei UI", 16, "bold"))
        lbl_combat_title.pack(anchor="w", padx=8, pady=(0, 4))

        chk_dmg = ttk.Checkbutton(left_pane, text="受创减半 (50% 伤害 / 双倍生命)", variable=self.opt_damage_mode, onvalue="halved", offvalue="normal")
        chk_dmg.pack(anchor="w", padx=8, pady=2)

        chk_guard = ttk.Checkbutton(left_pane, text="免破防 (Guard 锁死 103 点)", variable=self.opt_guard_crush)
        chk_guard.pack(anchor="w", padx=8, pady=2)

        chk_stun = ttk.Checkbutton(left_pane, text="免眩晕 (Stun 锁死 103 点)", variable=self.opt_dizzy_stun)
        chk_stun.pack(anchor="w", padx=8, pady=2)

        chk_avatar = ttk.Checkbutton(left_pane, text="同步选人立绘与 HUD 小头像", variable=self.sync_avatar_portraits)
        chk_avatar.pack(anchor="w", padx=8, pady=2)


        # 2. Center Column: Real-Time Character Stage (~460px)
        center_pane = ttk.Frame(container, style="Card.TFrame", padding=10)
        center_pane.pack(side="left", fill="both", expand=True, padx=4)

        c_head = ttk.Frame(center_pane, style="Card.TFrame")
        c_head.pack(fill="x", pady=(0, 4))

        self.lbl_char_preview_title = ttk.Label(
            c_head,
            text="八神 庵 (Iori Yagami) · 实时立绘全景预览",
            style="Card.TLabel",
            font=("Microsoft YaHei UI", 16, "bold"),
        )
        self.lbl_char_preview_title.pack(side="left")

        self.lbl_active_theme_badge = tk.Label(
            c_head,
            text="原版经典 (Original)",
            font=("Microsoft YaHei UI", 12, "bold"),
            bg="#1F2A37",
            fg="#58A6FF",
            padx=8,
            pady=3,
            relief="solid",
            bd=1,
        )
        self.lbl_active_theme_badge.pack(side="right")

        # Interactive Canvas for Character Preview
        self.canvas_char = tk.Canvas(
            center_pane,
            bg="#0B0F17",
            highlightthickness=1,
            highlightbackground="#30363D",
            width=360,
            height=430,
        )
        self.canvas_char.pack(fill="both", expand=True, pady=4)

        # Draw character model elements on Canvas
        self._init_character_canvas_items()

        # Bottom Color Harmony Indicators
        harmony_bar = tk.Frame(center_pane, bg="#16181D", bd=1, relief="solid", padx=8, pady=6)
        harmony_bar.pack(fill="x", pady=(4, 0))

        tk.Label(harmony_bar, text="上身:", font=("Microsoft YaHei UI", 12, "bold"), bg="#16181D", fg="#8B949E").pack(side="left")
        self.swatch_coat = tk.Label(harmony_bar, text="  ", bg="#3A3A4A", width=2, height=1, relief="solid", bd=1)
        self.swatch_coat.pack(side="left", padx=2)
        self.swatch_shirt = tk.Label(harmony_bar, text="  ", bg="#F7F7FF", width=2, height=1, relief="solid", bd=1)
        self.swatch_shirt.pack(side="left", padx=2)
        self.lbl_upper_desc = tk.Label(harmony_bar, text="深渊紫黑 / 纯白", font=("Microsoft YaHei UI", 11), bg="#16181D", fg="#E6EDF3")
        self.lbl_upper_desc.pack(side="left", padx=(2, 6))

        tk.Label(harmony_bar, text="下身/发:", font=("Microsoft YaHei UI", 12, "bold"), bg="#16181D", fg="#8B949E").pack(side="left")
        self.swatch_hair = tk.Label(harmony_bar, text="  ", bg="#DE3A21", width=2, height=1, relief="solid", bd=1)
        self.swatch_hair.pack(side="left", padx=2)
        self.swatch_pants = tk.Label(harmony_bar, text="  ", bg="#AD2910", width=2, height=1, relief="solid", bd=1)
        self.swatch_pants.pack(side="left", padx=2)
        self.lbl_lower_desc = tk.Label(harmony_bar, text="经典血月绯红", font=("Microsoft YaHei UI", 11), bg="#16181D", fg="#E6EDF3")
        self.lbl_lower_desc.pack(side="left", padx=(2, 6))

        tk.Label(
            harmony_bar,
            text="✓ 原生肤色锁死",
            font=("Microsoft YaHei UI", 11, "bold"),
            bg="#16181D",
            fg="#3FB950",
        ).pack(side="right")


        # 3. Right Column: Curated Harmonious Preset Library (~380px)
        right_scroll = ScrollableFrame(container, bg_color="#21262D", width=380, style="Card.TFrame")
        right_scroll.pack(side="right", fill="both", padx=(4, 0))
        right_pane = right_scroll.content

        lbl_lib_title = ttk.Label(right_pane, text="和谐预设皮肤库 (8套精选)", style="Card.TLabel", font=("Microsoft YaHei UI", 16, "bold"))
        lbl_lib_title.pack(anchor="w", padx=8, pady=(8, 2))
        lbl_lib_sub = ttk.Label(
            right_pane,
            text="已彻底去除杂乱16色板。上身为统一相近色，下身为统一相近色，肤色严格保持原版默认。",
            style="CardMuted.TLabel",
            wraplength=350,
            font=("Microsoft YaHei UI", 12),
        )
        lbl_lib_sub.pack(anchor="w", padx=8, pady=(0, 6))

        self.preset_card_frames: List[tk.Frame] = []
        for idx, theme in enumerate(PRESET_THEMES):
            card = tk.Frame(right_pane, bg="#16181D", bd=1, relief="solid", padx=8, pady=6, cursor="hand2")
            card.pack(fill="x", padx=6, pady=4)
            self.preset_card_frames.append(card)

            r1 = tk.Frame(card, bg="#16181D")
            r1.pack(fill="x")
            lbl_name = tk.Label(r1, text=theme["name_cn"], font=("Microsoft YaHei UI", 13, "bold"), bg="#16181D", fg="#E6EDF3")
            lbl_name.pack(side="left")
            lbl_cat = tk.Label(r1, text=f"[{theme['category']}]", font=("Microsoft YaHei UI", 11), bg="#16181D", fg="#8B949E")
            lbl_cat.pack(side="right")

            r2 = tk.Frame(card, bg="#16181D")
            r2.pack(fill="x", pady=2)
            lbl_desc = tk.Label(r2, text=theme["desc"], font=("Microsoft YaHei UI", 11), bg="#16181D", fg="#8B949E", wraplength=340, justify="left")
            lbl_desc.pack(anchor="w")

            r3 = tk.Frame(card, bg="#16181D")
            r3.pack(fill="x", pady=(2, 0))

            tk.Label(r3, text="上身:", font=("Microsoft YaHei UI", 11), bg="#16181D", fg="#8B949E").pack(side="left")
            for c in theme["upper_colors"][:3]:
                tk.Label(r3, text="  ", bg=c, width=2, height=1, relief="solid", bd=1).pack(side="left", padx=1)

            tk.Label(r3, text=" 下身/发:", font=("Microsoft YaHei UI", 11), bg="#16181D", fg="#8B949E").pack(side="left", padx=(4, 0))
            for c in theme["lower_colors"][:3]:
                tk.Label(r3, text="  ", bg=c, width=2, height=1, relief="solid", bd=1).pack(side="left", padx=1)

            tid = theme["id"]
            for widget in (card, r1, r2, r3, lbl_name, lbl_cat, lbl_desc):
                widget.bind("<Button-1>", lambda e, t=tid: self._load_preset_by_id(t))

        self._load_preset_by_id("classic")

    # ------------------------------------------------------------------------
    # Tab 2: Combat & Defense Properties
    # ------------------------------------------------------------------------
    def _build_combat_tab(self, parent: ttk.Frame) -> None:
        """Construct Tab 2: Combat & Defense Attributes Customizer."""
        scroll = ScrollableFrame(parent, bg_color="#16181D", style="TFrame")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)
        container = scroll.content

        # Section: P-ROM Static Defense Immunities
        c1 = ttk.Frame(container, style="Card.TFrame", padding=16)
        c1.pack(fill="x", padx=6, pady=(0, 12))

        ttk.Label(c1, text="🛡️ P-ROM 68000 战斗防御机制强化", style="Card.TLabel", font=("Microsoft YaHei UI", 18, "bold")).pack(anchor="w", pady=(0, 8))
        ttk.Label(
            c1,
            text="通过对 68000 主程序大端指令实施静态 Patch，彻底消除战斗受限状态（满槽值为 103 点）。",
            style="CardMuted.TLabel",
            font=("Microsoft YaHei UI", 14),
        ).pack(anchor="w", pady=(0, 10))

        chk_guard = ttk.Checkbutton(
            c1,
            text="免破防 (Guard Crush Immunity) - 拦截 0x01397E 处 SUB 指令为 NOP，破防槽恒定 103 点",
            variable=self.opt_guard_crush,
        )
        chk_guard.pack(anchor="w", pady=5)

        chk_dizzy = ttk.Checkbutton(
            c1,
            text="免眩晕 (Dizzy/Stun Immunity) - 拦截 0x0139A4 处 SUB 指令为 NOP，眩晕槽恒定 103 点",
            variable=self.opt_dizzy_stun,
        )
        chk_dizzy.pack(anchor="w", pady=5)

        # Section: Damage Multiplier & Code Cave
        c2 = ttk.Frame(container, style="Card.TFrame", padding=16)
        c2.pack(fill="x", padx=6, pady=(0, 12))

        ttk.Label(c2, text="🩸 角色受创伤害倍率调节 (Code Cave 0x000300 安全注入)", style="Card.TLabel", font=("Microsoft YaHei UI", 18, "bold")).pack(anchor="w", pady=(0, 8))
        ttk.Label(
            c2,
            text="在 0x01394A 掉血累加点切入短寻址跳转 JSR ($0300).W，在未使用的 Code Cave 注入位移指令：",
            style="CardMuted.TLabel",
            font=("Microsoft YaHei UI", 14),
        ).pack(anchor="w", pady=(0, 10))

        for mode in DAMAGE_MODES:
            row = ttk.Frame(c2, style="Card.TFrame")
            row.pack(fill="x", pady=4)

            rb = ttk.Radiobutton(
                row,
                text=mode["name_cn"],
                variable=self.opt_damage_mode,
                value=mode["id"],
            )
            rb.pack(side="left")

            lbl_d = ttk.Label(row, text=f"— {mode['desc']}", style="CardMuted.TLabel", font=("Microsoft YaHei UI", 14))
            lbl_d.pack(side="left", padx=10)

        # Section: Architectural Safeguards Notice
        c3 = ttk.Frame(container, style="Card.TFrame", padding=16)
        c3.pack(fill="x", padx=6)

        ttk.Label(c3, text="🔒 架构合规与零崩溃保证 (Rules.md Compliance)", style="Card.TLabel", font=("Microsoft YaHei UI", 16, "bold")).pack(anchor="w", pady=(0, 6))
        rules_text = (
            "• 偶数地址对齐：所有 68000 指令严格按照 2 字节（Word）对齐，绝不产生 Address Error 异常；\n"
            "• 字节序无损转换：开发态使用 68000 大端序，打包时自动执行硬件 bswap16 恢复磁盘镜像；\n"
            "• 资产安全隔离：宿主原生 ROM 目录绝对只读，所有构建与沙盒挂载均在工作区隔离沙盒进行。"
        )
        ttk.Label(c3, text=rules_text, style="CardMuted.TLabel", font=("Microsoft YaHei UI", 13), justify="left").pack(anchor="w")

    # ------------------------------------------------------------------------
    # Tab 3: Engine Paths & Diagnostics
    # ------------------------------------------------------------------------
    def _build_engine_tab(self, parent: ttk.Frame) -> None:
        """Construct Tab 3: Environment, Paths & Diagnostics."""
        scroll = ScrollableFrame(parent, bg_color="#16181D", style="TFrame")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)
        container = scroll.content

        card = ttk.Frame(container, style="Card.TFrame", padding=16)
        card.pack(fill="x", padx=6, pady=(0, 12))

        ttk.Label(card, text="📁 工程目录与资产配置", style="Card.TLabel", font=("Microsoft YaHei UI", 18, "bold")).pack(anchor="w", pady=(0, 10))

        paths_info = [
            ("原生只读资产", str(self.source_zip), "共享 40MB C-ROM、音频与 BIOS（绝对只读）"),
            ("解包工作目录", str(self.workdir), "存放 68K 大端序二进制 p1_be.bin / p2_be.bin"),
            ("交付魔改输出", str(self.output_zip), "WinKawaks 优先载入的定制 kof97pls.zip"),
            ("模拟器沙盒区", str(self.sandbox_dir), "隔离运行沙盒与实机截图存盘区"),
        ]

        for title, p_str, note in paths_info:
            row = ttk.Frame(card, style="Card.TFrame")
            row.pack(fill="x", pady=5)
            ttk.Label(row, text=f"{title}:", style="Card.TLabel", width=14, font=("Microsoft YaHei UI", 15, "bold")).pack(side="left")
            ttk.Label(row, text=p_str, style="Card.TLabel", foreground="#58A6FF", font=("Consolas", 13), width=46, anchor="w").pack(side="left", padx=6)
            ttk.Label(row, text=f"({note})", style="CardMuted.TLabel", font=("Microsoft YaHei UI", 13)).pack(side="left")

        # Action Buttons for diagnostics
        btn_box = ttk.Frame(container, style="Card.TFrame", padding=16)
        btn_box.pack(fill="x", padx=6, pady=(0, 12))

        ttk.Label(btn_box, text="🛠️ 一键维护与自检工具", style="Card.TLabel", font=("Microsoft YaHei UI", 18, "bold")).pack(anchor="w", pady=(0, 10))

        b_row = ttk.Frame(btn_box, style="Card.TFrame")
        b_row.pack(fill="x", pady=4)

        tk.Button(
            b_row,
            text="🔄 重新解包原生 ROM (刷新工作区)",
            bg="#30363D",
            fg="#E6EDF3",
            relief="flat",
            font=("Microsoft YaHei UI", 14),
            padx=10,
            pady=6,
            command=self._async_unpack_native_rom,
        ).pack(side="left", padx=(0, 8), pady=2)

        tk.Button(
            b_row,
            text="⏪ 一键还原官方原版风云再起",
            bg="#30363D",
            fg="#E6EDF3",
            relief="flat",
            font=("Microsoft YaHei UI", 14),
            padx=10,
            pady=6,
            command=self._async_build_baseline,
        ).pack(side="left", padx=8, pady=2)

        tk.Button(
            b_row,
            text="🧪 全局工具链核心自检",
            bg="#30363D",
            fg="#E6EDF3",
            relief="flat",
            font=("Microsoft YaHei UI", 14),
            padx=10,
            pady=6,
            command=self._async_run_self_test,
        ).pack(side="left", padx=8, pady=2)

        tk.Button(
            b_row,
            text="📂 打开交付输出目录",
            bg="#30363D",
            fg="#E6EDF3",
            relief="flat",
            font=("Microsoft YaHei UI", 14),
            padx=10,
            pady=6,
            command=lambda: os.startfile(str(self.output_zip.parent)),
        ).pack(side="left", padx=8, pady=2)

    # ------------------------------------------------------------------------
    # Bottom Fixed Action Bar: Pack ROM & Start Game
    # ------------------------------------------------------------------------
    def _create_bottom_action_bar(self) -> None:
        """Create the two prominent action buttons: Pack ROM and Start Game."""
        bar = tk.Frame(self, bg="#0D1117", padx=18, pady=10)
        bar.pack(fill="x", side="bottom")

        # Two primary buttons requested by the user:
        # 1. Pack ROM
        # 2. Start Game
        self.btn_pack_rom = tk.Button(
            bar,
            text="📦 打包Rom (Pack ROM)",
            bg="#238636",
            fg="#FFFFFF",
            activebackground="#2EA043",
            activeforeground="#FFFFFF",
            relief="flat",
            font=("Microsoft YaHei UI", 18, "bold"),
            padx=28,
            pady=10,
            cursor="hand2",
            command=self._on_click_pack_rom,
        )
        self.btn_pack_rom.pack(side="left", padx=(0, 14))

        self.btn_start_game = tk.Button(
            bar,
            text="🎮 开始游戏 (Start Game)",
            bg="#1F6FEB",
            fg="#FFFFFF",
            activebackground="#388BFD",
            activeforeground="#FFFFFF",
            relief="flat",
            font=("Microsoft YaHei UI", 18, "bold"),
            padx=28,
            pady=10,
            cursor="hand2",
            command=self._on_click_start_game,
        )
        self.btn_start_game.pack(side="left", padx=(0, 18))

        # Build status label
        self.lbl_bottom_info = tk.Label(
            bar,
            text="就绪：随时可点击【打包Rom】构建最新改版，或点击【开始游戏】秒进模拟器！",
            font=("Microsoft YaHei UI", 14),
            bg="#0D1117",
            fg="#8B949E",
        )
        self.lbl_bottom_info.pack(side="left", fill="x", expand=True)

    def _create_console_logger(self) -> None:
        """Create real-time console log view above the bottom action bar."""
        self.console_frame = tk.Frame(self, bg="#0D1117", padx=16, pady=4)
        self.console_frame.pack(fill="x", side="bottom")

        # Header with Clear and Toggle buttons
        head = tk.Frame(self.console_frame, bg="#0D1117")
        head.pack(fill="x", pady=(0, 2))

        tk.Label(
            head,
            text="📜 实机构建与沙盒运行日志 (Live Log Output)",
            font=("Microsoft YaHei UI", 13, "bold"),
            bg="#0D1117",
            fg="#8B949E",
        ).pack(side="left")

        self.btn_toggle_console = tk.Button(
            head,
            text="折叠 ▲",
            bg="#21262D",
            fg="#8B949E",
            relief="flat",
            font=("Microsoft YaHei UI", 12),
            padx=8,
            pady=2,
            command=self._toggle_console,
        )
        self.btn_toggle_console.pack(side="right", padx=(4, 0))

        tk.Button(
            head,
            text="清空日志",
            bg="#21262D",
            fg="#8B949E",
            relief="flat",
            font=("Microsoft YaHei UI", 12),
            padx=8,
            pady=2,
            command=self._clear_log,
        ).pack(side="right")

        self.txt_console = ScrolledText(
            self.console_frame,
            height=3,
            bg="#0A0C10",
            fg="#C9D1D9",
            insertbackground="#58A6FF",
            font=("Consolas", 14),
            relief="solid",
            bd=1,
        )
        self.txt_console.pack(fill="both", expand=True, pady=(2, 0))

        # Log tag highlights
        self.txt_console.tag_config("INFO", foreground="#58A6FF")
        self.txt_console.tag_config("SUCCESS", foreground="#3FB950")
        self.txt_console.tag_config("WARN", foreground="#F0883E")
        self.txt_console.tag_config("ERROR", foreground="#F85149")
        self.txt_console.tag_config("TIMESTAMP", foreground="#8B949E")

    def _toggle_console(self) -> None:
        """Toggle console text visibility to expand or collapse log view."""
        if self.txt_console.winfo_ismapped():
            self.txt_console.pack_forget()
            self.btn_toggle_console.configure(text="展开 ▼")
        else:
            self.txt_console.pack(fill="both", expand=True, pady=(2, 0))
            self.btn_toggle_console.configure(text="折叠 ▲")

    def log(self, msg: str, level: str = "INFO") -> None:
        """Append a message to the live console view with a timestamp."""
        def _append() -> None:
            if not self.txt_console.winfo_ismapped() and level in ("WARN", "ERROR", "SUCCESS"):
                self.txt_console.pack(fill="both", expand=True, pady=(2, 0))
                self.btn_toggle_console.configure(text="折叠 ▲")
            ts = time.strftime("[%H:%M:%S] ")
            self.txt_console.insert(tk.END, ts, "TIMESTAMP")
            self.txt_console.insert(tk.END, f"[{level}] ", level)
            self.txt_console.insert(tk.END, f"{msg}\n")
            self.txt_console.see(tk.END)
        self.after(0, _append)

    def _clear_log(self) -> None:
        """Clear all messages from the console view."""
        self.txt_console.delete("1.0", tk.END)

    # ------------------------------------------------------------------------
    # Character Canvas Graphics & Real-Time Preview
    # ------------------------------------------------------------------------
    def _init_character_canvas_items(self) -> None:
        """Draw the initial vectorized layers of the character on preview canvas."""
        c = self.canvas_char
        c.delete("all")
        self.char_canvas_items = {}

        # Background grid subtle effect
        for y in range(0, 440, 30):
            c.create_line(0, y, 360, y, fill="#121824", width=1)
        for x in range(0, 360, 30):
            c.create_line(x, 0, x, 440, fill="#121824", width=1)

        # Floor Shadow
        self.char_canvas_items["floor"] = c.create_oval(60, 380, 280, 410, fill="#05070B", outline="")

        # Crescent Moon Crest
        self.char_canvas_items["moon"] = c.create_text(170, 160, text="☾", font=("Segoe UI Symbol", 28), fill="#F8FAFC")

        # Pants Left & Right (Lower Body)
        self.char_canvas_items["pants_l"] = c.create_polygon([(120, 220), (95, 360), (135, 362), (155, 230)], fill="#DE3A21", outline="#4A0000", width=1.5)
        self.char_canvas_items["pants_r"] = c.create_polygon([(160, 230), (180, 360), (220, 358), (195, 220)], fill="#DE3A21", outline="#4A0000", width=1.5)
        self.char_canvas_items["pants_w"] = c.create_polygon([(115, 200), (200, 200), (190, 245), (125, 245)], fill="#AD2910", outline="#4A0000", width=1.5)
        self.char_canvas_items["pants_strap"] = c.create_polygon([(105, 300), (140, 320), (180, 320), (205, 300), (180, 310), (140, 310)], fill="#7B1908", outline="#4A0000", width=1.5)

        # Shoes
        self.char_canvas_items["shoes_l"] = c.create_polygon([(90, 360), (70, 385), (135, 385), (136, 362)], fill="#191929", outline="#000008", width=1.5)
        self.char_canvas_items["shoes_r"] = c.create_polygon([(180, 360), (178, 385), (242, 385), (220, 358)], fill="#191929", outline="#000008", width=1.5)

        # Coat tails
        self.char_canvas_items["coat_tails"] = c.create_polygon([(105, 190), (85, 290), (120, 275), (135, 210), (180, 210), (195, 275), (230, 290), (210, 190)], fill="#191929", outline="#000008", width=1.5)

        # Inner Shirt & Collar
        self.char_canvas_items["shirt_c"] = c.create_polygon([(140, 105), (155, 160), (175, 105), (168, 95), (148, 95)], fill="#F7F7FF", outline="#737B84", width=1.0)
        self.char_canvas_items["shirt_b"] = c.create_polygon([(142, 135), (155, 200), (168, 135)], fill="#BDBDC5", outline="")

        # Skin - Neck (Locked Default)
        self.char_canvas_items["skin_neck"] = c.create_polygon([(150, 100), (162, 100), (160, 128), (152, 128)], fill="#FFF7B5", outline="")

        # Coat Sleeves & Torso
        self.char_canvas_items["sleeve_l"] = c.create_polygon([(115, 120), (75, 205), (98, 212), (132, 138)], fill="#29293A", outline="#000008", width=1.5)
        self.char_canvas_items["sleeve_r"] = c.create_polygon([(195, 120), (235, 202), (215, 210), (178, 138)], fill="#29293A", outline="#000008", width=1.5)
        self.char_canvas_items["coat_torso"] = c.create_polygon([(118, 118), (105, 205), (135, 212), (145, 150), (165, 150), (175, 212), (205, 205), (192, 118)], fill="#3A3A4A", outline="#000008", width=1.5)

        # Skin - Hands (Locked Default)
        self.char_canvas_items["hand_l"] = c.create_polygon([(75, 205), (62, 224), (84, 228), (92, 213)], fill="#F7C584", outline="#B55229", width=1.0)
        self.char_canvas_items["hand_r"] = c.create_polygon([(232, 201), (248, 218), (234, 226), (222, 211)], fill="#F7C584", outline="#B55229", width=1.0)

        # Skin - Face (Locked Default)
        self.char_canvas_items["face"] = c.create_polygon([(140, 68), (170, 68), (175, 105), (158, 115), (138, 105)], fill="#FFF7B5", outline="#B55229", width=1.0)

        # Hair Back & Bangs
        self.char_canvas_items["hair_b"] = c.create_polygon([(132, 68), (118, 45), (142, 48), (155, 25), (172, 48), (192, 42), (182, 68)], fill="#AD2910", outline="#4A0000", width=1.5)
        self.char_canvas_items["hair_f"] = c.create_polygon([(140, 50), (152, 55), (180, 65), (188, 98), (178, 115), (165, 125), (172, 108), (175, 90), (158, 75), (145, 80), (132, 70)], fill="#DE3A21", outline="#4A0000", width=1.5)

    def _update_character_preview(self, theme: dict) -> None:
        """Update live character figure colors on Canvas with harmonious palette."""
        if not hasattr(self, "char_canvas_items"):
            return
        c = self.canvas_char
        items = self.char_canvas_items

        coat = theme["coat_color"]
        shirt = theme["shirt_color"]
        hair = theme["hair_color"]
        pants = theme["pants_color"]
        shoes = theme.get("shoes_color", "#191929")
        tail = theme["upper_colors"][2] if len(theme["upper_colors"]) > 2 else coat
        hair_dark = theme["lower_colors"][1] if len(theme["lower_colors"]) > 1 else hair
        strap = theme["lower_colors"][2] if len(theme["lower_colors"]) > 2 else pants

        c.itemconfig(items["coat_torso"], fill=coat)
        c.itemconfig(items["sleeve_l"], fill=coat)
        c.itemconfig(items["sleeve_r"], fill=coat)
        c.itemconfig(items["coat_tails"], fill=tail)

        c.itemconfig(items["shirt_c"], fill=shirt)
        c.itemconfig(items["shirt_b"], fill=shirt)

        c.itemconfig(items["pants_l"], fill=pants)
        c.itemconfig(items["pants_r"], fill=pants)
        c.itemconfig(items["pants_w"], fill=pants)
        c.itemconfig(items["pants_strap"], fill=strap)

        c.itemconfig(items["hair_f"], fill=hair)
        c.itemconfig(items["hair_b"], fill=hair_dark)

        c.itemconfig(items["shoes_l"], fill=shoes)
        c.itemconfig(items["shoes_r"], fill=shoes)

        # Update Bottom Harmony Indicator swatches & text
        if hasattr(self, "swatch_coat"):
            self.swatch_coat.configure(bg=coat)
            self.swatch_shirt.configure(bg=shirt)
            self.swatch_hair.configure(bg=hair)
            self.swatch_pants.configure(bg=pants)
            self.lbl_upper_desc.configure(text=f"{theme['upper_desc']}")
            self.lbl_lower_desc.configure(text=f"{theme['lower_desc'].split(' (')[0]}")
            self.lbl_active_theme_badge.configure(text=theme["name_cn"].split(" (")[0])

    def _refresh_all_color_slots(self) -> None:
        """Refresh character preview with the current theme colors."""
        theme_id = self.current_theme_id.get()
        theme = next((t for t in PRESET_THEMES if t["id"] == theme_id), PRESET_THEMES[0])
        self._update_character_preview(theme)

    # ------------------------------------------------------------------------
    # Preset & Palette Management
    # ------------------------------------------------------------------------
    def _load_preset_by_id(self, theme_id: str) -> None:
        """Load harmonious colors from the specified preset theme and update center preview."""
        theme = next((t for t in PRESET_THEMES if t["id"] == theme_id), None)
        if not theme:
            return
        self.current_theme_id.set(theme_id)

        for i, c in enumerate(theme["colors"]):
            self.slot_hex_vars[i].set(c)

        # Highlight active card in preset list
        if hasattr(self, "preset_card_frames"):
            for t, card in zip(PRESET_THEMES, self.preset_card_frames):
                if t["id"] == theme_id:
                    card.configure(bg="#1F2C3F", bd=2)
                    for child in card.winfo_children():
                        child.configure(bg="#1F2C3F")
                        for sub in child.winfo_children():
                            sub.configure(bg="#1F2C3F")
                else:
                    card.configure(bg="#16181D", bd=1)
                    for child in card.winfo_children():
                        child.configure(bg="#16181D")
                        for sub in child.winfo_children():
                            sub.configure(bg="#16181D")

        self._update_character_preview(theme)
        self.log(f"已载入和谐配色方案: 【{theme['name_cn']}】 (上身/下身已协调统一，原生肤色锁定)", "INFO")

    def _on_target_mode_changed(self) -> None:
        """Handle switching between All Characters and Single Character."""
        mode = self.target_mode.get()
        if mode == "ALL":
            self.cbo_character.configure(state="disabled")
            self.log("皮肤应用目标已切换为: 【全部 36 位角色】", "INFO")
        else:
            self.cbo_character.configure(state="readonly")
            char_info = CHARACTER_ROSTER[self.cbo_character.current()]
            self.log(f"皮肤应用目标已切换为: 【{char_info['name_cn']}】", "INFO")

    def _on_character_changed(self, event: Optional[tk.Event] = None) -> None:
        """Handle character dropdown selection change and update center preview."""
        idx = self.cbo_character.current()
        if 0 <= idx < len(CHARACTER_ROSTER):
            char_info = CHARACTER_ROSTER[idx]
            self.selected_char_id.set(char_info["id"])
            if hasattr(self, "lbl_char_preview_title"):
                self.lbl_char_preview_title.configure(text=f"{char_info['name_cn']} · 实时立绘全景预览")
            self.log(f"已选定目标角色: {char_info['name_cn']} (ID=0x{char_info['id']:02X})", "INFO")

    def _restore_all_default_rom_skins(self) -> None:
        """Restore all 36 characters to pristine SNK default palettes and repack."""
        try:
            self.log("正在从原始 kof97.zip 提取纯净调色板并重置全员皮肤...", "INFO")
            unpack_rom_set(self.source_zip, self.workdir)
            pack_rep = pack_rom_set(self.workdir, self.output_zip)
            self._load_preset_by_id("classic")
            self.log("全员 36 位角色皮肤已 100% 成功复原为官方原生原版！", "SUCCESS")
            messagebox.showinfo("恢复成功", "全员 36 位角色皮肤已 100% 成功复原为官方原生原版！\n\n所有角色默认皮肤均已恢复。")
        except Exception as exc:
            self.log(f"恢复原生皮肤失败: {exc}", "ERROR")
            messagebox.showerror("恢复失败", str(exc))

    # ------------------------------------------------------------------------
    # Health Check & Diagnostics
    # ------------------------------------------------------------------------
    def _initial_health_check(self) -> None:
        """Perform initial status check on project files and display badges."""
        p1_path = self.workdir / "p1_be.bin"
        p2_path = self.workdir / "p2_be.bin"
        zip_path = self.output_zip

        has_unpacked = p1_path.exists() and p2_path.exists()
        has_zip = zip_path.exists()

        if has_zip and has_unpacked:
            crc = crc32_hex(zip_path.read_bytes())
            self.lbl_status_badge.configure(text=f"就绪: 已打包 (CRC32: {crc})", bg="#238636", fg="#FFFFFF")
            self.log(f"工程状态检测正常：已就绪 (output: {zip_path.name}, CRC32={crc})", "SUCCESS")
        elif has_unpacked:
            self.lbl_status_badge.configure(text="就绪: 工作区已解包 (待打包)", bg="#1F6FEB", fg="#FFFFFF")
            self.log("工作区已准备就绪，可随时点击【打包Rom】生成定制 ROM。", "INFO")
        elif self.source_zip.exists():
            self.lbl_status_badge.configure(text="就绪: 原生 ROM 正常 (待首次构建)", bg="#30363D", fg="#8B949E")
            self.log(f"检测到原生 ROM: {self.source_zip.name}，首次打包时将自动完成解包流水线。", "INFO")
        else:
            self.lbl_status_badge.configure(text="警告: 缺少原生 ROM", bg="#DA3633", fg="#FFFFFF")
            self.log(f"未找到原生 ROM 文件: {self.source_zip}，请检查路径！", "WARN")

    # ------------------------------------------------------------------------
    # Build & Pack Pipeline
    # ------------------------------------------------------------------------
    def _on_click_pack_rom(self) -> None:
        """Handler for the primary '打包Rom' button."""
        if not self.build_lock.acquire(blocking=False):
            self.log("构建流水线正在运行中，请稍候...", "WARN")
            return

        self.btn_pack_rom.configure(state="disabled", text="正在打包中...")
        self.lbl_bottom_info.configure(text="正在应用属性 Patch、编码调色板并执行 bswap16 打包...")

        threading.Thread(target=self._worker_pack_rom, daemon=True).start()

    def _worker_pack_rom(self) -> None:
        """Worker thread to execute property patching, palette modification, and ROM packaging."""
        try:
            self.log("=== 开始执行【打包Rom】流水线 ===", "INFO")

            # 1. Ensure unpacked files exist
            p1_path = self.workdir / "p1_be.bin"
            p2_path = self.workdir / "p2_be.bin"
            s1_path = self.workdir / "s1.bin"

            if not (p1_path.exists() and p2_path.exists() and s1_path.exists()):
                self.log("解包缓存不完整，正在从原生 ROM 自动解包...", "INFO")
                unpack_rom_set(self.source_zip, self.workdir)
                self.log("原生 ROM 解包完成。", "SUCCESS")

            p1_data = bytearray(p1_path.read_bytes())
            p2_data = bytearray(p2_path.read_bytes())

            if len(p1_data) != EXPECTED_SIZES["p1"]:
                raise ValueError(f"Invalid p1_be.bin size: {len(p1_data)}")
            if len(p2_data) != EXPECTED_SIZES["p2"]:
                raise ValueError(f"Invalid p2_be.bin size: {len(p2_data)}")

            # 2. Apply Combat & Defense Patches to p1_be.bin
            self.log("正在应用 68000 战斗与防御属性 Patch...", "INFO")

            # Guard Crush Immunity
            if self.opt_guard_crush.get():
                p1_data[0x01397E:0x013982] = bytes.fromhex("4e714e71")  # NOP; NOP
                self.log("  [P1] 免破防 Patch: 0x01397E -> 4E714E71 (NOP; NOP, 破防槽锁死)", "INFO")
            else:
                p1_data[0x01397E:0x013982] = bytes.fromhex("916c013e")  # SUB.W D0, $013E(A4)
                self.log("  [P1] 恢复原版破防机制 (扣减防御槽)", "INFO")

            # Dizzy/Stun Immunity
            if self.opt_dizzy_stun.get():
                p1_data[0x0139A4:0x0139A8] = bytes.fromhex("4e714e71")  # NOP; NOP
                self.log("  [P1] 免眩晕 Patch: 0x0139A4 -> 4E714E71 (NOP; NOP, 眩晕槽锁死)", "INFO")
            else:
                p1_data[0x0139A4:0x0139A8] = bytes.fromhex("916c0146")  # SUB.W D0, $0146(A4)
                self.log("  [P1] 恢复原版眩晕机制 (扣减眩晕槽)", "INFO")

            # Damage Multiplier (Code Cave 0x000300)
            dmg_id = self.opt_damage_mode.get()
            selected_mode = next((m for m in DAMAGE_MODES if m["id"] == dmg_id), DAMAGE_MODES[0])

            if dmg_id == "normal":
                p1_data[0x01394A:0x01394E] = selected_mode["hook"]
                p1_data[0x000300:0x000308] = bytes.fromhex("ffffffffffffffff")
                self.log("  [P1] 恢复 100% 原始受创 (无伤害缩减)", "INFO")
            else:
                p1_data[0x01394A:0x01394E] = selected_mode["hook"]  # JSR ($0300).W
                p1_data[0x000300:0x000308] = selected_mode["cave"]
                self.log(f"  [P1] 注入伤害倍率 Hook: {selected_mode['name_cn']}", "INFO")

            # Save modified p1_be.bin
            p1_path.write_bytes(p1_data)

            # 3. Apply Custom Palette & Skins to p2_be.bin
            self.log("正在将定制配色方案编码为 Neo-Geo LSPC2-A2 硬件字阶...", "INFO")
            # Encode 15 colors to words
            current_hex_list = [v.get() for v in self.slot_hex_vars]
            lspc_words = [hex_to_lspc2(h) for h in current_hex_list]
            lspc_bytes = struct.pack(">15H", *lspc_words)

            target_mode = self.target_mode.get()
            apply_all_btns = self.apply_all_buttons.get()
            btn_count = 4 if apply_all_btns else 1

            if target_mode == "ALL":
                self.log("正在批量应用定制皮肤至全部 36 位角色...", "INFO")
                # Apply to all 36 characters
                for char_id in range(36):
                    for btn_idx in range(btn_count):
                        base_off = 0x483E + char_id * 8 + btn_idx * 2
                        pal_id = struct.unpack(">H", p1_data[base_off:base_off + 2])[0]
                        p2_addr = 0x2CFFF0 + pal_id * 32
                        # Preserve Word 0 (pal_id header)
                        p2_data[p2_addr + 2: p2_addr + 32] = lspc_bytes

                # Sync Iori legacy compatibility offset 0x2DC9F0 (PalID 0x0650)
                p2_data[0x2DC9F0 + 2: 0x2DC9F0 + 32] = lspc_bytes
                self.log("  [P2] 全员 36 位角色主调色板批量注入完成！", "SUCCESS")

            else:
                char_idx = self.cbo_character.current()
                char_info = CHARACTER_ROSTER[char_idx]
                char_id = char_info["id"]
                self.log(f"正在应用定制皮肤至单角色: {char_info['name_cn']}...", "INFO")

                for btn_idx in range(btn_count):
                    base_off = 0x483E + char_id * 8 + btn_idx * 2
                    pal_id = struct.unpack(">H", p1_data[base_off:base_off + 2])[0]
                    p2_addr = 0x2CFFF0 + pal_id * 32
                    p2_data[p2_addr + 2: p2_addr + 32] = lspc_bytes

                if char_id == 0x1B:
                    # Sync Iori legacy compatibility offset
                    p2_data[0x2DC9F0 + 2: 0x2DC9F0 + 32] = lspc_bytes

                self.log(f"  [P2] 角色 {char_info['name_cn']} 调色板注入完成！", "SUCCESS")

            # 4. Sync Avatar & Portrait Palettes for Iori (0x2DF990..0x2DF9EF)
            if self.sync_avatar_portraits.get():
                # Extract hair / primary ramp colors (Words 8..11, corresponding to lspc_words[7..10])
                c_high = lspc_words[7]  # Word 8
                c_mid = lspc_words[8]   # Word 9
                c_shad = lspc_words[9]  # Word 10
                c_deep = lspc_words[10] # Word 11

                # 0x2DF990 (PalID 0x07CD, Big Portrait)
                p2_data[0x2DF990 + 16: 0x2DF990 + 18] = struct.pack(">H", c_high)
                p2_data[0x2DF990 + 20: 0x2DF990 + 22] = struct.pack(">H", c_mid)
                p2_data[0x2DF990 + 22: 0x2DF990 + 24] = struct.pack(">H", c_shad)
                p2_data[0x2DF990 + 30: 0x2DF990 + 32] = struct.pack(">H", c_deep)

                # 0x2DF9B0 (PalID 0x07CE, Mid Portrait)
                p2_data[0x2DF9B0 + 14: 0x2DF9B0 + 16] = struct.pack(">H", c_high)
                p2_data[0x2DF9B0 + 16: 0x2DF9B0 + 18] = struct.pack(">H", c_mid)
                p2_data[0x2DF9B0 + 18: 0x2DF9B0 + 20] = struct.pack(">H", c_shad)

                # 0x2DF9D0 (PalID 0x07CF, Small HUD Portrait)
                p2_data[0x2DF9D0 + 12: 0x2DF9D0 + 14] = struct.pack(">H", c_high)
                p2_data[0x2DF9D0 + 14: 0x2DF9D0 + 16] = struct.pack(">H", c_mid)
                p2_data[0x2DF9D0 + 16: 0x2DF9D0 + 18] = struct.pack(">H", c_shad)
                p2_data[0x2DF9D0 + 28: 0x2DF9D0 + 30] = struct.pack(">H", c_high)
                self.log("  [P2] 选人界面立绘与 HUD 小头像发色联动同步完成！", "INFO")

            # Save modified p2_be.bin
            p2_path.write_bytes(p2_data)

            # 5. Pack into kof97pls.zip with bswap16
            self.log("正在执行 bswap16 硬件字节序交换并压缩打包 ROM...", "INFO")
            pack_rep = pack_rom_set(self.workdir, self.output_zip)
            zip_crc = crc32_hex(self.output_zip.read_bytes())

            self.log("=== 打包流水线执行完毕！===", "SUCCESS")
            self.log(f"交付成果物: {self.output_zip} (大小: {self.output_zip.stat().st_size:,} 字节, CRC32: 0x{zip_crc})", "SUCCESS")
            for role, info in pack_rep.items():
                arc_name = info.get("arcname", f"{role}.bin")
                disk_crc = info.get("disk_crc32", "N/A")
                self.log(f"  ROM 镜像 [{role.upper()}]: {arc_name} | 磁盘 CRC32: 0x{disk_crc}", "INFO")

            def _on_success() -> None:
                self.lbl_status_badge.configure(text=f"构建就绪 (CRC32: {zip_crc})", bg="#238636", fg="#FFFFFF")
                self.lbl_bottom_info.configure(text=f"打包成功！当前版本已生成至 output/roms/kof97pls.zip (CRC32: 0x{zip_crc})")
                messagebox.showinfo("打包成功", f"ROM 已成功打包！\n\n文件路径: {self.output_zip}\nCRC32: 0x{zip_crc}\n\n您可直接点击【开始游戏】秒进模拟器联调！")

            self.after(0, _on_success)

        except Exception as e:
            self.log(f"打包流水线异常中断: {e}", "ERROR")
            def _on_fail() -> None:
                messagebox.showerror("打包失败", f"打包过程中发生错误:\n{e}")
            self.after(0, _on_fail)

        finally:
            if self.build_lock.locked():
                self.build_lock.release()
            def _restore_btn() -> None:
                self.btn_pack_rom.configure(state="normal", text="📦 打包Rom (Pack ROM)")
            self.after(0, _restore_btn)

    # ------------------------------------------------------------------------
    # Start Game Launcher
    # ------------------------------------------------------------------------
    def _on_click_start_game(self) -> None:
        """Handler for the primary '开始游戏' button."""
        threading.Thread(target=self._worker_start_game, daemon=True).start()

    def _worker_start_game(self) -> None:
        """Worker thread to launch WinKawaks with memory patch."""
        try:
            # Check if output ROM exists
            if not self.output_zip.exists():
                self.log("未检测到 output/roms/kof97pls.zip，正在自动触发打包...", "WARN")
                # Trigger synchronous pack
                self._worker_pack_rom()
                if not self.output_zip.exists():
                    self.log("打包未生成有效 ROM，启动中止。", "ERROR")
                    return

            exe_path = self.sandbox_dir / "WinKawaks.exe"
            if not exe_path.exists():
                raise FileNotFoundError(f"未找到模拟器主程序: {exe_path}")

            self.log(f"正在启动沙盒模拟器 WinKawaks (挂载 RomPath1={self.output_zip.parent})...", "INFO")
            proc = start_sandbox_kawaks(self.sandbox_dir, rom_name="kof97pls", enable_bg_input=False)
            self.log(f"WinKawaks 模拟器已成功启动！(PID={proc.pid})，已自动施加内存反遮蔽 Patch，祝游戏愉快！", "SUCCESS")

        except Exception as e:
            self.log(f"启动模拟器失败: {e}", "ERROR")
            def _show_err() -> None:
                messagebox.showerror("启动游戏失败", f"无法启动沙盒模拟器:\n{e}")
            self.after(0, _show_err)

    # ------------------------------------------------------------------------
    # Maintenance Actions (Unpack, Baseline, Self-Test)
    # ------------------------------------------------------------------------
    def _async_unpack_native_rom(self) -> None:
        """Trigger background unpack of native kof97.ZIP."""
        def _task() -> None:
            try:
                self.log("正在从原生 ROM 重新解包...", "INFO")
                rep = unpack_rom_set(self.source_zip, self.workdir)
                self.log(f"解包成功！共解包 {len(rep)} 个核心 ROM 镜像至 {self.workdir}", "SUCCESS")
                self._initial_health_check()
                messagebox.showinfo("解包完成", "已成功刷新解包工作区！")
            except Exception as e:
                self.log(f"解包失败: {e}", "ERROR")
                messagebox.showerror("解包失败", str(e))
        threading.Thread(target=_task, daemon=True).start()

    def _async_build_baseline(self) -> None:
        """Trigger background build of official baseline ROM."""
        def _task() -> None:
            try:
                self.log("正在构建官方原版风云再起基线包...", "INFO")
                unpack_rom_set(self.source_zip, self.workdir)
                pack_rep = pack_rom_set(self.workdir, self.output_zip)
                self.log(f"基线包重置完成: {self.output_zip}", "SUCCESS")
                self._initial_health_check()
                messagebox.showinfo("还原完成", "已成功还原为官方原版风云再起基准 ROM！")
            except Exception as e:
                self.log(f"还原基线包失败: {e}", "ERROR")
                messagebox.showerror("还原失败", str(e))
        threading.Thread(target=_task, daemon=True).start()

    def _async_run_self_test(self) -> None:
        """Trigger background execution of rom_tool self-test."""
        def _task() -> None:
            try:
                self.log("正在执行全局工具链自检 (bswap16 / LSPC2 / 瓦片测试)...", "INFO")
                cmd = [sys.executable, str(PROJECT_ROOT / "src" / "rom" / "rom_tool.py"), "self-test"]
                res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
                if res.returncode == 0:
                    self.log(res.stdout.strip(), "INFO")
                    self.log("[PASS] 全局自检 100% 通过！", "SUCCESS")
                    messagebox.showinfo("自检通过", "全局工具链自检全部通过！\n- bswap16 双向无损\n- LSPC2 调色板编解码无损\n- 瓦片位平面 bit-exact")
                else:
                    self.log(res.stderr.strip(), "ERROR")
                    messagebox.showerror("自检未通过", res.stderr)
            except Exception as e:
                self.log(f"自检执行异常: {e}", "ERROR")
                messagebox.showerror("自检异常", str(e))
        threading.Thread(target=_task, daemon=True).start()


# ============================================================================
# Main Entry Point
# ============================================================================

def main() -> None:
    """Entry point for launching the KOF97 Mod Studio UI."""
    app = KOF97ModStudioGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
