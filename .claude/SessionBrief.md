# SessionBrief.md — KOF97 逆向魔改工程会话简报

## 当前目标
阶段五 **`TASK-ROM-005`（C-ROM 图像瓦片重绘归档与工具链沉淀）** 已由审核员 **Argon** 独立完成 Round 5 审查并正式签发 **`APPROVED`**：
- 独立核查了 [`tools/crom_tool.py`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/tools/crom_tool.py) 与 [`tools/rom_tool.py`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/tools/rom_tool.py) 中 SNK Neo-Geo MVS 16x16 4bpp 瓦片四象限（右上、右下、左上、左下）与位平面（奇数 ROM 平面 0/1、偶数 ROM 平面 2/3）编解码数学逻辑；
- 独立验证了 40MB 全量 6 颗 C-ROM（327,680 个瓦片）解交错（De-interleave）生成 `.spr` 二进制流、以及重新交错（Interleave）复原 C-ROM 镜像的完整链路，实测表明 `KOF97_C1.ROM` 至 `KOF97_C6.ROM` 全部 6 颗镜像在 CRC32、SHA-256 及逐字节比对上达到了 **100% bit-exact 绝对无损复原**；
- 独立核验单瓦片 (`crom-export-tile`) 与图集 (`crom-export-sheet`) PNG 导出构件，并通过动态沙盒测试确认 `import_tile_png()` 具备反向无损回写能力；
- 独立复核宿主目录 `C:\Program Files (x86)\KOF97\roms` 绝对只读零写入，源码 100% 遵守纯 ASCII 规范；前序阶段 P1 防御补丁（免破防、免眩晕、受创减半）与 P2 八神庵黑金调色板保持 100% 零回归。
本工程基线规划的五大核心阶段已全部取得独立审查批准（`APPROVED`），工程圆满收敛。

## 关键约束与安全基线
1. **宿主与资产只读保护**：WinKawaks 1.48 原始目录 `C:\Program Files (x86)\KOF97\roms` 下 `kof97.ZIP`、`kof97pls.zip` 与 `neogeo.zip` 保持 100% 绝对只读与零写入，沙盒通过 `RomPath1=..\output\roms` 挂载定制 Hack 包，通过 `RomPath2=C:\Program Files (x86)\KOF97\roms` 共享原版约 40MB 只读资产。
2. **字节序与硬件位规范**：Motorola 68000 运行态大端序与 16-bit 字偶数对齐严格保持；Neo-Geo `LSPC2-A2` 16-bit 调色板非线性位排布保持；Neo-Geo 16x16 4bpp 平面瓦片四象限位平面排布严格遵循硬件规范。
3. **脚本与协作规范**：所有工具源码（`tools/rom_tool.py`、`tools/crom_tool.py`、`sandbox/launch_sandbox.bat`）100% 遵守纯 ASCII 英文规范（非 ASCII 字节数为 `0`）；双角色（Antigravity 执行 / Argon 审核）协作严格以 `CRDocs/` 和 `PlanDocs/` 为唯一交接媒介。

## 阶段验收与审查核验总结
1. **阶段一（TASK-ROM-001，APPROVED）**：打通纯英文工具链 `rom_tool.py`，实现 `bswap16` 双向无损转换与 `kof97pls.zip` 重打包，配置 WinKawaks 双路径沙盒并验证无红屏黑屏启动。
2. **阶段二（TASK-ROM-002，APPROVED）**：实机探针精确定位 1P 角色结构体（HP、破防、眩晕）Work RAM 运行态数值流，验证满值常数 `103`，确认 `0x000194..0x000800` 安全 Code Cave 边界。
3. **阶段三（TASK-ROM-003，APPROVED）**：实施免破防（`0x01397E`）、免眩晕（`0x0139A4`）及 Code Cave 受创减半跳板（`0x01394A` $\rightarrow$ `0x000300`），经实机对战自动化验证掉血减半且破防/眩晕槽锁死不降。
4. **阶段四（TASK-ROM-004，APPROVED）**：实现 Neo-Geo `LSPC2-A2` 16-bit 调色板编解码器，修改八神庵 A 键主调色板 `0x2DF7F0` 及头像板 `0x2DF990..0x2DF9EF` 为黑金定制配色，实机全流程截获选人、顺位及对战 Round 1 纯金发黑风衣画面。
5. **阶段五（TASK-ROM-005，APPROVED）**：实现 C-ROM 16x16 4bpp 瓦片四象限编解码与 40MB 全量解交错/重构工具链，达成 6 颗 C-ROM 逐字节 bit-exact 复原与 PNG 图集导出/导入。

## 下一步与成果交付总结
1. **项目全阶段闭环交付**：前序 5 个底层 ROM 魔改阶段（解包/逆向/防御Patch/黑金调色板/C-ROM瓦片）均已全量验收。
2. **现代化桌面工作台（KOF97ModStudio）完整落地**：
   - 彻底解决 pywebview 运行卡死死锁问题（消除 COM 反射递归、解耦 window 句柄与异步派发日志）；
   - 前端采用 Design B 深色舞台 3 栏交互架构（左侧 36 位角色列表及实时换装标签、中间英雄舞台、右侧 8 套精选和谐配色库）；
   - 彻底修复多角色皮肤保存覆盖问题，实现 36 位角色完全独立的内存状态管理。
3. **ROM 调色板机理与选人联动全面完善**：
   - **敌人变色杜绝**：未定制角色（`themeId == "classic"`）100% 保持 SNK 原生字节零修改；定制角色仅修改 1P 专用的 A/B 键，保留 C/D 键给 CPU 敌人，实现玩家与电脑的彻底隔离；
   - **角色光影立体感与色块清晰度重构**：实现全员明度保持的和谐调色板合成算法（Luminance-Preserving Semantic Ramp Remapping）。大门五郎、陈国汉等全员原生肤色与肌肉轮廓 100% 保护，服饰色阶严格按亮度排名梯度映射，彻底告别杂乱失真；
   - **选人界面与 HUD 立绘全量联动**：补齐选人界面立绘调色板表（`0x499C` 指向的 `base_pid + 13, 14, 15`），使选人立绘与战斗中血条旁小头像实时呈现定制皮肤。
4. **编译构建与产物就绪**：
   - 通过 PyInstaller 自动化构建流水线成功编译单文件免安装可执行程序 `KOF97ModStudio.exe`（37.1MB）；
   - 提供 `launch_mod_studio.bat` 与根目录双击启动入口，交付成果物在 WinKawaks 沙盒中完成 100% 功能验证。
