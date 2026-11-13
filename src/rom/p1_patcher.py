#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P1 68000 combat/unlock patches and 0x0F0000 dynamic hit-effect VFX code cave."""

import struct
from typing import Any, Callable, Dict, List, Optional, Tuple

from src.core.presets import DAMAGE_MODES
from src.core.roster import CHARACTER_ROSTER, get_char_engine_info
from src.palette.vfx_shader import (
    VFX_COMMON_EFFECT_GROUPS,
    _read_p2_slot_words15,
    _recolor_hit_effect_slot,
    build_character_vfx_map,
    resolve_vfx_hues,
)

VFX_HIT_EFFECT_CAVE_BASE = 0x0F0000
VFX_HIT_EFFECT_CAVE_SIZE = 0x10000
VFX_THEME_ENTRY_STRIDE = 0x620

# Exact 6-byte P1 hook sites and their clean official machine code bytes
VFX_HIT_HOOK_ORIGINALS: Tuple[Tuple[str, int, bytes, str], ...] = (
    ("match_init_hook", 0x0251C4, bytes.fromhex("3b7cffff040c"), "match_init_hook"),
    ("f8_ptr_hook", 0x0041AE, bytes.fromhex("41f9002ff5f0"), "f8_ptr_hook"),
    ("f9_ptr_hook", 0x0041E6, bytes.fromhex("41f9002ff7f0"), "f9_ptr_hook"),
    ("fa_ptr_hook", 0x004254, bytes.fromhex("41f9002ff9f0"), "fa_ptr_hook"),
    ("impact_0", 0x012E64, bytes.fromhex("247b102c3212"), "on_impact_hook"),
    ("fire_0", 0x012F18, bytes.fromhex("197c00f8003a"), "on_fire_burn_hook"),
    ("fire_1", 0x012F8C, bytes.fromhex("197c00f8003a"), "on_fire_burn_hook"),
    ("fire_2", 0x013108, bytes.fromhex("197c00f8003a"), "on_fire_burn_hook"),
    ("fire_3", 0x013174, bytes.fromhex("197c00f8003a"), "on_fire_burn_hook"),
    ("purple_0", 0x012F9E, bytes.fromhex("197c00f9003a"), "on_purple_burn_hook"),
    ("purple_1", 0x01314E, bytes.fromhex("197c00f9003a"), "on_purple_burn_hook"),
    ("purple_2", 0x01316C, bytes.fromhex("197c00f9003a"), "on_purple_burn_hook"),
    ("elec_0", 0x012F42, bytes.fromhex("002c000200e3"), "on_elec_shock_hook"),
    ("elec_1", 0x013184, bytes.fromhex("002c000200e3"), "on_elec_shock_hook"),
    ("elec_2", 0x03376E, bytes.fromhex("002c000200e3"), "on_elec_shock_hook"),
    ("fa_flash", 0x01317C, bytes.fromhex("197c00fa003a"), "on_fa_flash_hook"),
)

# RAM owner cache addresses imported via vfx_shader constants
from src.palette.vfx_shader import (
    VFX_RAM_F8_OWNER,
    VFX_RAM_F9_OWNER,
    VFX_RAM_FA_OWNER,
    VFX_RAM_IM_OWNER,
)


