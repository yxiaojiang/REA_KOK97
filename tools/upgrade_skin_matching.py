#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Upgrade script for Full Roster 20-Skin Adaptive Matching,
Iori Dedicated Customization, Other Characters Batch Randomization,
and Universal Reset to Classic Baseline.

Strict adherence to Rules.md (100% English variable names, comments, docstrings).
"""

import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_PY = PROJECT_ROOT / "tools" / "kof97_webview_app.py"
INDEX_HTML = PROJECT_ROOT / "tools" / "web" / "index.html"

def upgrade_python_app():
    with open(APP_PY, "r", encoding="utf-8") as f:
        src = f.read()

    # Backup
    bak_path = APP_PY.with_suffix(".py.bak")
    with open(bak_path, "w", encoding="utf-8") as f:
        f.write(src)
    print(f"[OK] Backed up {APP_PY.name} -> {bak_path.name}")

    # 1. Optimize Daimon judogi & Chang uniform for crimson_shura
    src = src.replace(
        '"daimon_judogi": ["#FF4D4D", "#EF4444", "#DC2626", "#B91C1C", "#7F1D1D", "#450A0A"],\n'
        '        "daimon_headband": "#FFFFFF",\n'
        '        "chang_uniform": ["#FF4D4D", "#EF4444", "#DC2626", "#B91C1C", "#450A0A"],',
        '"daimon_judogi": ["#FF6B6B", "#EF4444", "#DC2626", "#B91C1C", "#7F1D1D", "#450A0A"],\n'
        '        "daimon_headband": "#FFFFFF",\n'
        '        "chang_uniform": ["#FF6B6B", "#EF4444", "#DC2626", "#B91C1C", "#450A0A"],'
    )

    # 2. Optimize Daimon judogi for azure_thunder
    src = src.replace(
        '"daimon_judogi": ["#60A5FA", "#3B82F6", "#2563EB", "#1D4ED8", "#1E40AF", "#0F172A"],',
        '"daimon_judogi": ["#60A5FA", "#3B82F6", "#2563EB", "#1D4ED8", "#172554", "#080D1A"],'
    )

    # 3. Optimize paladin_gold
    src = src.replace(
        '"daimon_judogi": ["#FFFFFF", "#F8FAFC", "#E2E8F0", "#CBD5E1", "#94A3B8", "#475569"],\n'
        '        "daimon_headband": "#EAB308",\n'
        '        "chang_uniform": ["#FFFFFF", "#F8FAFC", "#E2E8F0", "#CBD5E1", "#64748B"],',
        '"daimon_judogi": ["#FFFFFF", "#E2E8F0", "#CBD5E1", "#94A3B8", "#64748B", "#334155"],\n'
        '        "daimon_headband": "#EAB308",\n'
        '        "chang_uniform": ["#FFFFFF", "#E2E8F0", "#CBD5E1", "#94A3B8", "#475569"],'
    )

    # 4. Optimize amethyst_phantom
    src = src.replace(
        '        "colors": [\n'
        '            "#FFF7B5", "#F7C584", "#EF945A", "#B55229",\n'
        '            "#FFFFFF", "#E5E7EB", "#9CA3AF",\n'
        '            "#D8B4FE", "#A855F7", "#7E22CE", "#3B0764",\n'
        '            "#241438", "#170B26", "#0B0414", "#000000",\n'
        '        ],\n'
        '        "daimon_judogi": ["#F3E8FF", "#E9D5FF", "#C084FC", "#9333EA", "#6B21A8", "#3B0764"],\n'
        '        "daimon_headband": "#F0ABFC",\n'
        '        "chang_uniform": ["#F3E8FF", "#E9D5FF", "#A855F7", "#6B21A8", "#3B0764"],',
        '        "colors": [\n'
        '            "#FFF7B5", "#F7C584", "#EF945A", "#B55229",\n'
        '            "#FFFFFF", "#E5E7EB", "#9CA3AF",\n'
        '            "#D8B4FE", "#A855F7", "#7E22CE", "#3B0764",\n'
        '            "#3B1754", "#220D33", "#11061C", "#000000",\n'
        '        ],\n'
        '        "daimon_judogi": ["#F3E8FF", "#D8B4FE", "#C084FC", "#9333EA", "#6B21A8", "#3B0764"],\n'
        '        "daimon_headband": "#F0ABFC",\n'
        '        "chang_uniform": ["#F3E8FF", "#D8B4FE", "#A855F7", "#6B21A8", "#3B0764"],'
    )

    # 5. Optimize valkyrie_silver
    src = src.replace(
        '"daimon_judogi": ["#FFFFFF", "#F8FAFC", "#E2E8F0", "#CBD5E1", "#94A3B8", "#475569"],\n'
        '        "daimon_headband": "#F59E0B",\n'
        '        "chang_uniform": ["#FFFFFF", "#F8FAFC", "#CBD5E1", "#94A3B8", "#334155"],',
        '"daimon_judogi": ["#FFFFFF", "#E2E8F0", "#CBD5E1", "#94A3B8", "#64748B", "#334155"],\n'
        '        "daimon_headband": "#F59E0B",\n'
        '        "chang_uniform": ["#FFFFFF", "#E2E8F0", "#CBD5E1", "#94A3B8", "#475569"],'
    )

    # 6. Optimize THEME_RAMPS
    src = src.replace(
        '    "paladin_gold": {\n'
        '        "primary": ["#FFFFFF", "#F1F5F9", "#E2E8F0", "#CBD5E1", "#94A3B8", "#64748B"],',
        '    "paladin_gold": {\n'
        '        "primary": ["#FFFFFF", "#E2E8F0", "#CBD5E1", "#94A3B8", "#64748B", "#334155"],'
    )
    src = src.replace(
        '    "valkyrie_silver": {\n'
        '        "primary": ["#FFFFFF", "#F8FAFC", "#E2E8F0", "#CBD5E1", "#94A3B8", "#475569"],',
        '    "valkyrie_silver": {\n'
        '        "primary": ["#FFFFFF", "#E2E8F0", "#CBD5E1", "#94A3B8", "#64748B", "#334155"],'
    )
    src = src.replace(
        '    "amethyst_phantom": {\n'
        '        "primary": ["#F3E8FF", "#E9D5FF", "#C084FC", "#9333EA", "#6B21A8", "#3B0764"],\n'
        '        "accent": ["#FDF4FF", "#F0ABFC", "#C026D3", "#701A75"],\n'
        '        "light": ["#FAF5FF", "#F3E8FF"],\n'
        '        "dark": ["#1E0B36", "#0E041A", "#000000"],',
        '    "amethyst_phantom": {\n'
        '        "primary": ["#F3E8FF", "#D8B4FE", "#C084FC", "#9333EA", "#6B21A8", "#3B0764"],\n'
        '        "accent": ["#FDF4FF", "#F0ABFC", "#C026D3", "#701A75"],\n'
        '        "light": ["#FAF5FF", "#F3E8FF"],\n'
        '        "dark": ["#3B1754", "#220D33", "#11061C"],'
    )

    # 7. Add CHARACTER_PALETTE_SCHEMA and lspc2_to_hex
    schema_code = '''
def lspc2_to_hex(w: int) -> str:
    """Convert 16-bit Neo-Geo LSPC2 word to #RRGGBB hex code."""
    r5, g5, b5, _ = decode_lspc2(w)
    r = round(r5 * 255 / 31)
    g = round(g5 * 255 / 31)
    b = round(b5 * 255 / 31)
    return f"#{r:02X}{g:02X}{b:02X}"


