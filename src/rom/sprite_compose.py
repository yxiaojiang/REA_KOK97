# -*- coding: utf-8 -*-
"""Compose a KOF97 idle / standing sprite from official C-ROM tiles and a 15-color palette.

Layout parse follows the official obj_draw jump table at 0x6022 (also implemented
in arcade-sprite-viewer/neo/neo.js kofgetRomFrame). Data is read in 68000 / big-endian
order from a word-swapped P2 ROM:

  byte 0: palette
  byte 1: draw func (0x0-0xA)
  byte 2: nx (columns)
  byte 3: ny (rows)
  then func-specific tile and occupancy data

Occupancy: one mask per column, MSB (bit 7, or bit 15 for word masks) is the top row.
Empty columns still occupy a 16-pixel X slot; tiles are not packed and not overlapped.
A graph's image-definition entry is 6 bytes: signed X, signed Y, and flags+call index.
Bit 0x2000 on the flags word means another 6-byte group follows and is overlaid.

Standing frames come from ACT 00 (pointer table at 0x200002), not image-def index 0.
Comments and names are English per project rules.
"""
from __future__ import annotations

import io
import struct
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Iterator

from src.palette.color_utils import decode_lspc2, lspc2_to_hex
from src.rom.crom_tool import decode_tile_16x16
from src.rom.rom_tool import bswap16

DEV = 0x100000
P1_PAL_BASE = 0x483E
P2_PAL_BASE = 0x2CFFF0
IMG_DEF_TABLE = 0x100002
C_CALL_TABLE = 0x150000
ACT_TABLE = 0x200002

SLOT_GROUP_CN = {
    "skin": "\u76ae\u80a4",
    "white_trim": "\u767d\u8fb9",
    "hair": "\u5934\u53d1",
    "primary": "\u8863\u670d",
    "dark_anchor": "\u6697\u90e8",
    "accent": "\u8f85\u8272",
    "contour": "\u52fe\u8fb9",
}

Sprite = Tuple[int, int, int, bool, bool]  # x, y, tile, hflip, vflip


def be16(buf: bytes, off: int) -> int:
    return struct.unpack_from(">H", buf, off)[0]


def be32(buf: bytes, off: int) -> int:
    return struct.unpack_from(">I", buf, off)[0]


def se16(buf: bytes, off: int) -> int:
    v = be16(buf, off)
    return v - 0x10000 if v >= 0x8000 else v


def hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    h = hex_code.lstrip("#")
    if len(h) != 6:
        return (255, 0, 255)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


class SpriteRom:
    """Cached official P and C ROM access."""

    def __init__(self, zip_path: Path):
        self.zip_path = Path(zip_path)
        self._p1: Optional[bytes] = None
        self._p2: Optional[bytes] = None
        self._cs: Optional[Tuple[bytes, ...]] = None

    def load(self) -> None:
        if self._p1 is not None:
            return
        with zipfile.ZipFile(self.zip_path) as z:
            self._p1 = bytes(bswap16(z.read("KOF97_P1.ROM")))
            self._p2 = bytes(bswap16(z.read("KOF97_P2.ROM")))
            self._cs = (
                z.read("KOF97_C1.ROM"),
                z.read("KOF97_C2.ROM"),
                z.read("KOF97_C3.ROM"),
                z.read("KOF97_C4.ROM"),
                z.read("KOF97_C5.ROM"),
                z.read("KOF97_C6.ROM"),
            )

    @property
    def p1(self) -> bytes:
        self.load()
        return self._p1  # type: ignore

    @property
    def p2(self) -> bytes:
        self.load()
        return self._p2  # type: ignore

    @property
    def cs(self) -> Tuple[bytes, ...]:
        self.load()
        return self._cs  # type: ignore

    def read_tile(self, tile: int) -> Optional[List[List[int]]]:
        c1, c2, c3, c4, c5, c6 = self.cs
        if tile < 0x20000:
            odd, even, local = c1, c2, tile
        elif tile < 0x40000:
            odd, even, local = c3, c4, tile - 0x20000
        else:
            odd, even, local = c5, c6, tile - 0x40000
        o = odd[local * 64 : (local + 1) * 64]
        e = even[local * 64 : (local + 1) * 64]
        if len(o) != 64 or len(e) != 64:
            return None
        return decode_tile_16x16(o, e)


def official_pal_id(p1: bytes, pal_idx: int, btn_idx: int = 0) -> int:
    off = P1_PAL_BASE + pal_idx * 8 + btn_idx * 2
    return be16(p1, off)


