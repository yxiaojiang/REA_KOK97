# Plan.md — KOF97 逆向魔改工程活跃计划

## 活跃任务（已进入第 3 阶段实施）

1. **[TASK-ROM-003] P-ROM 静态数值与防御 Patch（当前活跃阶段，P1）**
   - 目标：在 `p1_be.bin` 中按真实指令首地址实施免疫破防（`0x01397E: 4E 71 4E 71`）、免疫眩晕（`0x0139A4: 4E 71 4E 71`）与受创减半（按 `[CR-002-P2-01]` 在 `0x01394A` 写入 `JSR ($0300).W` `4E B8 03 00`，在 `0x000300` 写入 `E2 40 D1 6C 01 3A 4E 75`），通过 `bswap16` 打包至 `output/roms/kof97pls.zip` 并完成 WinKawaks 1.48 实机对战验证。
   - 审查流：`CRDocs`（由 Antigravity 实施，Argon 独立审核）。
   - 前置状态：`TASK-ROM-001`（Round 1）与 `TASK-ROM-002`（Round 2）均已取得 `APPROVED`。

2. **[TASK-ROM-004] 调色板皮肤魔改（下一阶段，P1）**
   - 目标：按 Neo-Geo `LSPC2-A2` 16-bit 位布局修改 `232-p2p.bin` 偏移 `0x2DC9F0`（八神庵 A 键）为黑金配色并实机验证。
   - 前置依赖：`TASK-ROM-003` 取得 `APPROVED`。

3. **[TASK-ROM-005] C-ROM 图像瓦片重绘工具归档（延期阶段，P2）**
   - 目标：沉淀 40MB C-ROM 4bpp 瓦片解交错与重打包工具。
   - 前置依赖：`TASK-ROM-004`。