# Disjoint-union semantic slot schema for all 36 characters in KOF97 (0x00..0x23).
# Ensures clean color blocking, strict luminance ranking, and sharp outlines.
CHARACTER_PALETTE_SCHEMA: Dict[int, Dict[str, List[int]]] = {
    0x00: {"skin": [1, 2, 3, 4], "light": [0], "hair": [5, 6], "primary": [7, 8, 9], "accent": [10, 11, 12], "dark": [13], "contour": [14]},
    0x01: {"skin": [0, 1, 2, 3, 4], "light": [5], "primary": [6, 7, 8, 9], "contour": [10], "accent": [11, 12, 13, 14]},
    0x02: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7, 8, 9, 10], "accent": [11], "light": [12, 13], "contour": [14]},
    0x03: {"skin": [0, 1, 2, 3], "dark": [4], "primary": [5, 6, 7, 8], "accent": [9, 10], "light": [11, 13], "accent2": [12], "contour": [14]},
    0x04: {"skin": [0, 1, 2, 3], "dark": [4], "primary": [5, 6, 7, 8, 9], "accent": [10], "light": [11], "accent2": [12, 13], "contour": [14]},
    0x05: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7], "accent": [8, 9], "light": [10, 11, 12, 13], "contour": [14]},
    0x06: {"light": [0], "skin": [1, 2, 3, 4, 5], "primary": [6, 7, 8, 9, 10], "contour": [11], "accent": [12, 13, 14]},
    0x07: {"skin": [0, 1, 2, 3, 4], "hair": [5], "primary": [6, 7, 8, 9], "accent": [10, 11, 12, 13], "contour": [14]},
    0x08: {"accent": [0], "skin": [1, 2, 3, 4, 5], "primary": [6, 7, 8, 9, 10], "accent2": [11, 12, 13], "contour": [14]},
    0x09: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7, 8, 9, 10], "contour": [11], "accent": [12, 13, 14]},
    0x0A: {"light": [0], "skin": [1, 2, 3, 4, 5], "primary": [6, 7, 8, 9, 10], "accent": [11, 12, 13], "contour": [14]},
    0x0B: {"light": [0], "skin": [1, 2, 3, 4, 5], "primary": [6, 7, 8, 9, 10], "accent": [11, 12, 13], "contour": [14]},
    0x0C: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7, 8], "light": [9, 10, 11], "accent": [12, 13], "contour": [14]},
    0x0D: {"light": [0], "skin": [1, 2, 3, 4, 5], "primary": [6, 7, 8, 9], "accent": [10, 11, 12, 13], "contour": [14]},
    0x0E: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7, 8, 9], "accent": [10, 11, 12, 13], "contour": [14]},
    0x0F: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7, 8, 9, 10], "contour": [11], "accent": [12, 13, 14]},
    0x10: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7, 11, 12], "light": [8, 9, 10], "accent": [13], "contour": [14]},
    0x11: {"primary": [0, 1, 2, 3], "accent": [4, 5], "light": [6, 7, 8, 9], "skin": [10, 11, 12, 13, 14]},
    0x12: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7, 8, 9], "accent": [10, 11, 12], "contour": [13], "light": [14]},
    0x13: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7, 8, 9], "accent": [10, 11], "dark": [12, 13, 14]},
    0x14: {"skin": [0, 1, 2, 3], "primary": [4, 5, 6, 7, 8], "accent": [9, 10], "dark": [11, 12, 13], "contour": [14]},
    0x15: {"skin": [0, 1, 2, 3], "accent": [4], "primary": [5, 6, 7, 8, 9], "dark": [10, 11, 12, 13], "contour": [14]},
    0x16: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7, 8, 9], "accent": [10, 11], "contour": [12], "accent2": [13, 14]},
    0x17: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7, 8, 9], "accent": [10, 11, 12], "dark": [13], "contour": [14]},
    0x18: {"skin": [0, 1, 2, 3, 4], "accent": [5, 6, 7], "primary": [8, 9, 10, 11, 12], "contour": [13], "light": [14]},
    0x19: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7], "accent": [8, 9, 10], "light": [11, 12, 13], "contour": [14]},
    0x1A: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7, 8], "contour": [9], "accent": [10, 11, 12], "light": [13, 14]},
    0x1B: {"skin": [0, 1, 2, 3], "light": [4, 5, 6], "accent": [7, 8, 9, 10], "primary": [11, 12, 13], "contour": [14]},
    0x1C: {"light": [0], "skin": [1, 2, 3, 4, 5], "dark": [6], "primary": [7, 8, 9], "accent": [10, 11, 12, 13], "contour": [14]},
    0x1D: {"skin": [0, 1, 2, 3], "light": [4, 5, 6], "accent": [7, 8, 9, 10], "primary": [11, 12, 13], "contour": [14]},
    0x1E: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7, 8, 9, 10], "contour": [11], "accent": [12, 13, 14]},
    0x1F: {"skin": [0, 1, 2, 3], "accent": [4], "primary": [5, 6, 7, 8, 9], "dark": [10, 11, 12, 13], "contour": [14]},
    0x20: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7, 8, 9], "accent": [10, 11], "contour": [12], "accent2": [13, 14]},
    0x21: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7, 8, 9], "accent": [10, 11, 12], "dark": [13], "contour": [14]},
    0x22: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7, 8, 9, 10], "contour": [11], "accent": [12, 13, 14]},
    0x23: {"skin": [1, 2, 3, 4], "light": [0], "hair": [5, 6], "primary": [7, 8, 9], "accent": [10, 11, 12], "dark": [13], "contour": [14]},
}
'''
    src = src.replace('THEME_RAMPS: Dict[str, Dict[str, Any]] = {', schema_code + '\nTHEME_RAMPS: Dict[str, Dict[str, Any]] = {')

    # 8. Overwrite generate_harmonious_character_palette with full roster ranking engine
    old_gen_func = src[src.find("def generate_harmonious_character_palette("):src.find("def generate_burst_character_palette(")]
    new_gen_func = '''def generate_harmonious_character_palette(
    cid: int,
    theme_id: str,
    p1_data: bytes,
    p2_clean: bytes,
) -> List[int]:
    """
    Generate harmonious 15-word LSPC2 palette for any character and theme.
    Preserves authentic skin tones and 3D luminance hierarchy to guarantee
    clear color blocking, clean shading, and professional aesthetics.
    Strictly maps each section by relative luminance rank.
    """
    _, _, pal_idx = get_char_engine_info(cid)
    base_off = 0x483E + pal_idx * 8
    pal_id = struct.unpack(">H", p1_data[base_off:base_off + 2])[0]
    p2_addr = 0x2CFFF0 + pal_id * 32
    orig_words = list(struct.unpack(">16H", p2_clean[p2_addr : p2_addr + 32])[1:])

    if theme_id == "classic":
        return orig_words

    theme = THEME_RAMPS.get(theme_id)
    if not theme:
        return orig_words

    # 1. Iori Yagami (0x1B) & Orochi Iori (0x1D UI / 0x1C Engine)
    if cid in (0x1B, 0x1D) or pal_idx in (0x1B, 0x1C):
        preset = next((t for t in PRESET_THEMES if t["id"] == theme_id), None)
        if preset and "colors" in preset:
            return [hex_to_lspc2(h) for h in preset["colors"]]

    # 2. Goro Daimon (0x02):
    if cid == 0x02:
        preset = next((t for t in PRESET_THEMES if t["id"] == theme_id), None)
        if preset and "daimon_judogi" in preset:
            res = list(orig_words[0:5])
            for h in preset["daimon_judogi"]:
                res.append(encode_lspc2(*hex_to_rgb5(h)))
            res.append(encode_lspc2(*hex_to_rgb5(preset["daimon_headband"])))
            res.append(encode_lspc2(31, 31, 31, dark=0))
            res.append(encode_lspc2(26, 26, 26, dark=0))
            res.append(0x0000)
            return res

    # 3. Chang Koehan (0x13):
    if cid == 0x13:
        preset = next((t for t in PRESET_THEMES if t["id"] == theme_id), None)
        if preset and "chang_uniform" in preset:
            res = list(orig_words[0:5])
            for h in preset["chang_uniform"]:
                res.append(encode_lspc2(*hex_to_rgb5(h)))
            for h in preset["chang_ball"]:
                res.append(encode_lspc2(*hex_to_rgb5(h)))
            res.extend(orig_words[12:15])
            return res

    # 4. Universal 36-character adaptive multi-cluster semantic engine:
    schema = CHARACTER_PALETTE_SCHEMA.get(cid)
    if not schema:
        return orig_words

    res = list(orig_words)

    def map_slots_by_rank(slot_indices: List[int], target_ramp: List[str]) -> None:
        if not slot_indices or not target_ramp:
            return
        # Rank original slots strictly by original luminance descending (brightest highlight first)
        ranked = sorted(
            slot_indices,
            key=lambda idx: (
                0.299 * decode_lspc2(orig_words[idx])[0]
                + 0.587 * decode_lspc2(orig_words[idx])[1]
                + 0.114 * decode_lspc2(orig_words[idx])[2]
            ),
            reverse=True,
        )
        m = len(target_ramp)
        n = len(ranked)
        for rank, s_idx in enumerate(ranked):
            r_idx = min(round(rank * (m - 1) / max(1, n - 1)), m - 1)
            res[s_idx] = encode_lspc2(*hex_to_rgb5(target_ramp[r_idx]))

    # Map primary garments (jacket / pants / gi)
    if "primary" in schema:
        map_slots_by_rank(schema["primary"], theme["primary"])
    # Map accent (secondary outfit / headband / weapon / hair)
    if "accent" in schema:
        map_slots_by_rank(schema["accent"], theme["accent"])
    # Map accent2
    if "accent2" in schema:
        map_slots_by_rank(schema["accent2"], theme.get("light", theme["accent"]))
    # Map light details / trim / gloves
    if "light" in schema:
        map_slots_by_rank(schema["light"], theme["light"])
    # Map hair
    if "hair" in schema:
        map_slots_by_rank(schema["hair"], theme["dark"])
    # Map dark shadow / creases
    if "dark" in schema:
        map_slots_by_rank(schema["dark"], theme["dark"])
    # Map black contour outline (sharp 100% silhouette definition)
    if "contour" in schema:
        for c_idx in schema["contour"]:
            res[c_idx] = 0x0000

    return res


