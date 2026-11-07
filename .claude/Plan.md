# Plan.md — KOF97 逆向魔改工程活跃计划

## 活跃任务

1. **[TASK-ROM-004] 调色板皮肤魔改（已审查通过，APPROVED）**
   - 目标：在 `tools/rom_tool.py` 实现 Neo-Geo `LSPC2-A2` 16-bit 调色板编解码器；按 `[CR-003-P2-01]` 真实偏移修改 `build/unpacked/p2_be.bin` 中八神庵（`CharID=0x1B`）A 键调色板 `0x2DF7F0`（`0x07C0`，金发亮金裤、深黑风衣灰黑衬衣，含头像板 `0x2DF990..0x2DF9EF` 与兼容 `0x2DC9F0`）为黑金配色，打包至 `output/roms/kof97pls.zip` 并完成全流程实机验证。
   - 审查结论：`APPROVED`（Round 4，Argon 独立复核无误，`P0: 0, P1: 0, P2: 0`）。
   - 前置状态：`TASK-ROM-001`、`TASK-ROM-002`、`TASK-ROM-003`、`TASK-ROM-004` 全部取得 `APPROVED`。

2. **[TASK-ROM-005] C-ROM 图像瓦片重绘工具归档（实施完成，READY_FOR_REVIEW）**
   - 目标：沉淀 40MB C-ROM 4bpp 瓦片四象限解构与平面位图解交错/重交错工具链，提供单瓦片与图集 PNG 导出/反向回写功能，经全量 40MB 比对实现 100% bit-exact 复原。
   - 状态：实施完毕并完成自检，交接给审查员 Argon 进行 Round 5 审查。
