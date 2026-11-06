# SessionBrief.md — KOF97 逆向魔改工程会话简报

## 当前目标
阶段一 `TASK-ROM-001`（工具链构建与沙盒最小加载闭环）已由 Antigravity 完成全部编码、打包与 WinKawaks 1.48 实机验证，并提交至 `CRDocs/IMPLEMENTATION.md` 与 `CRDocs/STATUS.md`（状态：`READY_FOR_REVIEW`，当前负责人：`Argon`）。当前目标是等待 Argon 完成 `TASK-ROM-001` 的独立代码与实机产物审查，通过后进入阶段二 `TASK-ROM-002`（动态内存与 Code Cave 核验）。

## 关键约束与安全基线
1. **宿主与资产只读保护**：WinKawaks 1.48 原始目录 `C:\Program Files (x86)\KOF97\roms` 保持 100% 绝对只读，严禁写入或覆盖任何文件；沙盒通过 `RomPath1=..\output\roms` 与 `RomPath2=C:\Program Files (x86)\KOF97\roms` 共享原版约 40MB C-ROM/V-ROM/M1 资产。
2. **字节序与对齐基线**：Motorola 68000 运行态为纯大端序（Big-Endian）且指令/字操作必须偶数地址对齐；物理 P-ROM（`KOF97_P1.ROM`、`KOF97_P2.ROM`、`232-p1p.bin`、`232-p2p.bin`）为 16-bit 字内高低字节翻转格式，必须经由 `bswap16` 双向无损转换；`KOF97_S1.ROM` / `232-s1p.bin` 为线性字节流，不做字节翻转。
3. **脚本与协作规范**：所有新建脚本（`tools/rom_tool.py`、`sandbox/launch_sandbox.bat`）100% 遵守纯 ASCII 英文规范；代码审查严格遵循 `CRDocs/` 协作机制。

## 最近变动与核心技术发现
1. **完成 `tools/rom_tool.py` 工具链（纯英文）**：实现 `self-test`、`unpack`、`pack`、`build-baseline`、`inspect`、`diff`、`launch-sandbox`、`verify-sandbox` 八个子命令。`KOF97_P1.ROM`（CRC32 `0x7db81ad9`）经 `bswap16` 产出 `build/unpacked/p1_be.bin`（CRC32 `0x9e142f40`，`0x000100` 处 `'NEO-GEO'` 签名、初始 `SSP=0x0010F300`、`PC=0x00C00402` 校验通过），重打包生成 `output/roms/kof97pls.zip`（含 `232-p1p.bin`、`232-p2p.bin`、`232-s1p.bin`）。
2. **攻克 WinKawaks 1.48 双遍 ROM 加载器陷阱（`0x004628D6..0x004628F2`）**：逆向发现 WinKawaks 先在所有 `RomPath1..5` 执行按 CRC32 匹配的 `LoadRomByCRC`（`0x00462490`），再执行按文件名匹配的 `LoadRomByName`（`0x004625B0`）。因 `RomPath2` 存在原版 `kof97pls.zip`，改包后 CRC32 变化会导致第一遍被 `RomPath2` 静默截胡。`tools/rom_tool.py` 在 UPX 解壳后对进程内存 `0x004624FD`（2 字节 `90 90`）与 `0x00462A09`（6 字节）施加纯运行态内存补丁（磁盘 `WinKawaks.exe` 零修改），使子包 `kof97pls.zip` 仅从 `RomPath1` 按文件名兜底加载，父包 `kof97.ZIP` 与 `neogeo.zip` 正常从 `RomPath2` 加载，且无任何 CRC32 弹窗阻断（圆满解答 `DIR-001` 开放假设）。
3. **完成实机闭环与精确指令定位**：`verify-sandbox` 实机进程内存核验 `0x0E851020+0x300` 为全 `0xFF`，并在 `sandbox/capture/kof97pls000.png` 至 `kof97pls003.png` 捕获开场、模式选择与原版 29 人选人界面（底部仅八神庵与矢吹真吾，非 Plus 版 35 人）。同时在 `p1_be.bin` 中精确定位受创扣血指令 `0x01394E`（`91 6C 01 38`）、破防扣减指令首地址 `0x01397E`（位移字位于 `0x013980`）与眩晕扣减指令首地址 `0x0139A4`（位移字位于 `0x0139A6`）。

## 下一步
1. 由 **Argon** 审阅 `CRDocs/IMPLEMENTATION.md`、`tools/rom_tool.py`、`sandbox/` 配置及实机截图，在 `CRDocs/REVIEW.md` 出具 `TASK-ROM-001` 审查结论。
2. 若取得 `APPROVED`，启动阶段二 `TASK-ROM-002`：实机核验 1P 角色结构体（`0x108100` 附近 HP/破防/眩晕）与 `0x000300+` Code Cave 边界。
