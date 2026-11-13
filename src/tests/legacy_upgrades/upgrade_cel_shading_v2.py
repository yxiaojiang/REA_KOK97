#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Upgrade script V2 for KOF97 Mod Studio:
- Restores and exports THEME_RAMPS for all 20 themes.
- Implements anti-blowout cel-shading architecture matching Iori's visual balance.
- Accurately segments Athena (white sailor top, theme pleated skirt, accent ribbon).
- Accurately segments Kyo (white inner T-shirt, rich gakuran jacket, deep dark pants anchor).
- Accurately segments Shingo and all other fighters with dark trouser anchors and crisp white trims.
- Eliminates specular highlight blowout on clothing garments.
- 100% English variable names, comments, docstrings (Rules.md).
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_PY = PROJECT_ROOT / "tools" / "kof97_webview_app.py"

NEW_THEME_RAMPS_AND_SCHEMA = '''THEME_RAMPS: Dict[str, Dict[str, Any]] = {
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
    0x13: {"skin": [0, 1, 2, 3, 4], "primary": [5, 6, 7, 8, 9], "accent": [10, 11], "dark_anchor": [12, 13, 14]},
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


def generate_harmonious_character_palette(
    cid: int,
    theme_id: str,
    p1_data: bytes,
    p2_clean: bytes,
) -> List[int]:
    """
    Generate harmonious 15-word LSPC2 palette for any character and theme.
    Preserves authentic skin tones, avoids highlight blowout, and anchors
    pants and deep creases with rich dark shades (mirroring Iori's visual balance).
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

    pri = theme["primary"]
    acc = theme["accent"]
    drk = theme["dark"]

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

    # 4. Athena Asamiya (0x0C): Dedicated precision mapping
    # Words 0..4: Fair radiant skin
    # Words 5..8: Ribbon & Hairpins (Theme accent)
    # Words 9..11: Pure white sailor short-sleeve shirt (clean white -> crisp light gray)
    # Words 12..14: Pleated skirt & long hair (Theme rich primary midtones down to deep shadow)
    if cid == 0x0C:
        w_skin = list(orig_words[0:5])
        w_ribbon = [
            encode_lspc2(*hex_to_rgb5(acc[min(0, len(acc)-1)])),
            encode_lspc2(*hex_to_rgb5(acc[min(1, len(acc)-1)])),
            encode_lspc2(*hex_to_rgb5(acc[min(2, len(acc)-1)])),
            encode_lspc2(*hex_to_rgb5(acc[min(3, len(acc)-1)])),
        ]
        w_shirt = [
            encode_lspc2(31, 31, 31, dark=0),
            encode_lspc2(27, 27, 29, dark=0),
            encode_lspc2(18, 18, 20, dark=0),
        ]
        w_skirt = [
            encode_lspc2(*hex_to_rgb5(pri[min(1, len(pri)-1)])),
            encode_lspc2(*hex_to_rgb5(pri[min(3, len(pri)-1)])),
            encode_lspc2(*hex_to_rgb5(drk[min(1, len(drk)-1)])),
        ]
        return w_skin + w_ribbon + w_shirt + w_skirt

    # 5. Kyo Kusanagi (0x00) & '94 Kyo (0x23): Dedicated precision mapping
    # Word 0: Pure white inner T-shirt & glove accents
    # Words 1..4: Warm radiant muscle skin
    # Words 5..6: Natural dark brown & black hair
    # Words 7..9: Gakuran jacket (Rich controlled midtones, no blowout)
    # Words 10..13: Gakuran pants & deep coat folds (Deep dark anchor, like Iori coat!)
    # Word 14: Pure black outline
    if cid in (0x00, 0x23):
        w0 = encode_lspc2(31, 31, 31, dark=0)
        w_skin = list(orig_words[1:5])
        w_hair = [encode_lspc2(5, 3, 2, dark=0), encode_lspc2(0, 0, 0, dark=0)]
        w_jacket = [
            encode_lspc2(*hex_to_rgb5(pri[min(1, len(pri)-1)])),
            encode_lspc2(*hex_to_rgb5(pri[min(2, len(pri)-1)])),
            encode_lspc2(*hex_to_rgb5(pri[min(4, len(pri)-1)])),
        ]
        w_pants = [
            encode_lspc2(*hex_to_rgb5(drk[0])),
            encode_lspc2(*hex_to_rgb5(drk[min(1, len(drk)-1)])),
            encode_lspc2(*hex_to_rgb5(drk[min(2, len(drk)-1)])),
            encode_lspc2(1, 1, 1, dark=0),
        ]
        w14 = 0x0000
        return [w0] + w_skin + w_hair + w_jacket + w_pants + [w14]

    # 6. Universal character mapping with anti-blowout cel-shading:
    schema = CHARACTER_PALETTE_SCHEMA.get(cid)
    if not schema:
        return orig_words

    res = list(orig_words)

    # Standard clean white gradient for shirts / karate gi / bandages
    white_ramp = ["#FFFFFF", "#E2E8F0", "#CBD5E1", "#94A3B8", "#64748B", "#334155"]

    def map_slots_by_rank(slot_indices: List[int], target_ramp: List[str], avoid_specular: bool = False) -> None:
        if not slot_indices or not target_ramp:
            return
        ranked = sorted(
            slot_indices,
            key=lambda idx: (
                0.299 * decode_lspc2(orig_words[idx])[0]
                + 0.587 * decode_lspc2(orig_words[idx])[1]
                + 0.114 * decode_lspc2(orig_words[idx])[2]
            ),
            reverse=True,
        )
        usable = list(target_ramp)
        if avoid_specular:
            usable = [c for c in usable if hex_to_rgb5(c) != (31, 31, 31)]
            if len(usable) >= 4:
                usable = usable[1:]
        m = len(usable)
        n = len(ranked)
        for rank, s_idx in enumerate(ranked):
            r_idx = min(round(rank * (m - 1) / max(1, n - 1)), m - 1)
            res[s_idx] = encode_lspc2(*hex_to_rgb5(usable[r_idx]))

    # White details (shirts, gi, bandages)
    if "white_trim" in schema:
        map_slots_by_rank(schema["white_trim"], white_ramp)

    # Primary outfit: avoid pure white & drop extreme specular blowout
    if "primary" in schema:
        map_slots_by_rank(schema["primary"], pri, avoid_specular=True)

    # Dark anchor: pants, leather vests, deep folds (anchors character weight)
    if "dark_anchor" in schema:
        map_slots_by_rank(schema["dark_anchor"], drk)

    # Accent: headbands, hair, weapons, ribbons
    if "accent" in schema:
        map_slots_by_rank(schema["accent"], acc)

    # Hair
    if "hair" in schema:
        map_slots_by_rank(schema["hair"], drk)

    # Pure black contour silhouette
    if "contour" in schema:
        for c_idx in schema["contour"]:
            res[c_idx] = 0x0000

    return res
'''


