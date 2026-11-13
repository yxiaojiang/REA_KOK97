#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Frozen DIR-002 OKLCH natural costume painter and 15-color skin entry builders.
"""

import struct
from typing import Any, Dict, List, Optional, Tuple

from src.core.presets import THEME_KEYS, THEME_RAMPS
from src.core.roster import CHARACTER_PALETTE_SCHEMA, get_char_engine_info
from src.palette.color_utils import (
    _hex_luma,
    _oklch_word,
    _rgb5_to_hsv,
    _rgb_unit_to_oklch,
    _unit_luma,
    decode_lspc2,
    encode_lspc2,
    hex_to_rgb5,
    recolor_match_shade,
    theme_hsv,
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
