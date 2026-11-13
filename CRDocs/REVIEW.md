# 审查结论与问题清单 (CRDocs — TASK-STUDIO-020 Round 3: Implementation Review)

- **Task ID**：`TASK-STUDIO-020` (`DIR-003`)
- **Target**：`tools/` 全量代码向 `src/` 功能目录迁移与 `kof97_webview_app.py`（3,907 行）模块化拆分解耦及产物终验
- **Reviewer**：Argon
- **Review Round**：Round 3 (Implementation Review)
- **Decision**：**APPROVED**（Round 3 终验通过；`P0: 0`, `P1: 0`, `P2: 0`；Round 1 提出之 `5` 项问题及 Round 2 提出之 `3` 项非阻塞实施备忘均已落地并通过独立核验）

---

## Round 3 独立终验核查结果

依据 [`CRDocs/IMPLEMENTATION.md`](file:///d:/TEmp/REA/Fighter97/CRDocs/IMPLEMENTATION.md)、[`Plan.md`](file:///d:/TEmp/REA/Fighter97/Plan.md)（阶段八）与 [`PlanDocs/2026-11-13_DIR-003_TASK-STUDIO-020.md`](file:///d:/TEmp/REA/Fighter97/PlanDocs/2026-11-13_DIR-003_TASK-STUDIO-020.md)，Argon 已独立完成以下 6 个维度的源码审计与实测复核：

### 1. 工作区隔离与文件结构核查
- **旧 `tools/` 目录已彻底移除**：`tools_exists = False`，根目录仅保留 `src/` 及规范化产物/文档目录，5 个 `.bak*` 历史备份与 `__pycache__/` 未迁入 `src/`。
- **`src/` 目录结构完整**：共 40 个有效文件，分布于 `src/__init__.py` 与 7 个功能子包（`core/`, `palette/`, `rom/`, `emulator/`, `studio/`, `build/`, `tests/`，含只读归档 `tests/legacy_upgrades/`）。
- **原生 ROM 只读红线**：`C:\Program Files (x86)\KOF97\roms\kof97.ZIP` 大小 `29,286,731 B`（`mtime=946656000.0`），零写入触碰。

### 2. 静态门禁与 5 层单向 DAG 校验
- **0 `tools` 引用扫描**：对活跃 `src/` 代码及 `sandbox/` 执行正则与文本扫描，`TOOLS_REFS in active src/: []`、`TOOLS_REFS in sandbox/: []`。
- **0 非 ASCII 字节扫描**：除计划显式豁免的历史归档/前端/数据文件（[`src/studio/legacy_tk_gui.py`](file:///d:/TEmp/REA/Fighter97/src/studio/legacy_tk_gui.py)、[`src/studio/web/index.html`](file:///d:/TEmp/REA/Fighter97/src/studio/web/index.html)、[`src/tests/official_palettes.txt`](file:///d:/TEmp/REA/Fighter97/src/tests/official_palettes.txt) 与 `src/tests/legacy_upgrades/*`）外，活跃 `src/` 代码与可执行测试均为 **0 非 ASCII 字节**（`NON_ASCII = []`）。
- **严格 5 层单向 DAG（AST 实测）**：全量扫描 `src/` 下活跃 Python 模块，仅 [`src/rom/rom_tool.py`](file:///d:/TEmp/REA/Fighter97/src/rom/rom_tool.py#L1608-L1611) 在 `gui` 子命令分支存在计划允许的延迟导入 `from src.studio import legacy_tk_gui`，其余模块 100% 遵守 `core (L0) -> palette (L1) -> rom (L2) / emulator (L3) -> studio (L4) -> build/tests (L5)` 单向依赖。
- **二级脚本引导与 38 项兼容门面**：全部 13 个可执行二级脚本顶部均在 `src.*` 导入前插入 `Path(__file__).resolve().parents[2]`；[`src/studio/kof97_webview_app.py`](file:///d:/TEmp/REA/Fighter97/src/studio/kof97_webview_app.py#L65-L104) `__all__` 精确导出 38 项兼容白名单（`missing_in_app: []`）。

### 3. Round 2 实施期 3 项非阻塞备忘落地核验
1. **[`src/rom/sprite_compose.py`](file:///d:/TEmp/REA/Fighter97/src/rom/sprite_compose.py#L30-L158)**：第 30 行已改导 `from src.palette.color_utils import decode_lspc2, lspc2_to_hex`；第 41–49 行 `SLOT_GROUP_CN` 与第 148 行 `labels = ["\u8272\u69fd %d" % (i + 1) for i in range(15)]` 均已转义为 `\uXXXX`。
2. **[`src/rom/crom_tool.py`](file:///d:/TEmp/REA/Fighter97/src/rom/crom_tool.py#L21-L30) 与 [`src/rom/rom_tool.py`](file:///d:/TEmp/REA/Fighter97/src/rom/rom_tool.py#L26-L32)**：`crom_tool.py` 顶部导入区已补齐 `import sys`、`parents[2]` 引导及 `from src.core.paths import PROJECT_ROOT as WORKSPACE_ROOT`；`rom_tool.py` 已统一收口为 `from src.rom import crom_tool`。
3. **`pack_rom` 与 `p1_patcher` 边界**：[`src/rom/p1_patcher.py`](file:///d:/TEmp/REA/Fighter97/src/rom/p1_patcher.py#L430-L529) 的 `apply_combat_and_unlock_patches_to_p1(..., log_fn=None)` 仅负责 68000 战斗/防御/解锁补丁且通过 `log_fn` 回传日志；`KOF97_P2.ROM` 读取与 `apply_hit_effect_vfx_to_p1` 编排保留在 [`src/studio/bridge_api.py`](file:///d:/TEmp/REA/Fighter97/src/studio/bridge_api.py#L642-L666) `pack_rom` 中，`p1_patcher.py` 保持零 `zipfile`/`rom_tool` 依赖。

### 4. 功能与回归测试集独立复跑结果
Argon 在当前工作区独立执行以下全部命令并均以 `exit 0` 通过：
- `python src\rom\rom_tool.py self-test`：**PASS**（`bswap16` / `LSPC2-A2` 4 项自检全过）
- `python src\rom\crom_tool.py self-test`：**PASS**（16x16 瓦片 / C-ROM 交错 3 项自检全过）
- `python src\rom\rom_tool.py gui --help`：**PASS**（安全退出且未误弹 GUI）
- `python src\tests\test_highlight_luma.py`：**PASS**（`ALL HIGHLIGHT LUMA CHECKS PASSED`）
- `python src\tests\test_vfx_palette_suite.py`：**PASS**（6/6 unittest 用例通过）
- `python src\tests\verify_anti_blowout_and_clarity.py`：**PASS**（Athena / Kyo / 36x20 全员清晰度通过）
- `python src\tests\test_upgrade_suite.py`：**PASS**（21 主题、4 键立绘同步、`get_emulator_status()` 通过）

### 5. 基线文件与 `get_idle_preview()` 100% 字节级一致复核
- **`mod_studio_config.json`**（`21,370 B`）：SHA-256 `f7c9aff79db2482abae841746b1d3499a38aef2cf011b8ff44b6cc38ca66fe25`（已恢复基线状态）
- **`build/unpacked/p1_be.bin`**（`1,048,576 B`）：SHA-256 `1eb26542d04594e4d5895e72c0e3ce281979598b4e3d6cb54c985ab63260bd6e`（与报告基线 100% 一致）
- **`build/unpacked/p2_be.bin`**（`4,194,304 B`）：SHA-256 `f92e414c24d7e1e1ce06530aa72cfe0e3232faebf756d0bfbe55a1c8acaceff1`（与报告基线 100% 一致）
- **`output/roms/kof97pls.zip`**（`1,434,197 B`）：SHA-256 `c460f17df878b5051e4e83a0304e4ecef53aff2e9a314bcb0e2eda992ef2ed40`
- **6 名典型角色 `get_idle_preview()` 实测 SHA-256（`png_base64` 100% 一致）**：
  - `0x00` (`kyo`): `51912a17eae140905581fc22d6c3ea24f0b4c34f52d5cb8d2a674bb2c2be6d6a`, `labels[:3]=['白边', '皮肤 1', '皮肤 2']`
  - `0x1B` (`iori`): `d3d284e20f76b741538590e62c8b1e6305525abd5ee74666e0446860984e7fee`, `labels[:3]=['皮肤 1', '皮肤 2', '皮肤 3']`
  - `0x0A` (`leona`): `69d070217997e0496dd6821e7e781957c62e2bbe7a875770e56390d185a7c64c`, `labels[:3]=['白边', '皮肤 1', '皮肤 2']`
  - `0x10` (`mai`): `5ca1b9dd12ea26bc2d52a99e5b9a9834ac618043c239722127f2d921a5d3930d`, `labels[:3]=['皮肤 1', '皮肤 2', '皮肤 3']`
  - `0x0F` (`chizuru`): `59378f90090463e00f57d9689d39592e897000ac663f280c89d53f21186c7d01`, `labels[:3]=['皮肤 1', '皮肤 2', '皮肤 3']`
  - `0x1E` (`orochi`): `6f66d102f7813a5089588102682297dba65ea307b6656ac8f60b859343352af6`, `labels[:3]=['皮肤 1', '皮肤 2', '皮肤 3']`

### 6. 独立可执行产物与跨目录配置核查
- [`dist/KOF97ModStudio.exe`](file:///d:/TEmp/REA/Fighter97/dist/KOF97ModStudio.exe) 与 [`KOF97ModStudio.exe`](file:///d:/TEmp/REA/Fighter97/KOF97ModStudio.exe) 大小均为 `26,616,214 B`，SHA-256 均为 `a6062785d4865dd40edd03eb9f5afc8c6eaea6d9426f3a1e04b0cc5cb8e9b4e7`。
- [`src/build/build_exe.py`](file:///d:/TEmp/REA/Fighter97/src/build/build_exe.py#L44-L74) 已包含 `--paths={PROJECT_ROOT}`、`--add-data={html_asset};src/studio/web` 与全量 `src.*` `--hidden-import`；[`src/core/paths.py`](file:///d:/TEmp/REA/Fighter97/src/core/paths.py#L8-L48) 已修复 `sys.frozen` 下 `"src"`/`"sandbox"` 探测及 `resolve_web_index_html()` 路径解析；4 个 `.bat` 均使用 `for %%I in ("%~dp0..\..")`。

---

## 问题清单总表

- **Round 3 新增问题**：`P0: 0`, `P1: 0`, `P2: 0`。
- **历史问题状态**：
  - `[CR-020-P0-01]`：**RESOLVED**（Round 2 设计解决 + Round 3 实测确认）
  - `[CR-020-P1-01]`：**RESOLVED**（Round 2 设计解决 + Round 3 AST 校验确认）
  - `[CR-020-P1-02]`：**RESOLVED**（Round 2 设计解决 + Round 3 38 项门面与配置注入确认）
  - `[CR-020-P1-03]`：**RESOLVED**（Round 2 设计解决 + Round 3 移除 `tools/` 后全量门禁与字节一致性确认）
  - `[CR-020-P2-01]`：**RESOLVED**（Round 2 设计解决 + Round 3 0 非 ASCII 扫描与基线恢复确认）

## 终验签批
- **Argon 结论**：**APPROVED**。`TASK-STUDIO-020` (`DIR-003`) 准予结项归档。