def official_colors(p1: bytes, p2: bytes, pal_idx: int, btn_idx: int = 0) -> List[str]:
    """Return the 15 gameplay colors (palette words 1..15) as #RRGGBB."""
    pal_id = official_pal_id(p1, pal_idx, btn_idx)
    addr = P2_PAL_BASE + pal_id * 32
    return [lspc2_to_hex(be16(p2, addr + i * 2)) for i in range(1, 16)]


def official_header_word(p1: bytes, p2: bytes, pal_idx: int, btn_idx: int = 0) -> int:
    pal_id = official_pal_id(p1, pal_idx, btn_idx)
    addr = P2_PAL_BASE + pal_id * 32
    return be16(p2, addr)


def slot_labels(schema: Dict[str, List[int]]) -> List[str]:
    """Chinese body-part labels for the 15 gameplay slots, from the character schema."""
    labels = ["\u8272\u69fd %d" % (i + 1) for i in range(15)]
    for group, idxs in schema.items():
        base = SLOT_GROUP_CN.get(group, group)
        if len(idxs) == 1:
            if 0 <= idxs[0] < 15:
                labels[idxs[0]] = base
        else:
            for n, idx in enumerate(idxs, start=1):
                if 0 <= idx < 15:
                    labels[idx] = "%s %d" % (base, n)
    return labels


def idle_graph_indices(p2: bytes, engine_cid: int, max_groups: int = 80) -> List[int]:
    """Graph indices of ACT 00 (standing loop), in playback order."""
    char_init = be32(p2, ACT_TABLE + engine_cid * 4)
    if char_init > 0x400000:
        char_init &= 0xFFFFFF
    if not (0 <= char_init < len(p2) - 4):
        return [0]
    act_base = be32(p2, char_init)
    if act_base > 0x400000:
        act_base &= 0xFFFFFF
    if not (0 <= act_base < len(p2) - 6):
        return [0]
    graphs: List[int] = []
    off = act_base
    for _ in range(max_groups):
        b0 = p2[off]
        if b0 >= 0x80:
            if b0 in (0xFE, 0xFF):
                break
            off += 6
            continue
        graphs.append(be16(p2, off + 2))
        off += 6
    return graphs or [0]


def _xy(i: int, j: int, nx: int, hflip: bool, vflip: bool) -> Tuple[int, int]:
    x = ((nx - i - 1) if hflip else i) << 4
    y = ((-j) if vflip else j) << 4
    return x, y


