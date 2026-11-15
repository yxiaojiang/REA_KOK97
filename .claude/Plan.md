# Plan.md — KOF97 Mod Studio 活跃计划

## 活跃任务

### 1. TASK-STUDIO-021 / 022：onedir 启动与完整便携包
- **状态**：便携 ZIP 已构建，实施交接 READY_FOR_REVIEW；待 Argon 独立审查。
- **产物**：dist/KOF97-Portable-20261115.zip，含 studio.exe、KOF97GameLauncher.exe、共享运行库、模拟器、原版 ROM/BIOS、当前配置生成的魔改 ROM、说明和校验报告。
- **验证**：项目内外冻结程序打包/预览通过；项目外 Studio 前端及配置恢复通过；模拟器 P1/P2 与包内 ROM 逐字节一致，运行时补丁生效；9 项 VFX 回归通过。
- **未验证**：截图捕获超时，完整画面和对战未验；干净 Windows 上的 WebView2/.NET 依赖未验。第三方再分发许可未建立。
- **下一步**：Argon 核对 CRDocs/IMPLEMENTATION.md；补全画面/对战及干净机器测试。未提交或 push 本轮变更。

## 历史里程碑
- TASK-ROM-001 ~ 005：68000 补丁与 C-ROM 工具链基线冻结。
- TASK-STUDIO-001 ~ 019：Mod Studio、36 角色皮肤、VFX 基线完成。
- TASK-STUDIO-020 / DIR-003：目录迁移完成，Argon Round 3 APPROVED。