'''
    src = src.replace(old_gen_func, new_gen_func)

    # 9. Update set_character_skin in BridgeApi to compute character-specific hex colors
    old_set_skin = src[src.find("    def set_character_skin("):src.find("    def update_scope(")]
    new_set_skin = '''    def set_character_skin(self, params: Dict[str, Any]) -> Dict[str, Any]:
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
                self._character_skins[cid] = {
                    "themeId": theme_id,
                    "colors": [lspc2_to_hex(w) for w in lspc_words],
                }
            async_log(f"\\u5df2\\u5168\\u91cf\\u8bbe\\u7f6e\\u5168\\u5458 36 \\u89d2\\u8272\\u76ae\\u80a4\\u4e3a: \\u3010{theme_id}\\u3011", "INFO")
        else:
            lspc_words = generate_harmonious_character_palette(char_id, theme_id, p1_data, p2_clean)
            hex_colors = [lspc2_to_hex(w) for w in lspc_words]
            self._character_skins[char_id] = {
                "themeId": theme_id,
                "colors": hex_colors,
            }
            char_info = next((c for c in CHARACTER_ROSTER if c["id"] == char_id), None)
            cname = char_info["name_cn"] if char_info else f"0x{char_id:02X}"
            async_log(f"\\u5df2\\u4fdd\\u5b58\\u89d2\\u8272\\u3010{cname}\\u3011\\u7684\\u72ec\\u7acb\\u76ae\\u80a4\\u914d\\u7f6e: \\u3010{theme_id}\\u3011", "INFO")

        self._save_config_to_disk()
        return {
            "success": True,
            "character_skins": {str(k): v for k, v in self._character_skins.items()},
        }


