#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Skill / VFX palette slot discovery, luminous OKLCH shader, and hit-effect slot recolor."""

import struct
from typing import Any, Dict, List, Optional, Tuple

from src.core.presets import THEME_KEYS, VFX_PRESET_MAP
from src.core.roster import CHARACTER_ROSTER, get_char_engine_info
from src.palette.color_utils import (
    _hex_to_oklch,
    _lerp_hue,
    _oklch_gamut_word,
    _rgb_unit_to_oklch,
    decode_lspc2,
    encode_lspc2,
    lspc2_to_hex,
)

# Hardware sentinel / mask padding words embedded inside KOF97 VFX palette blocks:
# 0x0000 (0,0,0), 0x4553 (11,10,6), 0x305C (0,11,25), 0x304E (0,9,29),
# 0x20F0 (0,31,0), 0x4F00 (31,0,0), 0x4497 (9,18,14).
VFX_SENTINEL_WORDS = frozenset({0x0000, 0x4553, 0x305C, 0x304E, 0x20F0, 0x4F00, 0x4497})
VFX_SUBSLOT_OFFSETS: Tuple[int, ...] = (1, 2, 4, 5, 7, 8, 10, 11)
_VFX_MAP_CACHE: Dict[Tuple[int, int], Dict[int, Dict[str, Any]]] = {}

# Shared RAM owner cache offsets and common hit-effect slot group descriptors
VFX_RAM_F8_OWNER = 0x6E00
VFX_RAM_F9_OWNER = 0x6E02
VFX_RAM_FA_OWNER = 0x6E04
VFX_RAM_EL_OWNER = 0x6E06
VFX_RAM_IM_OWNER = 0x6E08

VFX_HIT_EFFECT_DARK_MASKS = frozenset({0x0010, 0x1210})
VFX_SMOKE_SPLIT_SLOTS = frozenset({0x0058, 0x005F})

# Ordered common effect groups stored per custom theme (+0x000..+0x21F, 17 * 32B)
VFX_COMMON_EFFECT_GROUPS: Tuple[Tuple[int, int, int, int, int, int, Tuple[int, ...]], ...] = (
    # (cache_off, common_off, cnt_m1, burn_pal_id, custom_burn_off, classic_burn_ptr, slot_ids)
    (VFX_RAM_F8_OWNER, 0x0000, 3, 0x00F8, 0x0220, 0x002FF5F0, (0x0057, 0x0058, 0x0059, 0x0061)),
    (VFX_RAM_F9_OWNER, 0x0080, 3, 0x00F9, 0x0420, 0x002FF7F0, (0x005B, 0x005F, 0x0067, 0x0068)),
    (VFX_RAM_EL_OWNER, 0x0100, 3, 0x0000, 0x0000, 0x00000000, (0x0052, 0x0062, 0x0053, 0x0054)),
    (VFX_RAM_IM_OWNER, 0x0180, 4, 0x0000, 0x0000, 0x00000000, (0x0051, 0x0055, 0x0054, 0x0064, 0x006A)),
    (VFX_RAM_FA_OWNER, 0x0000, 0xFFFF, 0x00FA, 0x0000, 0x002FF9F0, ()),
)


def _read_p2_slot_words15(p2_data: bytes, pal_id: int) -> List[int]:
    """Read color indices 1..15 (Big-Endian LSPC2 words) from a P2 palette slot."""
    off = 0x2CFFF0 + pal_id * 32
    return list(struct.unpack(">15H", p2_data[off + 2 : off + 32]))


