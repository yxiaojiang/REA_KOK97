# 已采纳的计划决定

## DIR-001（2026-11-06）拳皇97 ROM 静态逆向魔改技术方案与实施路线

本决定经 Round 2 审核收敛，由用户正式确认采纳。（注：部分偏移与路径已在后续实机核验中勘误，实施以文末**实测勘误表**为准。）

**决定**：
1. **技术路线定位**：确认属于 **Neo-Geo MVS 68000 ROM 静态逆向与二进制 Patch** 范畴。
2. **P-ROM 磁盘字节序规程**：工具链底层必须强制集成 **`bswap16`（16-bit 字高低字节交换）**转换与还原，所有反汇编、特征定位与数值 Patch 统一在 68000 运行态 Big-Endian 逻辑空间中进行。
3. **WinKawaks 1.48 沙盒多路径加载机制**：在工作区维护沙盒配置 `sandbox/WinKawaks.ini`，配置 `RomPath1`（魔改包优先，见勘误）与 `RomPath2=C:\Program Files (x86)\KOF97\roms`（复用 40MB C-ROM/音频，原生目录 100% 只读安全）；固定复用 **`output/roms/kof97pls.zip`** 槽位，内部标准封装 `232-p1p.bin`、`232-p2p.bin`、`232-s1p.bin`（约 1.4MB）作为交付载体。
4. **核心数值与防御修改逻辑**：破防槽 `$013E(A4)` 与眩晕槽 `$0146(A4)` 初始满值均为 `$0067`（103 点），受击递减小于 0 触发；通过在受创结算处将 `SUB.W` 替换为 `NOP; NOP`（`4E 71 4E 71`）实现绝对免疫破防与眩晕；血量等效倍增通过在受创扣血前经 Code Cave 插入 `LSR.W #1, D0` 实现全局伤害减半，不破坏每帧恢复与 UI 血条（精确指令地址见勘误）。
5. **调色板换肤机制**：按 Neo-Geo `LSPC2-A2` 非线性位布局（`Dark + R0/G0/B0 + R4..R1/G4..G1/B4..B1`）解析并修改 `232-p2p.bin` Bank 2 中八神庵 A 键调色板实现定制换肤（精确物理偏移见勘误）。
6. **阶段范围切割**：第一阶段聚焦工具链与沙盒上机加载闭环；第二阶段动态内存核验；第三阶段数值与防御 Patch；第四阶段调色板换肤；第五阶段 C-ROM 4bpp 瓦片重绘归档。

**原定顺序（第 1～5 步已全部实施并经 `CRDocs` `APPROVED`）**：
1. **第 1 步（P0-工具链构建与沙盒最小加载闭环）**：构建 `tools/rom_tool.py`（`bswap16` 转换与还原），生成 `output/roms/kof97pls.zip`，配置 `sandbox/WinKawaks.ini` 完成最小实机加载验证。
2. **第 2 步（P0-动态内存核验与 Code Cave 确认）**：实机核验 1P 角色结构体数值动态，核准 `0x000300+` Code Cave 空间。
3. **第 3 步（P1-静态数值与防御 Patch）**：实施免破防、免眩晕及受创减半 Code Cave Patch，实机对战验证。
4. **第 4 步（P1-调色板皮肤魔改）**：扩展 `rom_tool.py` 编解码 Neo-Geo 调色板，修改 `232-p2p.bin` 八神庵 A 键配色为黑金配色并实机验证。
5. **第 5 步（P2-C-ROM 瓦片重绘归档）**：沉淀 40MB C-ROM 瓦片交错解析工具（`tools/crom_tool.py`）与说明文档，实现 100% bit-exact 复原与 PNG 导出/导入。

### `DIR-001` 实测勘误与假设收口（2026-11-07 实施校准 / 2026-11-13 审校补正）

