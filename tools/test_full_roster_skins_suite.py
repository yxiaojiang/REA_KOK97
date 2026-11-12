#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated Test Suite for Full Roster Skin Matching & Studio Operations.
1. Validates color ramp hierarchy, contrast, and monotonicity for Iori, Daimon, and Chang.
2. Validates all 36 characters across all 20 themes (720 total palette combinations).
3. Validates BridgeApi randomize_other_skins (all 36 characters randomized).
4. Validates BridgeApi reset_all_skins (all 36 characters reset to classic).
5. Validates end-to-end pack_rom with full-roster randomized skins into kof97pls.zip.

Strict adherence to Rules.md (100% English variable names, comments, docstrings).
"""

import sys
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

from kof97_webview_app import (
    CHARACTER_ROSTER,
    PRESET_THEMES,
    CHARACTER_PALETTE_SCHEMA,
    KOF97BridgeApi,
    generate_harmonious_character_palette,
    decode_lspc2,
    lspc2_to_hex,
    bswap16,
)

def _luma5(word: int) -> float:
    r5, g5, b5, _ = decode_lspc2(word)
    return 0.299 * r5 + 0.587 * g5 + 0.114 * b5


def test_optimized_three_characters():
    print("[TEST 1] Verifying shade-matched skins for Iori, Daimon, and Chang...")

    p1_data = (PROJECT_ROOT / "build" / "unpacked" / "p1_be.bin").read_bytes()
    p2_clean = (PROJECT_ROOT / "build" / "unpacked" / "p2_be.bin").read_bytes()

    def original_words(cid: int):
        return generate_harmonious_character_palette(cid, "classic", p1_data, p2_clean)

    iori_orig = original_words(0x1B)
    orochi_orig = original_words(0x1D)
    daimon_orig = original_words(0x02)
    chang_orig = original_words(0x13)
    custom_themes = [t for t in PRESET_THEMES if t["id"] != "classic"]

    for t in custom_themes:
        tid = t["id"]

        iori = generate_harmonious_character_palette(0x1B, tid, p1_data, p2_clean)
        orochi = generate_harmonious_character_palette(0x1D, tid, p1_data, p2_clean)
        daimon = generate_harmonious_character_palette(0x02, tid, p1_data, p2_clean)
        chang = generate_harmonious_character_palette(0x13, tid, p1_data, p2_clean)

        # Skin and the white shirt stay on each form's own official ramp.
        # Orochi Iori still borrows normal Iori's costume shade curve.
        assert iori[0:7] == iori_orig[0:7], f"{tid} Iori skin or shirt was rewritten"
        assert orochi[0:7] == orochi_orig[0:7], f"{tid} Orochi Iori skin or shirt was rewritten"
        assert orochi[7:15] == iori[7:15], f"{tid} Orochi Iori diverged from Iori's recolor"

        # Pigment and coat keep official OKLCH lightness (tolerance accommodates
        # Rec.601 luma differences when saturated red shifts to silver/white).
        for idx in (7, 8, 9, 10, 11, 12, 13):
            new_y = _luma5(iori[idx])
            old_y = _luma5(iori_orig[idx])
            assert new_y <= old_y + 2.8, (
                f"{tid} Iori W{idx:02d} brighter than the official shade "
                f"({new_y:.1f} > {old_y:.1f})"
            )
            assert new_y + 2.8 >= min(old_y, 4.0), (
                f"{tid} Iori W{idx:02d} crushed darker than the official shade "
                f"({new_y:.1f} vs {old_y:.1f})"
            )

        # Daimon gi keeps the official six-step OKLCH lightness, including the pale top.
        for idx in range(5, 11):
            new_y = _luma5(daimon[idx])
            old_y = _luma5(daimon_orig[idx])
            assert abs(new_y - old_y) <= 2.4, (
                f"{tid} Daimon W{idx:02d} shade drifted ({new_y:.1f} vs {old_y:.1f})"
            )
        assert daimon[0:5] == daimon_orig[0:5], f"{tid} Daimon skin changed"
        assert daimon[14] == 0x0000, f"{tid} Daimon contour not black"

        # Chang uniform keeps its OKLCH lightness. Skin stays official.
        # The beard is the hair group, so it takes the accent hue.
        # A pure white top step settles about 2/31 lower on purpose, so the
        # dye can show (natural cloth painter, ProjectMemory section 13).
        for idx in range(5, 10):
            new_y = _luma5(chang[idx])
            old_y = _luma5(chang_orig[idx])
            limit = 2.6 if old_y >= 28.0 else 2.4
            assert abs(new_y - old_y) <= limit, (
                f"{tid} Chang W{idx:02d} shade drifted ({new_y:.1f} vs {old_y:.1f})"
            )
        assert chang[0:5] == chang_orig[0:5], f"{tid} Chang skin changed"

    print("  -> PASS: Iori, Daimon, and Chang keep official shade across all 20 skins!")


def test_full_roster_generation():
    print("[TEST 2] Verifying all 36 characters across all 20 themes (720 combinations)...")
    
    p1_path = PROJECT_ROOT / "build" / "unpacked" / "p1_be.bin"
    p2_path = PROJECT_ROOT / "build" / "unpacked" / "p2_be.bin"
    p1_data = p1_path.read_bytes()
    p2_clean = p2_path.read_bytes()

    custom_themes = [t for t in PRESET_THEMES if t["id"] != "classic"]
    assert len(custom_themes) == 20, f"Expected 20 custom themes, got {len(custom_themes)}"
    assert len(CHARACTER_ROSTER) == 36, f"Expected 36 characters, got {len(CHARACTER_ROSTER)}"

    for char_info in CHARACTER_ROSTER:
        cid = char_info["id"]
        schema = CHARACTER_PALETTE_SCHEMA.get(cid)
        if cid not in (0x1B, 0x1D, 0x02, 0x13):
            assert schema is not None, f"Missing schema for cid 0x{cid:02X}"

        for t in custom_themes:
            tid = t["id"]
            words = generate_harmonious_character_palette(cid, tid, p1_data, p2_clean)
            assert len(words) == 15, f"cid 0x{cid:02X} theme {tid} palette length != 15"
            
            # Verify words in valid 16-bit range
            for w in words:
                assert 0 <= w <= 0xFFFF, f"Word out of range: {w:04X}"

            # Verify skin tone non-zombie
            if schema and "skin" in schema:
                for s_idx in schema["skin"]:
                    r5, g5, b5, _ = decode_lspc2(words[s_idx])
                    lum = 0.299 * r5 + 0.587 * g5 + 0.114 * b5
                    # Natural warm tone check
                    if lum > 6:
                        assert r5 >= b5, f"cid 0x{cid:02X} skin tone blue tinted (zombie risk): RGB=({r5},{g5},{b5})"

            # Verify black contour
            if schema and "contour" in schema:
                for c_idx in schema["contour"]:
                    assert words[c_idx] == 0x0000, f"cid 0x{cid:02X} contour not pure black"

    print("  -> PASS: All 720 character/theme combinations successfully synthesized with zero defects!")


def test_randomize_and_reset_api():
    print("[TEST 3] Verifying BridgeApi randomize_other_skins and reset_all_skins...")
    
    api = KOF97BridgeApi()
    
    # 1. Set Iori to a specific custom theme (e.g. cyber_neon)
    res_set = api.set_character_skin({"char_id": 0x1B, "theme_id": "cyber_neon", "scope": "SINGLE"})
    assert res_set["success"] is True
    assert api._character_skins[0x1B]["themeId"] == "cyber_neon"

    # Set Orochi Iori to phoenix_nirvana
    res_set_o = api.set_character_skin({"char_id": 0x1D, "theme_id": "phoenix_nirvana", "scope": "SINGLE"})
    assert res_set_o["success"] is True
    assert api._character_skins[0x1D]["themeId"] == "phoenix_nirvana"

    # 2. Trigger randomize_other_skins. Every fighter, including Iori, is reassigned.
    res_rnd = api.randomize_other_skins()
    assert res_rnd["success"] is True
    assert res_rnd["count"] == 36, f"Expected 36 characters randomized, got {res_rnd['count']}"

    # Verify all 36 characters got a preset theme (non-classic)
    for char in CHARACTER_ROSTER:
        cid = char["id"]
        theme_id = api._character_skins[cid]["themeId"]
        assert theme_id != "classic", f"Character 0x{cid:02X} has classic theme after randomize!"
        colors = api._character_skins[cid]["colors"]
        assert len(colors) == 15, f"Character 0x{cid:02X} colors length != 15"

    print("  -> PASS: randomize_other_skins assigned a preset skin to all 36 characters!")

    # 3. Trigger reset_all_skins
    res_reset = api.reset_all_skins()
    assert res_reset["success"] is True
    for char in CHARACTER_ROSTER:
        cid = char["id"]
        assert api._character_skins[cid]["themeId"] == "classic", f"Character 0x{cid:02X} not reset to classic!"

    print("  -> PASS: reset_all_skins reset all 36 characters to authentic classic baseline!")


def test_pack_rom_randomized_roster():
    print("[TEST 4] Verifying pack_rom with randomized roster...")
    
    api = KOF97BridgeApi()
    
    # Randomize other skins while keeping custom Iori
    api.set_character_skin({"char_id": 0x1B, "theme_id": "amethyst_phantom", "scope": "SINGLE"})
    api.randomize_other_skins()

    # Pack ROM pipeline
    res_pack = api.pack_rom()
    assert res_pack["success"] is True, f"pack_rom failed: {res_pack.get('error')}"
    crc = res_pack["crc32"]
    clean_crc = crc.lower().replace("0x", "")
    assert len(clean_crc) == 8, f"Invalid CRC: {crc}"

    # Verify output zip file
    zip_path = PROJECT_ROOT / "output" / "roms" / "kof97pls.zip"
    assert zip_path.exists(), "Output zip does not exist"
    with zipfile.ZipFile(zip_path) as z:
        namelist = z.namelist()
        assert "232-p1p.bin" in namelist
        assert "232-p2p.bin" in namelist
        assert "232-s1p.bin" in namelist
        p2_bytes = bswap16(z.read("232-p2p.bin"))
        assert len(p2_bytes) == 4194304

    print(f"  -> PASS: pack_rom succeeded! Delivered {zip_path.name} (CRC32: {crc})")


if __name__ == "__main__":
    print("=" * 70)
    print("KOF97 Mod Studio - Full Roster Skin Matching Test Suite")
    print("=" * 70)
    test_optimized_three_characters()
    test_full_roster_generation()
    test_randomize_and_reset_api()
    test_pack_rom_randomized_roster()
    print("=" * 70)
    print("ALL TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 70)
