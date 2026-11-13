#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Neo-Geo LSPC2-A2 color codec, HSV, Rec.601 luma, and OKLCH gamut utilities."""

import math
from typing import Tuple

from src.core.presets import THEME_KEYS


def encode_lspc2(r5: int, g5: int, b5: int, dark: int = 0) -> int:
    """
    Encode 5-bit RGB components (0..31) into a 16-bit Neo-Geo LSPC2-A2 color word.
    Bit 15: Dark bit (D)
    Bit 14: R0 (LSB of Red)
    Bit 13: G0 (LSB of Green)
    Bit 12: B0 (LSB of Blue)
    Bits 11..8: R4..R1 (top 4 bits of Red)
    Bits 7..4:  G4..G1 (top 4 bits of Green)
    Bits 3..0:  B4..B1 (top 4 bits of Blue)
    """
    r0 = r5 & 1
    r_hi = (r5 >> 1) & 0xF
    g0 = g5 & 1
    g_hi = (g5 >> 1) & 0xF
    b0 = b5 & 1
    b_hi = (b5 >> 1) & 0xF
    return ((dark & 1) << 15) | (r0 << 14) | (g0 << 13) | (b0 << 12) | (r_hi << 8) | (g_hi << 4) | b_hi


def decode_lspc2(val: int) -> Tuple[int, int, int, int]:
    """
    Decode a 16-bit Neo-Geo LSPC2-A2 color word into 5-bit RGB components (0..31) and dark bit.
    Returns (r5, g5, b5, dark).
    """
    dark = (val >> 15) & 1
    r0 = (val >> 14) & 1
    g0 = (val >> 13) & 1
    b0 = (val >> 12) & 1
    r5 = (((val >> 8) & 0xF) << 1) | r0
    g5 = (((val >> 4) & 0xF) << 1) | g0
    b5 = ((val & 0xF) << 1) | b0
    return r5, g5, b5, dark


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
