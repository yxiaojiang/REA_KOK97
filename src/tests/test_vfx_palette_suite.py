#!/usr/bin/env python3
"""
Automated test suite for TASK-STUDIO-019: Character Skill VFX Palette Recoloring.
Verifies P1 0x004956 table lookup (including interleaved 0x15..0x1A rows),
whitelist filtering, luminous OKLCH shader properties, config round-tripping,
frozen costume isolation, and full pack_rom lossless classic restoration.
"""

from __future__ import annotations

import shutil
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import src.core.paths as _paths
from src.rom import rom_tool
from src.palette import vfx_shader
from src.studio import kof97_webview_app as app


class TestVfxPaletteSuite(unittest.TestCase):
    """Comprehensive verification for 36-character skill VFX recoloring."""

    @classmethod
    def setUpClass(cls) -> None:
        with zipfile.ZipFile(rom_tool.DEFAULT_KOF97_ZIP) as zf:
            cls.p1_clean = rom_tool.bswap16(zf.read("KOF97_P1.ROM"))
            cls.p2_clean = rom_tool.bswap16(zf.read("KOF97_P2.ROM"))
        cls.vfx_map = app.build_character_vfx_map(cls.p1_clean, cls.p2_clean)

    def test_p1_table_lookup_and_interleave(self) -> None:
        """P1 0x004956 must be read via table lookup, respecting 0x15..0x1A interleaving."""
        # Yashiro(0x15), Shermie(0x16), Chris(0x17) -> 0x0B40, 0x0B50, 0x0B60
        self.assertEqual(self.vfx_map[0x15]["vfx_base_pid"], 0x0B40)
        self.assertEqual(self.vfx_map[0x16]["vfx_base_pid"], 0x0B50)
        self.assertEqual(self.vfx_map[0x17]["vfx_base_pid"], 0x0B60)
        # Yamazaki(0x18), Blue Mary(0x19), Billy(0x1A) -> 0x0B10, 0x0B20, 0x0B30
        self.assertEqual(self.vfx_map[0x18]["vfx_base_pid"], 0x0B10)
        self.assertEqual(self.vfx_map[0x19]["vfx_base_pid"], 0x0B20)
        self.assertEqual(self.vfx_map[0x1A]["vfx_base_pid"], 0x0B30)
        # Orochi(0x22) -> table 0x1E (0x0BA0), Orochi Iori(0x1D) -> 0x0B80, '94 Kyo(0x23) -> 0x09C0
        self.assertEqual(self.vfx_map[0x22]["vfx_base_pid"], 0x0BA0)
        self.assertEqual(self.vfx_map[0x1D]["vfx_base_pid"], 0x0B80)
        self.assertEqual(self.vfx_map[0x23]["vfx_base_pid"], 0x09C0)

    def test_placeholder_and_body_flash_exclusions(self) -> None:
        """Solid placeholder blocks and stun/body flash sub-slots must be excluded."""
        # Non-projectile pure-melee roster entries have empty VFX slots
        for cid in (0x02, 0x0A, 0x0B, 0x12, 0x13, 0x1C):
            self.assertFalse(
                self.vfx_map[cid]["has_vfx"],
                f"Expected pure melee cid 0x{cid:02X} to have no standalone VFX slots",
            )

        # Every selected slot across all 36 chars must sit strictly above UI range 0x0000..0x00FF
        for cid, info in self.vfx_map.items():
            for pid in info["all_slots"]:
                self.assertGreater(pid, 0x00FF, f"Public UI pal_id 0x{pid:04X} leaked into VFX map")

        # Hit-stun / body sub-slots (+6 elec, +9 burn, Kyo +7, Orochi +2) must NEVER be included
        self.assertNotIn(7, self.vfx_map[0x00]["char_sub_offsets"])
        self.assertNotIn(9, self.vfx_map[0x00]["char_sub_offsets"])
        self.assertNotIn(6, self.vfx_map[0x00]["char_sub_offsets"])
        self.assertNotIn(2, self.vfx_map[0x22]["char_sub_offsets"])
        self.assertEqual(self.vfx_map[0x01]["char_sub_offsets"], [])
        self.assertEqual(self.vfx_map[0x19]["char_sub_offsets"], [])

        # Confirm pure uniform VFX sub-slots ARE captured for flame/lightning/slash users
        self.assertIn(2, self.vfx_map[0x00]["char_sub_offsets"])
        self.assertIn(1, self.vfx_map[0x14]["char_sub_offsets"])
        self.assertIn(1, self.vfx_map[0x22]["char_sub_offsets"])

    def test_luminous_vfx_shader_properties(self) -> None:
        """Shader keeps sentinels & incandescent white core, and produces high-chroma neon mids."""
        kyo_slot0 = app._read_p2_slot_words15(self.p2_clean, 0x09C0)
        mary_slot0 = app._read_p2_slot_words15(self.p2_clean, 0x0B20)
        yashiro_slot3 = app._read_p2_slot_words15(self.p2_clean, 0x0B43)

        for words, preset_id in (
            (kyo_slot0, "cangyan_blue"),
            (mary_slot0, "mingyan_purple"),
            (yashiro_slot3, "jade_venom"),
        ):
            inner_hex = app.VFX_PRESET_MAP[preset_id]["inner"]
            outer_hex = app.VFX_PRESET_MAP[preset_id]["outer"]
            recolored = app.recolor_vfx_palette(words, inner_hex, outer_hex)
            self.assertEqual(len(recolored), 15)

            mid_chromas = []
            for src_w, dst_w in zip(words, recolored):
                if src_w in app.VFX_SENTINEL_WORDS:
                    self.assertEqual(dst_w, src_w, f"Sentinel word 0x{src_w:04X} was altered!")
                    continue
                if src_w == 0x7FFF:
                    self.assertEqual(dst_w, 0x7FFF, "Pure white core 0x7FFF must stay pure white")
                    continue
                sr, sg, sb, _ = app.decode_lspc2(src_w)
                dr, dg, db, _ = app.decode_lspc2(dst_w)
                src_l, _, _ = app._rgb_unit_to_oklch(sr / 31.0, sg / 31.0, sb / 31.0)
                dst_l, dst_c, _ = app._rgb_unit_to_oklch(dr / 31.0, dg / 31.0, db / 31.0)
                if src_l >= 0.90:
                    self.assertGreaterEqual(dst_l, 0.85, "Incandescent core luminosity dropped")
                elif src_l >= 0.50:
                    mid_chromas.append(dst_c)

            self.assertTrue(mid_chromas, "Expected active mid-range VFX colors")
            self.assertGreaterEqual(
                max(mid_chromas),
                0.15,
                f"Expected high neon chroma in mid band for {preset_id}, got {mid_chromas}",
            )

    @staticmethod
    def _read_packed_rom(zip_path: Path, token: str) -> bytes:
        with zipfile.ZipFile(zip_path) as z_out:
            member = next(n for n in z_out.namelist() if token in n.lower())
            return rom_tool.bswap16(z_out.read(member))

    @classmethod
    def _read_packed_p2(cls, zip_path: Path) -> bytes:
        return cls._read_packed_rom(zip_path, "p2")

    @classmethod
    def _read_packed_p1(cls, zip_path: Path) -> bytes:
        return cls._read_packed_rom(zip_path, "p1")

    def test_pack_rom_classic_lossless_and_vfx_injection(self) -> None:
        """
        Verify in an isolated temp workspace that:
        1. 'classic' VFX preserves every P2 VFX slot byte-for-byte even when costume changes.
        2. Custom VFX themes + 'sync_skin' modify P2 VFX slots while preserving UI 0x0000..0x00FF
           and keeping the frozen costume generator bytes 100% identical.
        """
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            workdir = tmp_path / "unpacked"
            workdir.mkdir(parents=True, exist_ok=True)
            out_zip = tmp_path / "kof97pls.zip"
            cfg_file = tmp_path / "mod_studio_config.json"

            orig_cfg_fn = app.get_config_path
            orig_paths_cfg_fn = _paths.get_config_path
            app.get_config_path = lambda: cfg_file
            _paths.get_config_path = lambda: cfg_file
            try:
                rom_tool.unpack_rom_set(rom_tool.DEFAULT_KOF97_ZIP, workdir)
                api = app.KOF97BridgeApi()
                api._workdir = workdir
                api._output_zip = out_zip

                # Case 1: Custom costume on Iori (0x1B) with classic VFX -> VFX slots stay clean!
                api.reset_all_skins()
                api.set_character_skin({"char_id": 0x1B, "theme_id": "azure_thunder", "scope": "SINGLE"})
                res1 = api.pack_rom()
                self.assertTrue(res1.get("success"), res1)
                p2_case1 = self._read_packed_p2(out_zip)

                # Clean UI palettes 0x0000..0x00FF
                ui_end = 0x2CFFF0 + 0x0100 * 32
                ui_start = 0x2CFFF0
                self.assertEqual(p2_case1[ui_start:ui_end], self.p2_clean[ui_start:ui_end])

                # Iori VFX slots must remain byte-for-byte identical when vfxTheme == "classic"
                for vpid in self.vfx_map[0x1B]["all_slots"]:
                    off = 0x2CFFF0 + vpid * 32
                    self.assertEqual(p2_case1[off : off + 32], self.p2_clean[off : off + 32])

                # Snapshot Iori costume bytes produced by the frozen painter
                iori_cbase_off = 0x2CFFF0 + 0x07C0 * 32
                iori_costume_bytes = p2_case1[iori_cbase_off : iori_cbase_off + 32]

                # Case 2: Enable 'sync_skin' on Iori and 'mingyan_purple' on all others
                api.set_character_vfx({"char_id": 0x1B, "vfx_theme": "mingyan_purple", "scope": "ALL"})
                api.set_character_vfx({"char_id": 0x1B, "vfx_theme": "sync_skin", "scope": "SINGLE"})

                # Verify config reload keeps vfxTheme cleanly
                api_reloaded = app.KOF97BridgeApi()
                self.assertEqual(api_reloaded._character_skins[0x1B]["vfxTheme"], "sync_skin")
                self.assertEqual(api_reloaded._character_skins[0x00]["vfxTheme"], "mingyan_purple")

                res2 = api.pack_rom()
                self.assertTrue(res2.get("success"), res2)
                p2_case2 = self._read_packed_p2(out_zip)

                # UI palettes 0x0000..0x00FF still untouched
                self.assertEqual(p2_case2[ui_start:ui_end], self.p2_clean[ui_start:ui_end])

                # Frozen costume palette on Iori did NOT change when VFX was applied
                self.assertEqual(p2_case2[iori_cbase_off : iori_cbase_off + 32], iori_costume_bytes)

                # Every VFX-capable character now has modified VFX bytes (and intact sentinels)
                changed_chars = 0
                for cid, info in self.vfx_map.items():
                    if not info["has_vfx"]:
                        continue
                    char_changed = False
                    for vpid in info["all_slots"]:
                        off = 0x2CFFF0 + vpid * 32
                        old_ws = list(struct.unpack(">15H", self.p2_clean[off + 2 : off + 32]))
                        new_ws = list(struct.unpack(">15H", p2_case2[off + 2 : off + 32]))
                        if old_ws != new_ws:
                            char_changed = True
                        for ow, nw in zip(old_ws, new_ws):
                            if ow in app.VFX_SENTINEL_WORDS or ow == 0x7FFF:
                                self.assertEqual(nw, ow)
                    self.assertTrue(char_changed, f"VFX did not modify any slot for cid 0x{cid:02X}")
                    changed_chars += 1
                self.assertGreaterEqual(changed_chars, 28)

                # Case 3: Reset all skins restores classic VFX and classic P2 VFX bytes
                api.reset_all_skins()
                for cid in range(36):
                    self.assertEqual(api._character_skins[cid]["vfxTheme"], "classic")
                res3 = api.pack_rom()
                self.assertTrue(res3.get("success"), res3)
                p2_case3 = self._read_packed_p2(out_zip)
                for cid, info in self.vfx_map.items():
                    for vpid in info["all_slots"]:
                        off = 0x2CFFF0 + vpid * 32
                        self.assertEqual(
                            p2_case3[off : off + 32],
                            self.p2_clean[off : off + 32],
                            f"Classic reset failed to restore slot 0x{vpid:04X} for cid 0x{cid:02X}",
                        )
            finally:
                app.get_config_path = orig_cfg_fn
                _paths.get_config_path = orig_paths_cfg_fn

    def test_hit_effect_p1_hooks_burn_and_restore(self) -> None:
        """
        Verify P1 0x0F0000 dynamic on-hit burn/shock/flame code cave:
        - Keeps P2 0x0000..0x00FF and 0x17B0..0x17DF untouched.
        - Disassembles every generated 68000 instruction cleanly via capstone.
        - Preserves neutral grey smoke in split flame slots 0x0058/0x005F while recoloring flame band.
        - Restores all 16 P1 hook sites & 0x0F0000..0x0FFFFF to clean official bytes on classic reset.
        """
        from capstone import Cs, CS_ARCH_M68K, CS_MODE_M68K_000

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            workdir = tmp_path / "unpacked"
            workdir.mkdir(parents=True, exist_ok=True)
            out_zip = tmp_path / "kof97pls.zip"
            cfg_file = tmp_path / "mod_studio_config.json"

            orig_cfg_fn = app.get_config_path
            orig_paths_cfg_fn = _paths.get_config_path
            app.get_config_path = lambda: cfg_file
            _paths.get_config_path = lambda: cfg_file
            try:
                rom_tool.unpack_rom_set(rom_tool.DEFAULT_KOF97_ZIP, workdir)
                api = app.KOF97BridgeApi()
                api._workdir = workdir
                api._output_zip = out_zip

                # Mixed custom roster: Red Iori, Blue Kyo, Gold Benimaru, Purple Orochi; '94 Kyo classic
                api.reset_all_skins()
                api.set_character_vfx({"char_id": 27, "vfx_theme": "crimson_flame", "scope": "SINGLE"})
                api.set_character_vfx({"char_id": 0, "vfx_theme": "cangyan_blue", "scope": "SINGLE"})
                api.set_character_vfx({"char_id": 1, "vfx_theme": "holy_gold", "scope": "SINGLE"})
                api.set_character_vfx({"char_id": 34, "vfx_theme": "mingyan_purple", "scope": "SINGLE"})

                res = api.pack_rom()
                self.assertTrue(res.get("success"), res)
                p1_mod = self._read_packed_p1(out_zip)
                p2_mod = self._read_packed_p2(out_zip)

                # 1. P2 public palettes 0x0000..0x00FF AND burn tables 0x17B0..0x17DF stay untouched
                p2_ui_start = 0x2CFFF0
                p2_ui_end = 0x2CFFF0 + 0x0100 * 32
                self.assertEqual(p2_mod[p2_ui_start:p2_ui_end], self.p2_clean[p2_ui_start:p2_ui_end])
                p2_burn_s = 0x2CFFF0 + 0x17B0 * 32
                p2_burn_e = 0x2CFFF0 + 0x17E0 * 32
                self.assertEqual(p2_mod[p2_burn_s:p2_burn_e], self.p2_clean[p2_burn_s:p2_burn_e])

                # 2. Validate P1 code cave disassembly & all 16 hook sites
                patch = app.build_hit_effect_vfx_p1_patch(
                    api._character_skins, self.p1_clean, self.p2_clean
                )
                self.assertIsNotNone(patch)
                assert patch is not None
                hooks = patch["hooks"]
                code_len = hooks["char_theme_idx"] - app.VFX_HIT_EFFECT_CAVE_BASE
                md = Cs(CS_ARCH_M68K, CS_MODE_M68K_000)
                dis = list(
                    md.disasm(
                        p1_mod[app.VFX_HIT_EFFECT_CAVE_BASE : app.VFX_HIT_EFFECT_CAVE_BASE + code_len],
                        app.VFX_HIT_EFFECT_CAVE_BASE,
                    )
                )
                self.assertEqual(sum(i.size for i in dis), code_len)

                for _name, off, _orig, target_lbl in app.VFX_HIT_HOOK_ORIGINALS:
                    self.assertEqual(
                        p1_mod[off : off + 6],
                        struct.pack(">HI", 0x4EB9, hooks[target_lbl]),
                    )

                # 3. Verify smoke preservation in 0x0058 & 0x005F and red flame recoloring for Iori
                char_table_off = hooks["char_theme_idx"]
                iori_theme_idx = struct.unpack(">H", p1_mod[char_table_off + 27 * 2 : char_table_off + 28 * 2])[0]
                self.assertNotEqual(iori_theme_idx, 0xFFFF)
                kyo94_theme_idx = struct.unpack(">H", p1_mod[char_table_off + 35 * 2 : char_table_off + 36 * 2])[0]
                self.assertEqual(kyo94_theme_idx, 0xFFFF)

                entry_off = hooks["theme_entries"] + iori_theme_idx * app.VFX_THEME_ENTRY_STRIDE
                # 0x0058 is record index 1 in group 0 (+0x20), 0x005F is record index 1 in group 1 (+0xA0)
                for rec_off, pid in ((entry_off + 0x20, 0x0058), (entry_off + 0xA0, 0x005F)):
                    rec_pid = struct.unpack(">H", p1_mod[rec_off : rec_off + 2])[0]
                    self.assertEqual(rec_pid, pid)
                    smoke_mod = list(struct.unpack(">9H", p1_mod[rec_off + 2 : rec_off + 20]))
                    smoke_clean = app._read_p2_slot_words15(self.p2_clean, pid)[:9]
                    self.assertEqual(smoke_mod, smoke_clean, f"Neutral smoke changed for 0x{pid:04X}")
                    flame_mod = list(struct.unpack(">6H", p1_mod[rec_off + 20 : rec_off + 32]))
                    flame_clean = app._read_p2_slot_words15(self.p2_clean, pid)[9:15]
                    self.assertNotEqual(flame_mod, flame_clean)

                # Verify Iori F9 (0x17C0) cyclic burn frame 0 shifted to vivid crimson hue (R > B)
                f9_off = entry_off + 0x420
                f9_words = struct.unpack(">15H", p1_mod[f9_off + 2 : f9_off + 32])
                r5, _g5, b5, _ = app.decode_lspc2(f9_words[2])
                self.assertGreater(r5, b5 + 10, f"Expected crimson F9 burn color, got R={r5}, B={b5}")

                # 4. Reset to all-classic -> P1 hooks & 0x0F0000 cave must revert to 100% clean
                api.reset_all_skins()
                res_clean = api.pack_rom()
                self.assertTrue(res_clean.get("success"), res_clean)
                p1_clean_out = self._read_packed_p1(out_zip)
                for _name, off, orig_bytes, _lbl in app.VFX_HIT_HOOK_ORIGINALS:
                    self.assertEqual(p1_clean_out[off : off + 6], orig_bytes)
                self.assertEqual(
                    p1_clean_out[0x0F0000:0x100000],
                    self.p1_clean[0x0F0000:0x100000],
                )
            finally:
                app.get_config_path = orig_cfg_fn
                _paths.get_config_path = orig_paths_cfg_fn

    def _p2_bank(self, bank: int, addr: int, size: int) -> bytes:
        off = bank * 0x100000 + (addr - 0x200000)
        return self.p2_clean[off : off + size]

    def _spark_anim_palettes(self, anim: int) -> set:
        """Palette ids drawn by one common-effect (object 0x20) animation, via P1/P2 tables."""
        obj = 0x20
        p1 = self.p1_clean
        anim_tbl = struct.unpack(">I", p1[0xAFBCA + obj * 4 : 0xAFBCA + obj * 4 + 4])[0]
        d2 = struct.unpack(">H", p1[anim_tbl + anim * 2 : anim_tbl + anim * 2 + 2])[0]
        script_tbl = struct.unpack(">I", self._p2_bank(2, 0x200002 + obj * 4, 4))[0]
        pos = struct.unpack(">I", self._p2_bank(2, script_tbl + d2 * 4, 4))[0]
        frame_tbl = struct.unpack(">I", self._p2_bank(1, 0x200002 + obj * 4, 4))[0]
        def_tbl = struct.unpack(">I", self._p2_bank(1, 0x250000 + obj * 4, 4))[0]
        pals = set()
        for _ in range(64):
            head = self._p2_bank(2, pos, 4)
            if head[0] >= 0x80:
                if 0x100 - head[0] in (1, 2):
                    break
                pos += 6
                continue
            frame = struct.unpack(">H", head[2:4])[0]
            rec = frame_tbl + frame * 6
            sprite_def = struct.unpack(">H", self._p2_bank(1, rec + 4, 2))[0] & 0x3FF
            dptr = struct.unpack(">I", self._p2_bank(1, def_tbl + sprite_def * 4, 4))[0]
            pals.add(self._p2_bank(1, dptr, 1)[0])
            pos += 6
        return pals

    def test_hit_dispatcher_spark_palettes_covered_by_groups(self) -> None:
        """Every spark the P1 0x012E5C hit/guard dispatcher can spawn must use a slot of the group it triggers."""
        p1 = self.p1_clean
        w = lambda a: struct.unpack(">H", p1[a : a + 2])[0]
        groups = {g[0]: set(g[6]) for g in vfx_shader.VFX_COMMON_EFFECT_GROUPS[:4]}
        im, f8, f9, el = (groups[k] for k in (0x6E08, 0x6E00, 0x6E02, 0x6E06))
        multi = lambda tbl: {w(tbl + i * 2) for i in range(4)}

        # (class -> extra anims and the group responsible for them), records at P1 0x012E92
        spawned: list = []
        for eff in range(20):
            rec = struct.unpack(">I", p1[0x12E92 + eff * 4 : 0x12E96 + eff * 4])[0]
            cls = w(rec)
            spawned.append((w(rec + 2), el if cls == 3 else im))
            if cls == 1:
                spawned.append((w(rec + 4), im))
                spawned += [(a, im) for a in multi(0x1347A)]
            elif cls == 2:
                spawned += [(a, f8) for a in multi(0x1348A)]
            elif cls == 3:
                spawned += [(a, el) for a in multi(0x13482)]
            elif cls == 4:
                spawned += [(a, im) for a in multi(0x1347A)]
            elif cls == 6:
                spawned += [(a, f9) for a in multi(0x13492)]
        spawned += [(a, f8) for a in multi(0x1349A)]
        spawned += [(a, f9) for a in multi(0x134A4)]
        spawned += [(a, el) for a in multi(0x134AE)]

        for anim, group in spawned:
            for pal in self._spark_anim_palettes(anim):
                words = app._read_p2_slot_words15(self.p2_clean, pal)
                if all(x in app.VFX_SENTINEL_WORDS for x in words):
                    continue
                self.assertIn(pal, group, f"spark anim 0x{anim:02X} draws pal 0x{pal:02X} outside its group")

        # Guard sparks (blue 0x53, orange 0x54) switch on every impact
        self.assertTrue({0x51, 0x53, 0x54, 0x55} <= im)

    def test_hit_effect_groups_disjoint_and_attacker_id_low_byte(self) -> None:
        """Owner-cached groups must not share slots; attacker id is the low byte ($71) of word $70."""
        seen: set = set()
        for g in vfx_shader.VFX_COMMON_EFFECT_GROUPS[:4]:
            self.assertFalse(seen & set(g[6]), f"slot shared between groups: {seen & set(g[6])}")
            seen |= set(g[6])

        skins = {
            0: {"themeId": "classic", "vfxTheme": "cangyan_blue"},
            1: {"themeId": "classic", "vfxTheme": "holy_gold"},
            27: {"themeId": "classic", "vfxTheme": "crimson_flame"},
        }
        patch = app.build_hit_effect_vfx_p1_patch(skins, self.p1_clean, self.p2_clean)
        assert patch is not None
        blob = patch["blob"]
        code_len = patch["hooks"]["char_theme_idx"] - app.VFX_HIT_EFFECT_CAVE_BASE
        self.assertIn(bytes.fromhex("10280071"), blob[:code_len])
        self.assertNotIn(bytes.fromhex("10280070"), blob[:code_len])

        entries = patch["hooks"]["theme_entries"] - app.VFX_HIT_EFFECT_CAVE_BASE
        for idx in range(patch["theme_count"]):
            base = entries + idx * app.VFX_THEME_ENTRY_STRIDE
            for _, common_off, _, _, _, _, slot_ids in vfx_shader.VFX_COMMON_EFFECT_GROUPS[:4]:
                for i, pid in enumerate(slot_ids):
                    rec = base + common_off + i * 32
                    self.assertEqual(struct.unpack(">H", blob[rec : rec + 2])[0], pid)
            self.assertEqual(struct.unpack(">H", blob[base + 0x220 : base + 0x222])[0], 0x17B0)
            self.assertEqual(struct.unpack(">H", blob[base + 0x420 : base + 0x422])[0], 0x17C0)
        self.assertEqual(len(blob) - entries, patch["theme_count"] * app.VFX_THEME_ENTRY_STRIDE)

    def test_live_hit_effect_p1_writes(self) -> None:
        """Live writes install cave + hooks for custom configs and restore pristine hooks for classic."""
        from src.rom.p1_patcher import VFX_HIT_HOOK_ORIGINALS, build_live_hit_effect_p1_writes

        skins = {27: {"themeId": "classic", "vfxTheme": "crimson_flame"}}
        live = build_live_hit_effect_p1_writes(skins, self.p1_clean, self.p2_clean)
        self.assertTrue(live["active"])
        self.assertEqual(live["writes"][0][0], app.VFX_HIT_EFFECT_CAVE_BASE)
        hook_writes = dict(live["writes"][1:])
        for _name, off, _orig, _lbl in VFX_HIT_HOOK_ORIGINALS:
            self.assertEqual(hook_writes[off][:2], b"\x4e\xb9")

        classic = build_live_hit_effect_p1_writes({}, self.p1_clean, self.p2_clean)
        self.assertFalse(classic["active"])
        self.assertEqual(
            dict(classic["writes"]),
            {off: orig for _name, off, orig, _lbl in VFX_HIT_HOOK_ORIGINALS},
        )

    def test_hit_effect_worst_case_36_unique_themes_fits_64kb(self) -> None:
        """Even 36 simultaneously distinct custom hues must fit cleanly inside 0x0F0000..0x0FFFFF."""
        skins = {}
        for cid in range(36):
            r = 80 + (cid * 5) % 175
            g = 60 + (cid * 11) % 195
            b = 70 + (cid * 17) % 185
            skins[cid] = {
                "themeId": f"custom_{cid}",
                "vfxTheme": "sync_skin",
                "colors": [f"#{r:02X}{g:02X}{b:02X}"] * 15,
            }
        patch = app.build_hit_effect_vfx_p1_patch(skins, self.p1_clean, self.p2_clean)
        self.assertIsNotNone(patch)
        assert patch is not None
        self.assertGreaterEqual(patch["theme_count"], 24)
        self.assertLessEqual(len(patch["blob"]), app.VFX_HIT_EFFECT_CAVE_SIZE)
        header_and_code = len(patch["blob"]) - patch["theme_count"] * app.VFX_THEME_ENTRY_STRIDE
        self.assertLessEqual(
            header_and_code + 36 * app.VFX_THEME_ENTRY_STRIDE,
            app.VFX_HIT_EFFECT_CAVE_SIZE,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
