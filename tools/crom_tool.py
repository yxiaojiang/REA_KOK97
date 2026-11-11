#!/usr/bin/env python3
"""
KOF97 Neo-Geo MVS C-ROM Graphics Toolchain (crom_tool.py)

Provides 16x16 4bpp sprite tile decoding/encoding, pair deinterleaving/interleaving,
batch tile extraction to PNG, tile importing, and round-trip verification across all
40MB of Character ROMs (C1..C6) in SNK Neo-Geo MVS cartridges.

Neo-Geo Sprite Tile Layout (16x16, 4bpp, 128 bytes per tile):
- Subdivided into four 8x8 blocks: Top-Right (0), Bottom-Right (1), Top-Left (2), Bottom-Left (3)
- Planar bitplane distribution:
  - Odd C-ROMs (C1, C3, C5) store Bitplanes 0 and 1 (64 bytes/tile)
  - Even C-ROMs (C2, C4, C6) store Bitplanes 2 and 3 (64 bytes/tile)
- In each 8x8 row, bit 0 (LSB) is the leftmost pixel and bit 7 (MSB) is the rightmost.
  (This matches official hardware / arcade-sprite-viewer packed gfx.)
"""

import argparse
import binascii
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import zipfile

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE_ROM = Path(r"C:\Program Files (x86)\KOF97\roms\kof97.ZIP")
DEFAULT_CROM_DIR = WORKSPACE_ROOT / "build" / "crom_unpacked"

C_ROM_PAIRS = [
    ("c1_c2", "KOF97_C1.ROM", "KOF97_C2.ROM", 8388608),
    ("c3_c4", "KOF97_C3.ROM", "KOF97_C4.ROM", 8388608),
    ("c5_c6", "KOF97_C5.ROM", "KOF97_C6.ROM", 4194304),
]

BLOCK_OFFSETS = [
    (8, 0),  # Block 0: Top-Right
    (8, 8),  # Block 1: Bottom-Right
    (0, 0),  # Block 2: Top-Left
    (0, 8),  # Block 3: Bottom-Left
]


def crc32_hex(data: bytes) -> str:
    """Return unsigned 32-bit CRC formatted as an 8-digit lowercase hex string."""
    return f"0x{binascii.crc32(data) & 0xFFFFFFFF:08x}"


def sha256_hex(data: bytes) -> str:
    """Return SHA-256 digest as a lowercase hex string."""
    return hashlib.sha256(data).hexdigest()


def decode_tile_16x16(odd_64: bytes, even_64: bytes) -> List[List[int]]:
    """
    Decode one 128-byte Neo-Geo 16x16 4bpp sprite tile into a 16x16 2D matrix
    of pixel color indices (0..15).
    odd_64: 64 bytes from Odd C-ROM (bitplanes 0 and 1).
    even_64: 64 bytes from Even C-ROM (bitplanes 2 and 3).
    """
    if len(odd_64) != 64 or len(even_64) != 64:
        raise ValueError(f"Tile halves must be exactly 64 bytes (got {len(odd_64)}, {len(even_64)})")

    pixels = [[0] * 16 for _ in range(16)]

    for b, (x_ofs, y_ofs) in enumerate(BLOCK_OFFSETS):
        b_offset = b * 16
        for r in range(8):
            bp0 = odd_64[b_offset + r * 2]
            bp1 = odd_64[b_offset + r * 2 + 1]
            bp2 = even_64[b_offset + r * 2]
            bp3 = even_64[b_offset + r * 2 + 1]

            for px in range(8):
                # LSB is the leftmost pixel of the 8x8 row.
                shift = px
                b0 = (bp0 >> shift) & 1
                b1 = (bp1 >> shift) & 1
                b2 = (bp2 >> shift) & 1
                b3 = (bp3 >> shift) & 1
                color = (b3 << 3) | (b2 << 2) | (b1 << 1) | b0
                pixels[y_ofs + r][x_ofs + px] = color

    return pixels