| 项目 | `DIR-001` 原文（已废止） | 实机核验与代码真实值（现行基线） | 依据 |
| :--- | :--- | :--- | :--- |
| **`WinKawaks.ini` 路径** | `RomPath1=.\output\roms` | **`RomPath1=..\output\roms`**（相对 `sandbox/` 目录） | `sandbox/WinKawaks.ini`、`Plan.md` |
| **1P 结构体 RAM 地址** | `0x108138` / `0x10813E` / `0x108146` | **`0x108238`**（HP）、**`0x10823A`**（红血）、**`0x10823E`**（破防）、**`0x108246`**（眩晕），基址 `A4 = 0x108100` | `Plan.md`、`tools/rom_tool.py` |
| **免破防 / 免眩晕偏移** | `0x013980` / `0x0139A6` | 指令起始地址为 **`0x01397E`**（`91 6C 01 3E`）与 **`0x0139A4`**（`91 6C 01 46`）；`0x013980`/`0x0139A6` 为位移字 | `CR-001-P2-01`、`tools/rom_tool.py` |
| **受创减半注入点** | `0x01394E: LSR.W #1, D0` | 在 **`0x01394A`** 写入 `JSR ($0300).W`（`4E B8 03 00`），跳入 `0x000300` 执行 `E2 48 D1 6C 01 3A 4E 75` 后返回 `0x01394E` | `CR-002-P2-01`、`tools/rom_tool.py` |
| **八神庵 A 键调色板** | `0x2DC9F0` | 真实角色 ID 为 **`0x1B`**，主调色板物理偏移 **`0x2DF7F0`**（编号 `0x07C0`，并同步 `0x2DF850`、`0x2DF990..0x2DF9EF`；`0x2DC9F0` 仅作兼容覆盖） | `CR-003-P2-01`、`CRDocs/DEFERRED.md` |
| **CRC 改写弹窗假设** | 未决假设（待第 1 步实测） | **已关闭**：`TASK-ROM-001`~`005` 实机验证通过；`tools/rom_tool.py` 处理沙盒加载隔离，不回落原生 `kof97pls.zip` | `CRDocs/REVIEW.md`、`tools/rom_tool.py` |

* **待后续独立提案的未决事项**：单招判定盒（Hitbox）与招式伤害表的精确脚本格式尚未纳入当前阶段，如后续启动专项修改须另开提案。
* **设计基线与计划位置**：
  * 架构方案：[`Docs/KOF97_ROM_Hacking_Architecture_and_Workflow.md`](../Docs/KOF97_ROM_Hacking_Architecture_and_Workflow.md)（v1.1，其中旧地址已由 [`Docs/KOF97_ROM_Hacking_Operation_Guide.md`](../Docs/KOF97_ROM_Hacking_Operation_Guide.md) 与根目录 [`Plan.md`](../Plan.md) 校准）。
  * 活跃与归档计划：根目录 `Plan.md`、`.claude/Plan.md`、`.claude/SessionBrief.md`。

---

## DIR-002（2026-11-11 收敛 / 2026-11-13 补录对齐）Mod Studio 工作台、隐藏人物解锁与全员 OKLCH 自然染色方案

本条为根据已实装并经用户实机确认的 `TASK-STUDIO-001` ~ `TASK-STUDIO-018` 里程碑（见 `.claude/Plan.md`、`.claude/SessionBrief.md`、`.claude/ProjectMemory.md`）补录的对齐记录，使 `PlanDocs` 与工程现状保持一致。

