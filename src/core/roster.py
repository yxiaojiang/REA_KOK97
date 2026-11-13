#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""36-character KOF97 roster metadata, engine ID mapping, and semantic slot schema."""

from typing import Dict, List, Tuple

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
