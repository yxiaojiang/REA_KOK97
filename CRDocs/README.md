# 执行者–审核者 代码与 Patch 协作机制 (CRDocs)

本目录是执行者（Executor，Antigravity）与审核者（Reviewer，Argon）之间唯一的代码修改与二进制 Patch 交接区。

## 角色分工

### 执行者（Executor，Antigravity）
1. 读取 `STATUS.md` 和 `REVIEW.md`。
2. 处理 `REVIEW.md` 中属于当前阶段且处于 `OPEN` 状态的问题。
3. 执行代码编写、ROM 二进制修改，并在 WinKawaks/模拟器或自动化测试中严格验证。
4. 将本轮实际修改、未修改项及测试证据写入 `IMPLEMENTATION.md`（严禁把“已修改”当作“已验证”）。
5. 把 `STATUS.md` 更新为 `READY_FOR_REVIEW`，交接给 Argon。
6. 不得擅自编辑 `REVIEW.md` 中的审核者结论。

### 审核者（Reviewer，Argon）
1. 读取 `STATUS.md` 和 `IMPLEMENTATION.md`。
2. 独立核查实际代码 diff、68000 汇编指令对齐、大端序数值正确性及模拟器运行情况。
3. 将问题按严重度写入 `REVIEW.md`：
   - `P0` 阻断级（模拟器崩溃、红屏死机、校验和失败、非法内存访问）。
   - `P1` 核心功能缺陷（数值未生效、角色动作卡死、调色板颜色溢出错位）。
   - `P2` 次要优化（微小色阶差异、辅助脚本便利性）。
4. 已解决问题标为 `RESOLVED`；当前通过则将 `STATUS.md` 更新为 `APPROVED`。

## 状态流转
```text
IDLE
  → IMPLEMENTING
  → READY_FOR_REVIEW
  → CHANGES_REQUESTED → IMPLEMENTING（下一轮）
  → APPROVED
```

## 文件所有权
| 文件 | 主要写入者 | 用途 |
|---|---|---|
| `README.md` | 用户固定 | 固定协作规则 |
| `STATUS.md` | 当前交棒方 | 当前任务与状态 |
| `IMPLEMENTATION.md` | 执行者 (Antigravity) | 实现细节与验证证据 |
| `REVIEW.md` | 审核者 (Argon) | 审查结论与问题清单 |
| `DEFERRED.md` | 审核者 | 延期到后续阶段的问题 |
