#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MAX mode burst flash palette and portrait/HUD avatar synchronization."""

import struct
from typing import List

from src.core.presets import THEME_KEYS
from src.palette.color_utils import (
    decode_lspc2,
    encode_lspc2,
    recolor_match_shade,
    theme_hsv,
)


def generate_burst_character_palette(
    cid: int,
    theme_id: str,
    base_words: List[int],
) -> List[int]:
    """
    Generate luminous burst flash palette variant for MAX mode (ABC burst).
    In KOF97, MAX mode burst alternates between Button A/B palette and Button C/D palette.
    By populating Button C/D with this luminous harmonic variant, the character pulses
    with radiant energy matching the custom skin, completely eliminating original skin flicker.
    """
    burst_words = []
    for w in base_words:
        r5, g5, b5, dark = decode_lspc2(w)
        # Check if color is part of skin tone
        is_skin = (r5 >= g5 >= b5 and r5 >= 10 and r5 - b5 >= 3)
        # Keep dark outlines dark so silhouette remains razor sharp
        is_dark_outline = (r5 <= 1 and g5 <= 1 and b5 <= 1)

        if is_dark_outline:
            burst_words.append(w)
        elif is_skin:
            # Subtle skin highlight (+2 steps)
            nr = min(31, r5 + 2)
            ng = min(31, g5 + 2)
            nb = min(31, b5 + 1)
            burst_words.append(encode_lspc2(nr, ng, nb, dark=0))
        else:
            # Radiant highlight for hair and garments (+30% luminance + 4)
            nr = min(31, round(r5 * 1.30 + 4))
            ng = min(31, round(g5 * 1.30 + 4))
            nb = min(31, round(b5 * 1.30 + 4))
            burst_words.append(encode_lspc2(nr, ng, nb, dark=0))

    return burst_words


def sync_character_portraits(
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

    # 4. Universal portraits keep the artwork's own shade and only take the hue.
    else:
        if theme_id not in THEME_KEYS:
            return
        primary_h, primary_s, _, _ = theme_hsv(theme_id)
        for btn_idx in range(4):
            for slot_off in (13, 14, 15):
                pal_id = base_pid + slot_off + btn_idx * 16
                addr = 0x2CFFF0 + pal_id * 32
                p_words = list(struct.unpack(">16H", p2_clean[addr:addr + 32]))
                for i in range(1, 16):
                    r, g, b, _ = decode_lspc2(p_words[i])
                    is_skin = (r >= g >= b and r >= 10 and r - b >= 3)
                    if is_skin:
                        continue
                    nr, ng, nb = recolor_match_shade(r, g, b, primary_h, primary_s)
                    if (nr, ng, nb) != (r, g, b):
                        p_words[i] = encode_lspc2(nr, ng, nb, dark=0)
                p2_data[addr:addr + 32] = struct.pack(">16H", *p_words)
