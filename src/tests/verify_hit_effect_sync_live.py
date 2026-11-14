#!/usr/bin/env python3
"""
Real-machine verification of on-hit / on-guard effect palette sync in WinKawaks.

1. Backs up config + build artifacts, packs a ROM where Kyo (P1 leader) uses one VFX theme
   and every other character uses a different one.
2. Reaches a battle, drives P1 to attack (and to guard against the CPU), and samples the
   code-cave owner caches plus palette RAM after every owner change.
3. Asserts the common spark / guard / burn palettes always match the CURRENT attacker theme.
4. Hot-applies a new Kyo theme via apply_vfx_live and asserts the running P1 cave is refreshed.
5. Restores every backed-up file.
"""

import ctypes
import ctypes.wintypes as wt
import glob
import os
import shutil
import struct
import sys
import tempfile
import time
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import src.core.paths as _paths
from src.palette.vfx_shader import VFX_COMMON_EFFECT_GROUPS, VFX_RAM_F8_OWNER
from src.rom.p1_patcher import VFX_HIT_EFFECT_CAVE_BASE, VFX_THEME_ENTRY_STRIDE, build_hit_effect_vfx_p1_patch
from src.rom.rom_tool import DEFAULT_KOF97_ZIP, bswap16, start_sandbox_kawaks
from src.studio.bridge_api import KOF97BridgeApi

KEY_START, KEY_COIN, KEY_A, KEY_B, KEY_C = 2, 3, 79, 80, 81
KEY_LEFT, KEY_RIGHT = 30, 32
MENU_TURBO, MENU_SNAPSHOT = 32818, 32994
OWNER_NAMES = ("F8", "F9", "FA", "EL", "IM")
GROUP_BY_CACHE = {g[0]: g for g in VFX_COMMON_EFFECT_GROUPS[:4]}

k32 = ctypes.WinDLL("kernel32")
u32 = ctypes.WinDLL("user32")


class Emu:
    def __init__(self, sandbox: Path) -> None:
        os.system("taskkill /f /im WinKawaks.exe >nul 2>nul")
        time.sleep(1)
        self.sandbox = sandbox
        self.proc = start_sandbox_kawaks(sandbox, rom_name="kof97pls", enable_bg_input=True)
        self.h = int(self.proc._handle)
        time.sleep(4.0)
        self.hwnd = 0
        cb_t = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)

        def _cb(hwnd, _lp):
            pid = wt.DWORD()
            u32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value == self.proc.pid and u32.GetMenu(hwnd):
                self.hwnd = hwnd
            return True

        u32.EnumWindows(cb_t(_cb), 0)
        self.dinput = self.u32_at(0x00712614)
        self.prom = self.u32_at(0x00712660)
        self.pal = self.u32_at(0x007126B0)
        self.wram = self.u32_at(0x00712688)

    def read(self, va: int, n: int) -> bytes:
        buf = ctypes.create_string_buffer(n)
        got = ctypes.c_size_t(0)
        k32.ReadProcessMemory(self.h, ctypes.c_void_p(va), buf, n, ctypes.byref(got))
        return buf.raw

    def write(self, va: int, data: bytes) -> None:
        got = ctypes.c_size_t(0)
        k32.WriteProcessMemory(self.h, ctypes.c_void_p(va), data, len(data), ctypes.byref(got))

    def u32_at(self, va: int) -> int:
        return struct.unpack("<I", self.read(va, 4))[0]

    def hold(self, code: int, down: bool) -> None:
        self.write(self.dinput + 0x20 + code, b"\x80" if down else b"\x00")

    def tap(self, code: int, t: float = 0.1) -> None:
        self.hold(code, True)
        time.sleep(t)
        self.hold(code, False)

    def menu(self, cmd: int) -> None:
        u32.PostMessageW(self.hwnd, 0x0111, cmd, 0)

    def wram_words(self, addr68k: int, count: int):
        return list(struct.unpack(f"<{count}H", self.read(self.wram + (addr68k - 0x100000), count * 2)))

    def owners(self):
        return self.wram_words(0x108000 + VFX_RAM_F8_OWNER, 5)

    def pal_words15(self, slot: int):
        return list(struct.unpack("<15H", self.read(self.pal + slot * 32 + 2, 30)))

    def prom_be(self, p1_off: int, n: int) -> bytes:
        return bswap16(self.read(self.prom + p1_off, n))

    def in_battle(self) -> bool:
        hp1, hp2 = self.wram_words(0x108238, 1)[0], self.wram_words(0x108438, 1)[0]
        return 0 < hp1 <= 0x67 and 0 < hp2 <= 0x67

    def snapshot(self, dest: Path) -> None:
        cap = self.sandbox / "capture"
        before = set(glob.glob(str(cap / "*.png")))
        self.menu(MENU_SNAPSHOT)
        time.sleep(0.5)
        new = sorted(set(glob.glob(str(cap / "*.png"))) - before, key=os.path.getmtime)
        if new:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(new[-1], dest)

    def to_battle(self) -> None:
        time.sleep(1.0)
        self.menu(MENU_TURBO)
        time.sleep(1.0)
        self.menu(MENU_TURBO)
        time.sleep(2.0)
        for _ in range(4):
            self.tap(KEY_COIN)
            time.sleep(0.3)
        time.sleep(1.0)
        self.tap(KEY_START)
        time.sleep(3.0)
        self.tap(KEY_A)
        time.sleep(2.5)
        self.tap(KEY_A)
        time.sleep(3.0)
        for _ in range(3):
            self.tap(KEY_A)
            time.sleep(0.8)
        time.sleep(2.5)
        for _ in range(3):
            self.tap(KEY_A)
            time.sleep(0.8)
        self.menu(MENU_TURBO)
        for _ in range(60):
            time.sleep(0.5)
            if self.in_battle():
                break
        self.menu(MENU_TURBO)
        time.sleep(2.0)

    def kill(self) -> None:
        os.system("taskkill /f /im WinKawaks.exe >nul 2>nul")


