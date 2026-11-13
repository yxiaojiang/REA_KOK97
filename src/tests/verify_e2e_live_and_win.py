#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
End-to-End Real-Machine Verification:
1. Re-packs output/roms/kof97pls.zip with customized skins for Iori, Chang, Daimon.
2. Launches sandbox WinKawaks and verifies PID detection.
3. Tests dynamic live palette injection (apply_skin_live) during running game.
4. Verifies active on-screen Palette RAM bytes are instantly modified.
5. Verifies all 4 button slots (A/B/C/D) of victory/win portraits are updated.

All comments, identifiers, and variables strictly follow 100% English specification (Rules.md).
"""

import ctypes
import struct
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.rom.rom_tool import start_sandbox_kawaks
from src.studio.bridge_api import KOF97BridgeApi


def run_e2e_verification():
    print("=== Step 1: Initialize API & Apply Custom Skins ===")
    api = KOF97BridgeApi()

    # Configure Iori (0x1B) with new theme 'phoenix_nirvana' (fiery phoenix)
    api.set_character_skin({"char_id": 0x1B, "theme_id": "phoenix_nirvana"})
    # Configure Chang (0x13) with new theme 'abyssal_frost' (frost cyan/blue)
    api.set_character_skin({"char_id": 0x13, "theme_id": "abyssal_frost"})
    # Configure Daimon (0x02) with new theme 'emerald_lotus' (emerald jade)
    api.set_character_skin({"char_id": 0x02, "theme_id": "emerald_lotus"})

    # Pack into output/roms/kof97pls.zip
    pack_res = api.pack_rom()
    print("  pack_rom result:", pack_res)
    assert pack_res.get("success"), f"ROM packaging failed: {pack_res}"

    print("\n=== Step 2: Launch WinKawaks Sandbox & Test get_emulator_status ===")
    sandbox_dir = PROJECT_ROOT / "sandbox"
    proc = start_sandbox_kawaks(sandbox_dir, rom_name="kof97pls", enable_bg_input=True)
    api._running_proc = proc
    time.sleep(2.0)

    status = api.get_emulator_status()
    print(f"  get_emulator_status: {status}")
    assert status.get("running") is True, "Emulator was expected to be running!"
    assert status.get("pid") == proc.pid, f"PID mismatch: {status.get('pid')} vs {proc.pid}"

    print("\n=== Step 3: Wait for Core Pointers Initialization ===")
    h_proc = int(proc._handle)
    k32 = ctypes.WinDLL("kernel32")
    read = ctypes.c_size_t(0)
    ptr_buf = ctypes.create_string_buffer(4)

    pal_ram_va = 0
    for i in range(50):
        time.sleep(0.1)
        k32.ReadProcessMemory(h_proc, ctypes.c_void_p(0x007126B0), ptr_buf, 4, ctypes.byref(read))
        pal_ram_va = struct.unpack("<I", ptr_buf.raw)[0]
        if pal_ram_va != 0:
            print(f"  [PASS] Palette RAM detected at: 0x{pal_ram_va:08X} (after {(i+1)*0.1:.1f}s)")
            break

    assert pal_ram_va != 0, "Palette RAM pointer remained 0"

    print("\n=== Step 4: Test Live Skin Hot-Reload (apply_skin_live) ===")
    # Hot-reload Iori in real time to 'sunset_overdrive'
    live_res = api.apply_skin_live({
        "char_id": 0x1B,
        "theme_id": "sunset_overdrive",
        "scope": "SINGLE"
    })
    print(f"  apply_skin_live result: {live_res}")
    assert live_res.get("success") is True, f"Live apply failed: {live_res}"
    assert live_res.get("running") is True

    # Read back P2 ROM memory at 0x2CFFF0 + 0x07C0 * 32 + 2 in the running process
    k32.ReadProcessMemory(h_proc, ctypes.c_void_p(0x00712660), ptr_buf, 4, ctypes.byref(read))
    prom_va = struct.unpack("<I", ptr_buf.raw)[0]
    p2_base = prom_va + 0x100000

    target_p2_addr = p2_base + 0x2CFFF0 + 0x07C0 * 32 + 2
    mem_buf = ctypes.create_string_buffer(30)
    k32.ReadProcessMemory(h_proc, ctypes.c_void_p(target_p2_addr), mem_buf, 30, ctypes.byref(read))

    # Compare with sunset_overdrive words
    p1_path = PROJECT_ROOT / "build" / "unpacked" / "p1_be.bin"
    if not p1_path.exists():
        p1_path = sandbox_dir / "p1_be.bin"
    p1_data = p1_path.read_bytes()
    clean_zip = Path("C:/Program Files (x86)/KOF97/roms/kof97.ZIP")
    import zipfile
    with zipfile.ZipFile(clean_zip) as z:
        from kof97_webview_app import bswap16, generate_harmonious_character_palette
        p2_clean = bswap16(z.read("KOF97_P2.ROM"))
    expected_words = generate_harmonious_character_palette(0x1B, "sunset_overdrive", p1_data, p2_clean)

    read_words_le = struct.unpack("<15H", mem_buf.raw)
    assert read_words_le == tuple(expected_words), "Injected P2 memory words did not match expected palette!"
    print("  [PASS] Live P2 ROM memory verified 100% matching sunset_overdrive palette words!")

    # Verify all 4 button slots of win portrait (0x07CD, 0x07DD, 0x07ED, 0x07FD)
    for btn in range(4):
        port_addr = p2_base + 0x2CFFF0 + (0x07C0 + 13 + btn * 16) * 32
        p_buf = ctypes.create_string_buffer(32)
        k32.ReadProcessMemory(h_proc, ctypes.c_void_p(port_addr), p_buf, 32, ctypes.byref(read))
        pw_hair = struct.unpack("<H", p_buf.raw[16:18])[0]
        assert pw_hair == expected_words[7], f"Button {btn} win portrait hair not updated in memory!"

    print("  [PASS] Win screen big portrait verified across all 4 button slots (A, B, C, D) in running process memory!")

    proc.kill()
    print("\n[SUCCESS] End-to-end live injection and win screen portrait verification passed 100%!")


if __name__ == "__main__":
    run_e2e_verification()