class _M68kCodeCaveBuilder:
    """Minimal relocatable Motorola 68000 assembler for P1 code caves."""

    def __init__(self, base: int) -> None:
        self.base = base
        self.buf = bytearray()
        self.labels: Dict[str, int] = {}
        self.fixups: List[Tuple[int, str, str]] = []

    @property
    def pc(self) -> int:
        return self.base + len(self.buf)

    def label(self, name: str) -> None:
        if name in self.labels:
            raise ValueError(f"Duplicate 68k label: {name}")
        self.labels[name] = self.pc

    def w(self, *words: int) -> None:
        for val in words:
            self.buf += struct.pack(">H", val & 0xFFFF)

    def l(self, *longs: int) -> None:
        for val in longs:
            self.buf += struct.pack(">I", val & 0xFFFFFFFF)

    def b_branch(self, op_hi: int, target: str) -> None:
        self.w(op_hi)
        self.fixups.append((len(self.buf), "wrel", target))
        self.w(0)

    def dbra(self, dreg: int, target: str) -> None:
        self.w(0x51C8 | (dreg & 7))
        self.fixups.append((len(self.buf), "wrel", target))
        self.w(0)

    def ref_abs32(self, opcode_word: int, target: str) -> None:
        self.w(opcode_word)
        self.fixups.append((len(self.buf), "abs32", target))
        self.l(0)

    def finalize(self) -> bytes:
        for pos, kind, target in self.fixups:
            taddr = self.labels[target]
            if kind == "wrel":
                disp = taddr - (self.base + pos)
                if not (-32768 <= disp <= 32767):
                    raise ValueError(f"Branch displacement out of range for {target}: {disp}")
                self.buf[pos : pos + 2] = struct.pack(">h", disp)
            elif kind == "abs32":
                self.buf[pos : pos + 4] = struct.pack(">I", taddr)
        return bytes(self.buf)


