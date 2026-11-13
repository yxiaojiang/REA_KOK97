# 实施与验证交接 (CRDocs — TASK-STUDIO-020 Round 3: 迁移拆解完结与终验交接)

> **本轮性质说明**：依据 [`Plan.md`](file:///d:/TEmp/REA/Fighter97/Plan.md)（阶段八）、[`PlanDocs/2026-11-13_DIR-003_TASK-STUDIO-020.md`](file:///d:/TEmp/REA/Fighter97/PlanDocs/2026-11-13_DIR-003_TASK-STUDIO-020.md) 与 Round 2 已 `APPROVED` 的设计方案，已完成 `tools/` → `src/` 全量迁移、[`kof97_webview_app.py`](file:///d:/TEmp/REA/Fighter97/src/studio/kof97_webview_app.py) 分层拆解、工作区 `tools/` 隔离清理、全量静态/回归/字节级基线一致性门禁实测，以及 `KOF97ModStudio.exe` 重编与跨目录启动实测。现交接 **Argon** 执行 Round 3 Implementation Review。

---

## 本轮实际交付与模块清单 (`src/` 共 40 个活跃文件 / 7 个功能子包)

### 1. 严格 5 层单向依赖 DAG 与各层交付物

| 层级 | 目录 | 文件与核心职责 |
| :--- | :--- | :--- |
| **Layer 0** | `src/core/` | [`__init__.py`](file:///d:/TEmp/REA/Fighter97/src/core/__init__.py) (3 L)、[`paths.py`](file:///d:/TEmp/REA/Fighter97/src/core/paths.py) (49 L: `PROJECT_ROOT` / `BUNDLE_DIR` / `EXE_DIR` / `get_config_path` / `resolve_web_index_html`)、[`roster.py`](file:///d:/TEmp/REA/Fighter97/src/core/roster.py) (112 L: 36 角色花名册与 `CHARACTER_PALETTE_SCHEMA`)、[`presets.py`](file:///d:/TEmp/REA/Fighter97/src/core/presets.py) (795 L: `PRESET_THEMES` / `THEME_RAMPS` / `DAMAGE_MODES` / `VFX_PRESETS`)、[`config_store.py`](file:///d:/TEmp/REA/Fighter97/src/core/config_store.py) (151 L: `load_studio_config(..., skin_entry_factory=None)` 与 `save_studio_config`) |
| **Layer 1** | `src/palette/` | [`__init__.py`](file:///d:/TEmp/REA/Fighter97/src/palette/__init__.py) (3 L)、[`color_utils.py`](file:///d:/TEmp/REA/Fighter97/src/palette/color_utils.py) (390 L: 托管 `encode_lspc2` / `decode_lspc2` 与 HSV/OKLCH 编码)、[`costume_painter.py`](file:///d:/TEmp/REA/Fighter97/src/palette/costume_painter.py) (418 L: 冻结 `DIR-002` `_paint_costume_natural` / `generate_harmonious_character_palette`)、[`portrait_burst.py`](file:///d:/TEmp/REA/Fighter97/src/palette/portrait_burst.py) (172 L: `generate_burst_character_palette` / `sync_character_portraits`)、[`vfx_shader.py`](file:///d:/TEmp/REA/Fighter97/src/palette/vfx_shader.py) (353 L: `TASK-STUDIO-019` `0x004956` 查表与 `VFX_COMMON_EFFECT_GROUPS` / `_recolor_hit_effect_slot`) |
| **Layer 2** | `src/rom/` | [`__init__.py`](file:///d:/TEmp/REA/Fighter97/src/rom/__init__.py) (3 L)、[`crom_tool.py`](file:///d:/TEmp/REA/Fighter97/src/rom/crom_tool.py) (520 L: 顶部补全 `import sys` + `parents[2]` 引导与 `WORKSPACE_ROOT`)、[`rom_tool.py`](file:///d:/TEmp/REA/Fighter97/src/rom/rom_tool.py) (1,617 L: 重导出 `encode_lspc2`/`decode_lspc2`，`gui` 子命令延迟导入 `src.studio.legacy_tk_gui`)、[`sprite_compose.py`](file:///d:/TEmp/REA/Fighter97/src/rom/sprite_compose.py) (500 L: `SLOT_GROUP_CN` 与第 148 行 `"色槽 %d"` 转 `\uXXXX`)、[`p1_patcher.py`](file:///d:/TEmp/REA/Fighter97/src/rom/p1_patcher.py) (529 L: `apply_combat_and_unlock_patches_to_p1(..., log_fn=None)` + `0x0F0000` 68k Code Cave) |
| **Layer 3** | `src/emulator/` | [`__init__.py`](file:///d:/TEmp/REA/Fighter97/src/emulator/__init__.py) (1 L)、[`kawaks_live.py`](file:///d:/TEmp/REA/Fighter97/src/emulator/kawaks_live.py) (314 L: 仅依赖 Layer 0/1，`find_kawaks_pid` 与 `inject_live_palettes_to_kawaks(..., log_fn=None)`) |
| **Layer 4** | `src/studio/` | [`__init__.py`](file:///d:/TEmp/REA/Fighter97/src/studio/__init__.py) (1 L)、[`bridge_api.py`](file:///d:/TEmp/REA/Fighter97/src/studio/bridge_api.py) (922 L: 保留 25 个公开 RPC 方法与 `_` 私有字段，实现 `KOF97BridgeApi(config_path=None)` 与 `_resolve_config_path()`)、[`kof97_webview_app.py`](file:///d:/TEmp/REA/Fighter97/src/studio/kof97_webview_app.py) (127 L: `main()` + 精确 38 项兼容重导出白名单)、[`legacy_tk_gui.py`](file:///d:/TEmp/REA/Fighter97/src/studio/legacy_tk_gui.py) (1,599 L: 更新至 `src.rom.rom_tool`)、[`web/index.html`](file:///d:/TEmp/REA/Fighter97/src/studio/web/index.html) (2,443 L / 82,895 B 原封未改) |
| **Layer 5 (Build)** | `src/build/` | [`build_exe.py`](file:///d:/TEmp/REA/Fighter97/src/build/build_exe.py) (103 L)、[`BuildStudio.bat`](file:///d:/TEmp/REA/Fighter97/src/build/BuildStudio.bat) (25 L)、[`launch_mod_studio.bat`](file:///d:/TEmp/REA/Fighter97/src/build/launch_mod_studio.bat) (19 L)、[`launch_sandbox.bat`](file:///d:/TEmp/REA/Fighter97/src/build/launch_sandbox.bat) (23 L)、[`launch_gui.bat`](file:///d:/TEmp/REA/Fighter97/src/build/launch_gui.bat) (12 L) |
| **Layer 5 (Tests)** | `src/tests/` | 8 个可执行脚本：[`test_vfx_palette_suite.py`](file:///d:/TEmp/REA/Fighter97/src/tests/test_vfx_palette_suite.py)、[`test_full_roster_skins_suite.py`](file:///d:/TEmp/REA/Fighter97/src/tests/test_full_roster_skins_suite.py)、[`test_highlight_luma.py`](file:///d:/TEmp/REA/Fighter97/src/tests/test_highlight_luma.py)、[`test_upgrade_suite.py`](file:///d:/TEmp/REA/Fighter97/src/tests/test_upgrade_suite.py)、[`verify_anti_blowout_and_clarity.py`](file:///d:/TEmp/REA/Fighter97/src/tests/verify_anti_blowout_and_clarity.py)、[`verify_all.py`](file:///d:/TEmp/REA/Fighter97/src/tests/verify_all.py)、[`verify_e2e_live_and_win.py`](file:///d:/TEmp/REA/Fighter97/src/tests/verify_e2e_live_and_win.py)、[`dump_official_palettes.py`](file:///d:/TEmp/REA/Fighter97/src/tests/dump_official_palettes.py)；产物 [`official_palettes.txt`](file:///d:/TEmp/REA/Fighter97/src/tests/official_palettes.txt)；只读历史归档 [`legacy_upgrades/`](file:///d:/TEmp/REA/Fighter97/src/tests/legacy_upgrades)（3 个脚本） |
| **根目录包与产物** | `/` | [`src/__init__.py`](file:///d:/TEmp/REA/Fighter97/src/__init__.py) (3 L)、[`dist/KOF97ModStudio.exe`](file:///d:/TEmp/REA/Fighter97/dist/KOF97ModStudio.exe) 与 [`KOF97ModStudio.exe`](file:///d:/TEmp/REA/Fighter97/KOF97ModStudio.exe) (26,616,214 B, SHA-256 `a6062785d4865dd40edd03eb9f5afc8c6eaea6d9426f3a1e04b0cc5cb8e9b4e7`) |

### 2. 工作区隔离与基线冻结遵守情况
1. **旧 `tools/` 目录已从工作区彻底移除**：`tools_exists = False`（已移至工作区外部临时备份目录，5 个 `.bak*` 与 `__pycache__/` 未迁入 `src/`）。
2. **宿主只读保护与冻结算法保真**：`C:\Program Files (x86)\KOF97\roms` 零写入；`DIR-002` 着色算法、`TASK-STUDIO-019` `0x0F0000` Code Cave、25 个 RPC 接口与 `web/index.html` 均未改变逻辑；`mod_studio_config.json` 已恢复为实施前完全一致配置（SHA-256 `f7c9aff79db2482abae841746b1d3499a38aef2cf011b8ff44b6cc38ca66fe25`）。
3. **Round 2 审查 3 项备忘均已落地**：
   - `src/rom/sprite_compose.py` 第 41–49 行 `SLOT_GROUP_CN` 与第 148 行 `"色槽 %d"` 均转义为 `\uXXXX`。
   - `src/rom/crom_tool.py` 顶部补全 `import sys` + `parents[2]` 引导；`src/rom/rom_tool.py` 收口为 `from src.rom import crom_tool`。
   - `apply_combat_and_unlock_patches_to_p1` 仅覆盖 `L3287–L3364`，`KOF97_P2.ROM` 读取与 `apply_hit_effect_vfx_to_p1` 调用保留在 `src/studio/bridge_api.py:pack_rom`。

---

## 全量验证证据（全部在移除 `tools/` 后实测完成）

### 1. 静态门禁与入口导入（`tools_exists == False`）
- **0 `tools` 引用扫描**（AST + 正则 `tools[/\\.]|\bfrom\s+tools\b|\bimport\s+tools\b`）：`TOOLS_REF_ERRORS: []`。
- **0 非 ASCII 字节扫描**（覆盖 `src/{core,palette,rom,emulator,build}/`、`src/studio/{__init__,bridge_api,kof97_webview_app}.py` 与 8 个可执行 `src/tests/*.py`）：`NON_ASCII_ERRORS: []`。
- **5 层 DAG 与循环依赖检查**（共 31 个 Python 模块，除 `rom_tool.py:main()` 中 `gui` CLI 延迟导入外无跨层上行引用）：`DAG_ERRORS: []`。
- **兼容门面 38 项白名单校验**：`FACADE_EXPECTED: 38 MISSING: [] ALL_DIFF: []`。
- **CLI 与 Tk GUI 导入检查**：
  - `python -c "import src.studio.legacy_tk_gui"` → `LEGACY_TK_GUI_IMPORT_OK`
  - `python src\rom\rom_tool.py gui --help` → exit 0
  - `python src\rom\crom_tool.py --help` → exit 0

### 2. 功能与回归测试集
| 命令 | 实测结果 | 备注 |
| :--- | :--- | :--- |
| `python src\rom\rom_tool.py self-test` | **PASS** (exit 0) | `bswap16` / `LSPC2-A2` 4 项自检全过 |
| `python src\rom\crom_tool.py self-test` | **PASS** (exit 0) | 16x16 瓦片 / C-ROM 交错 3 项自检全过 |
| `python src\tests\test_highlight_luma.py` | **PASS** (exit 0) | `ALL HIGHLIGHT LUMA CHECKS PASSED` |
| `python src\tests\test_vfx_palette_suite.py` | **PASS** (exit 0) | 6/6 unittest 用例全过（0x004956、Capstone M68k、64KB 容纳性、classic 无损还原） |
| `python src\tests\test_full_roster_skins_suite.py` | **PASS** (exit 0) | 预先执行 `python src\rom\rom_tool.py unpack` 使 `build/unpacked/p2_be.bin` 为干净基线；全部 36 角色 x 20 主题 (720 组合) 与 `pack_rom` 全过（注：该套件同原版一样预期 `build/unpacked/p2_be.bin` 为解包态，实测后已按规则恢复真实配置与基线打包） |
| `python src\tests\verify_anti_blowout_and_clarity.py` | **PASS** (exit 0) | Athena / Kyo / 36x20 全员清晰度全过 |
| `python src\tests\test_upgrade_suite.py` | **PASS** (exit 0) | 21 主题、4 键立绘同步、`get_emulator_status()` 全过 |
| `python src\tests\dump_official_palettes.py` | **PASS** (exit 0) | 成功生成 `src/tests/official_palettes.txt` |
| `verify_all.py` / `verify_e2e_live_and_win.py` | **未运行实机窗体对抗** | 两者为启动真实 `WinKawaks.exe` 注入 DirectInput 的交互脚本；已完成 `tools` 移除与 `src.*` 路径迁移，静态门禁全过 |

### 3. `sprite_compose` 冒烟与 100% 字节级基线一致比对
在恢复备份的 `mod_studio_config.json`（SHA-256 `f7c9aff79db2482abae841746b1d3499a38aef2cf011b8ff44b6cc38ca66fe25`）后，通过 `src.studio.kof97_webview_app.KOF97BridgeApi` 重新打包并抽样预览：
- **`build/unpacked/p1_be.bin`**：SHA-256 `1eb26542d04594e4d5895e72c0e3ce281979598b4e3d6cb54c985ab63260bd6e` → **100% 字节级一致 (`BYTE_EXACT=True`)**
- **`build/unpacked/p2_be.bin`**：SHA-256 `f92e414c24d7e1e1ce06530aa72cfe0e3232faebf756d0bfbe55a1c8acaceff1` → **100% 字节级一致 (`BYTE_EXACT=True`)**
- **`output/roms/kof97pls.zip`**：zip 包内全部 3 个 ROM 成员（含 `232-p1p.bin` / `232-p2p.bin` / `232-s1.s1`）与实施前基线 zip **100% 字节级一致**
- **典型角色 `get_idle_preview()` SHA-256（6/6 100% 一致）**：
  - `kyo (0x00)`: `51912a17eae140905581fc22d6c3ea24f0b4c34f52d5cb8d2a674bb2c2be6d6a`, `labels=['白边', '皮肤 1', '皮肤 2']`
  - `iori (0x1B)`: `d3d284e20f76b741538590e62c8b1e6305525abd5ee74666e0446860984e7fee`, `labels=['皮肤 1', '皮肤 2', '皮肤 3']`
  - `leona (0x0A)`: `69d070217997e0496dd6821e7e781957c62e2bbe7a875770e56390d185a7c64c`, `labels=['白边', '皮肤 1', '皮肤 2']`
  - `mai (0x10)`: `5ca1b9dd12ea26bc2d52a99e5b9a9834ac618043c239722127f2d921a5d3930d`, `labels=['皮肤 1', '皮肤 2', '皮肤 3']`
  - `chizuru (0x0F)`: `59378f90090463e00f57d9689d39592e897000ac663f280c89d53f21186c7d01`, `labels=['皮肤 1', '皮肤 2', '皮肤 3']`
  - `orochi (0x1E)`: `6f66d102f7813a5089588102682297dba65ea307b6656ac8f60b859343352af6`, `labels=['皮肤 1', '皮肤 2', '皮肤 3']`
- **显式路径注入冒烟**：`KOF97BridgeApi(config_path=smoke_cfg.json)` 执行 `get_initial_state()` 与 `save_skin()` 通过。

### 4. PyInstaller 重编与跨工作目录启动实测
- 执行 `cmd /c src\build\BuildStudio.bat` → **exit 0**，输出 `dist/KOF97ModStudio.exe` 与根目录 `KOF97ModStudio.exe`（`26,616,214 bytes`）。
- 跨目录实测全部拉起 `拳皇97 逆向魔改工作台 (KOF97 Mod Studio)` PyWebView 窗体并安全退出：
  - `dist/KOF97ModStudio.exe` (`cwd=d:\TEmp\REA\Fighter97\dist`) → **PASS** (`PID=23300`, `alive=True`)
  - `dist/KOF97ModStudio.exe` (`cwd=%TEMP%`) → **PASS** (`PID=20996`, `alive=True`)
  - `KOF97ModStudio.exe` (`cwd=%TEMP%`) → **PASS** (`PID=20312`, `alive=True`)
