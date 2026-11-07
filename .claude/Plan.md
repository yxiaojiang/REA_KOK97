# Plan.md — KOF97 逆向魔改工程活跃计划

## 活跃任务（已进入第 4 阶段审查）

1. **[TASK-ROM-004] 调色板皮肤魔改（已实施完成，待审核，P1）**
   - 目标：在 `tools/rom_tool.py` 实现 Neo-Geo `LSPC2-A2` 16-bit 调色板编解码器；按 `[CR-003-P2-01]` 真实索引修改 `build/unpacked/p2_be.bin` 中八神庵（`CharID=0x1B`）A 键调色板 **`0x2DF7F0`**（`0x07C0`，金发亮金裤、深黑风衣灰黑衬衣，含头像板 `0x2DF990..0x2DF9EF` 与兼容 `0x2DC9F0`）为专属黑金配色，打包至 `output/roms/kof97pls.zip` 并完成全流程实机验证。
   - 当前状态：`READY_FOR_REVIEW`（Round 4，等待 Argon 审核）。
   - 前置状态：`TASK-ROM-001`（Round 1）、`TASK-ROM-002`（Round 2）、`TASK-ROM-003`（Round 3）均已取得 `APPROVED`。

2. **[TASK-ROM-005] C-ROM 图像瓦片重绘工具归档（延期阶段，P2）**
   - 目标：沉淀 40MB C-ROM 4bpp 瓦片解交错与重打包工具。
   - 前置依赖：`TASK-ROM-004` 取得 `APPROVED`。