def parse_layout_sprites(
    p2: bytes,
    file_off: int,
    vflip: bool = False,
    hflip: bool = False,
) -> List[Sprite]:
    """Parse one C-call layout into sprites at 16-pixel column / row slots."""
    if file_off < 0 or file_off + 8 > len(p2):
        return []
    func = p2[file_off + 1]
    pos = file_off + 2
    sprites: List[Sprite] = []

    def get_u8() -> int:
        nonlocal pos
        if pos >= len(p2):
            return 0
        b = p2[pos]
        pos += 1
        return b

    def get_u16() -> int:
        nonlocal pos
        if pos + 1 >= len(p2):
            pos += 2
            return 0
        v = be16(p2, pos)
        pos += 2
        return v

    def get_u32() -> int:
        nonlocal pos
        if pos + 3 >= len(p2):
            pos += 4
            return 0
        v = be32(p2, pos)
        pos += 4
        return v

    if func not in (0x0, 0x1, 0x2, 0x3, 0x5, 0x6, 0x7, 0x8, 0x9, 0xA):
        return []

    nx = get_u8()
    ny = get_u8()
    if nx < 1 or nx > 32 or ny < 1 or ny > 32:
        return []

    byte_mask = func in (0x1, 0x6, 0x8, 0xA)
    bitwidth = 8 if byte_mask else 16

    def take_fill() -> int:
        return get_u8() if byte_mask else get_u16()

    if func in (0x0, 0x1):
        tile = get_u32()
        for i in range(nx):
            fill = take_fill()
            for j in range(ny):
                if fill & ((1 << (bitwidth - 1)) >> j):
                    x, y = _xy(i, j, nx, hflip, vflip)
                    sprites.append((x, y, tile, hflip, vflip))
                    tile += 1
        return sprites

    if func in (0x8, 0x7):
        _tmp = get_u8()
        flag = get_u8()
        tileadd = (flag & 0xF0) << 12
        tile_pos = pos + (nx if func == 0x8 else nx * 2)
        if func == 0x8 and (tile_pos & 1):
            tile_pos += 1
        for i in range(nx):
            fill = take_fill()
            for j in range(ny):
                if fill & ((1 << (bitwidth - 1)) >> j):
                    if tile_pos + 1 >= len(p2):
                        break
                    tile = be16(p2, tile_pos) + tileadd
                    tile_pos += 2
                    x, y = _xy(i, j, nx, hflip, vflip)
                    sprites.append((x, y, tile, hflip, vflip))
        return sprites

    if func in (0xA, 0x9):
        flag = get_u16()
        tileadd = ((flag & 0xF0) << 12) + (flag & 0xFF00)
        tile_pos = pos + (nx if func == 0xA else nx * 2)
        for i in range(nx):
            fill = take_fill()
            for j in range(ny):
                if fill & ((1 << (bitwidth - 1)) >> j):
                    if tile_pos >= len(p2):
                        break
                    tile = p2[tile_pos] + tileadd
                    tile_pos += 1
                    x, y = _xy(i, j, nx, hflip, vflip)
                    sprites.append((x, y, tile, hflip, vflip))
        return sprites

    if func in (0x6, 0x5):
        tile_pos = pos + (nx if func == 0x6 else nx * 2)
        if func == 0x6 and (tile_pos & 1):
            tile_pos += 1
        cnt = 0
        for i in range(nx):
            fill = take_fill()
            for j in range(ny):
                if fill & ((1 << (bitwidth - 1)) >> j):
                    if tile_pos + 2 >= len(p2):
                        break
                    if cnt & 1:
                        flag = p2[tile_pos]
                        tile = be16(p2, tile_pos + 1)
                        tile_pos += 3
                    else:
                        tile = be16(p2, tile_pos)
                        flag = p2[tile_pos + 2]
                        tile_pos += 3
                    cnt += 1
                    tile = tile + ((flag & 0xF0) << 12)
                    x, y = _xy(i, j, nx, hflip, vflip)
                    sprites.append((x, y, tile, hflip, vflip))
        return sprites

    # func 0x2 / 0x3: full rectangle, no occupancy mask
    tileadd = 0
    if func == 0x3:
        _tmp = get_u8()
        flag = get_u8()
        tileadd = (flag & 0xF0) << 12
    cnt = 0
    for i in range(nx):
        for j in range(ny):
            if func == 0x2:
                if pos + 2 >= len(p2):
                    break
                if cnt & 1:
                    flag = get_u8()
                    tile = get_u16()
                else:
                    tile = get_u16()
                    flag = get_u8()
                cnt += 1
                tileadd = (flag & 0xF0) << 12
            else:
                tile = get_u16()
            tile = tile + tileadd
            x, y = _xy(i, j, nx, hflip, vflip)
            sprites.append((x, y, tile, hflip, vflip))
    return sprites


def iter_graph_groups(p2: bytes, img_base: int, graph_idx: int) -> Iterator[Tuple[int, int, int, bool, bool]]:
    """Yield (x, y, call_idx, vflip, hflip) for a graph and any chained extra groups."""
    off = img_base + graph_idx * 6
    for _ in range(16):
        if off < 0 or off + 6 > len(p2):
            return
        x = se16(p2, off)
        y = se16(p2, off + 2)
        af = be16(p2, off + 4)
        yield x, y, af & 0x3FF, bool(af & 0x4000), bool(af & 0x8000)
        if not (af & 0x2000):
            return
        off += 6


def layout_file_offset(p2: bytes, c_base: int, call_idx: int) -> int:
    return be32(p2, c_base + call_idx * 4) - DEV


def collect_graph_sprites(p2: bytes, engine_cid: int, graph_idx: int) -> List[Sprite]:
    img_base = be32(p2, IMG_DEF_TABLE + engine_cid * 4) - DEV
    c_base = be32(p2, C_CALL_TABLE + engine_cid * 4) - DEV
    if img_base <= 0 or c_base <= 0 or img_base >= len(p2) or c_base >= len(p2):
        return []
    out: List[Sprite] = []
    for gx, gy, call_idx, vflip, hflip in iter_graph_groups(p2, img_base, graph_idx):
        file_off = layout_file_offset(p2, c_base, call_idx)
        if file_off < 0 or file_off >= len(p2):
            continue
        for x, y, tile, hf, vf in parse_layout_sprites(p2, file_off, vflip=vflip, hflip=hflip):
            out.append((x + gx, y + gy, tile, hf, vf))
    return out


