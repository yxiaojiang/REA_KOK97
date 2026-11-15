# Plan.md — KOF97 Mod Studio 活跃计划

## 活跃任务

### 1. TASK-STUDIO-021：启动性能优化、全部随机扩展与独立游戏启动器
- **状态**：实施完成，onedir 构建成功；当前按用户要求准备提交并 push，随后交付 Argon 进行独立代码审查。
- **变更**：PyInstaller 改为 onedir；修复冻结态工作区根目录识别；“全部随机”同时分配皮肤和技能特效主题；抽取同步游戏启动流程，新增 dist/KOF97ModStudio/KOF97GameLauncher.exe。
- **验证边界**：构建成功；尚未实际运行独立启动器验证模拟器 ROM 启动，亦未完成启动时间对比。根目录原单文件 EXE 已恢复并保留。
- **交接文件**：CRDocs/IMPLEMENTATION.md 与 CRDocs/STATUS.md（独立审查待办）。

## 历史里程碑
- TASK-ROM-001 ~ TASK-ROM-005：68000 补丁与 C-ROM 工具链基线冻结。
- TASK-STUDIO-001 ~ TASK-STUDIO-019：Mod Studio、36 角色皮肤、VFX 功能完成并冻结。
- TASK-STUDIO-020 / DIR-003：目录迁移完成，Argon Round 3 APPROVED。
