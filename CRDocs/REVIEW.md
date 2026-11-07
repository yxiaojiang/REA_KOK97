# 审查结论与问题清单 (CRDocs — TASK-ROM-003 Round 3)

- **Task ID**：`TASK-ROM-003`
- **Target**：P-ROM 静态数值与防御 Patch（实施免破防 `0x01397E`、免眩晕 `0x0139A4` 与 Code Cave `0x000300` 受创减半跳板，打包交付与实机对战验证）
- **Reviewer**：Argon
- **Review Round**：Round 3
- **Decision**：**APPROVED**（`P0: 0`, `P1: 0`, `P2: 1 [DEFERRED TO TASK-ROM-004]`；上轮 `[CR-002-P2-01]` 已圆满闭环）

---

## 审查结论

经独立核查 [`tools/rom_tool.py`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/tools/rom_tool.py)、[`output/roms/kof97pls.zip`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/output/roms/kof97pls.zip) 二进制全量 Diff、Motorola 68000 机器码编码、原生目录只读隔离性及实机对战截图（[`kof97pls018.png`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/sandbox/capture/kof97pls018.png)、[`kof97pls019.png`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/sandbox/capture/kof97pls019.png)），**`TASK-ROM-003`（阶段三：P-ROM 静态数值与防御 Patch）100% 满足 `DIR-001` 与 [`Plan.md`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/Plan.md) 验收标准，予以通过（`APPROVED`）**。

### 独立核验清单与实测结果

1. **宿主目录只读安全与纯英文规范（100% 达标）**：
   - 独立复核 `C:\Program Files (x86)\KOF97\roms` 下 `kof97.ZIP`（`29,286,731 B`, `mtime=946656000.0`）、`kof97pls.zip`（`1,438,722 B`, `mtime=1075863528.0`）、`neogeo.zip`（`57,734 B`, `mtime=1036030632.0`），确认零写入、零改动。
   - 扫描 [`tools/rom_tool.py`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/tools/rom_tool.py)（48,630 B）与 [`sandbox/launch_sandbox.bat`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/sandbox/launch_sandbox.bat)（700 B），非 ASCII 字节数均为 `0`。

2. **68000 机器码编码与全量二进制 Diff 独立核验（100% 精准）**：
   - 将 [`output/roms/kof97pls.zip`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/output/roms/kof97pls.zip) 与原版 `kof97.ZIP` 在 68000 Big-Endian 逻辑空间进行全量逐字节 Diff：
     - `232-p1p.bin`（1,048,576 B，磁盘 CRC32 `0xff227541`，68K 大端 CRC32 `0x21465f0a`）仅存在 **4 处精确改动（共 20 字节）**，其余 1,048,556 字节零漂移：
       1. `0x000300..0x000308`（8B）：`ffffffffffffffff` $\rightarrow$ `e248d16c013a4e75`
          - `E2 48`：Motorola 68000 标准 `LSR.W #1, D0`（Bits 4..3 = `01` 逻辑右移，精确纠正了早期文档中的算术右移 `E2 40` `ASR.W #1, D0`）；
          - `D1 6C 01 3A`：`ADD.W D0, $013A(A4)`（将减半后的 `D0` 累加至 UI 红血计数器）；
          - `4E 75`：`RTS`（返回 `0x01394E` 继续执行 `91 6C 01 38` `SUB.W D0, $0138(A4)` 与 `0x013952` `BMI.W $013960`）。
       2. `0x01394A..0x01394E`（4B）：`d16c013a` $\rightarrow$ `4eb80300`（`JSR ($0300).W` 短绝对跳板，圆满落实 `[CR-002-P2-01]`）。
       3. `0x01397E..0x013982`（4B）：`916c013e` $\rightarrow$ `4e714e71`（`NOP; NOP`，免破防）。
       4. `0x0139A4..0x0139A8`（4B）：`916c0146` $\rightarrow$ `4e714e71`（`NOP; NOP`，免眩晕）。
     - `232-p2p.bin`（磁盘 CRC32 `0x158b23f6`）与 `232-s1p.bin`（磁盘 CRC32 `0x8514ecf5`）与原版基线差异为 `0` 字节。

