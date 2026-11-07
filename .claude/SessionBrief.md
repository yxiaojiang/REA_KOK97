# SessionBrief.md — KOF97 逆向魔改工程会话简报

## 当前目标
阶段三 **`TASK-ROM-003`（P-ROM 静态数值与防御 Patch）** 已通过 **Argon** Round 3 独立审查并取得 `APPROVED`（`P0: 0`, `P1: 0`, `P2: 1 [DEFERRED TO TASK-ROM-004]`；上轮 `[CR-002-P2-01]` 已圆满闭环）。当前活跃目标转入阶段四 **`TASK-ROM-004`（调色板皮肤魔改）**，由 Antigravity 在 `tools/rom_tool.py` 实现 Neo-Geo `LSPC2-A2` 16-bit 调色板编解码器，修改 `p2_be.bin` 八神庵 A 键配色为黑金皮肤，叠加前三阶段防御 Patch 打包进 `output/roms/kof97pls.zip` 并完成实机验证。

## 关键约束与安全基线
1. **宿主与资产只读保护**：WinKawaks 1.48 原始目录 `C:\Program Files (x86)\KOF97\roms` 保持 100% 绝对只读，严禁写入或覆盖任何文件；沙盒通过 `RomPath1=..\output\roms` 与 `RomPath2=C:\Program Files (x86)\KOF97\roms` 共享原版约 40MB 资产。
2. **字节序与对齐基线**：Motorola 68000 运行态为纯大端序（Big-Endian）且指令/字操作必须偶数地址对齐；物理 P-ROM（P1/P2）为 16-bit 字内高低字节翻转格式，必须经由 `bswap16` 双向无损转换；`KOF97_S1.ROM` 为线性字节流。
3. **脚本与协作规范**：所有脚本（`tools/rom_tool.py`、`sandbox/launch_sandbox.bat`）100% 遵守纯 ASCII 英文规范（非 ASCII 字节数为 `0`）；代码与 Patch 审查严格遵循 `CRDocs/` 协作规程。

## 最近变动与核心技术发现
1. **`TASK-ROM-003` 审查通过（`APPROVED`）**：
   - 全量二进制 Diff 确认 `output/roms/kof97pls.zip` 内 `232-p1p.bin`（磁盘 CRC32 `0xff227541`，大端 CRC32 `0x21465f0a`）仅存在 4 处共 20 字节改动：`0x000300..0x000308`（`e248d16c013a4e75`：`LSR.W #1, D0; ADD.W D0, $013A(A4); RTS`，其中 `E2 48` 为标准 68000 逻辑右移）、`0x01394A..0x01394E`（`4eb80300`：`JSR ($0300).W`）、`0x01397E..0x013982`（`4e714e71` 免破防）、`0x0139A4..0x0139A8`（`4e714e71` 免眩晕），其余字节零漂移。
   - 实机对战验证（`kof97pls018.png`、`kof97pls019.png`）证实单发重拳伤害由 15 减半至 6~7 点，破防与眩晕槽恒定 103 点。
2. **阶段四 `TASK-ROM-004` 关键前置校准（`[CR-003-P2-01]`）**：
   - 经 Argon 反汇编 `P1.ROM` `0x004798..0x004920` 调色板加载器确认：角色调色板 ID 表起始于 `0x00483E`（每角色 8 字节对应 A/B/C/D 四键），通过 `0x2CFFF0 + PalID * 32` 映射至 `P2.ROM` Bank 2。
   - 早期文档中的 `CharID = 0x18`（`0x0640`/`0x0650` 位于 `0x2DC7F0`/`0x2DC9F0`）实为山崎龙二；**八神庵（Iori Yagami）真实 `CharID = 0x1B`（27）**，其 A 键调色板编号为 **`0x07C0`**，对应 `P2.ROM` 物理偏移 **`0x2DF7F0`**（`Word #01..#04` 肤色，`#05..#07` 白衬衣，`#08..#11` 酒红发与红裤 `#D83820..#480000`，`#12..#15` 深色风衣 `#383848..#000008`；同块 `0x07C3` `0x2DF850` 为受击闪光，`0x07CD..0x07CF` `0x2DF990..0x2DF9EF` 为立绘/选人/HUD 头像板）。

## 下一步
1. 由 **Antigravity** 执行 `TASK-ROM-004`：在 `tools/rom_tool.py` 实现 `LSPC2-A2` 调色板编解码与黑金换肤 Patch（覆盖八神庵真实 A 键 `0x2DF7F0` 等及兼容 `0x2DC9F0`），打包并在 WinKawaks 1.48 中实机选中八神庵截图验证。
2. 将 `TASK-ROM-004` 实施结果写入 `CRDocs/IMPLEMENTATION.md` 并更新 `CRDocs/STATUS.md` 为 `READY_FOR_REVIEW`。
