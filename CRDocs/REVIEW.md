# 审查结论与问题清单 (CRDocs — TASK-ROM-002 Round 2)

- **Task ID**：`TASK-ROM-002`
- **Target**：动态内存与 Code Cave 核验（实机核验 1P/2P 结构体绝对内存映射、运行态数值流及 `0x000194..0x000800` Code Cave 边界）
- **Reviewer**：Argon
- **Review Round**：Round 2
- **Decision**：**APPROVED**（`P0: 0`, `P1: 0`, `P2: 1 [DEFERRED TO TASK-ROM-003]`；上轮 `[CR-001-P2-01]` 与 `[CR-001-P2-02]` 已核验闭环）

---

## 审查结论

经独立核查 [`tools/rom_tool.py`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/tools/rom_tool.py)、[`sandbox/launch_sandbox.bat`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/sandbox/launch_sandbox.bat)、`build/unpacked/p1_be.bin` 机器码反汇编、原生目录只读隔离性及实机对战截图（[`kof97pls013.png`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/sandbox/capture/kof97pls013.png)、[`kof97pls014.png`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/sandbox/capture/kof97pls014.png)），**`TASK-ROM-002`（阶段二：动态内存与 Code Cave 核验）100% 满足 `DIR-001` 与 [`Plan.md`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/Plan.md) 验收标准，予以通过（`APPROVED`）**。

### 独立核验清单与实测结果

1. **宿主目录只读安全与纯英文规范（100% 达标）**：
   - 独立复核 `C:\Program Files (x86)\KOF97\roms` 下 `kof97.ZIP`（`29,286,731 B`, `mtime=946656000.0`）、`kof97pls.zip`（`1,438,722 B`, `mtime=1075863528.0`）、`neogeo.zip`（`57,734 B`, `mtime=1036030632.0`），确认零写入、零改动。
   - 扫描 [`tools/rom_tool.py`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/tools/rom_tool.py)（37,942 B）与 [`sandbox/launch_sandbox.bat`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/sandbox/launch_sandbox.bat)（700 B），非 ASCII 字节数均为 `0`。
   - 本阶段未篡改 `build/unpacked/p1_be.bin` 与 `output/roms/kof97pls.zip` 静态基线数据，符合阶段二范围边界。

