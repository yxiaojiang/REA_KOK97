# Plan.md — KOF97 逆向魔改工程活跃计划

## 活跃任务

### 1. `TASK-STUDIO-020` / `DIR-003`：`tools/` 全量代码向 `src/` 功能目录迁移与 `kof97_webview_app.py` 拆分解耦（**已完成，APPROVED**）
- **状态**：**已完成（`PlanDocs` `ADOPTED` / `CRDocs` Round 3 Implementation Review `APPROVED`，2026-11-13）**
- **决策与设计文档**：
  - [`PlanDocs/DECISIONS.md`](file:///d:/TEmp/REA/Fighter97/PlanDocs/DECISIONS.md) (`DIR-003`) 与讨论按日期归档 [`PlanDocs/2026-11-13_DIR-003_TASK-STUDIO-020.md`](file:///d:/TEmp/REA/Fighter97/PlanDocs/2026-11-13_DIR-003_TASK-STUDIO-020.md)
  - 完整实施蓝图、实测记录与终验结论：[`Plan.md`](file:///d:/TEmp/REA/Fighter97/Plan.md)（阶段八）、[`CRDocs/IMPLEMENTATION.md`](file:///d:/TEmp/REA/Fighter97/CRDocs/IMPLEMENTATION.md) 与 [`CRDocs/REVIEW.md`](file:///d:/TEmp/REA/Fighter97/CRDocs/REVIEW.md)
- **Hydrogen 执行摘要与 Argon Round 2 实施备忘（必读）**：
  1. **严格 5 层单向无环 DAG（迁入 `src/` 7 个功能目录：`core`, `palette`, `rom`, `emulator`, `studio`, `build`, `tests`）**：
     - `encode_lspc2`/`decode_lspc2` 迁入 `src/palette/color_utils.py`（`rom_tool.py` 重导出）；
     - `config_store.py` 通过 `skin_entry_factory` 回调解耦 `make_skin_entry`（`src/core/` 零外依赖）；
     - 共用受击 VFX 表（`VFX_RAM_*_OWNER`、`VFX_HIT_EFFECT_DARK_MASKS`、`VFX_SMOKE_SPLIT_SLOTS`、`VFX_COMMON_EFFECT_GROUPS`）与 `_recolor_hit_effect_slot` 移入 `src/palette/vfx_shader.py`（消除 `emulator <-> rom` 耦合）；
     - `p1_patcher` 与 `kawaks_live` 均通过可选 `log_fn` 回调记录日志，且 `kawaks_live` 接收 `bridge_api` 传入的 `(p1_data, p2_clean)`；
     - `sprite_compose.py` 改从 `src.palette.color_utils` 导入 `lspc2_to_hex`。
  2. **Argon Round 2 3 项非阻塞实施细节（编码时同步落实）**：
     - [`tools/sprite_compose.py:L148`](file:///d:/TEmp/REA/Fighter97/tools/sprite_compose.py#L148) 的 `labels = ["色槽 %d" ...]` 与 `L41–L49` `SLOT_GROUP_CN`、以及 `L2803` `"自定义皮肤"` 须全部转为 `\uXXXX` 转义，确保活跃 `src/` 代码及可执行测试 **0 非 ASCII 字节**（仅 `legacy_tk_gui.py` 与只读 `legacy_upgrades/*` 列为历史豁免）；
     - [`tools/crom_tool.py`](file:///d:/TEmp/REA/Fighter97/tools/crom_tool.py#L18-L25) 顶部添加 `parents[2]` `sys.path` 引导时须将原仅在 `L514` 的 `import sys` 提到顶部；`rom_tool.py` 统一收口为 `from src.rom import crom_tool`；
     - `pack_rom` 与 `p1_patcher` 精确边界：仅 `L3287–L3364`（纯 68k 战斗/破防/眩晕/无限气/伤害/隐藏解锁）抽入 `src/rom/p1_patcher.py` 的 `apply_combat_and_unlock_patches_to_p1(..., log_fn=None)`；`L3366–L3379` 读取 `KOF97_P2.ROM`、`bswap16` 并调用 `apply_hit_effect_vfx_to_p1` 留在 `bridge_api.py` 的 `pack_rom` 中。
  3. **路径 / Frozen / Monkeypatch / 硬编码**：全部 13 个可执行两级脚本顶部加 `parents[2]` `sys.path`；`paths.py` frozen 探测 `"src"`/`"sandbox"`；`rom_tool`/`crom_tool` 复用 `src.core.paths.PROJECT_ROOT`；`bridge_api`/`config_store` 经 `_paths.get_config_path()` 与 `_resolve_config_path()` 解析配置；`kof97_webview_app.py` 保留 38 项兼容门面重导出白名单；替换 `bridge_api:L3844`、`legacy_tk_gui:L28,L32,L1573`、`rom_tool:L27,L1642`、`dump_official_palettes:L9,L12-13,L105`、`verify_all:L92`、`build_exe.py` 及 4 个 `.bat`。
  4. **不可跳过的验收顺序**：快照基线 SHA-256 与预览 → 按 DAG 迁移拆分 → **先移除/隔离 `tools/`** → 零 `tools` 引用 / 纯 ASCII / 无导入环 / `legacy_tk_gui` & `rom_tool.py gui --help` + 全量回归测试 + `sprite_compose`/`get_idle_preview()` 烟雾测试 + `p1_be.bin`/`p2_be.bin` 100% 字节级一致比对 + 恢复 `mod_studio_config.json` 基线 → `BuildStudio.bat` 重编并在 `dist/` 与 `%TEMP%` 等非根目录实测启动 `KOF97ModStudio.exe` → 更新 `CRDocs/IMPLEMENTATION.md` 提交 Argon Round 3 Implementation Review。
- **下一步**：`TASK-STUDIO-020` 已完成终验并签批结项（`CRDocs/STATUS.md` 为 `APPROVED`）。后续如开启新特性或优化任务，按 `.claude/Rules.md` 与 `PlanDocs/` 流程发起新议题。

### 2. `TASK-STUDIO-019`：人物技能特效调色板（VFX Palette）逆向映射与 Mod Studio 改色集成（已完成，2026-11-13）
- **状态**：**已完成并全量验证**（`rom_tool.py self-test`、`test_vfx_palette_suite.py` 6/6、`test_full_roster_skins_suite.py` 全部通过；`KOF97ModStudio.exe` 已重编译）。

---

## 阶段里程碑归档（已收敛冻结，严禁回退）
- **TASK-ROM-001 ~ TASK-ROM-005**：68000 汇编逆向、属性锁死、黑金八神调色板、C-ROM 瓦片重构（Argon 审核 APPROVED）。
- **TASK-STUDIO-001 ~ TASK-STUDIO-018**：Mod Studio 工作台、隐藏人物全解锁、ACT 00 站立图实时拼装、全员 36 名角色 20 款皮肤 OKLCH 自然染色标准（`_paint_costume_natural` / `_natural_cloth_word` 已固化至 `ProjectMemory.md` 第 13 节，**严禁回退服装染色生成器与 20 款皮肤参数**）。
