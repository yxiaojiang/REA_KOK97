#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WinKawaks process lookup and live palette RAM/ROM hot-injection."""

import ctypes
import struct
import subprocess
from typing import Any, Callable, Dict, Optional

from src.core.presets import VFX_PRESET_MAP, is_custom_theme_id
from src.core.roster import CHARACTER_ROSTER, get_char_engine_info
from src.palette.costume_painter import generate_harmonious_character_palette
from src.palette.portrait_burst import (
    generate_burst_character_palette,
    sync_character_portraits,
)
from src.palette.vfx_shader import (
    VFX_COMMON_EFFECT_GROUPS,
    _read_p2_slot_words15,
    _recolor_hit_effect_slot,
    build_character_vfx_map,
    recolor_vfx_palette,
    resolve_vfx_hues,
)


def find_kawaks_pid(running_proc: Optional[subprocess.Popen] = None) -> Optional[int]:
    """Locate running WinKawaks process PID with multi-layered detection."""
    try:
        if running_proc is not None and running_proc.poll() is None:
            return int(running_proc.pid)

        u32 = ctypes.WinDLL("user32")
        found_pid: Optional[int] = None

        def _enum_cb(hwnd: int, _lparam: int) -> bool:
            nonlocal found_pid
            pid = ctypes.c_ulong()
            u32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            buf = ctypes.create_unicode_buffer(256)
            u32.GetWindowTextW(hwnd, buf, 256)
            title = buf.value.lower()
            if "winkawaks" in title or "kawaks" in title:
                found_pid = int(pid.value)
                return False
            return True

        wndenum = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        u32.EnumWindows(wndenum(_enum_cb), 0)
        if found_pid is not None:
            return found_pid

        # Fallback to tasklist query
        cmd = ["tasklist", "/FI", "IMAGENAME eq WinKawaks.exe", "/FO", "CSV", "/NH"]
        out = subprocess.check_output(cmd, creationflags=0x08000000).decode(
            "latin1", errors="ignore"
        )
        for line in out.strip().splitlines():
            parts = [p.strip('"' + " ") for p in line.split('","')]
            if len(parts) >= 2 and "winkawaks" in parts[0].lower():
                try:
                    return int(parts[1])
                except ValueError:
                    pass
    except Exception:
        pass
    return None