2. **上轮遗留项核查（全部闭环）**：
   - **`[CR-001-P2-02]` (`RESOLVED`)**：核查 [`sandbox/launch_sandbox.bat`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/sandbox/launch_sandbox.bat#L16-L21)，已移除失败后的裸 `WinKawaks.exe` 启动回退，改为显式输出 `[ERROR]` 并 `exit /b 1`。
   - **`[CR-001-P2-01]` (`RESOLVED`)**：[`verify_memory_and_cave`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/tools/rom_tool.py#L534-L593) 已集成对 `0x01394A`、`0x01394E`、`0x01397E`、`0x0139A4` 四处 4 字节指令及 `0x01388C`、`0x0138BC`、`0x0138EC` 三处 `CMPI.W #$0067` 恢复上限指令的自动化静态断言。

3. **68000 Code Cave 边界与指令流反汇编独立复核（100% 吻合）**：
   - 独立扫描 `build/unpacked/p1_be.bin` 确认：`0x000194..0x000800` 区间共 **1,644 字节**全部为 `0xFF`（前接 `0x000192` 处的异常返回指令 `4E 73` `RTE`，后接 `0x000800` 处的 `52 39 00 10` 代码段），`0x000300` 位于该纯净区核心且符合 68000 短绝对寻址（`$0000..$7FFF`）条件。
   - 独立反汇编 `0x00ED10..0x00ED50` 与 `0x013870..0x0139C0` 确认：
     - `0x00ED22: 3B 7C 00 67 02 38`（`MOVE.W #$0067, $0238(A5)`）与 `0x00ED28: 3B 7C 00 67 04 38`（`MOVE.W #$0067, $0438(A5)`）直接证实 `A5 = 0x108000` 时 1P 实血位于 `0x108238`（`A4 = 0x108100` + `$0138`）、2P 实血位于 `0x108438`（`A4 = 0x108300` + `$0138`）。
     - `0x013870..0x0138FE` 为每帧状态衰减/恢复子程序：`$013A(A4)`、`$0140(A4)`、`$0148(A4)` 每帧非零时执行 `SUBQ.W #1`（`53 6C`），而 `$0138(A4)`、`$013E(A4)`、`$0146(A4)` 在计时器触发时执行 `ADDQ.W #1`（`52 6C`）并由 `CMPI.W #$0067`（`0C 6C 00 67`）钳位在上限 `103`（`$0067`）。

4. **WinKawaks 1.48 Work RAM 动态数值流与视觉截图验证（100% 达标）**：
   - 复核 `0x00712688` Work RAM 宿主指针提取逻辑与小端字解包逻辑（[`verify_memory_and_cave`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/tools/rom_tool.py#L664-L723)）。
   - 审阅 [`sandbox/capture/kof97pls013.png`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/sandbox/capture/kof97pls013.png)（开局 1P 草薙京 vs 2P 安迪满血 `103/103` 对峙）与 [`sandbox/capture/kof97pls014.png`](file:///c:/Users/mimovr/Desktop/TEmp/REA/Fighter97/sandbox/capture/kof97pls014.png)（1P 打出 `COUNTER!!` 重拳命中 2P，画面出现受击白光火花且 2P 顶部血条右侧明显扣除一段绿色血量），与 Work RAM 实测数值（2P `HP: 103 -> 88`、`Guard: 103 -> 82`）完全对应。

---

## 问题清单 (P0 / P1 / P2)

本轮无 `P0` 或 `P1` 问题。新增 1 项面向阶段三（`TASK-ROM-003`）的 `P2` 实施指引：

### 1. `[CR-002-P2-01]` 阶段三（`TASK-ROM-003`）受创减半跳板优先切入点（`0x01394A` vs `0x01394E`）
- **级别**：`P2`（实施建议，不阻断当前阶段）
- **状态**：`DEFERRED`（供 `TASK-ROM-003` 直接采用）
- **位置**：`build/unpacked/p1_be.bin`（`0x01394A..0x013955` 及 `0x000300` Code Cave）
- **技术说明**：
  - 经反汇编 `0x013870..0x013955` 确认：`0x01394A` 处的 `ADD.W D0, $013A(A4)`（`D1 6C 01 3A`）负责向 UI 红血/延迟扣血计数器 `$013A(A4)` 累加本次伤害 `D0`，紧接着 `0x01394E` 处的 `SUB.W D0, $0138(A4)`（`91 6C 01 38`）从实血 `$0138(A4)` 扣除 `D0`，并由 `0x013952` 处的 `BMI.W $013960`（`6B 00 00 0C`）直接依据 `SUB.W` 的负数标志位 `N` 判定 KO。
  - **推荐实现**：在阶段三实施受创减半时，建议优先将 **`0x01394A`**（`D1 6C 01 3A`）替换为 `JSR ($0300).W`（`4E B8 03 00`，4B），并在 `0x000300` 处写入 8 字节序列：
    - `E2 40`（`LSR.W #1, D0`：先将伤害 `D0` 减半）
    - `D1 6C 01 3A`（`ADD.W D0, $013A(A4)`：将减半后的 `D0` 累加至红血计数器）
    - `4E 75`（`RTS`：返回 `0x01394E` 继续执行原生 `SUB.W D0, $0138(A4)` 与 `BMI.W $013960`）
  - **优势**：既保证 UI 红血动画增量（`$013A`）与实血扣减量（`$0138`）严格同步减半，又完全保留 `0x01394E` 原生 `SUB.W` 对 `0x013952` `BMI.W` 的标志位（CCR）传递链。
