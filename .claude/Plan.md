# Plan.md — KOF97 逆向魔改工程活跃计划

## 活跃任务（全五大阶段已全部审核通过，工程圆满收口）

1. **[TASK-ROM-004] 调色板皮肤魔改（已审查通过，APPROVED）**
   - 目标：八神庵（`CharID=0x1B`）A 键调色板 `0x2DF7F0`（`0x07C0`）及头像板 `0x2DF990..0x2DF9EF` 黑金定制配色，打包并经实机验证。
   - 审查结论：`APPROVED`（Round 4）。

2. **[TASK-ROM-005] C-ROM 图像瓦片重绘工具归档（已审查通过，APPROVED）**
   - 目标：沉淀 40MB C-ROM 4bpp 瓦片四象限解构与平面位图解交错/重交错工具链，提供单瓦片与图集 PNG 导出/反向回写功能，经全量 40MB 比对实现 100% bit-exact 复原。
   - 审查结论：`APPROVED`（Round 5，Argon 独立复核 6 颗 C-ROM 逐字节与 CRC32 达到 100% bit-exact，`P0: 0, P1: 0, P2: 0`）。