def inject_live_palettes_to_kawaks(
    pid: int,
    char_id: int,
    vfx_only: bool,
    theme_id: str,
    scope: str,
    params: Dict[str, Any],
    character_skins: Dict[int, Dict[str, Any]],
    sync_avatar: bool,
    p1_data: bytes,
    p2_clean: bytes,
    last_vfx_ram_sigs: Dict[int, bytes],
    lspc_words_fn: Callable[[int, Dict[str, Any], bytes, bytes], tuple],
    log_fn: Optional[Callable[[str, str], None]] = None,
) -> Dict[str, Any]:
    """Hot-inject character and VFX palettes into active WinKawaks memory."""
    def _log(msg: str, lvl: str = "INFO") -> None:
        if log_fn is not None:
            log_fn(msg, lvl)

    k32 = ctypes.WinDLL("kernel32")
    process_all = 0x001F0FFF
    h_proc = k32.OpenProcess(process_all, False, pid)
    if not h_proc:
        return {
            "success": False,
            "running": True,
            "message": f"\u65e0\u6cd5\u6302\u8f7d\u6a21\u62df\u5668\u8fdb\u7a0b (PID={pid})",
        }

    try:
        read = ctypes.c_size_t(0)
        written = ctypes.c_size_t(0)
        ptr_buf = ctypes.create_string_buffer(4)

        # Read WinKawaks 1.48 Core Pointers
        k32.ReadProcessMemory(h_proc, ctypes.c_void_p(0x00712660), ptr_buf, 4, ctypes.byref(read))
        prom_va = struct.unpack("<I", ptr_buf.raw)[0]

        k32.ReadProcessMemory(h_proc, ctypes.c_void_p(0x007126B0), ptr_buf, 4, ctypes.byref(read))
        pal_ram_va = struct.unpack("<I", ptr_buf.raw)[0]

        k32.ReadProcessMemory(h_proc, ctypes.c_void_p(0x00712688), ptr_buf, 4, ctypes.byref(read))
        work_ram_va = struct.unpack("<I", ptr_buf.raw)[0]

        if prom_va == 0 or pal_ram_va == 0:
            return {
                "success": False,
                "running": True,
                "message": "\u6a21\u62df\u5668\u5c1a\u5728\u52a0\u8f7d\u6e38\u620f\u4e2d\uff0c\u8bf7\u7a0d\u5019\u518d\u70b9\u51fb\u5b9e\u65f6\u5e94\u7528\u76ae\u80a4",
            }

        p2_base = prom_va + 0x100000

        # Read current active 8KB Palette RAM to scan existing slots
        pal_ram_buf = ctypes.create_string_buffer(8192)
        k32.ReadProcessMemory(h_proc, ctypes.c_void_p(pal_ram_va), pal_ram_buf, 8192, ctypes.byref(read))
        pal_ram_bytes = bytearray(pal_ram_buf.raw)

        # Read 1P Active Palette Index from Work RAM (0x108130 -> WorkRAM + 0x8130)
        p1_active_slot = -1
        if work_ram_va != 0:
            slot_buf = ctypes.create_string_buffer(1)
            k32.ReadProcessMemory(h_proc, ctypes.c_void_p(work_ram_va + 0x8130), slot_buf, 1, ctypes.byref(read))
            p1_active_slot = slot_buf.raw[0]

        target_cids = [c["id"] for c in CHARACTER_ROSTER] if scope == "ALL" else [char_id]
        injected_total = 0

        for target_cid in target_cids:
            skin_entry = character_skins.get(target_cid, {})
            t_id = skin_entry.get("themeId", "classic")
            _engine_cid, _, pal_idx = get_char_engine_info(target_cid)
            base_off = 0x483E + pal_idx * 8
            base_pid = struct.unpack(">H", p1_data[base_off : base_off + 2])[0]

            _tid, lspc_words = lspc_words_fn(target_cid, skin_entry, p1_data, p2_clean)
            if _tid == "classic":
                burst_words = lspc_words
            else:
                burst_words = generate_burst_character_palette(target_cid, _tid, lspc_words)

            # Prepare Little-Endian packed words for WinKawaks RAM
            lspc_bytes_le = bytearray()
            for w in lspc_words:
                lspc_bytes_le += struct.pack("<H", w)

            burst_bytes_le = bytearray()
            for w in burst_words:
                burst_bytes_le += struct.pack("<H", w)

            # A. Overwrite all 4 button slots (A, B, C, D) in loaded P2 ROM memory.
            for btn_idx in range(4):
                btn_off = base_off + btn_idx * 2
                pal_id = struct.unpack(">H", p1_data[btn_off : btn_off + 2])[0]
                if is_custom_theme_id(t_id) or t_id == "classic":
                    btn_words = lspc_words
                    btn_burst = burst_words
                else:
                    btn_words = generate_harmonious_character_palette(
                        target_cid, t_id, p1_data, p2_clean, btn_idx
                    )
                    btn_burst = generate_burst_character_palette(target_cid, t_id, btn_words)
                btn_le = bytearray()
                for w in btn_words:
                    btn_le += struct.pack("<H", w)
                burst_le = bytearray()
                for w in btn_burst:
                    burst_le += struct.pack("<H", w)
                btn_addr = p2_base + 0x2CFFF0 + pal_id * 32 + 2
                k32.WriteProcessMemory(h_proc, ctypes.c_void_p(btn_addr), bytes(btn_le), 30, ctypes.byref(written))
                burst_addr = p2_base + 0x2CFFF0 + (pal_id + 3) * 32 + 2
                k32.WriteProcessMemory(h_proc, ctypes.c_void_p(burst_addr), bytes(burst_le), 30, ctypes.byref(written))

            # B. Synchronize all portrait and avatar palettes in P2 ROM
            if sync_avatar:
                p2_temp = bytearray(p2_clean)
                sync_character_portraits(target_cid, t_id, base_pid, lspc_words, p2_temp, p2_clean)
                for btn_idx in range(4):
                    for slot_off in (13, 14, 15):
                        port_pal = base_pid + slot_off + btn_idx * 16
                        port_addr = 0x2CFFF0 + port_pal * 32
                        port_words_be = [
                            struct.unpack(">H", p2_temp[port_addr + i * 2 : port_addr + i * 2 + 2])[0]
                            for i in range(16)
                        ]
                        port_bytes_le = bytearray()
                        for pw in port_words_be:
                            port_bytes_le += struct.pack("<H", pw)
                        k32.WriteProcessMemory(
                            h_proc, ctypes.c_void_p(p2_base + port_addr), bytes(port_bytes_le), 32, ctypes.byref(written)
                        )

            # C. Instant On-Screen Hot-Update (8KB Palette RAM)
            if p1_active_slot != -1 and p1_active_slot < 256:
                target_va = pal_ram_va + p1_active_slot * 32 + 2
                k32.WriteProcessMemory(h_proc, ctypes.c_void_p(target_va), bytes(lspc_bytes_le), 30, ctypes.byref(written))
                if p1_active_slot + 3 < 256:
                    target_burst_va = pal_ram_va + (p1_active_slot + 3) * 32 + 2
                    k32.WriteProcessMemory(
                        h_proc, ctypes.c_void_p(target_burst_va), bytes(burst_bytes_le), 30, ctypes.byref(written)
                    )

            clean_addr = 0x2CFFF0 + base_pid * 32 + 2
            clean_sig = bytearray()
            for i in range(4):
                cw = struct.unpack(">H", p2_clean[clean_addr + i * 2 : clean_addr + i * 2 + 2])[0]
                clean_sig += struct.pack("<H", cw)

            for slot_idx in range(256):
                slot_data = pal_ram_bytes[slot_idx * 32 + 2 : slot_idx * 32 + 10]
                if slot_data == clean_sig or slot_idx == p1_active_slot:
                    va = pal_ram_va + slot_idx * 32 + 2
                    k32.WriteProcessMemory(h_proc, ctypes.c_void_p(va), bytes(lspc_bytes_le), 30, ctypes.byref(written))

            # D. VFX Palette Hot-Update (P2 ROM + Active Palette RAM)
            vfx_info = build_character_vfx_map(p1_data, p2_clean).get(target_cid)
            vfx_theme = skin_entry.get("vfxTheme", "classic")
            if vfx_info and vfx_info.get("has_vfx"):
                vpair = resolve_vfx_hues(
                    vfx_theme, skin_entry, cid=target_cid, p1_data=p1_data, p2_clean=p2_clean
                )
                for v_pid in vfx_info["all_slots"]:
                    if v_pid <= 0x00FF:
                        continue
                    clean_v = _read_p2_slot_words15(p2_clean, v_pid)
                    new_v = clean_v if vpair is None else recolor_vfx_palette(clean_v, vpair[0], vpair[1])
                    v_le = struct.pack("<15H", *new_v)
                    v_addr = p2_base + 0x2CFFF0 + v_pid * 32 + 2
                    k32.WriteProcessMemory(h_proc, ctypes.c_void_p(v_addr), v_le, 30, ctypes.byref(written))

                    clean_vsig = struct.pack("<4H", *clean_v[:4])
                    prev_vsig = last_vfx_ram_sigs.get(v_pid)
                    for slot_idx in range(16, 256):
                        slot_data = pal_ram_bytes[slot_idx * 32 + 2 : slot_idx * 32 + 10]
                        if slot_data == clean_vsig or (prev_vsig and slot_data == prev_vsig):
                            va = pal_ram_va + slot_idx * 32 + 2
                            k32.WriteProcessMemory(h_proc, ctypes.c_void_p(va), v_le, 30, ctypes.byref(written))
                    if vpair is None:
                        last_vfx_ram_sigs.pop(v_pid, None)
                    else:
                        last_vfx_ram_sigs[v_pid] = v_le[:8]

                if p1_active_slot != -1 and p1_active_slot < 256:
                    btn0_pid = vfx_info["btn_pids"][0]
                    for sub in vfx_info["char_sub_offsets"]:
                        if p1_active_slot + sub < 256:
                            clean_sub = _read_p2_slot_words15(p2_clean, btn0_pid + sub)
                            new_sub = clean_sub if vpair is None else recolor_vfx_palette(clean_sub, vpair[0], vpair[1])
                            sub_va = pal_ram_va + (p1_active_slot + sub) * 32 + 2
                            k32.WriteProcessMemory(
                                h_proc,
                                ctypes.c_void_p(sub_va),
                                struct.pack("<15H", *new_sub),
                                30,
                                ctypes.byref(written),
                            )

                # Hot-update common battle effect slots in live Palette RAM only (never P2 ROM)
                seen_eff_slots: set = set()
                for _cache_off, _c_off, _cnt_m1, _b_id, _cb_off, _cl_ptr, slot_ids in VFX_COMMON_EFFECT_GROUPS[:4]:
                    for eff_pid in slot_ids:
                        if eff_pid in seen_eff_slots or eff_pid >= 256:
                            continue
                        seen_eff_slots.add(eff_pid)
                        eff_words = (
                            _read_p2_slot_words15(p2_clean, eff_pid)
                            if vpair is None
                            else _recolor_hit_effect_slot(eff_pid, p2_clean, vpair[0], vpair[1])
                        )
                        eff_va = pal_ram_va + eff_pid * 32 + 2
                        k32.WriteProcessMemory(
                            h_proc,
                            ctypes.c_void_p(eff_va),
                            struct.pack("<15H", *eff_words),
                            30,
                            ctypes.byref(written),
                        )

            injected_total += 1

        char_info = next((c for c in CHARACTER_ROSTER if c["id"] == char_id), None)
        cname = char_info["name_cn"] if char_info else f"0x{char_id:02X}"
        target_desc = f"\u3010{cname}\u3011" if scope == "SINGLE" else f"\u5168\u5458 {injected_total} \u4f4d\u89d2\u8272"
        applied_name = (
            VFX_PRESET_MAP.get(str(params.get("vfx_theme") or "classic"), {}).get("name_cn", "VFX")
            if vfx_only
            else theme_id
        )
        kind_label = "\u7279\u6548" if vfx_only else "\u76ae\u80a4"
        kind_msg = "\u6280\u80fd\u7279\u6548" if vfx_only else "\u76ae\u80a4"
        _log(
            f"[\u5b9e\u65f6\u70ed\u66f4\u65b0] {kind_label}\u3010{applied_name}\u3011\u5df2\u6210\u529f\u5b9e\u65f6\u6ce8\u5165\u8fd0\u884c\u4e2d\u7684\u6e38\u620f (PID={pid}, {target_desc})\uff01\u753b\u9762\u5df2\u5373\u65f6\u53d8\u8272\uff01",
            "SUCCESS",
        )
        return {
            "success": True,
            "running": True,
            "message": f"[\u5b9e\u65f6\u70ed\u66f4\u65b0] {kind_msg}\u5df2\u5b9e\u65f6\u70ed\u66f4\u65b0\u5230\u6e38\u620f\u4e2d\uff01{target_desc}\u753b\u9762\u5df2\u5373\u523b\u53d8\u8272\uff01",
        }
    except Exception as exc:
        _log(f"\u5b9e\u65f6\u70ed\u66f4\u65b0\u5931\u8d25: {exc}", "ERROR")
        return {"success": False, "running": True, "message": str(exc)}
    finally:
        k32.CloseHandle(h_proc)