def theme_records(p1_be: bytes, hooks, theme_idx: int):
    """Map pal_id -> 15 words for one theme entry inside the packed P1 cave."""
    base = hooks["theme_entries"] + theme_idx * VFX_THEME_ENTRY_STRIDE
    out = {}
    for _, common_off, _, _, _, _, slot_ids in VFX_COMMON_EFFECT_GROUPS[:4]:
        for i, pid in enumerate(slot_ids):
            rec = base + common_off + i * 32
            assert struct.unpack(">H", p1_be[rec : rec + 2])[0] == pid
            out[pid] = list(struct.unpack(">15H", p1_be[rec + 2 : rec + 32]))
    return out


def classic_records(p2_clean: bytes):
    out = {}
    for _, _, _, _, _, _, slot_ids in VFX_COMMON_EFFECT_GROUPS[:4]:
        for pid in slot_ids:
            off = 0x2CFFF0 + pid * 32 + 2
            out[pid] = list(struct.unpack(">15H", p2_clean[off : off + 30]))
    return out


def run() -> int:
    backups = [
        _paths.get_config_path(),
        PROJECT_ROOT / "output" / "roms" / "kof97pls.zip",
        PROJECT_ROOT / "build" / "unpacked" / "p1_be.bin",
        PROJECT_ROOT / "build" / "unpacked" / "p2_be.bin",
    ]
    tmp = Path(tempfile.mkdtemp(prefix="kof97_vfx_verify_"))
    for i, src in enumerate(backups):
        if src.exists():
            shutil.copy2(src, tmp / f"{i}.bak")
    shots = PROJECT_ROOT / "temp" / "shots"
    failures = []
    emu = None
    try:
        api = KOF97BridgeApi()
        api.reset_all_skins()
        api.set_character_vfx({"char_id": 0x1B, "vfx_theme": "jade_venom", "scope": "ALL"})
        api.set_character_vfx({"char_id": 0x00, "vfx_theme": "cangyan_blue", "scope": "SINGLE"})
        assert api.pack_rom().get("success"), "pack_rom failed"

        with zipfile.ZipFile(DEFAULT_KOF97_ZIP) as z:
            p1_clean = bswap16(z.read("KOF97_P1.ROM"))
            p2_clean = bswap16(z.read("KOF97_P2.ROM"))
        with zipfile.ZipFile(api._output_zip) as z:
            p1_out = bswap16(z.read(next(n for n in z.namelist() if "p1" in n.lower())))
        patch = build_hit_effect_vfx_p1_patch(api._character_skins, p1_clean, p2_clean)
        hooks = patch["hooks"]
        expected = {0: theme_records(p1_out, hooks, 0), 1: theme_records(p1_out, hooks, 1)}
        expected[0xFFFF] = classic_records(p2_clean)

        emu = Emu(api._sandbox_dir)
        cave_live = emu.prom_be(VFX_HIT_EFFECT_CAVE_BASE, 0x40)
        print(f"[layout] running P1 cave matches packed ROM: {cave_live == p1_out[0xF0000:0xF0040]}")
        if cave_live != p1_out[0xF0000:0xF0040]:
            failures.append("running P1 image layout does not match packed ROM")
        emu.to_battle()
        p1_char = emu.wram_words(0x108170, 1)[0]
        p2_char = emu.wram_words(0x108370, 1)[0]
        print(f"[battle] in_battle={emu.in_battle()} P1 char=0x{p1_char:02X} P2 char=0x{p2_char:02X}")
        emu.snapshot(shots / "verify_battle_start.png")

        checked = {"IM": 0, "F8": 0, "F9": 0, "EL": 0}
        seen_owner = {0: 0, 1: 0, 0xFFFF: 0}
        last = emu.owners()
        t_end = time.time() + 40.0
        phase = 0
        shot_idx = 0
        while time.time() < t_end and emu.in_battle():
            phase_t = (time.time() * 1000) % 4000
            emu.hold(KEY_RIGHT, phase_t < 1500)
            emu.hold(KEY_LEFT, 2500 <= phase_t)
            if phase_t < 1500 and int(phase_t / 120) % 2 == 0:
                emu.tap((KEY_A, KEY_B, KEY_C)[phase % 3], 0.03)
                phase += 1
            cur = emu.owners()
            for idx, name in enumerate(OWNER_NAMES):
                if cur[idx] == last[idx] or name == "FA":
                    continue
                owner = cur[idx]
                time.sleep(0.05)
                cache_off = VFX_RAM_F8_OWNER + idx * 2
                group = GROUP_BY_CACHE[cache_off]
                for pid in group[6]:
                    got = emu.pal_words15(pid)
                    want = expected.get(owner, {}).get(pid)
                    if want is None:
                        failures.append(f"{name}: unexpected owner 0x{owner:04X}")
                        break
                    if got != want:
                        failures.append(f"{name}: slot 0x{pid:02X} mismatch for owner 0x{owner:04X}")
                checked[name] += 1
                seen_owner[owner] = seen_owner.get(owner, 0) + 1
                if shot_idx < 6:
                    emu.snapshot(shots / f"verify_{name}_owner{owner:04X}_{shot_idx}.png")
                    shot_idx += 1
                print(f"[event] {name} owner -> 0x{owner:04X} palettes verified")
            last = cur
            time.sleep(0.03)
        emu.hold(KEY_RIGHT, False)
        emu.hold(KEY_LEFT, False)
        print(f"[summary] group switches checked: {checked}, owners seen: {seen_owner}")
        if checked["IM"] == 0:
            failures.append("no impact (hit/guard) event observed")

        # Live re-theme Kyo and confirm the running cave + caches are refreshed
        api.apply_vfx_live({"char_id": 0x00, "vfx_theme": "crimson_flame", "scope": "SINGLE"})
        new_patch = build_hit_effect_vfx_p1_patch(api._character_skins, p1_clean, p2_clean)
        blob = new_patch["blob"]
        live_blob = emu.prom_be(VFX_HIT_EFFECT_CAVE_BASE, len(blob))
        owners_after = emu.owners()
        print(f"[live] cave refreshed: {live_blob == blob}, owners after apply: {[hex(o) for o in owners_after]}")
        if live_blob != blob:
            failures.append("apply_vfx_live did not refresh the running P1 cave")
    finally:
        if emu is not None:
            emu.kill()
        for i, src in enumerate(backups):
            bak = tmp / f"{i}.bak"
            if bak.exists():
                shutil.copy2(bak, src)
        shutil.rmtree(tmp, ignore_errors=True)

    if failures:
        print("[FAIL]")
        for f in failures[:30]:
            print("  -", f)
        return 1
    print("[SUCCESS] on-hit / on-guard effect palettes follow the attacker theme")
    return 0


if __name__ == "__main__":
    sys.exit(run())