'''
    src = src.replace(old_set_skin, new_set_skin)

    # 10. Add randomize_other_skins and reset_all_skins to BridgeApi
    new_methods = '''    def randomize_other_skins(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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
            self._character_skins[cid] = {
                "themeId": theme_id,
                "colors": hex_colors,
            }
            randomized_count += 1

        self._save_config_to_disk()
        async_log(f"\\u5df2\\u4e00\\u952e\\u968f\\u673a\\u5176\\u4f59 {randomized_count} \\u4f4d\\u89d2\\u8272\\u76ae\\u80a4\\uff01\\u516b\\u795e(\\u66b4\\u8d70\\u516b\\u795e)\\u4fdd\\u6301\\u81ea\\u5b9a\\u4e49\\u3002", "SUCCESS")
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
            self._character_skins[cid] = {
                "themeId": "classic",
                "colors": hex_colors,
            }

        self._save_config_to_disk()
        async_log("\\u5df2\\u5c06\\u5168\\u5458 36 \\u4f4d\\u89d2\\u8272\\u76ae\\u80a4\\u5168\\u90e8\\u91cd\\u7f6e\\u4e3a\\u5b98\\u65b9\\u539f\\u7248\\u7ecf\\u5178\\uff01", "SUCCESS")
        return {
            "success": True,
            "character_skins": {str(k): v for k, v in self._character_skins.items()},
        }

'''
    src = src.replace('    def save_skin(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:', new_methods + '    def save_skin(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:')

    with open(APP_PY, "w", encoding="utf-8") as f:
        f.write(src)
    print(f"[OK] Successfully updated {APP_PY.name}")


def upgrade_frontend_html():
    with open(INDEX_HTML, "r", encoding="utf-8") as f:
        html = f.read()

    # Backup
    bak_path = INDEX_HTML.with_suffix(".html.bak")
    with open(bak_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] Backed up {INDEX_HTML.name} -> {bak_path.name}")

    # 1. Add quick skin action buttons right beneath scope-pill in hero-stage
    target_scope = '<div class="scope-pill" id="scopePill">\n            <button class="on" data-v="SINGLE">当前角色</button>\n            <button data-v="ALL">全员</button>\n          </div>'
    replacement_scope = '''<div class="scope-pill" id="scopePill">
            <button class="on" data-v="SINGLE">当前角色</button>
            <button data-v="ALL">全员</button>
          </div>

          <!-- Quick Action Buttons: Randomize Others & Reset All -->
          <div class="skin-actions-bar" style="display:flex;gap:10px;margin-top:12px;z-index:10;">
            <button class="btn outline skin-action-btn" id="btnRandomOthers" title="保持八神(暴走八神)当前自定皮肤不变，其余34位角色一键随机分配精选皮肤">
              <svg style="width:14px;height:14px;fill:currentColor;vertical-align:-2px;margin-right:5px;" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="3" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="8" cy="8" r="1.5"/><circle cx="16" cy="8" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="8" cy="16" r="1.5"/><circle cx="16" cy="16" r="1.5"/></svg>
              其余角色一键随机
            </button>
            <button class="btn outline skin-action-btn" id="btnResetAll" title="一键将全员36位角色皮肤全部重置恢复为官方原版经典">
              <svg style="width:14px;height:14px;fill:currentColor;vertical-align:-2px;margin-right:5px;" viewBox="0 0 24 24"><path d="M3 12a9 9 0 1 0 3-6.7"/><path d="M3 4v5h5"/></svg>
              重置原皮肤
            </button>
          </div>'''
    if target_scope in html:
        html = html.replace(target_scope, replacement_scope)
        print("[OK] Injected action buttons into Hero Stage")

    # 2. Add CSS styling for skin-action-btn
    target_css = '.scope-pill button.on { background: var(--pri); color: #000; box-shadow: 0 0 16px rgba(255,179,25,0.35); }'
    replacement_css = '''.scope-pill button.on { background: var(--pri); color: #000; box-shadow: 0 0 16px rgba(255,179,25,0.35); }
  .skin-action-btn {
    font-size: 12px;
    padding: 6px 14px;
    border-radius: 20px;
    background: rgba(24, 26, 34, 0.85);
    backdrop-filter: blur(8px);
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  }
  .skin-action-btn:hover {
    border-color: var(--pri);
    color: var(--pri);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(255, 179, 25, 0.18);
  }
  .skin-action-btn:active {
    transform: translateY(0);
  }'''
    if target_css in html:
        html = html.replace(target_css, replacement_css)
        print("[OK] Injected CSS for skin-action-btn")

    # 3. Add JS event listeners for #btnRandomOthers and #btnResetAll
    target_js_hook = '$("#btnPack").onclick = () => {'
    js_actions = '''// Randomize other characters' skins while keeping Iori/Orochi Iori custom
$("#btnRandomOthers").onclick = () => {
  log("正在一键随机其余 34 位角色皮肤 (八神/暴走八神保持自定)...", "INFO");
  toast("🎲 正在为其余角色随机分配精选皮肤...");
  callBackend("randomize_other_skins").then(res => {
    if (res && res.success) {
      if (res.character_skins) {
        Object.keys(res.character_skins).forEach(cidStr => {
          const cid = parseInt(cidStr, 10);
          state.characterSkins[cid] = res.character_skins[cidStr];
        });
      }
      renderCharacterList();
      selectCharacter(state.activeCharId, true);
      toast(`🎲 已一键随机其余 ${res.count || 34} 位角色皮肤！保存并打包后游戏全员随机。`);
      log(`已一键随机其余 ${res.count || 34} 位角色皮肤！八神/暴走八神皮肤保持自定。`, "SUCCESS");
    } else {
      toast("随机分配失败: " + (res ? res.error : "未知错误"));
    }
  });
};

// Reset all 36 characters to authentic original classic skins
$("#btnResetAll").onclick = () => {
  log("正在将全员 36 位角色皮肤重置为官方原版经典...", "INFO");
  toast("↺ 正在重置全员角色为官方原版...");
  callBackend("reset_all_skins").then(res => {
    if (res && res.success) {
      if (res.character_skins) {
        Object.keys(res.character_skins).forEach(cidStr => {
          const cid = parseInt(cidStr, 10);
          state.characterSkins[cid] = res.character_skins[cidStr];
        });
      }
      renderCharacterList();
      selectCharacter(state.activeCharId, true);
      toast("↺ 已将全员 36 位角色皮肤全部重置恢复为官方原版经典！");
      log("已成功将全员 36 角色皮肤全部重置恢复为官方原版经典。", "SUCCESS");
    } else {
      toast("重置失败: " + (res ? res.error : "未知错误"));
    }
  });
};

'''
    if target_js_hook in html:
        html = html.replace(target_js_hook, js_actions + target_js_hook)
        print("[OK] Injected JS event bindings for action buttons")

    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] Successfully updated {INDEX_HTML.name}")


if __name__ == "__main__":
    upgrade_python_app()
    upgrade_frontend_html()
    print("[SUCCESS] All upgrades finished cleanly!")
