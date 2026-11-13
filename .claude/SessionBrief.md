# SessionBrief.md — KOF97 逆向魔改工程会话简报

## 当前目标与最新状态
1. **`TASK-STUDIO-020` / `DIR-003` 已完成实施与终验签批（2026-11-13 `CRDocs` Round 3 `APPROVED`）**：
   - 旧 `tools/` 目录（原 28 个文件，含 23 个有效文件与 5 个 `.bak*` 历史备份）已从工作区彻底移除，`tools_exists = False`，5 个 `.bak*` 与 `__pycache__/` 未迁入有效代码树。
   - 全部 23 个有效文件以及原 3,907 行的 `kof97_webview_app.py` 已按既定蓝图迁入并拆分为 `src/` 下 **7 个功能子包、共 40 个文件**，并同步更新了 PyInstaller 打包配置、4 个批处理启动器以及 8 个可执行测试验证脚本的路径引导。
   - Argon 已完成 Round 3 独立复核：活跃 `src/` 代码及 `sandbox/` 满足零 `tools` 引用、零非 ASCII 字节（仅历史归档 `legacy_tk_gui.py`、前端 `web/index.html`、参考数据 `official_palettes.txt` 与只读归档 `legacy_upgrades/*` 依规则豁免）及严格 5 层单向无环依赖 DAG；全部可执行测试套件、6 名典型角色 `get_idle_preview()` 图像哈希与 `p1_be.bin`/`p2_be.bin`/`kof97pls.zip` 字节级基线保持百分百一致；独立可执行文件 `KOF97ModStudio.exe`（`26,616,214` 字节）已重新编译并在跨工作目录场景下校验通过。
   - 当前交接区状态：`PlanDocs/STATUS.md` 为 `IDLE`，`CRDocs/STATUS.md` 为 `APPROVED`（当前负责人已清零为 `None`），本阶段任务正式收口归档。
2. **已冻结基线与历史里程碑（严禁回退）**：
   - **68000 数值与程序补丁基线（`TASK-ROM-001` ~ `TASK-ROM-005`）**：维持 `bswap16` 大端序双向转换、`0x01397E` 免破防、`0x0139A4` 免眩晕、`0x01394A -> JSR $0300.W` 受创减半与伤害倍增、无限能量、选人界面隐藏人物全解锁，以及 40MB C-ROM 4bpp 瓦片编解码工具链。
   - **全员自然染色标准（`DIR-002` / `TASK-STUDIO-001` ~ `018`）**：全员 36 名角色 20 款服装皮肤 OKLCH 自然染色器（`_paint_costume_natural` 与 `_natural_cloth_word`）及相关亮暗色阶参数保持零逻辑改动。
   - **技能特效动态改色基线（`TASK-STUDIO-019`）**：基于 `P1 0x004956` 与 `0x00483E` 槽位映射的 VFX 着色器，以及 `0x0F0000` 空间 68000 动态受击燃烧、感电、火花 Code Cave 保持零逻辑改动，同时严格保留 `P2 0x0000..0x00FF` 原版公共色板不被污染。
   - **前后端通信契约**：`KOF97BridgeApi` 全部 25 个公开 RPC 方法签名及 `src/studio/web/index.html`（`82,895` 字节）前端页面保持行为完全一致。

## `src/` 5 层单向架构与模块索引
1. **Layer 0 [`src/core/`]（对外部 `src.*` 零依赖）**：
   - `paths.py`：解析 `PROJECT_ROOT`/`BUNDLE_DIR`/`EXE_DIR`（在 `sys.frozen` 下优先探测 `"src"` 或 `"sandbox"`），提供 `get_config_path()` 与 `resolve_web_index_html()`。
   - `roster.py`：维护 36 名角色花名册 `CHARACTER_ROSTER`、`CHAR_ENGINE_MAP` 与 `CHARACTER_PALETTE_SCHEMA`。
   - `presets.py`：维护 `PRESET_THEMES`、`THEME_RAMPS`、`DAMAGE_MODES`、`VFX_PRESETS` 与 `VFX_PRESET_MAP`。
   - `config_store.py`：提供 `load_studio_config(..., skin_entry_factory=None)` 回调解耦加载与原子替换写入 `save_studio_config()`。
