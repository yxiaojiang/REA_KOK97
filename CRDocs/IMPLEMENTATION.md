# 实施与验证交接 (CRDocs — TASK-ROM-001 Round 1)

## 本轮实际修改

### 1. 构建纯英文 ROM 逆向与打包工具链 [`tools/rom_tool.py`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/tools/rom_tool.py)
- **100% 纯英文规范**：全文件注释、文档字符串、变量命名与日志输出均为纯 ASCII 英文，无任何中文字符。
- **`bswap16` 双向无损字节序转换（[`bswap16`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/tools/rom_tool.py#L54-L62)）**：
  - 严格校验 16-bit 偶数地址对齐（奇数长度直接抛出 `ValueError`）；
  - 实现物理磁盘存储格式（Word-swapped）与 Motorola 68000 运行态大端序（Big-Endian）的高效切片互换；
  - 内置 [`detect_p1_endianness`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/tools/rom_tool.py#L73-L85) 自动识别 `0x000100` 处的磁盘签名 `'EN-OEG\x10'` 与 68000 大端签名 `'NEO-GEO'`。
- **解包与重打包流水线（[`unpack_rom_set`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/tools/rom_tool.py#L131-L185) / [`pack_rom_set`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/tools/rom_tool.py#L188-L246)）**：
  - 只读读取 `C:\Program Files (x86)\KOF97\roms\kof97.ZIP`，提取 `KOF97_P1.ROM` (1,048,576 B)、`KOF97_P2.ROM` (4,194,304 B)、`KOF97_S1.ROM` (131,072 B)；
  - 将 P1/P2 经 `bswap16` 转换为 68000 Big-Endian 逻辑镜像并落盘至 `build/unpacked/p1_be.bin`、`build/unpacked/p2_be.bin`（`s1.bin` 原样保留）；
  - 打包阶段将 `p1_be.bin`、`p2_be.bin` 再次执行 `bswap16` 还原为 MVS 磁盘字节序，并映射为 `232-p1p.bin`、`232-p2p.bin`、`232-s1p.bin` 封装生成 [`output/roms/kof97pls.zip`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/output/roms/kof97pls.zip)。
- **大端空间 Diff 与特征核验（[`diff_rom_sets`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/tools/rom_tool.py#L273-L309) / [`inspect_rom_set`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/tools/rom_tool.py#L312-L343)）**：
  - 支持在 68000 Big-Endian 逻辑空间对比任意两个 ROM 包（如 `kof97.ZIP` vs `kof97pls.zip`），输出连续差异区间与机器码对照；
  - 支持一键自检（`self-test`）、构建基线包（`build-baseline`）、启动沙盒（`launch-sandbox`）与自动化实机验证截图（`verify-sandbox`）。

### 2. 搭建沙盒运行环境与双 RomPath 启动配置
- **沙盒目录隔离**：在 `sandbox/` 下复制了 `WinKawaks.exe` 及非 ROM 运行时依赖目录（`ini/`、`lang/`、`eeprom/`、`saves/`、`capture/`、`sshots/` 等），**未复制任何 ROM 大文件**，且确保模拟器运行态读写（如 `WinKawaks.ini`、`WinKawaks.rom`、`eeprom/kof97pls.srm`、`capture/*.png`）100% 发生在工作区 `sandbox/` 内，绝不触碰原生目录。
- **沙盒配置文件 [`sandbox/WinKawaks.ini`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/sandbox/WinKawaks.ini)**：
  - 配置 `RomPath1=..\output\roms`（优先指向工作区构建产物）；
  - 配置 `RomPath2=C:\Program Files (x86)\KOF97\roms`（直接复用原目录 40MB C-ROM、12MB 语音 V-ROM、M1 及 `neogeo.zip`）；
  - 配置 `AutoPause=0`，支持后台自动化测试与无焦点运行。
- **纯英文启动脚本 [`sandbox/launch_sandbox.bat`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/sandbox/launch_sandbox.bat)**：
  - 校验 `..\output\roms\kof97pls.zip` 存在性后调用 `rom_tool.py launch-sandbox kof97pls` 启动模拟器。

### 3. 实机加载机制关键发现与沙盒加载优先级修正（核心工程收获）
在对 WinKawaks 1.48 (`WinKawaks.exe`) 进行实机进程内存核验与 x86 机器码反汇编时，定位并解决了两个直接影响沙盒闭环的底层问题：
1. **WinKawaks 1.48 双趟 ROM 加载器（Pass-1 CRC 抢占陷阱，`0x004628D6..0x004628F2`）**：
   - 经反汇编核实，WinKawaks 加载每个驱动 ROM 条目时，先调用 `0x00462490`（`LoadRomByCRC`）遍历 `RomPath1..RomPath5` 查找匹配的 CRC32；**仅当所有 `RomPath1..5` 均未命中目标 CRC32 时**，才会调用 `0x004625B0`（`LoadRomByName`）按文件名回退加载。
   - 由于 `RomPath2`（`C:\Program Files (x86)\KOF97\roms`）下同时存在原版未修改的 `kof97pls.zip`（其 `232-p1p.bin` CRC32 正好是驱动表硬编码的 `0xC01FDA46`），一旦 `RomPath1\kof97pls.zip` 的 CRC32 发生改变（如本阶段裝入原版 `KOF97_P1.ROM` `0x7DB81AD9` 或后续阶段打 Patch），`0x00462490` 的 Loop 1 在扫描完 `RomPath1\kof97pls.zip` 未命中 CRC 后会继续扫描 `RomPath2\kof97pls.zip` 并命中 `0xC01FDA46`，导致模拟器静默加载 `RomPath2` 下的未修改版 `kof97pls.zip`，使 `RomPath1\kof97pls.zip` 被完全旁路！
   - **沙盒解决方案**：在不修改磁盘 `WinKawaks.exe` 二进制文件、不触碰原生目录的前提下，由 [`start_sandbox_kawaks`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/tools/rom_tool.py#L357-L398) 在启动子进程并完成 UPX 解壳后，通过 `WriteProcessMemory` 将 `0x004624FD`（`7C B9` -> `90 90`）与 `0x00462A09`（`0F 8C 6D FF FF FF` -> `90 * 6`）处的子集 `kof97pls.zip` 跨目录循环分支 NOP 掉。这样子集 `kof97pls.zip` 严格锁定仅从 `RomPath1`（`..\output\roms`）按 CRC 或文件名加载，而母集 `kof97.ZIP`（Loop 2，`0x004624FF`）与 BIOS `neogeo.zip`（Loop 3，`0x0046255B`）依然正常遍历至 `RomPath2` 加载。
2. **WinKawaks 1.48 命令行解析器引号缺陷（`0x0042082E`）**：
   - `0x0042082E` 假定 `GetCommandLineA()` 中的 `argv[0]` 必然被双引号 `"` 包裹，直接从偏移 `+2` 处循环扫描闭合的 `0x22`（`"`）。若工作区路径无空格且调用方未给 `argv[0]` 加双引号，扫描将越过字符串末尾 `\0` 导致游戏名参数丢失（显示 `No game loaded`）。[`start_sandbox_kawaks`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/tools/rom_tool.py#L369) 已强制使用 `f'"{exe_path}" {rom_name}'` 传参。

---

## 判定未修改

1. **原生安装目录零写入**：`C:\Program Files (x86)\KOF97` 及其子目录 `roms\` 下的所有原始文件（`kof97.ZIP`、`kof97pls.zip`、`neogeo.zip`）保持 100% 原始状态，修改时间戳分毫无损。
2. **ROM 逻辑数据零篡改（符合阶段一最小基线要求）**：本阶段仅对原版 `KOF97_P1.ROM`、`KOF97_P2.ROM` 执行 `bswap16` 解包与 `bswap16` 还原重命名封装，未注入任何数值或调色板 Patch。
3. **预先记录供阶段二/三核验的机器码偏移修正项（暂未修改静态文档）**：
   - 在通过 `rom_tool.py inspect` 检查 68000 大端逻辑空间时发现：`KOF97_P1.ROM` 中 `SUB.W D0, $0138(A4)` 的真实机器码为 `91 6C 01 38`（位于 `0x01394E`）；而破防扣减 `SUB.W D0, $013E(A4)`（`91 6C 01 3E`）真实起始地址为 **`0x01397E`**（`0x013980` 为其位移字 `01 3E`），眩晕扣减 `SUB.W D0, $0146(A4)`（`91 6C 01 46`）真实起始地址为 **`0x0139A4`**（`0x0139A6` 为其位移字 `01 46`）。该发现已在 `rom_tool.py inspect` 中精确标注，留待阶段二/三正式核验。

---

## 验证证据与模拟器运行记录

### 1. 工具链自检、双向无损 `bswap16` 与打包校验日志
执行 `python tools/rom_tool.py build-baseline` 与 `python tools/rom_tool.py inspect` 实测输出：

```text
=== Running rom_tool.py Self-Test ===
  [PASS] bswap16 header vector test (100000f3 -> 0010f300, EN-OEG -> NEO-GE)
  [PASS] bswap16 odd-length alignment guard test
  [PASS] bswap16 bidirectional lossless round-trip test

=== Unpacked ROM Set from C:\Program Files (x86)\KOF97\roms\kof97.ZIP ===
  [P1] KOF97_P1.ROM -> C:\Users\mimovr\Desktop\TEmp\REA\Fighter97\build\unpacked\p1_be.bin
       size=1048576 B | bswap16=True | disk_crc32=0x7db81ad9 -> be_crc32=0x9e142f40
  [P2] KOF97_P2.ROM -> C:\Users\mimovr\Desktop\TEmp\REA\Fighter97\build\unpacked\p2_be.bin
       size=4194304 B | bswap16=True | disk_crc32=0x158b23f6 -> be_crc32=0xe797c5c8
  [S1] KOF97_S1.ROM -> C:\Users\mimovr\Desktop\TEmp\REA\Fighter97\build\unpacked\s1.bin
       size=131072 B | bswap16=False | disk_crc32=0x8514ecf5 -> be_crc32=0x8514ecf5

=== Packed ROM Set into C:\Users\mimovr\Desktop\TEmp\REA\Fighter97\output\roms\kof97pls.zip ===
  [P1] 232-p1p.bin | size=1048576 B | bswap16=True | be_crc32=0x9e142f40 -> disk_crc32=0x7db81ad9
  [P2] 232-p2p.bin | size=4194304 B | bswap16=True | be_crc32=0xe797c5c8 -> disk_crc32=0x158b23f6
  [S1] 232-s1p.bin | size=131072 B | bswap16=False | be_crc32=0x8514ecf5 -> disk_crc32=0x8514ecf5

[SUCCESS] Baseline kof97pls.zip built and verified (100% lossless round-trip).

=== 68000 P1 Header & Key Logical Offsets ===
  Disk 0x000000..0x000007 : 100000f3c0000204
  68K  0x000000..0x000007 : 0010f30000c00402 (Initial SSP=0x0010F300, Initial PC=0x00C00402)
  Disk 0x000100 Signature : 'EN-OEG\x10' (454e2d4f4547104f)
  68K  0x000100 Signature : 'NEO-GEO' (4e454f2d47454f10)
  68K  0x000300 Code Cave : ffffffffffffffffffffffffffffffff
  68K  0x012020 Init Stat : 397c00670138397c0067013e397c00670146
  68K  0x01394E HP Sub    : 916c01386b00000c
  68K  0x01397E Guard Sub : 916c013e6b00000c
  68K  0x0139A4 Dizzy Sub : 916c01466b00000c
  68K  P2 0x2DC9F0 Iori A : 06504fd96fa65c73783125117fff2bac47783562535142415130402020004cdc
  S1   0x000000..0x000010 : 11111111111111111111111111111111
```

### 2. 原版 `kof97.ZIP` 与 `kof97pls.zip` 的 68000 大端空间 Diff 摘要
执行 `python tools/rom_tool.py diff` 实测输出：
- **P1 (`KOF97_P1.ROM` vs `232-p1p.bin`)**：共 3,890 字节差异（分布在 100 个连续区间）。其中 `0x000300..0x000532` 在原版 `KOF97_P1.ROM` 中为全 `0xFF` 空闲区（Code Cave），而在风云再起 `232-p1p.bin` 中被注入了 `4eb831f4...` 等选人解锁与无限气钩子代码。
- **P2 (`KOF97_P2.ROM` vs `232-p2p.bin`)**：仅 2 字节差异（`0x2C7000..0x2C7002`：原版 `ffff` vs 风云再起 `2003`）。
- **S1 (`KOF97_S1.ROM` vs `232-s1p.bin`)**：共 1,506 字节差异（`0x008000+` 固定层 UI 字模图元）。

### 3. WinKawaks 1.48 实机内存校验与运行截图证据
执行 `python tools/rom_tool.py verify-sandbox` 实测输出：

```text
=== Launching WinKawaks 1.48 Sandbox Verification ===
  [PASS] Main Window Handle : 0x008203F8 ("Kawaks 1.48 - The King of Fighters '97 Plus (bootleg)")
  [PASS] Loaded P1 ROM VA   : 0x0E851020
  [PASS] P1 0x000300 Bytes  : ffffffffffffffffffffffffffffffff (expected ffffffffffffffffffffffffffffffff)
  [PASS] Captured Screenshots (4): kof97pls000.png, kof97pls001.png, kof97pls002.png, kof97pls003.png
[SUCCESS] Sandbox real-machine verification completed with zero errors.
```

- **未决假设实测结论（回应 `DIR-001`）**：WinKawaks 1.48 在通过文件名回退加载 CRC32 改变的 `output/roms/kof97pls.zip` 时，**全程静默直通，无任何阻断或非阻断警告弹窗**（`WARNING: wrong CRC32` 仅在手动点击 `Tools -> Audit romsets` 时输出至审计文本）。
- **进程内存实锤**：在运行态 WinKawaks 进程内存 `0x0E851020` 处定位到已加载的 P1 ROM 缓冲区，核实偏移 `0x000300..0x00030F` 为 `ffffffffffffffffffffffffffffffff`（而非 `RomPath2\kof97pls.zip` 的 `b84ef431...`），100% 证明模拟器加载的是工作区 `output/roms/kof97pls.zip`。
- **实机运行截图文件（位于 `sandbox/capture/`）**：
  - [`sandbox/capture/kof97pls000.png`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/sandbox/capture/kof97pls000.png)：成功进入 KOF 97 片头动画（Terry Bogard 镜头，`PRESS 1P OR 2P BUTTON`）；
  - [`sandbox/capture/kof97pls001.png`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/sandbox/capture/kof97pls001.png)：按 1P Start 后进入 `MODE SELECT` 主菜单（`TEAM PLAY` / `SINGLE PLAY`）；
  - [`sandbox/capture/kof97pls002.png`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/sandbox/capture/kof97pls002.png)：进入 29 人选人面板（底部仅显示八神庵与矢吹真吾，无风云再起自带的隐藏 Boss 行，视觉实锤加载了由原版 `kof97.ZIP` 转换封装的 P1/P2/S1）；
  - [`sandbox/capture/kof97pls003.png`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/sandbox/capture/kof97pls003.png)：`ADVANCED / EXTRA` 模式选择与选人界面正常交互，无红屏、无黑屏、无贴图或音频异常。