**决定**：
1. **桌面工作台与交付形态**：在 CLI 工具链之上新增基于 HTML5/CSS3 + `pywebview`（EdgeChromium）的桌面工具台 `tools/kof97_webview_app.py`，并通过 `tools/BuildStudio.bat` 打包为仓库根目录交付物 `KOF97ModStudio.exe`；主界面依 `TASK-STUDIO-016` 精简为三栏角色换肤、战斗属性强化与工程维护三页，「全部随机」（含八神）与「重置原皮肤」置于底栏，已移除自定义皮肤页与实时注入按钮，标准流转通过「保存设置 → 打包 ROM / 开始游戏」生效。
2. **隐藏人物全解锁与战斗属性扩展**：
   - **隐藏人物全解锁**：通过修改 `p1_be.bin` 偏移 `0x009976`（`4E 71 1B 7C 00 1F 6C 34`）、`0x01F7C8`（`4E 71`）并在全部 8 个选人网格表（`0x0A9499`..`0x0A95D4`）补入大蛇引擎 ID `0x1E`，实现无需按键直接选择暴走八神（引擎 `0x1C` / UI `0x1D`）、暴走莉安娜（引擎 `0x1D` / UI `0x1E`）、真大蛇队（引擎 `0x15..0x17` + `alt=1` / UI `0x1F..0x21`）、'94 草薙京（引擎 `0x00` + `alt=1` / UI `0x23`）与大蛇（引擎 `0x1E` / UI `0x22`）；矢吹真吾对应引擎 `0x1F` / UI `0x1C`。
   - **战斗属性扩展（P1 Patch）**：除 `DIR-001` 的免破防（`0x01397E`）、免眩晕（`0x0139A4`）外，新增可开关/可逆的**无限能量**（`0x025160` 跳入 `0x000320` Code Cave 锁定开局 3 气 `$01E3(A4)=3` 与满槽 `$01E8(A4)=$80`，并将 `0x01117C`、`0x018206`、`0x01E7EC`、`0x01E7F8` 四处超必杀/MAX 爆气扣气指令置 `NOP; NOP`）、**眩晕持续时间调节**（覆写 `0x0167D4`、`0x018210`、`0x01E80A`、`0x01E81A` 四处 60Hz 帧数常量）及**多档受创伤害倍率**（`0x01394A` + `0x000300`，支持切换倍率或恢复 100% 原版扣血）。
3. **ACT 00 站立图实时拼装预览**：由 `tools/sprite_compose.py` 实现；读取 `bswap16` 后的 P2 `0x200002` ACT 00 布局，C-ROM 16×16 瓦片按 `TR / BR / TL / BL` 四象限与每行 LSB 在左解码，保留空列槽位（禁止抽列压缩）。
4. **四键独立换色、MAX 爆气/立绘同步与公共色板保护**：打包或调用后端 `apply_skin_live` 接口（挂载 `WinKawaks.exe` 写入运行态 Palette RAM `0x007126B0` 与 P2 调色板区 `0x00712660 + 0x100000`）时，A/B/C/D 四键（`btn_idx = 0..3`）各自读取该键官方 15 色生成基础调色板（`pal_id + 0`），同步生成 MAX 爆气闪烁调色板（`pal_id + 3`）并联动覆写四键大立绘/选人与结算立绘/HUD 小头像（`base_pid + 13/14/15 + btn*16`）；未定制角色（`classic`）、技能特效色与界面公共色板保持 100% 官方原样。
5. **全员 36 名角色统一 OKLCH 自然染色标准（最终定稿）**：
   - 全员服装与毛发统一采用 `_paint_costume_natural` / `_natural_cloth_word`（见 `.claude/ProjectMemory.md` 第 13 节）：锁死原画每格槽位 OKLCH 明度 `L`，按感知明度断层（`> 0.24`）自动拆分上下装簇，彩度按钟形曲线封顶到 SNK 官方 B/C/D 换色实测范围（`light: 0.105`、`full: 0.11`、`dark: 0.13`，原画高饱和部位放宽至 `min(src_c, 0.20)`），`accent` 组遇浅色/白色主题执行明度补偿（`lift_neutral`）。
   - `skin`（肤色）、`white_trim`（锁定白边）与 `contour`（纯黑勾边 `0x0000`）严禁参与换色；已取代旧版高彩度直接覆盖方案，不得回退生成器。
