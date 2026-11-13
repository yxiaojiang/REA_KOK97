# Rules.md — 项目记忆与协作规则（KOF97 逆向魔改工程）

## 记忆结构

| 文件 | 用途 | 启动时是否读取 |
| :--- | :--- | :--- |
| `SessionBrief.md` | 当前目标、风险、下一步、模块索引；保持 800~1500 中文字 | **是** |
| `Plan.md` | 仅当前 1~3 个活跃事项（当前推进或待交接的任务） | **是** |
| `PlanDocs/` | 方向、顺序和验收口径的方案讨论与交接（供 Argon 审核） | 否；`STATUS.md` 不是 `IDLE` 时读 |
| `CRDocs/` | 代码与 ROM 数据 Patch 的审查与实施交接（供 Argon 审核） | 否；`STATUS.md` 不是 `IDLE` 时读 |
| `ProjectMemory.md` | 稳定架构、68000 硬件规范、内存映射基线、硬约束；保持精简 | 否，涉及全局设计时读 |

## 会话开始与按需加载

1. 每个任务开始前先读取 `.claude/SessionBrief.md` 与 `.claude/Plan.md`。若 `PlanDocs/STATUS.md` 不是 `IDLE`，接着读 `PlanDocs/README.md`、`STATUS.md` 和 `PROPOSAL.md`。若 `CRDocs/STATUS.md` 不是 `IDLE`，接着读 `CRDocs/` 相应文件。
2. 再按任务选择上下文：
   - **ROM 逆向与数值分析**：读取 `Docs/KOF97_ROM_Hacking_Architecture_and_Workflow.md`。
   - **历史追溯**：仅按需查阅归档文件，不要整目录无脑加载大文件。

---

## 上下文压缩（对标 Codex 的 90% → 10%）

对话可能被宿主自动截断，本项目用 `.claude/` 记忆文件做持久化工作记忆，不以聊天全文为长期记忆。

触发任一条件即先压缩、再继续当前任务：
1. 用户说“压缩上下文”或“保存记忆”。
2. 本轮对话显著变长（长审核、多文档对比、多文件实现）。
3. 即将开始下一段独立工作或交接给审核方 **Argon**。

压缩步骤（刷新，不追加）：
1. 把**当前目标、未关闭风险、关键约束、下一步**写入 `SessionBrief.md`，保持 800～1500 中文字。
2. `Plan.md` 只留仍在进行的 1～3 项。
3. 压缩完成后从 `SessionBrief.md` 的「下一步」接着执行。

---

## 双角色（Antigravity 执行 / Argon 审核）协作与工程约束

- **PlanDocs 计划讨论交接（强制规程）**：
  - 工程根目录 `PlanDocs/` 是讨论方案方向、修改顺序和验收口径的唯一交接区。
  - **角色分工**：
    - `PROPOSAL.md`：只由提案方（Antigravity）填写，遵循固定标题。
    - `REVIEW.md`：只由审核方（Argon）填写，遵循固定标题，同意也要指出核对过的文件。
    - `STATUS.md`：由当前交棒方更新状态（`IDLE` / `PROPOSING` / `READY_FOR_REVIEW` / `CHANGES_REQUESTED` / `CONVERGED` / `ADOPTED` / `BLOCKED`）。
    - `DECISIONS.md`：用户/Argon 确认收口后追加短决定，写回 `.claude/Plan.md` 与 `Plan.md`。
    - `YYYY-MM-DD_<DIR-ID>_<TaskID>.md`：讨论收敛（`CONVERGED -> ADOPTED`）收口时，必须将本话题完整多轮讨论过程（各轮 `PROPOSAL` 与 `REVIEW`）按日期命名归档在 `PlanDocs/` 目录下，再重置活跃交接文件，以便日后复盘。
  - **用户最简交互**：
    - 对提案方：`读取 PlanDocs，把这件事写成提案并交接。`
    - 对审核方：`读取 PlanDocs，独立审核这一轮提案。`
    - 审核意见处理：`读取 PlanDocs，按 REVIEW.md 修正提案并交接。`
    - 确认收口：`读取 PlanDocs，讨论已收敛，按日期归档讨论过程，写入决定并更新计划。`

- **CRDocs 代码与 Patch 审查交接（强制规程）**：
  - 工程根目录 `CRDocs/` 是执行者与审核者之间唯一的代码与二进制修改交接区。
  - `IMPLEMENTATION.md` 由执行者填写，记录实际修改、未改项及验证证据（严禁把“已修改”当作“已验证”）。
  - `REVIEW.md` 由审核者填写，将问题按 `P0` 阻断、`P1` 必修、`P2` 延期记录，标记 `OPEN` / `RESOLVED` / `DEFERRED` / `WONT_FIX`。

- **KOF97 逆向与工程红线约束**：
  1. **原始文件安全隔离**：严禁直接在 `C:\Program Files (x86)\KOF97\roms` 原始文件上原地写覆盖！所有解包、分析、Patch 必须在工作区独立目录操作，测试时以副本或独立 Hack 包导入。
  2. **大端序（Big Endian）与总线对齐**：Motorola 68000 是纯大端序架构，字（Word, 16位）与长字（Long, 32位）访问必须偶数地址对齐，任何数值修改严禁破坏指令长度与对齐约束。
  3. **校验和与保护机制**：Neo-Geo MVS / WinKawaks 拥有程序 ROM 校验机制（Checksum），静态 Patch 必须同步处理或绕过自检，防止模拟器报红屏或非法指令崩溃。
  4. **脚本纯英文规范**：新建任何 Python、批处理脚本或工具链源码中，注释与变量命名必须 100% 全英文，杜绝 Windows 编码乱码。
  5. **回答前保持独立判断**：指出真实机器码、硬件架构与算法边界，严禁臆测数据偏移，凡未核实的内存地址与数据表必须明确标注为“待动态验证”。
