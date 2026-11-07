# SessionBrief.md — KOF97 逆向魔改工程会话简报

## 当前目标
阶段五 **`TASK-ROM-005`（C-ROM 图像瓦片重绘归档与工具链沉淀）** 已完成全套工程化实施并提交至 **`READY_FOR_REVIEW`**，交接给审核方 **Argon** 开展 Round 5 审查：
- 在 [`tools/crom_tool.py`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/tools/crom_tool.py) 中完整实现了 SNK Neo-Geo MVS 16x16 4bpp 瓦片架构（四象限子块排列：Block 0 右上、Block 1 右下、Block 2 左上、Block 3 左下；奇数 C-ROM 存储 Bitplane 0/1、偶数 C-ROM 存储 Bitplane 2/3）；
- 实现全量 40MB（`C1/C2`, `C3/C4`, `C5/C6`，共 327,680 个瓦片）极速解交错（De-interleave）生成 `.spr` 二进制流；
- 实现全量 40MB 重交错（Interleave）复原 C-ROM 镜像，经对 6 颗 ROM（`KOF97_C1.ROM` 至 `KOF97_C6.ROM`）逐一校验，达到 100% bit-exact 无损复原（CRC32 完全吻合）；
- 实现单瓦片 (`export-tile`) 与连续瓦片集图集 (`export-sheet`) PNG 格式导出与反向瓦片回写导入 (`import-tile`)；
- 将 C-ROM 工具链子命令（`crom-deinterleave`, `crom-interleave`, `crom-export-tile`, `crom-export-sheet`, `crom-import-tile`, `crom-self-test`）平滑集成入 [`tools/rom_tool.py`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/tools/rom_tool.py)，并纳入 `self-test` 全局自检；
- 代码与注释保持 100% 纯 ASCII（0 非 ASCII 字节）。

## 关键约束与安全基线
1. **宿主与资产只读保护**：WinKawaks 1.48 原始目录 `C:\Program Files (x86)\KOF97\roms` 下 `kof97.ZIP`、`kof97pls.zip` 与 `neogeo.zip` 保持 100% 绝对只读与零写入。
2. **字节序与硬件位规范**：Motorola 68000 运行态大端序与 16-bit 字偶数对齐严格保持；Neo-Geo `LSPC2-A2` 16-bit 调色板非线性位排布保持；Neo-Geo 16x16 4bpp 平面瓦片四象限位平面排布严格遵循硬件规范。
3. **脚本与协作规范**：所有工具源码（`tools/rom_tool.py`、`tools/crom_tool.py`、`sandbox/launch_sandbox.bat`）100% 遵守纯 ASCII 英文规范（非 ASCII 字节数为 `0`）；双角色（Antigravity 执行 / Argon 审核）协作严格以 `CRDocs/` 和 `PlanDocs/` 为唯一交接媒介。

## 最近变动与审查核验结论
1. **`TASK-ROM-005` 实施就绪（READY_FOR_REVIEW）**：
   - 编写 `tools/crom_tool.py`，并在 `tools/rom_tool.py` 中暴露 `crom-*` 子命令与集成单元测试；
   - 40MB C-ROM 对解交错与重交错实测耗时 <0.3 秒；
   - 重构生成的 6 颗 C-ROM CRC32 与原版 `kof97.ZIP` 逐一精确比对通过（`0x5F8BF0A1`, `0xE4D45C81`, `0x581D6618`, `0x49BB1E68`, `0x34FC4E51`, `0x4FF4D47B`）；
   - 前序阶段所有功能（解包重包、沙盒探针、P1 免破防/免眩晕/受创减半、P2 黑金八神庵调色板）100% 零回退保持；
   - 更新 `CRDocs/IMPLEMENTATION.md` 与 `CRDocs/STATUS.md`（状态设置为 `READY_FOR_REVIEW`，Round 5，交接给审查员 Argon）。
2. **问题清单状态**：
   - 当前未关闭延期问题：`P0: 0`, `P1: 0`, `P2: 0`。

## 下一步
交接由审核员 Argon 执行 Round 5 审查并签署 `CRDocs/REVIEW.md`。
