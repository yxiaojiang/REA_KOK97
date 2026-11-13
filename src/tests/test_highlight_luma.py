#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ROM-free checks for costume recolor luma.

Highlights brighter than mid gray keep their perceptual luma, easing
saturation when the new hue is darker. Dark saturated pigment keeps its
saturation and does not get brighter.
"""

import sys
import types
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.palette.color_utils import (
    _hex_hsv,
    _rgb5_to_hsv,
    hex_to_rgb5,
    recolor_match_shade,
)


def _luma5(r5: int, g5: int, b5: int) -> float:
    return 0.299 * r5 + 0.587 * g5 + 0.114 * b5


def _sat(r5: int, g5: int, b5: int) -> float:
    return _rgb5_to_hsv(r5, g5, b5)[1]


def _recolor(src_hex: str, theme_hex: str):
    r5, g5, b5 = hex_to_rgb5(src_hex)
    hue, theme_sat, _ = _hex_hsv(theme_hex)
    out = recolor_match_shade(r5, g5, b5, hue, theme_sat)
    return (r5, g5, b5), out


def test_yellow_highlight_keeps_luma_on_darker_hues():
    print("[TEST] Bright yellow highlight keeps luma on red, blue, and purple...")
    # Chang shirt highlight measured near #F8D068 (Y5 about 25, sat about 0.57).
    src_hex = "#F8D068"
    themes = {
        "crimson": "#DC2626",
        "azure": "#0284C7",
        "aurora": "#7E22CE",
        "amethyst": "#A855F7",
    }
    (r5, g5, b5), _ = _recolor(src_hex, "#DC2626")
    old_y = _luma5(r5, g5, b5)
    old_sat = _sat(r5, g5, b5)
    assert old_y > 20.0, f"fixture is not a bright highlight ({old_y:.1f})"
    assert old_sat >= 0.50, f"fixture is not on the saturated path ({old_sat:.2f})"

    for name, theme_hex in themes.items():
        _, (nr, ng, nb) = _recolor(src_hex, theme_hex)
        new_y = _luma5(nr, ng, nb)
        new_sat = _sat(nr, ng, nb)
        assert abs(new_y - old_y) <= 1.6, (
            f"{name} highlight luma drifted ({new_y:.1f} vs {old_y:.1f})"
        )
        assert new_sat < old_sat - 0.15, (
            f"{name} held saturation {new_sat:.2f} and collapsed the highlight"
        )

    # Crimson must read as lit pink cloth, not the dull same-sat red.
    _, (nr, ng, nb) = _recolor(src_hex, "#DC2626")
    assert ng >= 18 and nb >= 18, (
        f"crimson highlight is a dull red rgb5=({nr},{ng},{nb}), not lit cloth"
    )
    assert _luma5(nr, ng, nb) >= 23.0
    print("  -> PASS")


def test_reachable_highlight_keeps_saturation():
    print("[TEST] Highlight keeps saturation when the new hue can carry the luma...")
    (r5, g5, b5), (nr, ng, nb) = _recolor("#F8D068", "#EAB308")
    old_y = _luma5(r5, g5, b5)
    new_y = _luma5(nr, ng, nb)
    assert abs(new_y - old_y) <= 1.6, f"gold highlight luma drifted ({new_y:.1f} vs {old_y:.1f})"
    assert _sat(nr, ng, nb) >= _sat(r5, g5, b5) - 0.08, (
        f"gold highlight was washed out ({_sat(nr, ng, nb):.2f})"
    )
    print("  -> PASS")


def test_dark_pigment_stays_saturated_and_is_not_lifted():
    print("[TEST] Dark saturated pigment stays saturated and is not lifted...")
    # Official Iori red ramp, brightest first. All sit under mid gray.
    sources = ("#DE3A21", "#AD2910", "#7B1908", "#4A0000")
    themes = ("#DC2626", "#0284C7", "#7E22CE", "#A855F7", "#059669", "#EAB308", "#DB2777")

    for src_hex in sources:
        (r5, g5, b5), _ = _recolor(src_hex, "#DC2626")
        old_y = _luma5(r5, g5, b5)
        old_sat = _sat(r5, g5, b5)
        assert old_y / 31.0 <= 0.5, f"{src_hex} is not a dark pigment (Y5={old_y:.1f})"
        assert old_sat >= 0.80, f"{src_hex} is not saturated ({old_sat:.2f})"
        for theme_hex in themes:
            _, (nr, ng, nb) = _recolor(src_hex, theme_hex)
            new_y = _luma5(nr, ng, nb)
            new_sat = _sat(nr, ng, nb)
            assert new_y <= old_y + 1.2, (
                f"{src_hex} -> {theme_hex} lifted ({new_y:.1f} > {old_y:.1f})"
            )
            assert new_sat >= 0.75, (
                f"{src_hex} -> {theme_hex} became a pastel (sat {new_sat:.2f})"
            )
            assert new_y <= 16.0, (
                f"{src_hex} -> {theme_hex} brightened into a highlight ({new_y:.1f})"
            )

    # Amethyst on the brightest Iori red stays the solid pigment, not #D6B5FF.
    _, amethyst = _recolor("#DE3A21", "#A855F7")
    assert amethyst == (18, 5, 31), f"amethyst pigment shifted to rgb5={amethyst}"
    _, aurora = _recolor("#DE3A21", "#7E22CE")
    assert aurora == (18, 5, 31), f"aurora pigment shifted to rgb5={aurora}"

    # A darker hue that cannot carry the luma must still not lift the pigment.
    r5, g5, b5 = hex_to_rgb5("#DE3A21")
    nr, ng, nb = recolor_match_shade(r5, g5, b5, 240.0, 1.0)
    assert _luma5(nr, ng, nb) <= _luma5(r5, g5, b5) + 1.2
    assert _sat(nr, ng, nb) >= 0.75, f"pure blue washed the pigment (sat {_sat(nr, ng, nb):.2f})"
    print("  -> PASS")


def test_white_and_outline_stay_put():
    print("[TEST] Pure white and near-black outlines are not recolored...")
    hue, theme_sat, _ = _hex_hsv("#DC2626")
    assert recolor_match_shade(31, 31, 31, hue, theme_sat) == (31, 31, 31)
    assert recolor_match_shade(1, 0, 0, hue, theme_sat) == (1, 0, 0)
    print("  -> PASS")


def test_silver_theme_still_matches_luma():
    print("[TEST] Silver themes still match luma below the chroma cutoff...")
    r5, g5, b5 = hex_to_rgb5("#F8D068")
    hue, _, _ = _hex_hsv("#94A3B8")
    nr, ng, nb = recolor_match_shade(r5, g5, b5, hue, 0.10)
    assert abs(_luma5(nr, ng, nb) - _luma5(r5, g5, b5)) <= 1.6
    assert _sat(nr, ng, nb) <= 0.20, f"silver theme stayed chromatic (sat {_sat(nr, ng, nb):.2f})"
    print("  -> PASS")


def test_soft_cloth_still_matches_luma():
    print("[TEST] Soft cloth still eases saturation to keep luma...")
    # Pale low-sat cloth. Saturation is under 0.50, so this is the soft path.
    r5, g5, b5 = 31, 28, 22
    assert _sat(r5, g5, b5) < 0.50
    hue, theme_sat, _ = _hex_hsv("#DC2626")
    nr, ng, nb = recolor_match_shade(r5, g5, b5, hue, theme_sat)
    assert abs(_luma5(nr, ng, nb) - _luma5(r5, g5, b5)) <= 1.6, (
        f"soft cloth luma drifted ({_luma5(nr, ng, nb):.1f} vs {_luma5(r5, g5, b5):.1f})"
    )
    print("  -> PASS")


if __name__ == "__main__":
    print("=" * 70)
    print("Highlight luma / dark pigment recolor checks")
    print("=" * 70)
    test_yellow_highlight_keeps_luma_on_darker_hues()
    test_reachable_highlight_keeps_saturation()
    test_dark_pigment_stays_saturated_and_is_not_lifted()
    test_white_and_outline_stay_put()
    test_silver_theme_still_matches_luma()
    test_soft_cloth_still_matches_luma()
    print("=" * 70)
    print("ALL HIGHLIGHT LUMA CHECKS PASSED")
    print("=" * 70)