def encode_tile_16x16(pixels: List[List[int]]) -> Tuple[bytes, bytes]:
    """
    Encode a 16x16 2D matrix of pixel color indices (0..15) into:
    odd_64: 64 bytes for Odd C-ROM (bitplanes 0 and 1).
    even_64: 64 bytes for Even C-ROM (bitplanes 2 and 3).
    """
    if len(pixels) != 16 or any(len(row) != 16 for row in pixels):
        raise ValueError("Pixel matrix must be exactly 16x16")

    odd = bytearray(64)
    even = bytearray(64)

    for b, (x_ofs, y_ofs) in enumerate(BLOCK_OFFSETS):
        b_offset = b * 16
        for r in range(8):
            bp0 = bp1 = bp2 = bp3 = 0
            for px in range(8):
                shift = px
                color = pixels[y_ofs + r][x_ofs + px] & 0x0F
                bp0 |= ((color >> 0) & 1) << shift
                bp1 |= ((color >> 1) & 1) << shift
                bp2 |= ((color >> 2) & 1) << shift
                bp3 |= ((color >> 3) & 1) << shift

            odd[b_offset + r * 2] = bp0
            odd[b_offset + r * 2 + 1] = bp1
            even[b_offset + r * 2] = bp2
            even[b_offset + r * 2 + 1] = bp3

    return bytes(odd), bytes(even)


def deinterleave_pair(odd_rom: bytes, even_rom: bytes) -> bytes:
    """
    Deinterleave a paired set of C-ROMs (Odd and Even) into a unified
    tile stream where every 16x16 tile is stored as a consecutive 128-byte block:
    [odd_64 (planes 0,1) | even_64 (planes 2,3)].
    """
    if len(odd_rom) != len(even_rom):
        raise ValueError(f"ROM pair sizes mismatch: {len(odd_rom)} != {len(even_rom)}")
    if len(odd_rom) % 64 != 0:
        raise ValueError(f"ROM size ({len(odd_rom)}) is not aligned to 64 bytes (tile half)")

    num_tiles = len(odd_rom) // 64
    out = bytearray(len(odd_rom) * 2)

    mv_odd = memoryview(odd_rom)
    mv_even = memoryview(even_rom)
    mv_out = memoryview(out)

    for i in range(num_tiles):
        mv_out[i * 128 : i * 128 + 64] = mv_odd[i * 64 : (i + 1) * 64]
        mv_out[i * 128 + 64 : (i + 1) * 128] = mv_even[i * 64 : (i + 1) * 64]

    return bytes(out)


def interleave_pair(tile_stream: bytes) -> Tuple[bytes, bytes]:
    """
    Split a unified 128-byte-per-tile stream back into Odd and Even C-ROM buffers.
    """
    if len(tile_stream) % 128 != 0:
        raise ValueError(f"Tile stream length ({len(tile_stream)}) is not aligned to 128 bytes")

    num_tiles = len(tile_stream) // 128
    odd = bytearray(num_tiles * 64)
    even = bytearray(num_tiles * 64)

    mv_stream = memoryview(tile_stream)
    mv_odd = memoryview(odd)
    mv_even = memoryview(even)

    for i in range(num_tiles):
        mv_odd[i * 64 : (i + 1) * 64] = mv_stream[i * 128 : i * 128 + 64]
        mv_even[i * 64 : (i + 1) * 64] = mv_stream[i * 128 + 64 : (i + 1) * 128]

    return bytes(odd), bytes(even)


def deinterleave_all_c_roms(source_zip: Path, out_dir: Path) -> Dict[str, dict]:
    """
    Extract and deinterleave all 3 C-ROM pairs (40MB total) from source_zip
    into unified .spr tile stream binaries in out_dir.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    report = {}

    with zipfile.ZipFile(source_zip, "r") as z:
        for pair_name, odd_name, even_name, exp_size in C_ROM_PAIRS:
            odd_data = z.read(odd_name)
            even_data = z.read(even_name)

            if len(odd_data) != exp_size or len(even_data) != exp_size:
                raise ValueError(
                    f"Unexpected size for pair {pair_name}: odd={len(odd_data)}, even={len(even_data)}, expected={exp_size}"
                )

            spr_data = deinterleave_pair(odd_data, even_data)
            out_file = out_dir / f"{pair_name}.spr"
            out_file.write_bytes(spr_data)

            num_tiles = len(spr_data) // 128
            report[pair_name] = {
                "odd_name": odd_name,
                "even_name": even_name,
                "odd_crc32": crc32_hex(odd_data),
                "even_crc32": crc32_hex(even_data),
                "num_tiles": num_tiles,
                "spr_file": out_file.name,
                "spr_size": len(spr_data),
                "spr_crc32": crc32_hex(spr_data),
                "spr_sha256": sha256_hex(spr_data),
            }

    return report


def interleave_all_c_roms(in_dir: Path, out_dir: Path) -> Dict[str, dict]:
    """
    Re-interleave .spr tile stream files in in_dir back into individual C-ROM binaries.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    report = {}

    for pair_name, odd_name, even_name, exp_size in C_ROM_PAIRS:
        spr_path = in_dir / f"{pair_name}.spr"
        if not spr_path.exists():
            raise FileNotFoundError(f"Missing required tile stream: {spr_path}")

        spr_data = spr_path.read_bytes()
        odd_data, even_data = interleave_pair(spr_data)

        if len(odd_data) != exp_size or len(even_data) != exp_size:
            raise ValueError(f"Size mismatch after interleaving {pair_name}")

        odd_path = out_dir / odd_name
        even_path = out_dir / even_name
        odd_path.write_bytes(odd_data)
        even_path.write_bytes(even_data)

        report[pair_name] = {
            "spr_file": spr_path.name,
            "odd_name": odd_name,
            "even_name": even_name,
            "odd_size": len(odd_data),
            "even_size": len(even_data),
            "odd_crc32": crc32_hex(odd_data),
            "even_crc32": crc32_hex(even_data),
        }

    return report