def build_hit_effect_vfx_p1_patch(
    character_skins: Dict[int, Dict[str, Any]],
    p1_data: bytes,
    p2_clean: bytes,
) -> Optional[Dict[str, Any]]:
    """
    Build the P1 0x0F0000 code cave and deduplicated theme tables for dynamic
    on-hit elemental burn/shock/spark palette switching. Returns None if every
    character uses the classic VFX theme.
    """
    vfx_map = build_character_vfx_map(p1_data, p2_clean)
    char_slot_table = [0xFFFF] * 36
    pair_to_idx: Dict[Tuple[str, str], int] = {}
    unique_pairs: List[Tuple[str, str]] = []
    orochi_pair: Optional[Tuple[str, str]] = None

    for char_info in CHARACTER_ROSTER:
        cid = int(char_info["id"])
        skin_entry = character_skins.get(cid)
        if not skin_entry:
            continue
        vfx_theme = skin_entry.get("vfxTheme", "classic")
        if vfx_theme == "classic":
            continue
        pair = resolve_vfx_hues(
            vfx_theme, skin_entry, cid=cid, p1_data=p1_data, p2_clean=p2_clean
        )
        if pair is None:
            continue
        cinfo = vfx_map.get(cid)
        if not cinfo or not cinfo.get("has_vfx"):
            continue
        eid, alt_flag, pal_idx = get_char_engine_info(cid)
        runtime_slot = 35 if (eid == 0 and alt_flag != 0) else pal_idx
        if pair not in pair_to_idx:
            pair_to_idx[pair] = len(unique_pairs)
            unique_pairs.append(pair)
        char_slot_table[runtime_slot] = pair_to_idx[pair]
        if runtime_slot == 30:
            orochi_pair = pair

    if not unique_pairs:
        return None

    asm = _M68kCodeCaveBuilder(VFX_HIT_EFFECT_CAVE_BASE)

    # 1. match_init_hook: execute replaced insn & reset owner caches to 0xFFFE
    asm.label("match_init_hook")
    asm.w(0x3B7C, 0xFFFF, 0x040C)
    asm.w(0x2B7C, 0xFFFE, 0xFFFE, VFX_RAM_F8_OWNER)
    asm.w(0x2B7C, 0xFFFE, 0xFFFE, VFX_RAM_FA_OWNER)
    asm.w(0x3B7C, 0xFFFE, VFX_RAM_IM_OWNER)
    asm.w(0x4E75)

    # 2. f8_ptr_hook / f9_ptr_hook / fa_ptr_hook (returns table ptr in a0, preserves d0)
    for hook_name, cache_reg, burn_off, classic_addr in (
        ("f8_ptr_hook", VFX_RAM_F8_OWNER, 0x0220, 0x002FF5F0),
        ("f9_ptr_hook", VFX_RAM_F9_OWNER, 0x0420, 0x002FF7F0),
    ):
        classic_lbl = f"{hook_name}_classic"
        asm.label(hook_name)
        asm.w(0x2F00)
        asm.w(0x302D, cache_reg)
        asm.b_branch(0x6B00, classic_lbl)
        asm.w(0xC0FC, VFX_THEME_ENTRY_STRIDE)
        asm.ref_abs32(0x41F9, "theme_entries")
        asm.w(0xD1C0)  # adda.l d0, a0 (avoid sign-extending products >= 0x8000)
        asm.w(0xD0FC, burn_off)
        asm.w(0x201F, 0x4E75)
        asm.label(classic_lbl)
        asm.w(0x41F9, (classic_addr >> 16) & 0xFFFF, classic_addr & 0xFFFF)
        asm.w(0x201F, 0x4E75)

    asm.label("fa_ptr_hook")
    asm.w(0x4A6D, VFX_RAM_FA_OWNER)
    asm.b_branch(0x6B00, "fa_ptr_hook_classic")
    asm.ref_abs32(0x41F9, "fa_custom_table")
    asm.w(0x4E75)
    asm.label("fa_ptr_hook_classic")
    asm.w(0x41F9, 0x002F, 0xF9F0)
    asm.w(0x4E75)

    # 3. Entry stubs for hit/effect hooks
    asm.label("on_fire_burn_hook")
    asm.w(0x197C, 0x00F8, 0x003A)
    asm.w(0x48E7, 0xF0F0)
    asm.w(0x7600)
    asm.b_branch(0x6000, "update_effect_group")

    asm.label("on_purple_burn_hook")
    asm.w(0x197C, 0x00F9, 0x003A)
    asm.w(0x48E7, 0xF0F0)
    asm.w(0x7601)
    asm.b_branch(0x6000, "update_effect_group")

    asm.label("on_elec_shock_hook")
    asm.w(0x002C, 0x0002, 0x00E3)
    asm.w(0x48E7, 0xF0F0)
    asm.w(0x7602)
    asm.b_branch(0x6000, "update_effect_group")

    asm.label("on_impact_hook")
    asm.w(0x45F9, 0x0001, 0x2E92)
    asm.w(0x2472, 0x1000)
    asm.w(0x3212)
    asm.w(0x48E7, 0xF0F0)
    asm.w(0x7603)
    asm.b_branch(0x6000, "update_effect_group")

    asm.label("on_fa_flash_hook")
    asm.w(0x197C, 0x00FA, 0x003A)
    asm.w(0x48E7, 0xF0F0)
    asm.w(0x7604)

    # 4. Shared group updater: a4 = victim, d3.w = group_idx (0..4)
    asm.label("update_effect_group")
    asm.w(0x206C, 0x00B6)               # movea.l $b6(a4), a0 (attacker fighter)
    asm.w(0x2008)                       # move.l a0, d0
    asm.b_branch(0x6700, "atk_classic")
    asm.w(0x7000)
    asm.w(0x1028, 0x0070)               # move.b $70(a0), d0
    asm.w(0x0C00, 0x001F)
    asm.b_branch(0x6200, "atk_classic")
    asm.w(0x4A28, 0x01D6)               # tst.b $1d6(a0)
    asm.b_branch(0x6700, "got_slot")
    asm.w(0x4A00)
    asm.b_branch(0x6600, "alt_non_kyo")
    asm.w(0x7023)                       # 94 Kyo -> runtime slot 35
    asm.b_branch(0x6000, "got_slot")
    asm.label("alt_non_kyo")
    asm.w(0x0600, 0x000B)
    asm.w(0x0C00, 0x0023)
    asm.b_branch(0x6200, "atk_classic")
    asm.label("got_slot")
    asm.w(0xD040)                       # add.w d0, d0
    asm.ref_abs32(0x41F9, "char_theme_idx")
    asm.w(0x3030, 0x0000)               # move.w (a0, d0.w), d0
    asm.b_branch(0x6000, "have_theme")
    asm.label("atk_classic")
    asm.w(0x303C, 0xFFFF)

    asm.label("have_theme")
    asm.w(0xE94B)                       # lsl.w #4, d3
    asm.ref_abs32(0x47F9, "group_descs")
    asm.w(0xD6C3)                       # adda.w d3, a3 (d3 is 0..64)
    asm.w(0x3413)                       # move.w (a3), d2 (cache_off)
    asm.w(0x3235, 0x2000)               # move.w (a5, d2.w), d1 (prev_owner)
    asm.w(0xB041)
    asm.b_branch(0x6700, "done_exit")
    asm.w(0x3B80, 0x2000)               # move.w d0, (a5, d2.w)

    asm.w(0x4A40)
    asm.b_branch(0x6B00, "switch_classic")

    # Custom theme path (d0 >= 0)
    asm.w(0xC0FC, VFX_THEME_ENTRY_STRIDE)
    asm.ref_abs32(0x45F9, "theme_entries")
    asm.w(0xD5C0)                       # adda.l d0, a2
    asm.w(0x240A)                       # move.l a2, d2 (save ThemeEntry base)
    asm.w(0x322B, 0x0004)               # common_cnt_m1
    asm.b_branch(0x6B00, "custom_burn")
    asm.w(0x2042)                       # movea.l d2, a0
    asm.w(0xD0EB, 0x0002)               # adda.w 2(a3), a0
    asm.b_branch(0x6100, "push_n_records")
    asm.label("custom_burn")
    asm.w(0x2042)                       # reload ThemeEntry base BEFORE clobbering d2.w
    asm.w(0x342B, 0x0006)               # burn_pal_id
    asm.b_branch(0x6700, "done_exit")
    asm.w(0x0C42, 0x00FA)
    asm.b_branch(0x6600, "custom_burn_off")
    asm.ref_abs32(0x41F9, "fa_custom_table")
    asm.b_branch(0x6000, "call_push_burn")
    asm.label("custom_burn_off")
    asm.w(0xD0EB, 0x0008)               # adda.w 8(a3), a0
    asm.label("call_push_burn")
    asm.b_branch(0x6100, "push_burn_slot")
    asm.b_branch(0x6000, "done_exit")

    # Classic restore path (d0 == 0xFFFF)
    asm.label("switch_classic")
    asm.w(0x4A41)
    asm.b_branch(0x6B00, "done_exit")   # 0xFFFE/0xFFFF -> RAM already clean
    asm.w(0x322B, 0x0004)
    asm.b_branch(0x6B00, "classic_burn")
    asm.ref_abs32(0x41F9, "classic_common")
    asm.w(0xD0EB, 0x0002)
    asm.b_branch(0x6100, "push_n_records")
    asm.label("classic_burn")
    asm.w(0x342B, 0x0006)
    asm.b_branch(0x6700, "done_exit")
    asm.w(0x206B, 0x000C)
    asm.b_branch(0x6100, "push_burn_slot")

    asm.label("done_exit")
    asm.w(0x4CDF, 0x0F0F)
    asm.w(0x4E75)

    # Helper: push_n_records (a0 = [pal_id.w, 15 words] * (d1+1))
    asm.label("push_n_records")
    asm.w(0x246D, 0x5924)
    asm.w(0x43ED, 0x5B30)
    asm.label("pn_loop")
    asm.w(0xB5C9)
    asm.b_branch(0x6400, "pn_done")
    asm.w(0x34D8, 0x34D8)
    for _ in range(7):
        asm.w(0x24D8)
    asm.dbra(1, "pn_loop")
    asm.label("pn_done")
    asm.w(0x34BC, 0xFFFF)
    asm.w(0x2B4A, 0x5924)
    asm.w(0x4E75)

    # Helper: push_burn_slot (a0 = 32B LSPC record, d2.w = target pal_id 00F8/00F9/00FA)
    asm.label("push_burn_slot")
    asm.w(0x246D, 0x5924)
    asm.w(0x43ED, 0x5B30)
    asm.w(0xB5C9)
    asm.b_branch(0x6400, "pb_done")
    asm.w(0x5488, 0x34C2, 0x34D8)
    for _ in range(7):
        asm.w(0x24D8)
    asm.w(0x34BC, 0xFFFF)
    asm.w(0x2B4A, 0x5924)
    asm.label("pb_done")
    asm.w(0x4E75)

    if len(asm.buf) % 2:
        asm.buf.append(0)

    # 5. Data tables
    asm.label("char_theme_idx")
    for tid in char_slot_table:
        asm.w(tid)

    asm.label("group_descs")
    for cache_off, common_off, cnt_m1, burn_id, custom_burn_off, classic_ptr, _ in VFX_COMMON_EFFECT_GROUPS:
        asm.w(cache_off, common_off, cnt_m1, burn_id, custom_burn_off, 0)
        asm.l(classic_ptr)

    asm.label("classic_common")
    for _, _, _, _, _, _, slot_ids in VFX_COMMON_EFFECT_GROUPS[:4]:
        for pid in slot_ids:
            clean_w = _read_p2_slot_words15(p2_clean, pid)
            asm.w(pid, *clean_w)

    asm.label("fa_custom_table")
    for frame in range(16):
        src_pid = 0x17D0 + frame
        if orochi_pair is not None:
            words15 = _recolor_hit_effect_slot(src_pid, p2_clean, orochi_pair[0], orochi_pair[1])
        else:
            words15 = _read_p2_slot_words15(p2_clean, src_pid)
        asm.w(src_pid, *words15)

    asm.label("theme_entries")
    for inner_hex, outer_hex in unique_pairs:
        # +0x000..+0x21F: 17 common hit/flame/shock/spark records (32B each)
        for _, _, _, _, _, _, slot_ids in VFX_COMMON_EFFECT_GROUPS[:4]:
            for pid in slot_ids:
                words15 = _recolor_hit_effect_slot(pid, p2_clean, inner_hex, outer_hex)
                asm.w(pid, *words15)
        # +0x220..+0x41F: 0xF8 16 cyclic burn frames (0x17B0..0x17BF)
        for frame in range(16):
            src_pid = 0x17B0 + frame
            words15 = (
                [0] * 15
                if frame == 15
                else _recolor_hit_effect_slot(src_pid, p2_clean, inner_hex, outer_hex)
            )
            asm.w(src_pid, *words15)
        # +0x420..+0x61F: 0xF9 16 cyclic purple-burn frames (0x17C0..0x17CF)
        for frame in range(16):
            src_pid = 0x17C0 + frame
            words15 = (
                [0] * 15
                if frame == 15
                else _recolor_hit_effect_slot(src_pid, p2_clean, inner_hex, outer_hex)
            )
            asm.w(src_pid, *words15)

    blob = asm.finalize()
    if len(blob) > VFX_HIT_EFFECT_CAVE_SIZE:
        raise ValueError(f"Hit-effect VFX code cave exceeds 64KB limit: {len(blob)} bytes")

    return {
        "blob": blob,
        "hooks": dict(asm.labels),
        "theme_count": len(unique_pairs),
        "char_slots": sum(1 for v in char_slot_table if v != 0xFFFF),
    }