def scan_character_vfx_slots(
    cid: int,
    p1_data: bytes,
    p2_clean: bytes,
) -> Dict[str, Any]:
    """
    Scan and whitelist clean VFX palette slots for one roster character.
    Reads P1 0x004956 directly (handling the 0x15..0x1A interleaving) and filters
    out solid placeholders, dark shadow silhouettes, and button-variant body flashes.
    """
    _, _, pal_idx = get_char_engine_info(cid)

    # 1. Read VFX base ID from P1 0x004956 (35 word entries: 0x00..0x22)
    vfx_base_off = 0x4956 + pal_idx * 2
    vfx_base_pid = struct.unpack(">H", p1_data[vfx_base_off : vfx_base_off + 2])[0]

    # 2. Scan vfx_base + 0..15 for real luminous projectile / flame / spark palettes
    vfx_slots: List[int] = []
    vfx_signatures: set = set()
    for s in range(16):
        pid = vfx_base_pid + s
        words = _read_p2_slot_words15(p2_clean, pid)
        active_words = [w for w in words if w not in VFX_SENTINEL_WORDS]
        if len(set(active_words)) < 2:
            continue
        has_energy = any(
            max(r, g, b) >= 16 and (r, g, b) != (31, 31, 31)
            for r, g, b, _ in (decode_lspc2(w) for w in active_words)
        )
        if not has_energy:
            continue
        vfx_slots.append(pid)
        vfx_signatures.add(tuple(words))

    # 3. Scan character button sub-slots in P1 0x00483E that hold pure uniform VFX
    btn_base_off = 0x483E + pal_idx * 8
    btn_pids = [
        struct.unpack(">H", p1_data[btn_base_off + b * 2 : btn_base_off + b * 2 + 2])[0]
        for b in range(4)
    ]
    char_sub_offsets: List[int] = []
    char_sub_slots: List[int] = []

    for sub in VFX_SUBSLOT_OFFSETS:
        banks = [tuple(_read_p2_slot_words15(p2_clean, bp + sub)) for bp in btn_pids]
        if len(set(banks)) != 1:
            # Differs per button -> character body/costume flash, never recolor as VFX
            continue
        words_tup = banks[0]
        active_words = [w for w in words_tup if w not in VFX_SENTINEL_WORDS]
        if len(set(active_words)) < 2:
            continue

        decoded = [decode_lspc2(w)[:3] for w in active_words]
        matches_vfx_bank = words_tup in vfx_signatures
        has_white_core = any(r == 31 and g >= 30 and b >= 27 for r, g, b in decoded)
        is_slash_spark = decoded[0][0] >= 30 and decoded[0][1] >= 30 and decoded[0][2] >= 28
        is_pure_flame = len(decoded) >= 5 and all(r >= 28 and r >= b + 4 for r, g, b in decoded)
        if matches_vfx_bank or has_white_core or is_slash_spark or is_pure_flame:
            char_sub_offsets.append(sub)
            for bp in btn_pids:
                char_sub_slots.append(bp + sub)

    return {
        "cid": cid,
        "pal_idx": pal_idx,
        "vfx_base_pid": vfx_base_pid,
        "btn_pids": btn_pids,
        "vfx_slots": vfx_slots,
        "char_sub_offsets": char_sub_offsets,
        "char_sub_slots": char_sub_slots,
        "all_slots": vfx_slots + char_sub_slots,
        "has_vfx": bool(vfx_slots or char_sub_slots),
    }


def build_character_vfx_map(p1_data: bytes, p2_clean: bytes) -> Dict[int, Dict[str, Any]]:
    """Build and cache the 36-character VFX palette slot map from P1 and clean P2."""
    cache_key = (len(p1_data), hash(bytes(p1_data[0x4956:0x499C])))
    cached = _VFX_MAP_CACHE.get(cache_key)
    if cached is not None:
        return cached
    result = {
        ch["id"]: scan_character_vfx_slots(ch["id"], p1_data, p2_clean)
        for ch in CHARACTER_ROSTER
    }
    _VFX_MAP_CACHE[cache_key] = result
    return result


def _dominant_palette_accent(colors: List[str]) -> Tuple[str, str]:
    """Extract a vivid inner/outer hex pair from a 15-color character palette."""
    best_hex = "#38BDF8"
    best_c = -1.0
    best_l = 0.65
    for hx in colors or []:
        lum, chm, _hue = _hex_to_oklch(hx)
        if chm > best_c and lum >= 0.35:
            best_c = chm
            best_l = lum
            best_hex = hx
    if best_c < 0.05:
        return "#F8FAFC", "#38BDF8"
    # Build bright core shifted slightly warmer/brighter and vivid outer hue
    lum, chm, hue = _hex_to_oklch(best_hex)
    inner_word = _oklch_gamut_word(min(0.95, max(0.88, lum + 0.22)), min(0.10, chm * 0.55), hue)
    outer_word = _oklch_gamut_word(min(0.76, max(0.58, best_l)), max(0.20, min(0.26, chm * 1.35)), hue)
    return lspc2_to_hex(inner_word), lspc2_to_hex(outer_word)


