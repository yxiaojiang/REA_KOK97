# -*- coding: utf-8 -*-
"""
End-to-end verification script for:
1. Hidden character select screen unlock (Row 4 + Orochi).
2. Live hot-reload palette injection while in combat.
"""

import os
import sys
import glob
import time
import shutil
import struct
import ctypes
import ctypes.wintypes as wt
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.kof97_webview_app import KOF97BridgeApi
from tools.rom_tool import start_sandbox_kawaks

def run_verification():
    print("=== Starting Full E2E Verification ===")
    api = KOF97BridgeApi()

    # Step 1: Reset all skins to classic and pack ROM
    for c in api._character_skins:
        api._character_skins[c] = {"themeId": "classic", "colors": []}
    api._save_config_to_disk()
    res = api.pack_rom()
    print("Pack ROM Result (Classic baseline):", res)
    assert res["success"], "Pack ROM failed!"

    # Clean capture directory
    capture_dir = api._sandbox_dir / "capture"
    capture_dir.mkdir(parents=True, exist_ok=True)
    for old_png in glob.glob(str(capture_dir / "*.png")):
        try:
            os.remove(old_png)
        except Exception:
            pass

    # Step 2: Start Emulator
    os.system("taskkill /f /im WinKawaks.exe 2>nul")
    time.sleep(1)

    proc = start_sandbox_kawaks(api._sandbox_dir, rom_name="kof97pls", enable_bg_input=True)
    h_proc = int(proc._handle)
    k32 = ctypes.WinDLL("kernel32")
    u32 = ctypes.WinDLL("user32")

    print(f"Emulator started with PID={proc.pid}")
    time.sleep(4.0)

    # Find Main Window Handle
    main_hwnd = 0
    WNDENUMPROC = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def _enum_cb(hwnd: int, _lparam: int) -> bool:
        nonlocal main_hwnd
        pid = wt.DWORD()
        u32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == proc.pid and u32.GetMenu(hwnd):
            main_hwnd = hwnd
        return True

    u32.EnumWindows(WNDENUMPROC(_enum_cb), 0)
    assert main_hwnd != 0, "Could not find WinKawaks main window handle"
    print(f"Main Window Handle: 0x{main_hwnd:08X}")

    # Read DirectInput pointer
    ptr_buf = ctypes.create_string_buffer(4)
    read = ctypes.c_size_t(0)
    k32.ReadProcessMemory(h_proc, ctypes.c_void_p(0x00712614), ptr_buf, 4, ctypes.byref(read))
    dinput_ptr = struct.unpack("<I", ptr_buf.raw)[0]
    assert dinput_ptr != 0, "DirectInput buffer pointer not initialized"

    def press_key(scancode: int, hold: float = 0.12):
        written = ctypes.c_size_t(0)
        k32.WriteProcessMemory(h_proc, ctypes.c_void_p(dinput_ptr + 0x20 + scancode), b"\x80", 1, ctypes.byref(written))
        time.sleep(hold)
        k32.WriteProcessMemory(h_proc, ctypes.c_void_p(dinput_ptr + 0x20 + scancode), b"\x00", 1, ctypes.byref(written))

    def capture_screenshot(tag: str) -> Path:
        u32.PostMessageW(main_hwnd, 0x0111, 32994, 0)
        time.sleep(0.5)
        pngs = sorted(glob.glob(str(capture_dir / "*.png")), key=os.path.getmtime)
        assert pngs, f"No screenshot generated for {tag}"
        latest = Path(pngs[-1])
        artifacts_dir = Path(r"C:\Users\mimovr\.gemini\antigravity\brain\3f9cc201-9f7e-4ce0-b657-b6debcec509d")
        dest = artifacts_dir / f"{tag}.png"
        shutil.copy2(latest, dest)
        print(f"[{tag}] Saved screenshot to: {dest}")
        return dest

    # Fast forward past BIOS splash
    time.sleep(1.0)
    u32.PostMessageW(main_hwnd, 0x0111, 32818, 0) # Fast-forward on
    time.sleep(1.0)
    u32.PostMessageW(main_hwnd, 0x0111, 32818, 0) # Fast-forward off
    time.sleep(1.5)

    # Insert coin (5 = scancode 6)
    print("Inserting coins...")
    for _ in range(4):
        press_key(6)
        time.sleep(0.2)

    # 1P Start (1 = scancode 2)
    print("Pressing 1P Start...")
    press_key(2)
    time.sleep(1.0)

    # Select TEAM PLAY (Button A: U = scancode 22)
    print("Selecting TEAM PLAY...")
    press_key(22)
    time.sleep(1.5)

    # Select ADVANCED MODE (Button A: U = scancode 22)
    print("Selecting ADVANCED MODE...")
    press_key(22)
    time.sleep(2.0)

    # NOW ON CHARACTER SELECT SCREEN!
    print("Arrived at Character Select Screen!")
    cap_select = capture_screenshot("e2e_select_screen")

    # Pick 3 characters: press A (scancode 22) 3 times
    print("Picking 3 characters...")
    for _ in range(3):
        press_key(22)
        time.sleep(0.6)

    # Order selection screen: press A 3 times
    time.sleep(1.5)
    print("Confirming character order...")
    for _ in range(3):
        press_key(22)
        time.sleep(0.6)

    # Fast forward during match loading intro
    print("Waiting for match intro and battle start...")
    u32.PostMessageW(main_hwnd, 0x0111, 32818, 0)
    time.sleep(4.0)
    u32.PostMessageW(main_hwnd, 0x0111, 32818, 0)
    time.sleep(1.5)

    # Capture battle screenshot BEFORE live injection
    cap_pre = capture_screenshot("e2e_battle_pre_inject")

    # LIVE INJECT SKIN!
    print("\n--- Triggering Live Skin Injection ---")
    live_res = api.apply_skin_live({
        "char_id": 0x00, # Kyo / 1P team leader
        "theme_id": "cyber_neon",
        "scope": "ALL",
    })
    print("Live Inject Result:", live_res)
    assert live_res["success"], f"Live inject failed: {live_res}"

    # Wait 1s and capture battle screenshot AFTER live injection
    time.sleep(1.0)
    cap_post = capture_screenshot("e2e_battle_post_inject")

    # Clean shutdown
    os.system("taskkill /f /im WinKawaks.exe 2>nul")
    print("=== Verification Finished Successfully! ===")

if __name__ == "__main__":
    run_verification()