def restore_hit_effect_vfx_p1(p1_data: bytearray) -> None:
    """Restore all 16 P1 hit-effect hook sites and clear 0x0F0000..0x0FFFFF to 0xFF."""
    for _name, off, orig_bytes, _lbl in VFX_HIT_HOOK_ORIGINALS:
        p1_data[off : off + 6] = orig_bytes
    p1_data[VFX_HIT_EFFECT_CAVE_BASE : VFX_HIT_EFFECT_CAVE_BASE + VFX_HIT_EFFECT_CAVE_SIZE] = (
        bytes([0xFF] * VFX_HIT_EFFECT_CAVE_SIZE)
    )


def apply_hit_effect_vfx_to_p1(
    p1_data: bytearray,
    character_skins: Dict[int, Dict[str, Any]],
    p2_clean: bytes,
) -> Optional[Dict[str, Any]]:
    """
    Inject dynamic P1 on-hit elemental burn/shock/flame code cave when any character
    has custom VFX enabled, or restore pristine official bytes if all are classic.
    """
    restore_hit_effect_vfx_p1(p1_data)
    patch = build_hit_effect_vfx_p1_patch(character_skins, p1_data, p2_clean)
    if patch is None:
        return None
    blob = patch["blob"]
    p1_data[VFX_HIT_EFFECT_CAVE_BASE : VFX_HIT_EFFECT_CAVE_BASE + len(blob)] = blob
    hooks = patch["hooks"]
    for _name, off, _orig, target_lbl in VFX_HIT_HOOK_ORIGINALS:
        target_addr = hooks[target_lbl]
        p1_data[off : off + 6] = struct.pack(">HI", 0x4EB9, target_addr)
    return patch


