# SessionBrief.md — KOF97 逆向魔改工程会话简报

## 当前目标
阶段一 `TASK-ROM-001`（工具链构建）与阶段二 `TASK-ROM-002`（动态内存与 Code Cave 核验）均已通过 **Argon** 独立审查并取得 `APPROVED`。当前活跃目标转入阶段三 **`TASK-ROM-003`（P-ROM 静态数值与防御 Patch）**：由 Antigravity 按 `[CR-002-P2-01]` 实施免疫破防（`0x01397E`）、免疫眩晕（`0x0139A4`）以及受创减半定长跳板（`0x01394A -> 0x000300`），经 `bswap16` 打包后在 WinKawaks 实机中验证免疫与减半表现。

## 关键约束与安全基线
1. **宿主与资产只读保护**：WinKawaks 1.48 原始目录 `C:\Program Files (x86)\KOF97\roms` 保持 100% 绝对只读，严禁写入或覆盖任何文件；沙盒通过 `RomPath1=..\output\roms` 与 `RomPath2=C:\Program Files (x86)\KOF97\roms` 共享原版约 40MB 资产。
2. **字节序与对齐基线**：Motorola 68000 运行态为纯大端序（Big-Endian）且指令/字操作必须偶数地址对齐；物理 P-ROM 为 16-bit 字内高低字节翻转格式，必须经由 `bswap16` 双向无损转换；`KOF97_S1.ROM` 为线性字节流。
3. **脚本与协作规范**：所有新建或修改脚本（`tools/rom_tool.py`、`sandbox/launch_sandbox.bat`）100% 遵守纯 ASCII 英文规范（非 ASCII 字节数为 0）；代码与 Patch 审查严格遵循 `CRDocs/` 协作规程。

## 最近变动与核心技术发现
1. **`TASK-ROM-002` 审查通过（`APPROVED`）**：Argon 独立复核确认 Work RAM 宿主指针常驻 `0x00712688`，纠偏确认 1P 角色结构体物理映射为 HP `0x108238`、Red HP `0x10823A`、Guard `0x10823E`、Dizzy `0x108246`（基址 `A4 = 0x108100`）；2P 位于 `A4 = 0x108300`；实战对战态下初始数值满值 `$0067`（103）及受创动态削减（HP: 103 -> 88, Guard: 103 -> 82）与实机截图（`kof97pls013.png`、`kof97pls014.png`）100% 吻合。
2. **`[CR-001-P2-02]` 成功关闭**：`sandbox/launch_sandbox.bat` 裸启动回退已移除，改为显式报错退出。
3. **受创减半推荐切入点确立（`[CR-002-P2-01]`）**：
   - 在 `0x01394A`（`D1 6C 01 3A`，`ADD.W D0, $013A(A4)`，4B）处写入 `JSR ($0300).W`（`4E B8 03 00`，4B）；
   - 在 `0x000300` 处写入 8 字节序列：`E2 40` (`LSR.W #1, D0`) + `D1 6C 01 3A` (`ADD.W D0, $013A(A4)`) + `4E 75` (`RTS`)；
   - 保证红血计数器与实血扣减同步减半，且完全保留 `0x01394E` 原生 `SUB.W` 对 `0x013952` `BMI.W` 的负数标志传递链。
4. **免破防与免眩晕机器码定长替换确立**：
   - 免破防：在 `0x01397E` 将 `91 6C 01 3E`（4B）替换为 `4E 71 4E 71`（`NOP; NOP`，4B）；
   - 免眩晕：在 `0x0139A4` 将 `91 6C 01 46`（4B）替换为 `4E 71 4E 71`（`NOP; NOP`，4B）。

## 下一步
1. 由 **Antigravity** 在 `tools/rom_tool.py` 中实现 P-ROM 静态防御 Patch 构建逻辑（`patch-defense` 或集成至打包流水线）。
2. 构建魔改版 `output/roms/kof97pls.zip` 并运行实机自动化对战核验。
3. 将 `TASK-ROM-003` 实施证据写入 `CRDocs/IMPLEMENTATION.md` 并更新 `CRDocs/STATUS.md` 为 `READY_FOR_REVIEW`，交接给 Argon 进行 Round 3 独立审核。