def resolve_vfx_hues(
    vfx_theme_id: str,
    skin_entry: Optional[Dict[str, Any]] = None,
    cid: Optional[int] = None,
    p1_data: Optional[bytes] = None,
    p2_clean: Optional[bytes] = None,
) -> Optional[Tuple[str, str]]:
    """
    Resolve (inner_hex, outer_hex) for a VFX preset. Returns None for 'classic'.
    Supports 'sync_skin' by reading THEME_KEYS, custom skin colors, or clean ROM clothes.
    """
    vid = str(vfx_theme_id or "classic")
    if vid == "classic":
        return None
    if vid == "sync_skin":
        entry = skin_entry or {}
        skin_tid = str(entry.get("themeId", "classic"))
        if skin_tid in THEME_KEYS:
            primary_hex, accent_hex = THEME_KEYS[skin_tid]
            return primary_hex, accent_hex
        colors = entry.get("colors")
        if isinstance(colors, list) and len(colors) == 15 and skin_tid != "classic":
            return _dominant_palette_accent(colors)
        if cid is not None and p1_data is not None and p2_clean is not None:
            _, _, pal_idx = get_char_engine_info(cid)
            off = 0x483E + pal_idx * 8
            base_pid = struct.unpack(">H", p1_data[off : off + 2])[0]
            clean_hexes = [lspc2_to_hex(w) for w in _read_p2_slot_words15(p2_clean, base_pid)]
            return _dominant_palette_accent(clean_hexes)
        return "#F8FAFC", "#38BDF8"

    preset = VFX_PRESET_MAP.get(vid)
    if preset:
        return preset["inner"], preset["outer"]
    return None


def recolor_vfx_palette(
    words15: List[int],
    inner_hex: str,
    outer_hex: str,
) -> List[int]:
    """
    Independent luminous gradient shader for VFX palettes.
    - Preserves sentinel mask/padding words verbatim.
    - Keeps pure white (31,31,31) and high-luminance core near-white incandescent.
    - Drives mid/high tiers to vivid neon chroma (up to ~0.24 OKLCH, gamut-safe)
      with smooth inner-to-outer dual-hue progression.
    """
    _li, c_in, h_in = _hex_to_oklch(inner_hex)
    _lo, c_out, h_out = _hex_to_oklch(outer_hex)
    inner_is_neutral = c_in < 0.03
    outer_is_neutral = c_out < 0.03
    if inner_is_neutral and not outer_is_neutral:
        h_in = h_out
    elif outer_is_neutral and not inner_is_neutral:
        h_out = h_in

    non_white_ls: List[float] = []
    for w in words15:
        if w in VFX_SENTINEL_WORDS:
            continue
        r5, g5, b5, _ = decode_lspc2(w)
        if r5 >= 31 and g5 >= 31 and b5 >= 31:
            continue
        sl, _, _ = _rgb_unit_to_oklch(r5 / 31.0, g5 / 31.0, b5 / 31.0)
        non_white_ls.append(sl)
    min_act_l = min(non_white_ls) if non_white_ls else 0.4
    max_act_l = max(non_white_ls) if non_white_ls else 0.9
    pale_source_only = len(non_white_ls) >= 2 and min_act_l > 0.62

    out_words: List[int] = []
    for w in words15:
        if w in VFX_SENTINEL_WORDS:
            out_words.append(w)
            continue
        r5, g5, b5, _dark = decode_lspc2(w)
        if r5 >= 31 and g5 >= 31 and b5 >= 31:
            out_words.append(0x7FFF)
            continue

        src_l, _src_c, _src_h = _rgb_unit_to_oklch(r5 / 31.0, g5 / 31.0, b5 / 31.0)
        # Progress from bright flame core (0.0) toward outer aura tail (1.0)
        grad_t = min(1.0, max(0.0, (0.94 - src_l) / 0.30))
        target_h = _lerp_hue(h_in, h_out, grad_t)

        if src_l >= 0.90:
            # Incandescent flame heart: bright, crisp, light inner glow tint
            target_l = max(src_l, 0.91)
            target_c = min(0.11, max(0.025, (0.985 - src_l) * 1.15))
        elif pale_source_only:
            # Pale cyan/pink sources lack dark steps; stretch midtones to saturated neon
            sub_max = min(0.899, max_act_l)
            rank_t = min(1.0, max(0.0, (sub_max - src_l) / max(0.04, sub_max - min_act_l)))
            target_l = min(0.87, max(0.54, 0.87 - 0.32 * rank_t))
            target_c = max(0.17, min(0.25, 0.16 + 0.08 * rank_t))
        elif src_l >= 0.45:
            # Neon mid/high energy body: preserve brightness hierarchy, lift chroma
            target_l = min(0.89, max(src_l, 0.48))
            peak_c = max(0.18, min(0.25, max(c_out, 0.21)))
            # Gentle peak in the middle luminous band (0.58..0.82)
            band = 1.0 - 0.18 * abs(src_l - 0.68) / 0.25
            target_c = max(0.17, min(0.25, peak_c * band))
        else:
            # Dark outer ember / trail outline: crisp dark tone with rich tint
            target_l = max(0.16, src_l * 0.96)
            target_c = min(0.21, max(0.06, src_l * 0.42))

        out_words.append(_oklch_gamut_word(target_l, target_c, target_h))

    return out_words


