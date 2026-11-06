# 已采纳的计划决定

## DIR-001（2026-11-06）拳皇97 ROM 静态逆向魔改技术方案与实施路线

本决定经 Round 2 审核收敛，由用户正式确认采纳。

**决定**：
1. **技术路线定位**：确认属于 **Neo-Geo MVS 68000 ROM 静态逆向与二进制 Patch** 范畴。
2. **P-ROM 磁盘字节序规程**：工具链底层必须强制集成 **`bswap16`（16-bit 字高低字节交换）**转换与还原，所有反汇编、特征定位与数值 Patch 统一在 68000 运行态 Big-Endian 逻辑空间中进行。
3. **WinKawaks 1.48 沙盒多路径加载机制**：在工作区维护沙盒配置 `sandbox/WinKawaks.ini`，配置 `RomPath1=.\output\roms`（魔改包优先）与 `RomPath2=C:\Program Files (x86)\KOF97\roms`（复用 40MB C-ROM/音频，原生目录 100% 只读安全）；固定复用 **`output/roms/kof97pls.zip`** 槽位，内部标准封装 `232-p1p.bin`、`232-p2p.bin`、`232-s1p.bin`（约 1.4MB）作为交付载体。
4. **核心数值与防御修改逻辑**：破防槽 `$013E(A4)` 与眩晕槽 `$0146(A4)` 初始满值均为 `$0067`（103 点），受击递减小于 0 触发；通过在受创结算处（`0x013980` 与 `0x0139A6`）将 `SUB.W` 替换为 `NOP; NOP`（`4E 71 4E 71`）实现绝对免疫破防与眩晕；血量等效倍增通过在受创扣血前插入 `LSR.W #1, D0` 实现全局伤害减半，不破坏每帧恢复与 UI 血条。
5. **调色板换肤机制**：按 Neo-Geo `LSPC2-A2` 非线性位布局（`Dark + R0/G0/B0 + R4..R1/G4..G1/B4..B1`）解析并修改 `232-p2p.bin` Bank 2 偏移 `0x2DC9F0`（八神庵 A 键）实现定制换肤。
6. **阶段范围切割**：第一阶段聚焦工具链与沙盒上机加载闭环；第二阶段动态内存核验；第三阶段数值与防御 Patch；第四阶段调色板换肤；第五阶段 C-ROM 4bpp 瓦片重绘作为 P2 明确延期。

**顺序**：
1. **第 1 步（P0-工具链构建与沙盒最小加载闭环）**：
   - 编写纯英文 Python 脚本 `tools/rom_tool.py`，实现 P-ROM `bswap16` 转换与还原；
   - 提取原版 `KOF97_P1.ROM`、`P2.ROM`、`S1.ROM`，转换为 `232-p1p.bin`、`232-p2p.bin`、`232-s1p.bin` 打包为 `output/roms/kof97pls.zip`；
   - 配置 `sandbox/WinKawaks.ini`，启动模拟器完成最小实机加载验证。
2. **第 2 步（P0-动态内存核验与 Code Cave 确认）**：
   - 实机核验 1P 角色结构体（`0x108138`、`0x10813E`、`0x108146`）数值动态，核准 `0x000300+` Code Cave 空间。
3. **第 3 步（P1-静态数值与防御 Patch）**：
   - 实施免破防（`0x013980: NOP`）、免眩晕（`0x0139A6: NOP`）及伤害减半（`0x01394E: LSR.W #1, D0`），实机对战验证。
4. **第 4 步（P1-调色板皮肤魔改）**：
   - 扩展 `rom_tool.py` 编解码 Neo-Geo 调色板，修改 `232-p2p.bin` 八神庵 A 键配色（`0x2DC9F0`）为黑金配色并实机验证。
5. **第 5 步（P2-C-ROM 瓦片重绘归档）**：
   - 沉淀 40MB C-ROM 瓦片交错解析工具与说明文档。

**未决假设**：
- WinKawaks 1.48 在加载 CRC 改变的 `kof97pls.zip` 时是否弹出非阻断式警告框，待第 1 步实测确认。
- 单招判定盒（Hitbox）与招式伤害表的精确脚本格式待阶段三深入分析。

**设计基线**：[`Docs/KOF97_ROM_Hacking_Architecture_and_Workflow.md`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/Docs/KOF97_ROM_Hacking_Architecture_and_Workflow.md)（v1.1）。  
**计划位置**：根目录 `Plan.md`、`.claude/Plan.md`、`.claude/SessionBrief.md`。