def upgrade_app():
    with open(APP_PY, "r", encoding="utf-8") as f:
        src = f.read()

    # Find the block from CHARACTER_PALETTE_SCHEMA to generate_burst_character_palette
    # Or from where lspc2_to_hex ends to generate_burst_character_palette
    hook_str = 'def lspc2_to_hex(w: int) -> str:\n    """Convert 16-bit Neo-Geo LSPC2 word to #RRGGBB hex code."""\n    r5, g5, b5, _ = decode_lspc2(w)\n    r = round(r5 * 255 / 31)\n    g = round(g5 * 255 / 31)\n    b = round(b5 * 255 / 31)\n    return f"#{r:02X}{g:02X}{b:02X}"\n'
    idx_hook = src.find(hook_str)
    assert idx_hook != -1, "Could not locate lspc2_to_hex hook"
    insert_pos = idx_hook + len(hook_str)

    end_pos = src.find("def generate_burst_character_palette(")
    assert end_pos != -1, "Could not locate generate_burst_character_palette"

    new_src = src[:insert_pos] + "\n\n" + NEW_THEME_RAMPS_AND_SCHEMA + "\n\n" + src[end_pos:]

    with open(APP_PY, "w", encoding="utf-8") as f:
        f.write(new_src)

    print(f"[OK] Successfully upgraded {APP_PY.name} with THEME_RAMPS, CHARACTER_PALETTE_SCHEMA, and Cel-Shading V2!")


if __name__ == "__main__":
    upgrade_app()