def generate_vfx_preview_ramp(
    vfx_theme_id: str,
    skin_entry: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """Generate a 6-step luminous preview hex ramp for UI glow badges."""
    pair = resolve_vfx_hues(vfx_theme_id, skin_entry)
    if not pair:
        pair = ("#FFFFFF", "#FF8C1A")
    sample_words = [
        encode_lspc2(31, 31, 31),
        encode_lspc2(31, 31, 24),
        encode_lspc2(31, 28, 17),
        encode_lspc2(31, 21, 6),
        encode_lspc2(26, 13, 1),
        encode_lspc2(14, 5, 0),
    ]
    recolored = recolor_vfx_palette(sample_words, pair[0], pair[1])
    return [lspc2_to_hex(w) for w in recolored]


def apply_vfx_palettes_to_p2(
    cid: int,
    vfx_theme_id: str,
    skin_entry: Optional[Dict[str, Any]],
    p1_data: bytes,
    p2_data: bytearray,
    p2_clean: bytes,
) -> int:
    """
    Patch whitelisted VFX palette slots (P1 0x004956 + pure-VFX 0x00483E sub-slots)
    into P2 ROM buffer for one character. Returns count of P2 slots written.
    """
    pair = resolve_vfx_hues(vfx_theme_id, skin_entry, cid=cid, p1_data=p1_data, p2_clean=p2_clean)
    if pair is None:
        return 0
    vfx_map = build_character_vfx_map(p1_data, p2_clean)
    info = vfx_map.get(cid)
    if not info or not info.get("has_vfx"):
        return 0

    inner_hex, outer_hex = pair
    written_slots = 0
    for pid in info["all_slots"]:
        if pid <= 0x00FF:
            # Never touch public UI / system palettes 0x0000..0x00FF
            continue
        clean_words = _read_p2_slot_words15(p2_clean, pid)
        new_words = recolor_vfx_palette(clean_words, inner_hex, outer_hex)
        p2_addr = 0x2CFFF0 + pid * 32
        p2_data[p2_addr + 2 : p2_addr + 32] = struct.pack(">15H", *new_words)
        written_slots += 1
    return written_slots


def _recolor_hit_effect_slot(
    pal_id: int,
    p2_clean: bytes,
    inner_hex: str,
    outer_hex: str,
) -> List[int]:
    """
    Recolor a single common effect or cyclic victim burn slot while keeping
    neutral grey smoke in split slots (0x0058/0x005F) and dark outline sentinels intact.
    """
    clean_words = _read_p2_slot_words15(p2_clean, pal_id)
    mask_positions = {
        idx: w for idx, w in enumerate(clean_words) if w in VFX_HIT_EFFECT_DARK_MASKS
    }
    if pal_id in VFX_SMOKE_SPLIT_SLOTS:
        smoke_head = list(clean_words[:9])
        flame_tail = recolor_vfx_palette(clean_words[9:15], inner_hex, outer_hex)
        out_words = smoke_head + flame_tail
    else:
        out_words = recolor_vfx_palette(clean_words, inner_hex, outer_hex)
    for idx, orig_w in mask_positions.items():
        out_words[idx] = orig_w
    return out_words
