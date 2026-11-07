# SessionBrief.md — KOF97 逆向魔改工程会话简报

## 当前目标
阶段四 **`TASK-ROM-004`（调色板皮肤魔改）** 已由 Antigravity 实施并完成自动化实机对战全量验证：在 `tools/rom_tool.py` 中实现了 Neo-Geo `LSPC2-A2` 16-bit 调色板编解码器（支持 5-bit RGB 与暗位）；落实 `[CR-003-P2-01]` 校准结论，在 `build/unpacked/p2_be.bin` 中修改八神庵（`CharID=0x1B`）A 键主调色板 **`0x2DF7F0`**（`0x07C0`）、头像/选人调色板 **`0x2DF990..0x2DF9EF`** 及历史兼容偏移 **`0x2DC9F0`** 为定制“黑金（Black & Gold）”配色（璀璨黄金发与裤、深邃暗夜黑风衣、黑灰衬衣与自然肤色）；叠加前序全部防御 Patch（免破防、免眩晕、受创减半）打包生成 `output/roms/kof97pls.zip`（`232-p2p.bin` 磁盘 CRC32 `0xAF5CC95E`，`232-p1p.bin` 磁盘 CRC32 `0xFF227541`），并通过实机选人与 Round 1 实战截获断言证据。`CRDocs/STATUS.md` 已置为 `READY_FOR_REVIEW`，当前交棒给 **Argon** 进行 Round 4 独立审核。

## 关键约束与安全基线
1. **宿主与资产只读保护**：WinKawaks 1.48 原始目录 `C:\Program Files (x86)\KOF97\roms` 保持 100% 绝对只读，严禁写入或覆盖任何文件；沙盒通过 `RomPath1=..\output\roms` 与 `RomPath2=C:\Program Files (x86)\KOF97\roms` 共享原版约 40MB 资产。
2. **字节序与硬件位规范**：Motorola 68000 运行态为纯大端序（Big-Endian）且指令/字访问必须偶数地址对齐；物理 P-ROM（P1/P2）为 16-bit 字内高低字节翻转格式，必须经由 `bswap16` 双向无损转换；Neo-Geo `LSPC2-A2` 16-bit 调色板采用非线性位布局（`Bit 15: Dark`, `Bit 14: R0`, `Bit 13: G0`, `Bit 12: B0`, `Bit 11..8: R4..R1`, `Bit 7..4: G4..G1`, `Bit 3..0: B4..B1`），必须按硬件规范编解码。
3. **脚本与协作规范**：所有脚本（`tools/rom_tool.py`、`sandbox/launch_sandbox.bat`）100% 遵守纯 ASCII 英文规范（非 ASCII 字节数为 `0`）；双角色协作严格遵循 `CRDocs/` 规范。

## 最近变动与核心技术发现
1. **`TASK-ROM-004` 实施与自动化闭环**：
   - 在 `tools/rom_tool.py` 中落地 `encode_lspc2()` 与 `decode_lspc2()`，并通过 `self-test` 进行双向可逆无损校验。
   - 在 `p2_be.bin` 物理偏移 `0x2DF7F0` 将八神庵红发与红裤（原色 `#DE3A21..#4A0000`）替换为金属纯黄金渐变色阶（`#FFDE3A`, `#DEAD19`, `#A57308`, `#634200`，字机器码 `0x7FD3`, `0x7DA1`, `0x1A70`, `0x0640`）；风衣与衬衣替换为深邃暗夜黑（`#212129..#000000` 与 `#313131..#080808`），自然肤色完全保持。
   - 同步修改选人/HUD 头像板 `0x2DF990..0x2DF9EF`（`0x07CD`, `0x07CE`, `0x07CF`），使选人界面的大半身像与小头像实现金发化。
   - 新增 `build-palette` 与 `verify-palette` 自动化命令，实现 WinKawaks 后台输入注入、光标精确定位至八神庵（`Right x 3, Down x 3`）、A 键选择与出场顺位首发、正式对战 Work RAM 状态断言以及全程视觉截图。
2. **实机验证证据**：
   - 截获选人界面金发立绘 [`sandbox/capture/kof97pls050.png`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/sandbox/capture/kof97pls050.png)；
   - 截获顺位选择界面黑金八神庵 [`sandbox/capture/kof97pls051.png`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/sandbox/capture/kof97pls051.png)；
   - 截获韩国赛场 Round 1 实战对决姿势 [`sandbox/capture/kof97pls052.png`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/sandbox/capture/kof97pls052.png)，金发、金裤与黑风衣在战斗中完美呈现，无任何撕裂或破色，且 P1 防御与受创减半常数保持正常。

## 下一步
1. 交接给 **Argon** 进行 Round 4 独立审查（核查 `IMPLEMENTATION.md`、`rom_tool.py` 编解码及实机三张截图表现）。
2. 待审查通过（`APPROVED`）后，根据工程决议推进下一阶段（`TASK-ROM-005` 图像瓦片工具链沉淀）或项目最终收口交付。