def apply_combat_and_unlock_patches_to_p1(
    p1_data: bytearray,
    *,
    guard: bool,
    stun: bool,
    dizzy_duration: float,
    infinite_power: bool,
    damage_mode: str,
    log_fn: Optional[Callable[[str, str], None]] = None,
) -> None:
    """Apply 68000 combat/defense rules and hidden-character select unlocks to P1."""
    def _log(msg: str, lvl: str = "INFO") -> None:
        if log_fn is not None:
            log_fn(msg, lvl)

    _log("\u6b63\u5728\u6ce8\u5165 68000 \u6218\u6597\u4e0e\u9632\u5fa1\u5c5e\u6027 Patch...", "INFO")

    # Guard Crush
    if guard:
        p1_data[0x01397E:0x013982] = bytes.fromhex("4e714e71")
        _log("  [P1] \u514d\u7834\u9632: 0x01397E -> NOP; NOP (\u9501\u6b7b 103 \u70b9)", "INFO")
    else:
        p1_data[0x01397E:0x013982] = bytes.fromhex("916c013e")
        _log("  [P1] \u6062\u590d\u539f\u7248\u7834\u9632\u8ba1\u7b97\u673a\u5236", "INFO")

    # Dizzy / Stun Immunity
    if stun:
        p1_data[0x0139A4:0x0139A8] = bytes.fromhex("4e714e71")
        _log("  [P1] \u514d\u7729\u6655: 0x0139A4 -> NOP; NOP (\u9501\u6b7b 103 \u70b9)", "INFO")
    else:
        p1_data[0x0139A4:0x0139A8] = bytes.fromhex("916c0146")
        _log("  [P1] \u6062\u590d\u539f\u7248\u7729\u6655\u8ba1\u7b97\u673a\u5236", "INFO")

    # Dizzy / Stun Duration Timer (frames at 60Hz)
    dizzy_frames = max(1, min(1800, round(dizzy_duration * 60)))
    dizzy_frame_bytes = struct.pack(">H", dizzy_frames)
    p1_data[0x0167D4:0x0167D6] = dizzy_frame_bytes
    p1_data[0x018210:0x018212] = dizzy_frame_bytes
    p1_data[0x01E80A:0x01E80C] = dizzy_frame_bytes
    p1_data[0x01E81A:0x01E81C] = dizzy_frame_bytes
    _log(
        f"  [P1] \u7729\u6655\u6301\u7eed\u65f6\u95f4: \u5df2\u6ce8\u5165 {dizzy_duration:.1f} \u79d2 ({dizzy_frames} \u5e27)",
        "INFO",
    )

    # Infinite Super Meter / Power Option
    if infinite_power:
        # Hook match start round setup: 0x025160 -> JSR $0320.W (4EB8 0320)
        p1_data[0x025160:0x025164] = bytes.fromhex("4eb80320")
        # Code Cave 0x000320: JSR $31F4.W; MOVE.B #3, $01E3(A4); MOVE.B #$80, $01E8(A4); RTS
        p1_data[0x000320:0x000332] = bytes.fromhex("4eb831f4197c000301e3197c008001e84e75")
        # NOP power stock deductions across super moves and MAX burst
        p1_data[0x01117C:0x011180] = bytes.fromhex("4e714e71")
        p1_data[0x018206:0x01820A] = bytes.fromhex("4e714e71")
        p1_data[0x01E7EC:0x01E7F0] = bytes.fromhex("4e714e71")
        p1_data[0x01E7F8:0x01E7FC] = bytes.fromhex("4e714e71")
        _log(
            "  [P1] \u65e0\u9650\u80fd\u91cf: \u5df2\u542f\u7528 (\u521d\u59cb3\u6c14+\u6ee1\u80fd\u91cf\u69fd\uff0c\u8d85\u5fc5\u6740/MAX\u7206\u6c14\u96f6\u6d88\u8017)",
            "INFO",
        )
    else:
        p1_data[0x025160:0x025164] = bytes.fromhex("4eb831f4")
        p1_data[0x000320:0x000332] = bytes([0xFF] * 18)
        p1_data[0x01117C:0x011180] = bytes.fromhex("532c01e3")
        p1_data[0x018206:0x01820A] = bytes.fromhex("532c01e3")
        p1_data[0x01E7EC:0x01E7F0] = bytes.fromhex("532c01e3")
        p1_data[0x01E7F8:0x01E7FC] = bytes.fromhex("532c01e3")
        _log("  [P1] \u6062\u590d\u539f\u7248\u80fd\u91cf\u6263\u51cf\u673a\u5236", "INFO")

    # Damage Multiplier Hook (Code Cave 0x000300)
    selected_mode = next((m for m in DAMAGE_MODES if m["id"] == damage_mode), DAMAGE_MODES[3])
    if damage_mode == "normal":
        p1_data[0x01394A:0x01394E] = selected_mode["hook"]
        p1_data[0x000300:0x000308] = bytes.fromhex("ffffffffffffffff")
        _log("  [P1] \u6062\u590d 100% \u539f\u59cb\u53d7\u521b\u4f24\u5bb3", "INFO")
    else:
        p1_data[0x01394A:0x01394E] = selected_mode["hook"]
        p1_data[0x000300:0x000308] = selected_mode["cave"]
        _log(f"  [P1] \u6ce8\u5165 Code Cave \u4f24\u5bb3 Hook (\u6a21\u5f0f: {damage_mode})", "INFO")

    # Clean / restore all character select / spawn hooks to 100% pristine original SNK code
    p1_data[0x01FE54:0x01FE5A] = bytes.fromhex("1c830fa80010")
    p1_data[0x021F1E:0x021F22] = bytes.fromhex("422d2784")
    p1_data[0x025178:0x02517C] = bytes.fromhex("41ed2847")
    p1_data[0x011FDC:0x011FE0] = bytes.fromhex("61000212")
    p1_data[0x0868A0:0x0868A4] = bytes.fromhex("4eb878c0")
    p1_data[0x022334:0x02234C] = bytes.fromhex("1b6d284b27ed1b6d284c27ee1b6d284d27ef1b6d285727f0")
    p1_data[0x000350:0x000450] = bytes([0xFF] * 256)

    # Unlock all hidden characters directly on character select screen
    # 1. 0x009976: Set $6c34(a5) = 0x1F (move.b #$1f, $6c34(a5); NOP)
    p1_data[0x009976:0x00997E] = bytes.fromhex("4e711b7c001f6c34")
    # 2. 0x01F7C8: Guarantee $6c34(a5) = 0x1F is always set during character select
    p1_data[0x01F7C8:0x01F7CA] = bytes.fromhex("4e71")
    # 3. Add Orochi (0x1E) into Row 3 Col 4 of all 8 select screen grid tables
    for orochi_off in [0x0A9499, 0x0A94C6, 0x0A94F3, 0x0A9520, 0x0A954D, 0x0A957A, 0x0A95A7, 0x0A95D4]:
        p1_data[orochi_off] = 0x1E
    _log(
        "  [P1] \u5df2\u5168\u9762\u89e3\u9501\u9009\u4eba\u754c\u9762\u9690\u85cf\u4eba\u7269 (\u66b4\u8d70\u516b\u795e\u3001\u66b4\u8d70\u8389\u5b89\u5a1c\u3001\u771f\u5927\u86c7\u961f\u4e09\u4eba\u7ec4\u3001\u5927\u86c7\u53ca\u7ecf\u5178\u8349\u8599\u4eac)",
        "INFO",
    )
