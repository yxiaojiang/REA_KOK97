#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump official A-button 15-color palettes for all 36 roster characters."""
import sys
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.roster import CHARACTER_PALETTE_SCHEMA, CHARACTER_ROSTER, get_char_engine_info
from src.palette.color_utils import _rgb5_to_hsv, _unit_luma, decode_lspc2, lspc2_to_hex
from src.rom.rom_tool import DEFAULT_KOF97_ZIP, bswap16

def group_of(schema, idx):
    for name, slots in schema.items():
        if idx in slots:
            return name
    return "UNGROUPED"


def main():
    p1_path = ROOT / "build" / "unpacked" / "p1_be.bin"
    p1 = p1_path.read_bytes()
    with zipfile.ZipFile(DEFAULT_KOF97_ZIP) as z:
        p1_official = bswap16(z.read("KOF97_P1.ROM"))
        p2 = bswap16(z.read("KOF97_P2.ROM"))

    out_lines = []

    def emit(s=""):
        out_lines.append(s)
        print(s)

    diffs = 0
    for pal_idx in range(0x24):
        off = 0x483E + pal_idx * 8
        a = p1[off:off + 8]
        b = p1_official[off:off + 8]
        if a != b:
            diffs += 1
            emit(
                "P1 pal table DIFF pal_idx=0x%02X: unpacked=%s official=%s"
                % (pal_idx, a.hex(), b.hex())
            )
    emit("P1 pal_id table diffs in 0x00..0x23: %d" % diffs)
    emit("")

    emit("=== pal_id table (4 buttons) ===")
    for pal_idx in range(0x24):
        off = 0x483E + pal_idx * 8
        pids = struct.unpack(">4H", p1[off:off + 8])
        emit("  pal_idx=0x%02X: %s" % (pal_idx, " ".join("%04X" % pid for pid in pids)))
    emit("")

    for char in CHARACTER_ROSTER:
        cid = char["id"]
        engine_cid, alt_flag, pal_idx = get_char_engine_info(cid)
        base_off = 0x483E + pal_idx * 8
        pal_id = struct.unpack(">H", p1[base_off:base_off + 2])[0]
        p2_addr = 0x2CFFF0 + pal_id * 32
        words = list(struct.unpack(">16H", p2[p2_addr:p2_addr + 32]))
        body = words[1:]
        schema = CHARACTER_PALETTE_SCHEMA.get(cid, {})
        used = set()
        for slots in schema.values():
            used.update(slots)
        missing = [i for i in range(15) if i not in used]
        emit("=" * 88)
        emit(
            "%s / %s  UI=0x%02X  eng=0x%02X  alt=%s  pal_idx=0x%02X  pal_id=0x%04X"
            % (char["name_cn"], char["name_en"], cid, engine_cid, alt_flag, pal_idx, pal_id)
        )
        emit("  schema=%s" % schema)
        if missing:
            emit("  MISSING SLOTS: %s" % missing)
        for i, w in enumerate(body):
            r5, g5, b5, dark = decode_lspc2(w)
            hx = lspc2_to_hex(w)
            h, s, v = _rgb5_to_hsv(r5, g5, b5)
            y = _unit_luma(r5 / 31.0, g5 / 31.0, b5 / 31.0)
            grp = group_of(schema, i)
            flags = []
            if s <= 0.12 and v >= 0.90:
                flags.append("TRUE_WHITE")
            elif v <= 0.06:
                flags.append("NEAR_BLACK")
            elif s <= 0.18 and v >= 0.75:
                flags.append("PALE")
            elif 8 <= h <= 48 and s >= 0.20 and 0.18 <= y <= 0.85:
                flags.append("SKINLIKE")
            emit(
                "  W%02d idx=%2d %s  %-12s  H=%6.1f S=%5.2f V=%5.2f Y=%5.3f  RGB5=(%2d,%2d,%2d) %s"
                % (i + 1, i, hx, grp, h, s, v, y, r5, g5, b5, " ".join(flags))
            )
        emit("")

    out_path = ROOT / "src" / "tests" / "official_palettes.txt"
    out_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print("Wrote %s" % out_path)


if __name__ == "__main__":
    main()