def compose_sprites(rom: SpriteRom, pal_rgb: Sequence[Tuple[int, int, int]], sprites: Sequence[Sprite]):
    """Blit sprites onto a transparent RGBA image. pal_rgb[0] is unused (index 0 = transparent)."""
    from PIL import Image

    if not sprites:
        return Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    xs = [s[0] for s in sprites]
    ys = [s[1] for s in sprites]
    minx, miny = min(xs), min(ys)
    width = max(xs) + 16 - minx
    height = max(ys) + 16 - miny
    img = Image.new("RGBA", (max(1, width), max(1, height)), (0, 0, 0, 0))
    px = img.load()
    for x0, y0, tile, hflip, vflip in sprites:
        mat = rom.read_tile(tile)
        if not mat:
            continue
        for yy in range(16):
            src_y = 15 - yy if vflip else yy
            for xx in range(16):
                src_x = 15 - xx if hflip else xx
                idx = mat[src_y][src_x]
                if not idx:
                    continue
                rgb = pal_rgb[idx] if idx < len(pal_rgb) else (255, 0, 255)
                x, y = x0 - minx + xx, y0 - miny + yy
                if 0 <= x < img.width and 0 <= y < img.height:
                    px[x, y] = (*rgb, 255)
    return img


def trim_and_pad(img, pad: int = 2):
    from PIL import Image

    bbox = img.getbbox()
    if not bbox:
        return img
    cropped = img.crop(bbox)
    out = Image.new("RGBA", (cropped.width + pad * 2, cropped.height + pad * 2), (0, 0, 0, 0))
    out.paste(cropped, (pad, pad), cropped)
    return out


def palette_from_colors(colors15: Sequence[str], header_rgb: Tuple[int, int, int] = (16, 0, 0)) -> List[Tuple[int, int, int]]:
    """Build a 16-entry RGB list: index 0 is transparent in sprites, 1..15 are the gameplay slots."""
    pal = [header_rgb]
    for i in range(15):
        if i < len(colors15):
            pal.append(hex_to_rgb(colors15[i]))
        else:
            pal.append((255, 0, 255))
    return pal


def _header_rgb(header_word: Optional[int]) -> Tuple[int, int, int]:
    if header_word is None:
        return (16, 0, 0)
    r5, g5, b5, _d = decode_lspc2(header_word)
    return (r5 * 8 + r5 // 4, g5 * 8 + g5 // 4, b5 * 8 + b5 // 4)


def render_graph_frame(
    rom: SpriteRom,
    engine_cid: int,
    colors15: Sequence[str],
    graph_idx: int,
    scale: int = 5,
    header_word: Optional[int] = None,
    skip_sparse_at_most: int = 1,
    h8_bit0_top: bool = True,
):
    """Render one image-definition graph, including chained extra groups."""
    del skip_sparse_at_most, h8_bit0_top
    sprites = collect_graph_sprites(rom.p2, engine_cid, graph_idx)
    if not sprites:
        return None
    pal = palette_from_colors(colors15, _header_rgb(header_word))
    img = compose_sprites(rom, pal, sprites)
    img = trim_and_pad(img, pad=2)
    if scale > 1:
        img = img.resize((img.width * scale, img.height * scale), __import__("PIL").Image.NEAREST)
    return img


def render_idle_frame(
    rom: SpriteRom,
    engine_cid: int,
    colors15: Sequence[str],
    frame_i: int = 0,
    scale: int = 5,
    header_word: Optional[int] = None,
    skip_sparse_at_most: int = 1,
    h8_bit0_top: bool = True,
):
    """Render a standing-action frame. frame_i is an index into ACT 00 (0 = first idle graph)."""
    graphs = idle_graph_indices(rom.p2, engine_cid)
    if not graphs:
        return None
    if frame_i < 0 or frame_i >= len(graphs):
        graph_idx = graphs[0]
    else:
        graph_idx = graphs[frame_i]
    return render_graph_frame(
        rom, engine_cid, colors15, graph_idx,
        scale=scale, header_word=header_word,
    )


def render_idle_png(
    rom: SpriteRom,
    engine_cid: int,
    colors15: Sequence[str],
    frame_i: int = 0,
    scale: int = 5,
    header_word: Optional[int] = None,
) -> Optional[bytes]:
    img = render_idle_frame(rom, engine_cid, colors15, frame_i=frame_i, scale=scale, header_word=header_word)
    if img is None:
        return None
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