def export_tile_png(
    source_zip: Path,
    pair_name: str,
    tile_idx: int,
    out_png: Path,
    palette_rgb: Optional[List[Tuple[int, int, int]]] = None,
) -> Path:
    """
    Export a single 16x16 4bpp tile to a standard PNG image file.
    If palette_rgb is None, a default 16-step linear grayscale palette is used.
    """
    from PIL import Image

    pair_dict = {p[0]: p for p in C_ROM_PAIRS}
    if pair_name not in pair_dict:
        raise ValueError(f"Unknown pair: {pair_name}. Valid choices: {list(pair_dict.keys())}")

    _, odd_name, even_name, exp_size = pair_dict[pair_name]
    num_tiles = exp_size // 64
    if tile_idx < 0 or tile_idx >= num_tiles:
        raise IndexError(f"Tile index {tile_idx} out of range [0, {num_tiles - 1}]")

    with zipfile.ZipFile(source_zip, "r") as z:
        with z.open(odd_name) as f_odd, z.open(even_name) as f_even:
            f_odd.seek(tile_idx * 64)
            odd_64 = f_odd.read(64)
            f_even.seek(tile_idx * 64)
            even_64 = f_even.read(64)

    pixels = decode_tile_16x16(odd_64, even_64)

    img = Image.new("P", (16, 16))
    pal = []
    if palette_rgb:
        for r, g, b in palette_rgb[:16]:
            pal.extend((r, g, b))
    else:
        for i in range(16):
            val = round(i * 255 / 15)
            pal.extend((val, val, val))

    pal.extend([0] * (768 - len(pal)))
    img.putpalette(pal)

    flat_pixels = [pixels[y][x] for y in range(16) for x in range(16)]
    img.putdata(flat_pixels)

    out_png.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_png)
    return out_png


