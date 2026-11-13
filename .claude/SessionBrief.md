# SessionBrief.md — KOF97 逆向魔改工程会话简报

## 当前目标
1. **已冻结基线（严禁回退）**：全员 36 名角色的 20 款服装皮肤继续统一走 OKLCH 自然染色器（`_paint_costume_natural` / `_natural_cloth_word`，详见 `ProjectMemory.md` 第 13 节），服装明暗与色相参数保持锁定。
2. **已完成的里程碑（`TASK-STUDIO-019` 全功能 + 68000 动态受击变色同步）**：
   - 角色技能特效调色板定制已在 `tools/kof97_webview_app.py` 与 `tools/web/index.html` 落地，支持 `classic` 原版、`sync_skin` 跟随皮肤与苍炎蓝/冥炎紫/赤焰红/圣耀金等 8 款高饱和发光渐变预设。
   - **68000 动态受击效果同步（`0x0F0000` Code Cave）**：解决招式命中对手后紫炎/赤炎灼烧（`0xF8`/`0xF9` + 附着火苗 `0x57..0x68`）、感电火花（`$e3 |= 2` + `0x52, 0x62, 0x53, 0x54`）、大蛇闪光（`0xFA`）与冲击火花（`0x51, 0x55, 0x54, 0x64, 0x6A`）仍显示原版紫/橙的问题；保留 `0x0058/0x005F` 中性灰烟雾与 `0x0010/0x1210` 暗色遮罩，保持 `P2 0x0000..0x00FF` 与 `P2 0x17B0..0x17DF` 100% 官方原版，支持 1P/2P 各自独立特效色并在切回 `classic` 时无损还原。

## 已核实的硬件与代码基线（详见 `ProjectMemory.md` 第 14 节）
1. **主技能特效表（`P1 0x004956`）**：按 `pal_idx` 直接查表（`0x15..0x17` 与 `0x18..0x1A` 交错），映射 `vfx_base_pid`（`0x09C0..0x0BE0`）；跳过占位纯色及人物本体受创闪烁子槽（仅联动 `VFX_SUBSLOT_OFFSETS` 纯光效子槽）。
2. **P1 动态受击同步 Hook（`0x0F0000..0x0FFFFF`）**：挂钩 16 处 6 字节指令（`0x0251C4`、`0x0041AE/E6/0x004254`、`0x012E64`、`0x012F18..0x013184`、`0x03376E`），经受击者 `$b6(a4)` 查攻击者运行时槽位 `0..35`，通过 `$5924(a5)` 队列更新 Palette RAM，缓存于未用 Work RAM `A5+$6E00..$6E08`。不占用现有 `0x000300..0x000530` 战斗 Hook。

## 关键约束与验证现状
1. 宿主 `C:\Program Files (x86)\KOF97\roms` 只读；`P2 0x0000..0x00FF` 官方界面公共色板零改动。
2. 工具链源码注释与标识符 100% 全英文；`apply_skin_live` 仅写运行态显存 Palette RAM 与 P2 `> 0x00FF` 槽。
3. 全量回归测试（`tools/rom_tool.py self-test`、`tools/test_vfx_palette_suite.py` 6/6、`tools/test_full_roster_skins_suite.py`）已通过，根目录 `KOF97ModStudio.exe` 与 `dist/KOF97ModStudio.exe` 已同步至最新编译版。

## 下一步
- 当前工作区与记忆文件已同步更新；后续如需新增机制或新特性，按 `.claude/Rules.md` 从 `PlanDocs` 或独立 `TASK-STUDIO-020` 启动。