3. **实机对战数值与视觉截图核验（100% 达标）**：
   - 复核 [`verify_defense_execution`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/tools/rom_tool.py#L787-L935) 实测结果：2P 受创单发重拳掉血由原版 15 点降至 `6~7` 点（`HP: 103 -> 96~97`），1P/2P 破防槽（`Guard = 103/103`）与眩晕槽（`Dizzy = 103/103`）全程恒定满值。
   - 审阅 [`sandbox/capture/kof97pls018.png`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/sandbox/capture/kof97pls018.png) 与 [`kof97pls019.png`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/sandbox/capture/kof97pls019.png)，画面打击火花清晰，顶部 2P 血条右侧削减幅度仅为阶段二基线截图 [`kof97pls014.png`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/sandbox/capture/kof97pls014.png) 的一半，UI 血条动画正常无撕裂。

---

## 问题清单 (P0 / P1 / P2)

本轮无 `P0` 或 `P1` 问题。上轮 `[CR-002-P2-01]` 已标记为 `RESOLVED`。
为确保下一阶段 `TASK-ROM-004`（八神庵黑金调色板换肤）一次命中真实角色配色，Argon 预先对 `P1.ROM` 调色板索引表与 `P2.ROM` 调色板主表进行了交叉反汇编，记录 1 项 `P2` 实施指引：

### 1. `[CR-003-P2-01]` 阶段四（`TASK-ROM-004`）八神庵真实角色 ID（`0x1B`）与 A 键调色板物理偏移校准（`0x2DF7F0` vs `0x2DC9F0`）
- **级别**：`P2`（阶段四前置关键发现，不阻断 `TASK-ROM-003`）
- **状态**：`DEFERRED`（供 `TASK-ROM-004` 直接采用）
- **位置**：`build/unpacked/p1_be.bin`（`0x004798..0x004920`）、`build/unpacked/p2_be.bin`（`0x2CFFF0+`）
- **独立反汇编发现**：
  1. 经反汇编 `P1.ROM` `0x004798..0x00483E` 角色调色板加载器：
     - `0x004798: MOVE.W $0070(A4), D0` 读取角色 ID，经 `LSL.W #3, D0`（每角色 8 字节 = A/B/C/D 四个 16-bit 调色板编号）后，以 **`0x00483E`** 为基址（`0x00483E` 处首字为草薙京 A 键 `0x0100`）查表，再由 `0x004AD4: LEA $002CFFF0, A1` 按 `0x2CFFF0 + PalID * 32` 定位 `P2.ROM` Bank 2 物理偏移。
  2. 核对角色 ID 与调色板编号映射：
     - 早期文档中的 `CharID = 0x18`（24）实为 `'97 特别队` 的**山崎龙二（Ryuji Yamazaki）**（A 键 `0x0640` 位于 `0x2DC7F0`，B 键 `0x0650` 位于 `0x2DC9F0`，其颜色为深绿外套+白衬衣）；
     - **八神庵（Iori Yagami）的真实 `CharID` 为 `0x1B`（27）**！其在 `P1.ROM` `0x004916`（`0x00483E + 0x1B * 8`）处的 4 键调色板编号为：
       - **A 键：`0x07C0` $\rightarrow$ `P2.ROM` 物理偏移 `0x2DF7F0`**（`0x2CFFF0 + 0x07C0 * 32`）
       - **B 键：`0x07D0` $\rightarrow$ `P2.ROM` 物理偏移 `0x2DF9F0`**
       - **C 键：`0x07E0` $\rightarrow$ `P2.ROM` 物理偏移 `0x2DFBF0`**
       - **D 键：`0x07F0` $\rightarrow$ `P2.ROM` 物理偏移 `0x2DFDF0`**
  3. 核对 `P2.ROM` **`0x2DF7F0`**（`hdr=0x07C0`，32 字节）的 16 色解码结果，100% 吻合八神庵经典 A 键外观：
     - `Word #01..#04`：肤色渐变（`#F8F0B0`, `#F0C080`, `#E89058`, `#B05028`）；
     - `Word #05..#07`：白色衬衣（`#F0F0F8`, `#B8B8C0`, `#707880`）；
     - **`Word #08..#11`：经典酒红头发与红裤子（`#D83820`, `#A82810`, `#781808`, `#480000`）**；
     - **`Word #12..#15`：深藏青/紫黑风衣（`#383848`, `#282838`, `#181828`, `#000008`）**；
     - 此外，同块内的 `0x07C3`（`0x2DF850`）为受击/闪光辅色，`0x07C6`（`0x2DF8B0`）为紫炎特效，`0x07CD..0x07CF`（`0x2DF990..0x2DF9EF`）为胜利立绘、选人头像与顶部 HUD 小头像调色板。
  4. **阶段四实施建议**：在 `TASK-ROM-004` 实施八神庵黑金换肤时，请将主修改目标对准真实的八神庵 A 键调色板 **`0x2DF7F0`（`0x07C0`，以及可选同步 `0x07C3`/`0x07CD..0x07CF` 头像或兼容修改 `0x2DC9F0`）**，并在实机中选择八神庵（或通过选人/对战界面）验证黑金换肤效果！