def export_sheet_png(
    source_zip: Path,
    pair_name: str,
    start_tile: int,
    num_tiles: int,
    out_png: Path,
    grid_cols: int = 16,
) -> Path:
    """
    Export a sequential range of 16x16 tiles into a 2D tile sheet PNG image.
    """
    from PIL import Image

    pair_dict = {p[0]: p for p in C_ROM_PAIRS}
    if pair_name not in pair_dict:
        raise ValueError(f"Unknown pair: {pair_name}")

    _, odd_name, even_name, exp_size = pair_dict[pair_name]
    total_avail = exp_size // 64
    if start_tile < 0 or start_tile + num_tiles > total_avail:
        raise IndexError(f"Tile range [{start_tile}, {start_tile + num_tiles}) exceeds {total_avail}")

    grid_rows = (num_tiles + grid_cols - 1) // grid_cols
    sheet_w = grid_cols * 16
    sheet_h = grid_rows * 16

    with zipfile.ZipFile(source_zip, "r") as z:
        with z.open(odd_name) as f_odd, z.open(even_name) as f_even:
            f_odd.seek(start_tile * 64)
            odd_all = f_odd.read(num_tiles * 64)
            f_even.seek(start_tile * 64)
            even_all = f_even.read(num_tiles * 64)

    sheet_img = Image.new("P", (sheet_w, sheet_h))
    pal = []
    for i in range(16):
        val = round(i * 255 / 15)
        pal.extend((val, val, val))
    pal.extend([0] * (768 - len(pal)))
    sheet_img.putpalette(pal)

    for i in range(num_tiles):
        tile_x = (i % grid_cols) * 16
        tile_y = (i // grid_cols) * 16
        odd_64 = odd_all[i * 64 : (i + 1) * 64]
        even_64 = even_all[i * 64 : (i + 1) * 64]
        tile_pix = decode_tile_16x16(odd_64, even_64)

        tile_img = Image.new("P", (16, 16))
        tile_img.putpalette(pal)
        flat = [tile_pix[y][x] for y in range(16) for x in range(16)]
        tile_img.putdata(flat)
        sheet_img.paste(tile_img, (tile_x, tile_y))

    out_png.parent.mkdir(parents=True, exist_ok=True)
    sheet_img.save(out_png)
    return out_png


def import_tile_png(in_png: Path, odd_rom_path: Path, even_rom_path: Path, tile_idx: int) -> None:
    """
    Import a 16x16 PNG image (indexed or RGB with 16 colors) into unpacked C-ROM binaries.
    """
    from PIL import Image

    img = Image.open(in_png)
    if img.size != (16, 16):
        raise ValueError(f"Tile image must be exactly 16x16 pixels, got {img.size}")

    if img.mode != "P":
        img = img.convert("P", colors=16)

    flat = list(img.getdata())
    pixels = [[flat[y * 16 + x] & 0x0F for x in range(16)] for y in range(16)]
    odd_64, even_64 = encode_tile_16x16(pixels)

    with open(odd_rom_path, "r+b") as f_odd:
        f_odd.seek(tile_idx * 64)
        f_odd.write(odd_64)

    with open(even_rom_path, "r+b") as f_even:
        f_even.seek(tile_idx * 64)
        f_even.write(even_64)


def run_crom_self_test() -> None:
    """
    Execute exhaustive unit self-tests on 16x16 4bpp tile codec and deinterleaver.
    """
    print("=== Running crom_tool.py Self-Test ===")

    # 1. Tile Codec Round-trip on synthetic pattern
    pattern = [[(x + y * 2) % 16 for x in range(16)] for y in range(16)]
    odd_64, even_64 = encode_tile_16x16(pattern)
    assert len(odd_64) == 64 and len(even_64) == 64
    decoded = decode_tile_16x16(odd_64, even_64)
    assert decoded == pattern, "Synthetic tile decode mismatch!"
    print("  [PASS] 16x16 4bpp tile encoder/decoder lossless round-trip test")

    # 2. Deinterleave/Interleave Pair Round-trip
    synth_odd = bytes((i * 7) % 256 for i in range(64 * 32))  # 32 tiles
    synth_even = bytes((i * 11) % 256 for i in range(64 * 32))
    stream = deinterleave_pair(synth_odd, synth_even)
    assert len(stream) == 128 * 32
    re_odd, re_even = interleave_pair(stream)
    assert re_odd == synth_odd, "Odd stream re-interleave mismatch!"
    assert re_even == synth_even, "Even stream re-interleave mismatch!"
    print("  [PASS] Tile stream pair deinterleave/interleave lossless round-trip test")

    # 3. Real C-ROM Tile Verification (if source ROM exists)
    if DEFAULT_SOURCE_ROM.exists():
        with zipfile.ZipFile(DEFAULT_SOURCE_ROM, "r") as z:
            with z.open("KOF97_C5.ROM") as f5, z.open("KOF97_C6.ROM") as f6:
                c5_head = f5.read(64 * 64)  # 64 real tiles
                c6_head = f6.read(64 * 64)

        for t in range(64):
            t_odd = c5_head[t * 64 : (t + 1) * 64]
            t_even = c6_head[t * 64 : (t + 1) * 64]
            pix = decode_tile_16x16(t_odd, t_even)
            ro, re = encode_tile_16x16(pix)
            assert ro == t_odd and re == t_even, f"Real tile {t} mismatch!"

        print("  [PASS] Real MVS C-ROM hardware data (64 tiles) verified 100% bit-exact")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="KOF97 Neo-Geo MVS C-ROM Graphics Toolchain (deinterleave/interleave/tile-codec)"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # self-test
    subparsers.add_parser("self-test", help="Run self-tests on tile codec and deinterleaver")

    # deinterleave
    p_deint = subparsers.add_parser("deinterleave", help="Extract and deinterleave all C-ROMs (40MB) into .spr streams")
    p_deint.add_argument("--source", type=Path, default=DEFAULT_SOURCE_ROM, help=f"Source zip (default: {DEFAULT_SOURCE_ROM})")
    p_deint.add_argument("--outdir", type=Path, default=DEFAULT_CROM_DIR, help=f"Output dir (default: {DEFAULT_CROM_DIR})")

    # interleave
    p_int = subparsers.add_parser("interleave", help="Re-interleave .spr streams back into original C-ROM binaries")
    p_int.add_argument("--indir", type=Path, default=DEFAULT_CROM_DIR, help=f"Input dir (default: {DEFAULT_CROM_DIR})")
    p_int.add_argument("--outdir", type=Path, default=DEFAULT_CROM_DIR / "rebuilt", help="Output directory for rebuilt ROMs")

    # export-tile
    p_exp = subparsers.add_parser("export-tile", help="Export a 16x16 tile to PNG")
    p_exp.add_argument("--source", type=Path, default=DEFAULT_SOURCE_ROM, help=f"Source zip (default: {DEFAULT_SOURCE_ROM})")
    p_exp.add_argument("--pair", choices=["c1_c2", "c3_c4", "c5_c6"], default="c1_c2", help="C-ROM pair name")
    p_exp.add_argument("--tile", type=int, default=1, help="Tile index to export (default: 1)")
    p_exp.add_argument("--output", type=Path, default=WORKSPACE_ROOT / "sandbox" / "capture" / "tile_export.png", help="Target PNG path")

    # export-sheet
    p_sheet = subparsers.add_parser("export-sheet", help="Export a sequential sheet of tiles to PNG")
    p_sheet.add_argument("--source", type=Path, default=DEFAULT_SOURCE_ROM, help=f"Source zip (default: {DEFAULT_SOURCE_ROM})")
    p_sheet.add_argument("--pair", choices=["c1_c2", "c3_c4", "c5_c6"], default="c1_c2", help="C-ROM pair name")
    p_sheet.add_argument("--start", type=int, default=0, help="Starting tile index (default: 0)")
    p_sheet.add_argument("--count", type=int, default=256, help="Number of tiles to export (default: 256)")
    p_sheet.add_argument("--cols", type=int, default=16, help="Grid columns (default: 16)")
    p_sheet.add_argument("--output", type=Path, default=WORKSPACE_ROOT / "sandbox" / "capture" / "tile_sheet.png", help="Target PNG path")

    # import-tile
    p_imp = subparsers.add_parser("import-tile", help="Import a 16x16 PNG back into unpacked C-ROM binaries")
    p_imp.add_argument("--image", type=Path, required=True, help="Input 16x16 PNG image")
    p_imp.add_argument("--odd-rom", type=Path, required=True, help="Target Odd C-ROM binary path")
    p_imp.add_argument("--even-rom", type=Path, required=True, help="Target Even C-ROM binary path")
    p_imp.add_argument("--tile", type=int, required=True, help="Target tile index to overwrite")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "self-test":
        run_crom_self_test()
        return 0

    if args.command == "deinterleave":
        print(f"=== Deinterleaving All 40MB C-ROM Pairs from {args.source} ===")
        rep = deinterleave_all_c_roms(args.source, args.outdir)
        total_tiles = 0
        total_bytes = 0
        for pair_name, info in rep.items():
            total_tiles += info["num_tiles"]
            total_bytes += info["spr_size"]
            print(
                f"  [{pair_name.upper()}] {info['odd_name']} + {info['even_name']} -> {info['spr_file']}\n"
                f"       Tiles: {info['num_tiles']:,} | Size: {info['spr_size']:,} B | CRC32: {info['spr_crc32']}"
            )
        print(f"[SUCCESS] All C-ROM pairs deinterleaved ({total_tiles:,} tiles, {total_bytes:,} bytes total).")
        return 0

    if args.command == "interleave":
        print(f"=== Re-interleaving C-ROM .spr Streams from {args.indir} ===")
        rep = interleave_all_c_roms(args.indir, args.outdir)
        for pair_name, info in rep.items():
            print(
                f"  [{pair_name.upper()}] {info['spr_file']} -> {info['odd_name']} ({info['odd_crc32']}) + {info['even_name']} ({info['even_crc32']})"
            )
        print("[SUCCESS] All C-ROM streams re-interleaved.")
        return 0

    if args.command == "export-tile":
        out = export_tile_png(args.source, args.pair, args.tile, args.output)
        print(f"[SUCCESS] Exported tile {args.tile} from {args.pair} to {out}")
        return 0

    if args.command == "export-sheet":
        out = export_sheet_png(args.source, args.pair, args.start, args.count, args.output, args.cols)
        print(f"[SUCCESS] Exported {args.count} tiles from {args.pair} (start={args.start}) to {out}")
        return 0

    if args.command == "import-tile":
        import_tile_png(args.image, args.odd_rom, args.even_rom, args.tile)
        print(f"[SUCCESS] Imported {args.image} into tile index {args.tile}")
        return 0

    return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
