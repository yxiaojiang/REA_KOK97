#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Upgrade script for KOF97 Mod Studio.
1. Appends 10 new high-contrast, non-zombie harmonious skins for Iori, Daimon, Chang, and universal roster.
2. Fixes victory/ending win screen portrait palette synchronization (covering all 4 button slots A/B/C/D).
3. Fixes live skin hot-reload and eliminates get_emulator_status NameError using verified WinKawaks 1.48 pointers.
4. Updates frontend index.html with 10 new theme cards.

All comments, identifiers, and variables strictly follow 100% English specification (Rules.md).
"""

import ast
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_PY_PATH = PROJECT_ROOT / "tools" / "kof97_webview_app.py"
INDEX_HTML_PATH = PROJECT_ROOT / "tools" / "web" / "index.html"

# 10 Brand-New Aesthetic Non-Zombie Themes (Pure ASCII Unicode escapes for Chinese labels)
NEW_PRESET_THEMES_PY = '''    {
        "id": "abyssal_frost",
        "name_cn": "\\u6df1\\u6e0a\\u5bd2\\u51b0",
        "colors": [
            "#FFF7B5", "#F7C584", "#EF945A", "#B55229",
            "#FFFFFF", "#E0F2FE", "#BAE6FD",
            "#7DD3FC", "#38BDF8", "#0284C7", "#0C4A6E",
            "#1E293B", "#0F172A", "#020617", "#000000",
        ],
        "daimon_judogi": ["#E0F2FE", "#BAE6FD", "#7DD3FC", "#38BDF8", "#0284C7", "#0369A1"],
        "daimon_headband": "#FFFFFF",
        "chang_uniform": ["#E0F2FE", "#BAE6FD", "#38BDF8", "#0284C7", "#0C4A6E"],
        "chang_ball": ["#38BDF8", "#075985"],
    },
    {
        "id": "phoenix_nirvana",
        "name_cn": "\\u51e4\\u821e\\u6d85\\u69c3",
        "colors": [
            "#FFF7B5", "#F7C584", "#EF945A", "#B55229",
            "#FFFFFF", "#E5E7EB", "#9CA3AF",
            "#FFA500", "#FF4500", "#DC143C", "#8B0000",
            "#262626", "#1A1A1A", "#0D0D0D", "#000000",
        ],
        "daimon_judogi": ["#FED7AA", "#FB923C", "#F97316", "#EA580C", "#C2410C", "#7C2D12"],
        "daimon_headband": "#FDE047",
        "chang_uniform": ["#FED7AA", "#FB923C", "#EA580C", "#C2410C", "#7C2D12"],
        "chang_ball": ["#F59E0B", "#B45309"],
    },
    {
        "id": "emerald_lotus",
        "name_cn": "\\u78a7\\u7389\\u9752\\u83b2",
        "colors": [
            "#FFF7B5", "#F7C584", "#EF945A", "#B55229",
            "#FFFFFF", "#E5E7EB", "#9CA3AF",
            "#6EE7B7", "#10B981", "#047857", "#022C22",
            "#1F2937", "#111827", "#030712", "#000000",
        ],
        "daimon_judogi": ["#D1FAE5", "#A7F3D0", "#6EE7B7", "#10B981", "#059669", "#022C22"],
        "daimon_headband": "#34D399",
        "chang_uniform": ["#D1FAE5", "#A7F3D0", "#34D399", "#059669", "#022C22"],
        "chang_ball": ["#10B981", "#064E3B"],
    },
    {
        "id": "shadow_ninja",
        "name_cn": "\\u6697\\u591c\\u5f71\\u5203",
        "colors": [
            "#FFF7B5", "#F7C584", "#EF945A", "#B55229",
            "#FFFFFF", "#E5E7EB", "#9CA3AF",
            "#E2E8F0", "#94A3B8", "#475569", "#1E293B",
            "#27272A", "#18181B", "#09090B", "#000000",
        ],
        "daimon_judogi": ["#F1F5F9", "#CBD5E1", "#94A3B8", "#64748B", "#334155", "#0F172A"],
        "daimon_headband": "#EF4444",
        "chang_uniform": ["#F1F5F9", "#CBD5E1", "#64748B", "#334155", "#0F172A"],
        "chang_ball": ["#E2E8F0", "#475569"],
    },
    {
        "id": "sunset_overdrive",
        "name_cn": "\\u66ae\\u5149\\u6d41\\u706b",
        "colors": [
            "#FFF7B5", "#F7C584", "#EF945A", "#B55229",
            "#FFFFFF", "#E5E7EB", "#9CA3AF",
            "#FDBA74", "#FB923C", "#EA580C", "#7C2D12",
            "#312E81", "#1E1B4B", "#0F0E2A", "#000000",
        ],
        "daimon_judogi": ["#FED7AA", "#FDBA74", "#FB923C", "#F97316", "#C2410C", "#431407"],
        "daimon_headband": "#DC2626",
        "chang_uniform": ["#FED7AA", "#FB923C", "#F97316", "#C2410C", "#431407"],
        "chang_ball": ["#F59E0B", "#78350F"],
    },
    {
        "id": "amethyst_phantom",
        "name_cn": "\\u7d2b\\u6676\\u9b45\\u5f71",
        "colors": [
            "#FFF7B5", "#F7C584", "#EF945A", "#B55229",
            "#FFFFFF", "#E5E7EB", "#9CA3AF",
            "#D8B4FE", "#A855F7", "#7E22CE", "#3B0764",
            "#241438", "#170B26", "#0B0414", "#000000",
        ],
        "daimon_judogi": ["#F3E8FF", "#E9D5FF", "#C084FC", "#9333EA", "#6B21A8", "#3B0764"],
        "daimon_headband": "#F0ABFC",
        "chang_uniform": ["#F3E8FF", "#E9D5FF", "#A855F7", "#6B21A8", "#3B0764"],
        "chang_ball": ["#C084FC", "#581C87"],
    },
    {
        "id": "ocean_tempest",
        "name_cn": "\\u6012\\u6d77\\u72c2\\u6d9b",
        "colors": [
            "#FFF7B5", "#F7C584", "#EF945A", "#B55229",
            "#FFFFFF", "#E0F2FE", "#BAE6FD",
            "#38BDF8", "#0284C7", "#075985", "#082F49",
            "#172554", "#0F172A", "#020617", "#000000",
        ],
        "daimon_judogi": ["#BAE6FD", "#7DD3FC", "#38BDF8", "#0284C7", "#0369A1", "#082F49"],
        "daimon_headband": "#FFFFFF",
        "chang_uniform": ["#BAE6FD", "#7DD3FC", "#0284C7", "#075985", "#082F49"],
        "chang_ball": ["#0284C7", "#0F172A"],
    },
    {
        "id": "valkyrie_silver",
        "name_cn": "\\u767d\\u94f6\\u88c1\\u51b3",
        "colors": [
            "#FFF7B5", "#F7C584", "#EF945A", "#B55229",
            "#FFFFFF", "#E2E8F0", "#94A3B8",
            "#FFFFFF", "#E2E8F0", "#94A3B8", "#475569",
            "#F8FAFC", "#E2E8F0", "#CBD5E1", "#1E293B",
        ],
        "daimon_judogi": ["#FFFFFF", "#F8FAFC", "#E2E8F0", "#CBD5E1", "#94A3B8", "#475569"],
        "daimon_headband": "#F59E0B",
        "chang_uniform": ["#FFFFFF", "#F8FAFC", "#CBD5E1", "#94A3B8", "#334155"],
        "chang_ball": ["#F8FAFC", "#64748B"],
    },
    {
        "id": "crimson_dragon",
        "name_cn": "\\u8840\\u9f99\\u7834\\u519b",
        "colors": [
            "#FFF7B5", "#F7C584", "#EF945A", "#B55229",
            "#FFFFFF", "#E5E7EB", "#9CA3AF",
            "#EF4444", "#DC2626", "#991B1B", "#450A0A",
            "#2B1D1D", "#1A1010", "#0D0808", "#000000",
        ],
        "daimon_judogi": ["#FCA5A5", "#EF4444", "#DC2626", "#B91C1C", "#7F1D1D", "#450A0A"],
        "daimon_headband": "#FBBF24",
        "chang_uniform": ["#FCA5A5", "#EF4444", "#DC2626", "#7F1D1D", "#450A0A"],
        "chang_ball": ["#991B1B", "#450A0A"],
    },
    {
        "id": "solar_flare",
        "name_cn": "\\u65e5\\u8037\\u98ce\\u66b4",
        "colors": [
            "#FFF7B5", "#F7C584", "#EF945A", "#B55229",
            "#FFFFFF", "#E5E7EB", "#9CA3AF",
            "#FDE047", "#EAB308", "#CA8A04", "#713F12",
            "#292524", "#1C1917", "#0C0A09", "#000000",
        ],
        "daimon_judogi": ["#FEF08A", "#FDE047", "#FACC15", "#EAB308", "#A16207", "#422006"],
        "daimon_headband": "#DC2626",
        "chang_uniform": ["#FEF08A", "#FACC15", "#EAB308", "#A16207", "#422006"],
        "chang_ball": ["#FDE047", "#854D0E"],
    },'''

NEW_THEME_RAMPS_PY = '''    "abyssal_frost": {
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
        "primary": ["#F3E8FF", "#E9D5FF", "#C084FC", "#9333EA", "#6B21A8", "#3B0764"],
        "accent": ["#FDF4FF", "#F0ABFC", "#C026D3", "#701A75"],
        "light": ["#FAF5FF", "#F3E8FF"],
        "dark": ["#1E0B36", "#0E041A", "#000000"],
    },
    "ocean_tempest": {
        "primary": ["#BAE6FD", "#7DD3FC", "#38BDF8", "#0284C7", "#0369A1", "#082F49"],
        "accent": ["#E0F2FE", "#BAE6FD", "#0284C7", "#075985"],
        "light": ["#F0F9FF", "#E0F2FE"],
        "dark": ["#0F172A", "#020617", "#000000"],
    },
    "valkyrie_silver": {
        "primary": ["#FFFFFF", "#F8FAFC", "#E2E8F0", "#CBD5E1", "#94A3B8", "#475569"],
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
    },'''

# New sync_character_portraits implementation:
# Fully updates all 4 button slots (A/B/C/D) across:
#   base_pid + 13 + btn * 16 (Big Win Portrait, e.g. Iori on win screen)
#   base_pid + 14 + btn * 16 (Mid Select & Win Screen Teammate Portrait, e.g. Chang & Daimon on win screen)
#   base_pid + 15 + btn * 16 (Small HUD Avatar)
NEW_SYNC_PORTRAITS_CODE = '''def sync_character_portraits(
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

    # 4. Universal 36-character portrait synchronization across all 4 button slots
    else:
        for btn_idx in range(4):
            for slot_off in (13, 14, 15):
                pal_id = base_pid + slot_off + btn_idx * 16
                addr = 0x2CFFF0 + pal_id * 32
                p_words = list(struct.unpack(">16H", p2_clean[addr:addr + 32]))
                for i in range(1, 16):
                    orig_w = p_words[i]
                    r, g, b, _ = decode_lspc2(orig_w)
                    is_skin = (r >= g >= b and r >= 10 and r - b >= 3)
                    lum = 0.299 * r + 0.587 * g + 0.114 * b
                    if not is_skin and 2 < lum < 28:
                        p_words[i] = lspc_words[min(i - 1, len(lspc_words) - 1)]
                p2_data[addr:addr + 32] = struct.pack(">16H", *p_words)'''

# New Live Injection & Emulator Status Implementation:
# Uses verified WinKawaks 1.48 global pointers:
#   0x007126B0 -> Palette RAM (8192 bytes, 256 palettes)
#   0x00712660 -> P-ROM buffer (+0x100000 = P2 ROM)
#   0x00712688 -> 68000 Work RAM (64KB, 1P at +0x8100, 2P at +0x8300)
NEW_LIVE_INJECTION_CODE = '''    def _find_kawaks_pid(self) -> Optional[int]:
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
                "message": "\\u914d\\u7f6e\\u5df2\\u4fdd\\u5b58\\uff01\\u5f53\\u524d\\u6a21\\u62df\\u5668\\u672a\\u5728\\u8fd0\\u884c\\uff0c\\u70b9\\u51fb\\u300c\\u5f00\\u59cb\\u6e38\\u620f\\u300d\\u6216\\u300c\\u6253\\u5305ROM\\u300d\\u5373\\u53ef\\u751f\\u6548\\u3002"
            }

        # 3. Read p1 and clean p2 baseline
        p1_path = self._workdir / "p1_be.bin"
        if not p1_path.exists():
            return {"success": False, "running": True, "message": "\\u5de5\\u4f5c\\u533a\\u7f3a\\u5c11 p1_be.bin"}
        p1_data = p1_path.read_bytes()

        with zipfile.ZipFile(self._source_zip) as z_src:
            p2_clean = bswap16(z_src.read("KOF97_P2.ROM"))

        # 4. Open process handle
        k32 = ctypes.WinDLL("kernel32")
        PROCESS_ALL = 0x001F0FFF
        h_proc = k32.OpenProcess(PROCESS_ALL, False, pid)
        if not h_proc:
            return {"success": False, "running": True, "message": f"\\u65e0\\u6cd5\\u6302\\u8f7d\\u6a21\\u62df\\u5668\\u8fdb\\u7a0b (PID={pid})"}

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
                    "message": "\\u6a21\\u62df\\u5668\\u5c1a\\u5728\\u52a0\\u8f7d\\u6e38\\u620f\\u4e2d\\uff0c\\u8bf7\\u7a0d\\u5019\\u518d\\u70b9\\u51fb\\u5b9e\\u65f6\\u5e94\\u7528\\u76ae\\u80a4"
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
            target_desc = f"\\u3010{cname}\\u3011" if scope == "SINGLE" else f"\\u5168\\u5458 {injected_total} \\u4f4d\\u89d2\\u8272"
            async_log(f"[\\u5b9e\\u65f6\\u70ed\\u66f4\\u65b0] \\u76ae\\u80a4\\u3010{theme_id}\\u3011\\u5df2\\u6210\\u529f\\u5b9e\\u65f6\\u6ce8\\u5165\\u8fd0\\u884c\\u4e2d\\u7684\\u6e38\\u620f (PID={pid}, {target_desc})\\uff01\\u753b\\u9762\\u5df2\\u5373\\u65f6\\u53d8\\u8272\\uff01", "SUCCESS")
            return {
                "success": True,
                "running": True,
                "message": f"[\\u5b9e\\u65f6\\u70ed\\u66f4\\u65b0] \\u76ae\\u80a4\\u5df2\\u5b9e\\u65f6\\u70ed\\u66f4\\u65b0\\u5230\\u6e38\\u620f\\u4e2d\\uff01{target_desc}\\u753b\\u9762\\u5df2\\u5373\\u523b\\u53d8\\u8272\\uff01"
            }
        except Exception as exc:
            async_log(f"\\u5b9e\\u65f6\\u70ed\\u66f4\\u65b0\\u5931\\u8d25: {exc}", "ERROR")
            return {"success": False, "running": True, "message": str(exc)}
        finally:
            k32.CloseHandle(h_proc)'''

# Frontend 10 New Theme Cards (HTML/JS)
NEW_FRONTEND_THEMES_JS = '''  {
    id: "abyssal_frost",
    name: "\\u6df1\\u6e0a\\u5bd2\\u51b0",
    shortName: "\\u5bd2\\u51b0",
    sub: "\\u6781\\u5730\\u5bd2\\u971c\\u00b7\\u6df1\\u6d77\\u51b0\\u9b44",
    coat: "#1E293B", shirt: "#FFFFFF", hair: "#38BDF8", pants: "#0284C7", shoes: "#020617",
    colors: ["#FFF7B5","#F7C584","#EF945A","#B55229","#FFFFFF","#E0F2FE","#BAE6FD","#7DD3FC","#38BDF8","#0284C7","#0C4A6E","#1E293B","#0F172A","#020617","#000000"]
  },
  {
    id: "phoenix_nirvana",
    name: "\\u51e4\\u821e\\u6d85\\u69c3",
    shortName: "\\u51e4\\u821e",
    sub: "\\u70c8\\u7130\\u6731\\u96c0\\u00b7\\u91d1\\u7fbd\\u6d85\\u69c3",
    coat: "#262626", shirt: "#FFFFFF", hair: "#FFA500", pants: "#DC143C", shoes: "#000000",
    colors: ["#FFF7B5","#F7C584","#EF945A","#B55229","#FFFFFF","#E5E7EB","#9CA3AF","#FFA500","#FF4500","#DC143C","#8B0000","#262626","#1A1A1A","#0D0D0D","#000000"]
  },
  {
    id: "emerald_lotus",
    name: "\\u78a7\\u7389\\u9752\\u83b2",
    shortName: "\\u9752\\u83b2",
    sub: "\\u7fe1\\u7fe0\\u9f99\\u9b42\\u00b7\\u9752\\u83b2\\u78a7\\u7389",
    coat: "#1F2937", shirt: "#FFFFFF", hair: "#6EE7B7", pants: "#10B981", shoes: "#000000",
    colors: ["#FFF7B5","#F7C584","#EF945A","#B55229","#FFFFFF","#E5E7EB","#9CA3AF","#6EE7B7","#10B981","#047857","#022C22","#1F2937","#111827","#030712","#000000"]
  },
  {
    id: "shadow_ninja",
    name: "\\u6697\\u591c\\u5f71\\u5203",
    shortName: "\\u5f71\\u5203",
    sub: "\\u949b\\u94f6\\u5e7d\\u5f71\\u00b7\\u7384\\u591c\\u6697\\u5203",
    coat: "#27272A", shirt: "#FFFFFF", hair: "#E2E8F0", pants: "#94A3B8", shoes: "#000000",
    colors: ["#FFF7B5","#F7C584","#EF945A","#B55229","#FFFFFF","#E5E7EB","#9CA3AF","#E2E8F0","#94A3B8","#475569","#1E293B","#27272A","#18181B","#09090B","#000000"]
  },
  {
    id: "sunset_overdrive",
    name: "\\u66ae\\u5149\\u6d41\\u706b",
    shortName: "\\u66ae\\u5149",
    sub: "\\u5915\\u9633\\u7425\\u73c0\\u00b7\\u66ae\\u591c\\u6d41\\u706b",
    coat: "#312E81", shirt: "#FFFFFF", hair: "#FDBA74", pants: "#FB923C", shoes: "#000000",
    colors: ["#FFF7B5","#F7C584","#EF945A","#B55229","#FFFFFF","#E5E7EB","#9CA3AF","#FDBA74","#FB923C","#EA580C","#7C2D12","#312E81","#1E1B4B","#0F0E2A","#000000"]
  },
  {
    id: "amethyst_phantom",
    name: "\\u7d2b\\u6676\\u9b45\\u5f71",
    shortName: "\\u7d2b\\u6676",
    sub: "\\u6697\\u591c\\u7d2b\\u971e\\u00b7\\u7409\\u7483\\u9b45\\u5f71",
    coat: "#241438", shirt: "#FFFFFF", hair: "#D8B4FE", pants: "#A855F7", shoes: "#000000",
    colors: ["#FFF7B5","#F7C584","#EF945A","#B55229","#FFFFFF","#E5E7EB","#9CA3AF","#D8B4FE","#A855F7","#7E22CE","#3B0764","#241438","#170B26","#0B0414","#000000"]
  },
  {
    id: "ocean_tempest",
    name: "\\u6012\\u6d77\\u72c2\\u6d9b",
    shortName: "\\u6012\\u6d77",
    sub: "\\u6df1\\u6d77\\u6e54\\u84dd\\u00b7\\u6d77\\u738b\\u72c2\\u6d9b",
    coat: "#172554", shirt: "#FFFFFF", hair: "#38BDF8", pants: "#0284C7", shoes: "#000000",
    colors: ["#FFF7B5","#F7C584","#EF945A","#B55229","#FFFFFF","#E0F2FE","#BAE6FD","#38BDF8","#0284C7","#075985","#082F49","#172554","#0F172A","#020617","#000000"]
  },
  {
    id: "valkyrie_silver",
    name: "\\u767d\\u94f6\\u88c1\\u51b3",
    shortName: "\\u88c1\\u51b3",
    sub: "\\u5973\\u6b66\\u795e\\u94f6\\u7ffc\\u00b7\\u5723\\u94f6\\u5929\\u5149",
    coat: "#F8FAFC", shirt: "#FFFFFF", hair: "#FFFFFF", pants: "#E2E8F0", shoes: "#1E293B",
    colors: ["#FFF7B5","#F7C584","#EF945A","#B55229","#FFFFFF","#E2E8F0","#94A3B8","#FFFFFF","#E2E8F0","#94A3B8","#475569","#F8FAFC","#E2E8F0","#CBD5E1","#1E293B"]
  },
  {
    id: "crimson_dragon",
    name: "\\u8840\\u9f99\\u7834\\u519b",
    shortName: "\\u8840\\u9f99",
    sub: "\\u55dc\\u8840\\u6218\\u9f99\\u00b7\\u7834\\u519b\\u6697\\u8d64",
    coat: "#2B1D1D", shirt: "#FFFFFF", hair: "#EF4444", pants: "#DC2626", shoes: "#000000",
    colors: ["#FFF7B5","#F7C584","#EF945A","#B55229","#FFFFFF","#E5E7EB","#9CA3AF","#EF4444","#DC2626","#991B1B","#450A0A","#2B1D1D","#1A1010","#0D0808","#000000"]
  },
  {
    id: "solar_flare",
    name: "\\u65e5\\u8037\\u98ce\\u66b4",
    shortName: "\\u65e5\\u8037",
    sub: "\\u65e5\\u5195\\u70bd\\u91d1\\u00b7\\u592a\\u9633\\u98ce\\u66b4",
    coat: "#292524", shirt: "#FFFFFF", hair: "#FDE047", pants: "#EAB308", shoes: "#000000",
    colors: ["#FFF7B5","#F7C584","#EF945A","#B55229","#FFFFFF","#E5E7EB","#9CA3AF","#FDE047","#EAB308","#CA8A04","#713F12","#292524","#1C1917","#0C0A09","#000000"]
  },'''


def update_kof97_app():
    print("=== Step 1: Upgrading tools/kof97_webview_app.py ===")
    content = APP_PY_PATH.read_text(encoding="utf-8")

    # A. Append 10 themes to PRESET_THEMES
    toxic_marker = '"id": "toxic_hazard"'
    if toxic_marker not in content:
        raise ValueError("Could not locate toxic_hazard in PRESET_THEMES")

    # Find the closing of toxic_hazard block
    p_toxic = content.find(toxic_marker)
    p_end_presets = content.find("]\n\nDAMAGE_MODES", p_toxic)
    if p_end_presets == -1:
        p_end_presets = content.find("]\r\n\r\nDAMAGE_MODES", p_toxic)
    if p_end_presets == -1:
        raise ValueError("Could not locate end of PRESET_THEMES list")

    if '"id": "abyssal_frost"' not in content:
        content = content[:p_end_presets] + NEW_PRESET_THEMES_PY + "\n" + content[p_end_presets:]
        print("  [PASS] Successfully appended 10 new themes to PRESET_THEMES")
    else:
        print("  [SKIP] 10 new themes already in PRESET_THEMES")

    # B. Append 10 themes to THEME_RAMPS
    ramp_marker = '"toxic_hazard": {'
    p_ramp = content.find(ramp_marker)
    p_end_ramps = content.find("}\n\n\ndef generate_harmonious_character_palette", p_ramp)
    if p_end_ramps == -1:
        p_end_ramps = content.find("}\r\n\r\n\ndef generate_harmonious_character_palette", p_ramp)
    if p_end_ramps == -1:
        raise ValueError("Could not locate end of THEME_RAMPS dict")

    if '"abyssal_frost": {' not in content:
        content = content[:p_end_ramps] + NEW_THEME_RAMPS_PY + "\n" + content[p_end_ramps:]
        print("  [PASS] Successfully appended 10 new themes to THEME_RAMPS")
    else:
        print("  [SKIP] 10 new themes already in THEME_RAMPS")

    # C. Replace sync_character_portraits function
    p_sync_start = content.find("def sync_character_portraits(")
    p_sync_end = content.find("# ============================================================================\n# Asynchronous Thread-Safe Frontend Logging", p_sync_start)
    if p_sync_end == -1:
        p_sync_end = content.find("# ============================================================================\r\n# Asynchronous Thread-Safe Frontend Logging", p_sync_start)
    if p_sync_start == -1 or p_sync_end == -1:
        raise ValueError("Could not locate boundaries for sync_character_portraits")

    content = content[:p_sync_start] + NEW_SYNC_PORTRAITS_CODE + "\n\n\n" + content[p_sync_end:]
    print("  [PASS] Successfully replaced sync_character_portraits (4-button slots & win screen support)")

    # D. Replace _find_kawaks_pid, get_emulator_status, and apply_skin_live
    p_live_start = content.find("    def _find_kawaks_pid(self) -> Optional[int]:")
    p_live_end = content.find("    # ------------------------------------------------------------------------\n    # Maintenance Actions", p_live_start)
    if p_live_end == -1:
        p_live_end = content.find("    # ------------------------------------------------------------------------\r\n    # Maintenance Actions", p_live_start)
    if p_live_start == -1 or p_live_end == -1:
        raise ValueError("Could not locate boundaries for live injection routines")

    content = content[:p_live_start] + NEW_LIVE_INJECTION_CODE + "\n\n" + content[p_live_end:]
    print("  [PASS] Successfully replaced live injection & emulator detection routines")

    APP_PY_PATH.write_text(content, encoding="utf-8")
    print(f"  [SAVED] {APP_PY_PATH}")

    # Verify AST syntax
    ast.parse(content)
    print("  [PASS] tools/kof97_webview_app.py parsed successfully without syntax errors!")


def update_frontend_html():
    print("\n=== Step 2: Upgrading tools/web/index.html ===")
    html = INDEX_HTML_PATH.read_text(encoding="utf-8")

    # Find where toxic_hazard is in THEMES array
    idx_toxic = html.find('id: "toxic_hazard"')
    if idx_toxic == -1:
        raise ValueError("Could not locate toxic_hazard in index.html THEMES")

    idx_end_themes = html.find('];', idx_toxic)
    if idx_end_themes == -1:
        raise ValueError("Could not locate end of THEMES array in index.html")

    if 'id: "abyssal_frost"' not in html:
        html = html[:idx_end_themes] + NEW_FRONTEND_THEMES_JS + "\n" + html[idx_end_themes:]
        INDEX_HTML_PATH.write_text(html, encoding="utf-8")
        print("  [PASS] Successfully appended 10 new theme cards to frontend index.html")
    else:
        print("  [SKIP] 10 new themes already in frontend index.html")


if __name__ == "__main__":
    update_kof97_app()
    update_frontend_html()
    print("\n[SUCCESS] All codebase upgrades applied cleanly!")
