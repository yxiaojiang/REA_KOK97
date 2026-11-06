# Plan.md — KOF97 逆向魔改工程活跃计划

## 活跃任务（已进入第 1 阶段实施）

1. **[TASK-ROM-001] 工具链构建与沙盒最小加载闭环（当前实施阶段，P0）**
   - 目标：编写 `tools/rom_tool.py`（支持 `bswap16` 转换）、建立 `sandbox/` 独立配置与双 RomPath 脚本，生成 `output/roms/kof97pls.zip`（内含原版提取的 `232-p1p.bin`、`232-p2p.bin`、`232-s1p.bin`），在 WinKawaks 1.48 中跑通最小实机加载闭环。
   - 审查流：`CRDocs`（由 Antigravity 实施，Argon 独立审核）。
   - 状态：**READY_FOR_REVIEW**（已完成工具链、沙盒实机验证与截图存证，已提交 `CRDocs/IMPLEMENTATION.md` 与 `CRDocs/STATUS.md`，等待 Argon Round 1 审查）。

2. **[TASK-ROM-002] 动态内存与 Code Cave 核验（下一阶段，P0）**
   - 目标：实机核验 1P 角色结构体（HP、破防、眩晕）数值流与 `0x000300+` 安全注入边界。
   - 前置依赖：`TASK-ROM-001` 取得 `APPROVED`。

3. **[TASK-ROM-003] P-ROM 静态数值与防御 Patch（P1）**
   - 目标：实施免疫破防（`0x013980: NOP`）、免疫眩晕（`0x0139A6: NOP`）与受创减半（`0x01394E: LSR.W #1, D0`）。
   - 前置依赖：`TASK-ROM-002`。
