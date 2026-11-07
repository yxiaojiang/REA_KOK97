# 当前代码与 Patch 审查状态

- **Task ID**：`TASK-ROM-005`
- **Target**：C-ROM 图像瓦片解交错与重构工具链工程化沉淀（40MB 全量双向无损校验、单瓦片/瓦片集导出与导入）
- **Round**：5
- **Status**：**READY_FOR_REVIEW**
- **Current owner**：Argon
- **Last updated at**：2026-11-07

## 下一步
`TASK-ROM-005` 实施完毕，请审查员 Argon 执行 Round 5 审查：
1. 验证 [`tools/crom_tool.py`](file:///c:/Users/mimovr/Desktop/TEmp\REA\Fighter97\tools\crom_tool.py) 与 [`tools/rom_tool.py`](file:///c:/Users/mimovr/Desktop/TEmp\REA\Fighter97\tools\rom_tool.py) 的 16x16 4bpp 瓦片编解码、象限解构与位平面解交错逻辑；
2. 验证 40MB 全量 C-ROM 解交错与重构是否达到 100% bit-exact（比对 6 颗 C-ROM CRC32）；
3. 验证无损瓦片/图集 PNG 导出与导入能力；
4. 验证宿主目录与 P1/P2 Patch 未发生回归或非预期改动。
审查记录请输出至 [`CRDocs/REVIEW.md`](file:///c:/Users/mimovr/Desktop/TEmp\REA\Fighter97\CRDocs\REVIEW.md)。
