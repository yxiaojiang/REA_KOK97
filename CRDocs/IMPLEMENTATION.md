# 实施与验证交接 (CRDocs — TASK-ROM-005 Round 5)

## 本轮实际修改

### 1. Neo-Geo MVS C-ROM 图像瓦片架构与平面位图编解码器
在 [`tools/crom_tool.py`](file:///c:/Users/mimovr/Desktop/TEmp\REA\Fighter97\tools\crom_tool.py) 中完整实现了 SNK Neo-Geo MVS 硬件规范的 16x16 4bpp 瓦片编解码与位平面解交错引擎：
- **硬件位平面（Bitplane）物理组织**：
  - 瓦片尺寸：16x16 像素，4-bit 色深（16 色），每个完整瓦片占用 128 字节；
  - 奇数编号 C-ROM（`C1`, `C3`, `C5`）存储 Bitplane 0 和 Bitplane 1（每个瓦片 64 字节）；
  - 偶数编号 C-ROM（`C2`, `C4`, `C6`）存储 Bitplane 2 和 Bitplane 3（每个瓦片 64 字节）；
- **四象限（Quadrant Blocks）排列顺序**：
  每个 16x16 瓦片在 128 字节内划分为 4 个 8x8 像素子块，物理存储次序如下：
  - 子块 0（Block 0）：右上象限（`X_offset = 8, Y_offset = 0`）；
  - 子块 1（Block 1）：右下象限（`X_offset = 8, Y_offset = 8`）；
  - 子块 2（Block 2）：左上象限（`X_offset = 0, Y_offset = 0`）；
  - 子块 3（Block 3）：左下象限（`X_offset = 0, Y_offset = 8`）。
- **像素位映射**：
  在每个 8x8 象限的行中，像素 `px`（0..7，0 为最左侧像素）对应字节的第 `7 - px` 位（MSB 为左，LSB 为右）。4 个平面合并形成 4-bit 颜色索引 `(bp3 << 3) | (bp2 << 2) | (bp1 << 1) | bp0`。
- **核心编解码函数**：
  - `decode_tile_16x16(odd_64: bytes, even_64: bytes) -> List[List[int]]`：将奇偶 C-ROM 各 64 字节解析为 16x16 颜色索引矩阵（0..15）；
  - `encode_tile_16x16(pixels: List[List[int]]) -> Tuple[bytes, bytes]`：将 16x16 颜色索引矩阵无损重编码为奇偶 C-ROM 各 64 字节平面数据。

### 2. 40MB 全量 C-ROM 瓦片对解交错（De-interleave）与重构（Interleave）流
针对 KOF97 全量 6 颗 C-ROM（共 41,943,040 字节，327,680 个瓦片）实现极速、100% 双向无损转换：
- **C-ROM 组成规格**：
  - `c1_c2` 对：`KOF97_C1.ROM` (8MB) + `KOF97_C2.ROM` (8MB) = 131,072 瓦片（生成 16MB `c1_c2.spr`）；
  - `c3_c4` 对：`KOF97_C3.ROM` (8MB) + `KOF97_C4.ROM` (8MB) = 131,072 瓦片（生成 16MB `c3_c4.spr`）；
  - `c5_c6` 对：`KOF97_C5.ROM` (4MB) + `KOF97_C6.ROM` (4MB) = 65,536 瓦片（生成 8MB `c5_c6.spr`）；
- **高性能流转**：
  采用 Python `memoryview` 切片内存直传，40MB 全量解交错与重新交错重构耗时均低于 0.3 秒；
- **全量重构 CRC32 严格比对**：
  将解交错生成的 `.spr` 文件重新交错输出至 `build/crom_unpacked/rebuilt/`，逐字节比对原版 ROM，全部 6 颗 ROM 达到 100% bit-exact 无损复原。

### 3. 单瓦片与图集导出/导入（PNG）
- `export_tile_png(...)`：提取指定 C-ROM 对指定瓦片并保存为 16x16 标准 PNG 格式（支持自定义 RGB 调色板或默认灰度阶梯）；
- `export_sheet_png(...)`：按指定列宽（默认 16 列）将连续瓦片序列拼接渲染为瓦片图集（Tile Sheet）PNG；
- `import_tile_png(...)`：将用户编辑后的 16x16 PNG 瓦片重新编译为 4bpp 平面格式，直接回写至解包后的奇偶 C-ROM 二进制文件指定瓦片位置。

### 4. 统一命令行工具链集成 [`tools/rom_tool.py`](file:///c:/Users/mimovr/Desktop/TEmp\REA\Fighter97\tools\rom_tool.py)
在保留原有 `unpack`, `pack`, `build-baseline`, `build-defense`, `build-palette`, `verify-palette` 等子命令的基础上，平滑扩展集成 C-ROM 子命令并注入全局自检：
- `rom_tool.py self-test`：自动串行执行 68000 `bswap16` 自检、`LSPC2-A2` 调色板自检、以及 `crom_tool` 瓦片编解码与实机硬件 64 瓦片无损自检；
- `rom_tool.py crom-self-test`：独立执行 C-ROM 瓦片与流测试；
- `rom_tool.py crom-deinterleave`：解交错生成 `.spr` 文件；
- `rom_tool.py crom-interleave`：重交错复原 C-ROM 二进制；
- `rom_tool.py crom-export-tile`：导出单瓦片 PNG；
- `rom_tool.py crom-export-sheet`：导出瓦片集 PNG；
- `rom_tool.py crom-import-tile`：导入瓦片 PNG；
- 脚本保持 100% 纯 ASCII（0 非 ASCII 字节）。

---

## 判定未修改

1. **宿主只读保护**：`C:\Program Files (x86)\KOF97\roms` 严格只读，无任何写操作。
2. **P-ROM 防御与调色板基线完全保持**：
   - `build/unpacked/p1_be.bin`（校验和 `0x21465F0A`，磁盘 CRC32 `0xFF227541`）中的全局免疫破防、免疫眩晕、受创减半 Code Cave 补丁保持 100% 不变；
   - `build/unpacked/p2_be.bin`（校验和 `0xF1187330`，磁盘 CRC32 `0xAF5CC95E`）中的八神庵黑金调色板保持 100% 不变；
   - [`output/roms/kof97pls.zip`](file:///c:/Users/mimovr/Desktop/TEmp\REA\Fighter97\output\roms\kof97pls.zip) 维持实机已验证状态。
3. **ROM 构件隔离**：40MB C-ROM 中间体 `.spr` 和复原 `.ROM` 存放于 `build/crom_unpacked/`，已由 [`.gitignore`](file:///c:/Users/mimovr/Desktop/TEmp\REA\Fighter97\.gitignore) 严密排除，避免仓库体积膨胀。

---

## 验证证据与实测记录

### 1. 单元与实机硬件自检输出
执行 `python tools/rom_tool.py self-test` 实测输出：

```text
=== Running rom_tool.py Self-Test ===
  [PASS] bswap16 header vector test (100000f3 -> 0010f300, EN-OEG -> NEO-GE)
  [PASS] bswap16 odd-length alignment guard test
  [PASS] bswap16 bidirectional lossless round-trip test
  [PASS] LSPC2-A2 16-bit color encoder/decoder lossless round-trip test
=== Running crom_tool.py Self-Test ===
  [PASS] 16x16 4bpp tile encoder/decoder lossless round-trip test
  [PASS] Tile stream pair deinterleave/interleave lossless round-trip test
  [PASS] Real MVS C-ROM hardware data (64 tiles) verified 100% bit-exact
```

### 2. 40MB 全量 C-ROM 解交错输出
执行 `python tools/rom_tool.py crom-deinterleave` 实测输出：

```text
=== Deinterleaving All 40MB C-ROM Pairs from C:\Program Files (x86)\KOF97\roms\kof97.ZIP ===
  [C1_C2] KOF97_C1.ROM + KOF97_C2.ROM -> c1_c2.spr
       Tiles: 131,072 | Size: 16,777,216 B | CRC32: 0xc576e44b
  [C3_C4] KOF97_C3.ROM + KOF97_C4.ROM -> c3_c4.spr
       Tiles: 131,072 | Size: 16,777,216 B | CRC32: 0x8ccacfff
  [C5_C6] KOF97_C5.ROM + KOF97_C6.ROM -> c5_c6.spr
       Tiles: 65,536 | Size: 8,388,608 B | CRC32: 0x32dfa9bf
[SUCCESS] All C-ROM pairs deinterleaved (327,680 tiles, 41,943,040 bytes total).
```

### 3. 40MB 全量 C-ROM 重构回写与 100% bit-exact 比对
执行 `python tools/rom_tool.py crom-interleave` 重构输出：

```text
=== Re-interleaving C-ROM .spr Streams from C:\Users\mimovr\Desktop\TEmp\REA\Fighter97\build\crom_unpacked ===
  [C1_C2] c1_c2.spr -> KOF97_C1.ROM (0x5f8bf0a1) + KOF97_C2.ROM (0xe4d45c81)
  [C3_C4] c3_c4.spr -> KOF97_C3.ROM (0x581d6618) + KOF97_C4.ROM (0x49bb1e68)
  [C5_C6] c5_c6.spr -> KOF97_C5.ROM (0x34fc4e51) + KOF97_C6.ROM (0x4ff4d47b)
[SUCCESS] All C-ROM streams re-interleaved.
```

与原版 `kof97.ZIP` 逐一 CRC 比对核验结果：
| C-ROM 成员文件 | 规格尺寸 (Bytes) | 原版 CRC32 | 重构生成的 CRC32 | 校验结论 |
| :--- | :--- | :--- | :--- | :--- |
| `KOF97_C1.ROM` | 8,388,608 | `0x5F8BF0A1` | `0x5F8BF0A1` | **100% 绝对一致** |
| `KOF97_C2.ROM` | 8,388,608 | `0xE4D45C81` | `0xE4D45C81` | **100% 绝对一致** |
| `KOF97_C3.ROM` | 8,388,608 | `0x581D6618` | `0x581D6618` | **100% 绝对一致** |
| `KOF97_C4.ROM` | 8,388,608 | `0x49BB1E68` | `0x49BB1E68` | **100% 绝对一致** |
| `KOF97_C5.ROM` | 4,194,304 | `0x34FC4E51` | `0x34FC4E51` | **100% 绝对一致** |
| `KOF97_C6.ROM` | 4,194,304 | `0x4FF4D47B` | `0x4FF4D47B` | **100% 绝对一致** |

### 4. 图像导出验证
- `tools/rom_tool.py crom-export-tile --pair c1_c2 --tile 10 --output sandbox/capture/tile_10.png` -> 成功生成 16x16 PNG；
- `tools/rom_tool.py crom-export-sheet --pair c5_c6 --start 0 --count 128 --output sandbox/capture/sheet_c5c6.png` -> 成功生成 256x128 瓦片图集 PNG。
