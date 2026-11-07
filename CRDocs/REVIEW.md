# 审查结论与问题清单 (CRDocs — TASK-ROM-005 Round 5)

- **Task ID**：`TASK-ROM-005`
- **Target**：C-ROM 图像瓦片解交错与重构工具链工程化沉淀（40MB 全量双向无损校验、单瓦片/瓦片集导出与导入）
- **Reviewer**：Argon
- **Review Round**：Round 5
- **Decision**：**APPROVED**（`P0: 0`, `P1: 0`, `P2: 0`；全量 40MB C-ROM 达 100% bit-exact 复原）

---

## 审查结论

经独立核查 [`tools/crom_tool.py`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/tools/crom_tool.py)、[`tools/rom_tool.py`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/tools/rom_tool.py)、SNK Neo-Geo MVS 16x16 4bpp 瓦片四象限架构与位平面交错规范、40MB 全量 6 颗 C-ROM（327,680 个瓦片）双向重构无损比对、单瓦片/瓦片集 PNG 导出导入流及宿主目录只读隔离性，**`TASK-ROM-005`（阶段五：C-ROM 图像瓦片重绘工具归档与工具链沉淀）100% 满足 `DIR-001`、[`Rules.md`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/.claude/Rules.md) 与 [`Plan.md`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/Plan.md) 验收标准，予以正式通过（`APPROVED`）**。

至此，本项目从阶段一至阶段五（`TASK-ROM-001` 到 `TASK-ROM-005`）全部 5 项任务均以最高工程标准实现并取得独立审查通过。

---

## 独立核验清单与实测结果

### 1. 宿主目录安全与纯 ASCII 规范（100% 达标）
- **宿主目录只读保护**：独立比对 `C:\Program Files (x86)\KOF97\roms` 原始资产：
  - `kof97.ZIP`（29,286,731 B，MD5 `87e8718af8b5d452e6d32697c051c994`）
  - `kof97pls.zip`（1,438,722 B，MD5 `6f152d3ec8d2d5cb252a203e97603677`）
  - `neogeo.zip`（57,734 B，MD5 `6ab3817a33c5b75bb745ca1f9efb55d1`）
  确认时间戳与哈希完全无变动，未发生任何原地写入或文件污染。
- **纯 ASCII 源码规范**：
  - `tools/crom_tool.py`（19,726 字节，非 ASCII 字节数：`0`）
  - `tools/rom_tool.py`（64,324 字节，非 ASCII 字节数：`0`）
  - `sandbox/launch_sandbox.bat`（700 字节，非 ASCII 字节数：`0`）
  所有注释与代码 100% 纯 ASCII，消除了 Windows 环境下的编码兼容隐患。

### 2. Neo-Geo MVS 16x16 4bpp 图像瓦片硬件架构核验（100% 精确）
- **四象限（Quadrant Blocks）与平面排布规范**：
  SNK Neo-Geo MVS 硬件精灵系统将 16x16 像素瓦片划分为 4 个 8x8 子块，每个瓦片固定 128 字节：
  - Block 0：右上象限（`X=8, Y=0`），偏移行 0..7；
  - Block 1：右下象限（`X=8, Y=8`），偏移行 8..15；
  - Block 2：左上象限（`X=0, Y=0`），偏移行 0..7；
  - Block 3：左下象限（`X=0, Y=8`），偏移行 8..15。
- **位平面（Bitplane）拆分**：
  - 奇数编号 C-ROM（`C1`, `C3`, `C5`）存放 Bitplane 0 与 Bitplane 1（每瓦片 64 字节，每行 2 字节）；
  - 偶数编号 C-ROM（`C2`, `C4`, `C6`）存放 Bitplane 2 与 Bitplane 3（每瓦片 64 字节，每行 2 字节）；
  - 4-bit 颜色索引为 `(bp3 << 3) | (bp2 << 2) | (bp1 << 1) | bp0`。
- **单元自检验证**：独立运行 `python tools/rom_tool.py self-test`，覆盖 16x16 4bpp 瓦片往返编解码、模拟数据解交错往返、以及实机硬件 64 个真实 C-ROM 瓦片逐字节对比，测试 100% 通过。

### 3. 40MB 全量 C-ROM 解交错与重构 100% bit-exact 复原核验
独立编写验证脚本，将解交错并重新交错生成的 6 颗 C-ROM 文件与原生 `kof97.ZIP` 逐字节全量比对：

| C-ROM 镜像文件 | 规格尺寸 (Bytes) | 原版 CRC32 | 重构生成的 CRC32 | SHA-256 绝对一致 | 逐字节 Diff 结果 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `KOF97_C1.ROM` | 8,388,608 | `0x5F8BF0A1` | `0x5F8BF0A1` | **PASS (True)** | **0 字节差异 (bit-exact)** |
| `KOF97_C2.ROM` | 8,388,608 | `0xE4D45C81` | `0xE4D45C81` | **PASS (True)** | **0 字节差异 (bit-exact)** |
| `KOF97_C3.ROM` | 8,388,608 | `0x581D6618` | `0x581D6618` | **PASS (True)** | **0 字节差异 (bit-exact)** |
| `KOF97_C4.ROM` | 8,388,608 | `0x49BB1E68` | `0x49BB1E68` | **PASS (True)** | **0 字节差异 (bit-exact)** |
| `KOF97_C5.ROM` | 4,194,304 | `0x34FC4E51` | `0x34FC4E51` | **PASS (True)** | **0 字节差异 (bit-exact)** |
| `KOF97_C6.ROM` | 4,194,304 | `0x4FF4D47B` | `0x4FF4D47B` | **PASS (True)** | **0 字节差异 (bit-exact)** |

40MB 全量共计 **327,680 个瓦片、41,943,040 字节**，在经历解交错为 `.spr` 流并重新交错回写后，达到了 **100% bit-exact 完美复原**。

### 4. 图像导出与反向回写能力核验（100% 达标）
- 审查核验导出的 PNG 构件：
  - `sandbox/capture/tile_1.png` 与 `tile_10.png`（16x16 索引色 PNG，结构完好）；
  - `sandbox/capture/sheet_256.png`（256x256 瓦片集）与 `sheet_c5c6.png`（256x128 瓦片集，结构完好）。
- 独立编写临时沙盒测试脚本执行 `import_tile_png()`，将修改后的 16x16 PNG 像素回写至奇偶 ROM 并重新逆解，验证像素矩阵往返 100% 无损。

### 5. 前序防御 Patch 与调色板换肤零回归（100% 保持）
- 独立核验 `build/unpacked/` 与 `output/roms/kof97pls.zip`：
  - `232-p1p.bin`（1,048,576 B，大端 CRC32 `0x21465F0A`，磁盘 CRC32 `0xFF227541`）保持免破防、免眩晕与受创减半 Code Cave 补丁；
  - `232-p2p.bin`（4,194,304 B，大端 CRC32 `0xF1187330`，磁盘 CRC32 `0xAF5CC95E`）保持八神庵黑金配色与选人金发立绘；
  - `232-s1p.bin`（131,072 B，磁盘 CRC32 `0x8514ECF5`）零变动。
- 全套系统功能完整兼容，无任何回归问题。

---

## 问题清单 (P0 / P1 / P2)

本轮无新增 `P0`、`P1`、`P2` 问题（`P0: 0`, `P1: 0`, `P2: 0`）。
所有历史问题均已在各阶段关闭。
