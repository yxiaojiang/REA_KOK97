# SessionBrief.md — KOF97 逆向魔改工程会话简报

## 当前目标
阶段三 **`TASK-ROM-003`（P-ROM 静态数值与防御 Patch）** 已由 Antigravity 实施完成：成功在 `build/unpacked/p1_be.bin` 施加免破防（`0x01397E`）、免眩晕（`0x0139A4`）及基于 Code Cave `0x000300` 的受创扣血减半跳板（`0x01394A`），通过 `bswap16` 封装生成 `output/roms/kof97pls.zip`（`232-p1p.bin` 磁盘 CRC32 `0xFF227541`），并通过实机自动化对战全量断言验证（伤害由 15 降至 6~7，Guard/Dizzy 恒定 103）。`CRDocs/STATUS.md` 已置为 `READY_FOR_REVIEW`，当前交棒给 **Argon** 进行 Round 3 独立审核。

## 关键约束与安全基线
1. **宿主与资产只读保护**：WinKawaks 1.48 原始目录 `C:\Program Files (x86)\KOF97\roms` 保持 100% 绝对只读，严禁写入或覆盖任何文件；沙盒通过 `RomPath1=..\output\roms` 与 `RomPath2=C:\Program Files (x86)\KOF97\roms` 共享原版约 40MB 资产。
2. **字节序与对齐基线**：Motorola 68000 运行态为纯大端序（Big-Endian）且指令/字操作必须偶数地址对齐；物理 P-ROM 为 16-bit 字内高低字节翻转格式，必须经由 `bswap16` 双向无损转换；`KOF97_S1.ROM` 为线性字节流。
3. **脚本与协作规范**：所有新建或修改脚本（`tools/rom_tool.py`、`sandbox/launch_sandbox.bat`）100% 遵守纯 ASCII 英文规范（非 ASCII 字节数为 0）；代码与 Patch 审查严格遵循 `CRDocs/` 协作规程。

## 最近变动与核心技术发现
1. **P-ROM 静态防御 Patch 闭环**：
   - 受创扣血减半：在 `0x01394A` 写入 4 字节短绝对调用 `JSR ($0300).W`（`4E B8 03 00`），等长替换 `ADD.W D0, $013A(A4)`；在 `0x000300` Code Cave 写入 `E2 48` (`LSR.W #1, D0`) + `D1 6C 01 3A` (`ADD.W D0, $013A(A4)`) + `4E 75` (`RTS`)，返回 `0x01394E` 继续扣减实血，保证 UI 红血条与实血扣减严格同步减半，且 KO 负数判定无损。
   - 免破防：在 `0x01397E` 将 `SUB.W D0, $013E(A4)` 替换为 `4E 71 4E 71`（`NOP; NOP`，4 字节）。
   - 免眩晕：在 `0x0139A4` 将 `SUB.W D0, $0146(A4)` 替换为 `4E 71 4E 71`（`NOP; NOP`，4 字节）。
2. **工具链集成与实机验证**：
   - [`tools/rom_tool.py`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/tools/rom_tool.py) 新增 `build-defense` 与 `verify-defense` 命令，全量自检通过且非 ASCII 字节数为 0。
   - 实机实测：交锋受创单发伤害由 15 点削减为 6~7 点（等效双倍血量）；破防槽与眩晕槽在连续打击下全程恒定 103 点（100% 免疫破防与眩晕）；视觉截图（`kof97pls018.png`、`kof97pls019.png`）清晰呈现受创火花与血条微扣。

## 下一步
1. 交接给 **Argon** 进行 Round 3 独立审核：核查 `CRDocs/IMPLEMENTATION.md` 与实机验证数据。
2. 审核通过后，开启阶段四 **`TASK-ROM-004`（调色板皮肤魔改）**：按 Neo-Geo `LSPC2-A2` 非线性 16-bit 格式修改 `232-p2p.bin` 偏移 `0x2DC9F0`（八神庵 A 键）为黑金配色并实机验证。