2. **Layer 1 [`src/palette/`]（仅依赖 Layer 0 与 Layer 1）**：
   - `color_utils.py`：统一托管 `encode_lspc2`/`decode_lspc2` 与 hex、rgb5、HSV、OKLCH 色彩空间转换函数。
   - `costume_painter.py`：封装冻结的服装染色算法与 `make_skin_entry`、`figure_preview_colors`。
   - `portrait_burst.py`：负责 `generate_burst_character_palette` 与四键立绘及头像同步 `sync_character_portraits`。
   - `vfx_shader.py`：提供角色技能特效扫描建表、霓虹发光着色器，以及共用受击通用组表与 `_recolor_hit_effect_slot`。
3. **Layer 2 [`src/rom/`]（仅依赖 Layer 0/1/2，仅 `rom_tool.py` 在 `gui` 子命令延迟导入 Tk GUI）**：
   - `crom_tool.py`：C-ROM 16x16 4bpp 瓦片编解码与交错打包工具（顶部已补齐 `import sys` 与两级路径引导）。
   - `rom_tool.py`：`bswap16` 解包打包、重导出 `encode_lspc2`/`decode_lspc2` 并统一收口导入 `from src.rom import crom_tool`。
   - `sprite_compose.py`：ACT 00 站立图实时拼装，中文色槽标签均已转为 `\uXXXX` 纯 ASCII 转义。
   - `p1_patcher.py`：`_M68kCodeCaveBuilder`、`0x0F0000` 受击 VFX Hook 与 `apply_combat_and_unlock_patches_to_p1(..., log_fn=None)`。
4. **Layer 3 [`src/emulator/`]（仅依赖 Layer 0 与 Layer 1）**：
   - `kawaks_live.py`：实现 `find_kawaks_pid` 与 `inject_live_palettes_to_kawaks(..., log_fn=None)`，由调用方传入 `p1_data`/`p2_clean` 与 `lspc_words_fn`，彻底消除与 ROM 层的交叉耦合。
5. **Layer 4 [`src/studio/`] 与 Layer 5 [`src/build/`, `src/tests/`]**：
   - `bridge_api.py`：实现 `KOF97BridgeApi(config_path=None)`，通过 `_paths` 模块间接访问与 `_resolve_config_path()` 兼容外部 monkeypatch，在 `pack_rom` 内保留 `KOF97_P2.ROM` 读取与 `apply_hit_effect_vfx_to_p1` 编排。
   - `kof97_webview_app.py`：`main()` 桌面窗口入口与精确 38 项 `__all__` 兼容重导出门面；`legacy_tk_gui.py` 与 `web/index.html` 已完整迁入。
   - `src/build/`：`build_exe.py`（含 `--paths`、`--add-data` 与全量 `src.*` 隐式导入）及 4 个使用 `%~dp0..\..` 定位根目录的 `.bat` 启动脚本。
   - `src/tests/`：包含 8 个可执行测试与验证脚本、`official_palettes.txt` 以及只读历史归档 `legacy_upgrades/`。

## 关键工程约束与风险提示
- **原始 ROM 隔离红线**：严禁原地写覆盖 `C:\Program Files (x86)\KOF97\roms` 宿主目录，所有解包、补丁与测试均须在工作区或隔离临时目录执行。
- **纯英文与纯 ASCII 规范**：活跃 `src/` 代码保持零非 ASCII 字节，面向用户的中文提示统一采用 `\uXXXX` 转义，避免 Windows 终端或构建编码异常。
- **动态实机交互脚本边界**：`verify_all.py` 与 `verify_e2e_live_and_win.py` 为调用真实 `WinKawaks.exe` DirectInput 的实机交互脚本，当前已完成路径迁移与静态门禁核验；后续若涉及 68000 汇编或内存偏移改动，仍须启动沙盒模拟器实机对照核验。

## 下一步
- 当前阶段 `TASK-STUDIO-020` 已完结归档，等待用户明确下一阶段需求后，再依据 `.claude/Rules.md` 与 `PlanDocs/` 流程发起新的提案讨论。
