# 计划讨论交接 (PlanDocs)

本目录是当前工作模型（Antigravity）与审核方（Argon）讨论**方案方向、实现顺序和验收口径**时的唯一交接区。代码与二进制修改的审核走 `CRDocs/`。技术全景方案存放于 `Docs/`。

双方开始前先读本文件与 `STATUS.md`。提案方（Antigravity）写 `PROPOSAL.md`。审核方（Argon）写 `REVIEW.md`。

## 角色职责

### 提案方（Antigravity）
1. 将要决定的技术方案与实施路径写成 `PROPOSAL.md`。
2. 收到审核后，只改 `PROPOSAL.md`。每一条审核意见标明 `采纳`、`部分采纳` 或 `不采纳`，并给出证据。
3. 写完把 `STATUS.md` 改为 `READY_FOR_REVIEW`，交接给 Argon。
4. 不得擅自修改 `REVIEW.md` 与 `DECISIONS.md`。

### 审核方（Argon）
1. 依据 `PROPOSAL.md` 与 `Docs/` 文档进行独立审核。
2. 核对真实文件、硬件边界与架构规范，指出事实错误、顺序隐患或风险遗漏。
3. 结论写入 `REVIEW.md`，使用固定标题。
4. 只有下一件工作会因此做错时，才要求改顺序。
5. 结论输出 `CHANGES_REQUESTED`、`CONVERGED` 或 `BLOCKED`。

## 状态流转
```text
IDLE
  → PROPOSING
  → READY_FOR_REVIEW
  → CHANGES_REQUESTED → PROPOSING（下一轮）
  → CONVERGED
  → ADOPTED
  → IDLE
```

## 文件所有权
| 文件 | 谁写 | 用途 |
|---|---|---|
| `README.md` | 用户固定 | 协作规则 |
| `STATUS.md` | 当前交棒方 | 话题、轮次、状态 |
| `PROPOSAL.md` | 提案方 (Antigravity) | 方案提案正文 |
| `REVIEW.md` | 审核方 (Argon) | 独立审核意见 |
| `DECISIONS.md` | 确认收口方 | 已采纳决定的短记录 |
| `YYYY-MM-DD_<DIR-ID>_<TaskID>.md` | 确认收口方 | 按日期归档当次完整多轮讨论过程（PROPOSAL + REVIEW），供日后复盘 |

## 讨论过程按日期归档规则（强制复盘留痕）

1. 当某一话题完成多轮审核并输出 `CONVERGED`、用户确认收口后：
   - 先将该话题自 Round 1 至最终收敛轮的完整讨论过程（每轮 `PROPOSAL` 核心内容与建议、每轮 `REVIEW` 核对结论、遗留备忘与收敛意见）整理归档至 **`PlanDocs/YYYY-MM-DD_<DIR-ID>_<TaskID>.md`**（如 `PlanDocs/2026-11-13_DIR-003_TASK-STUDIO-020.md`；若同日多话题可附加短后缀区分）。
   - 再将精炼后的正式决定追加写入 `DECISIONS.md`（并附上该按日期归档文件的链接），更新 `STATUS.md` 为 `IDLE`，随后将 `PROPOSAL.md` 与 `REVIEW.md` 重置为待新话题占位状态。
2. 历史追溯与工程复盘时，只需按日期文件名打开对应归档文件即可完整回看“为什么这么改、审出了什么坑、怎么修正收敛”，无需污染 `PROPOSAL.md`/`REVIEW.md` 或翻找聊天记录。

## 提案固定标题
```text
## 要决定的问题
## 建议决定
## 证据
## 未核实
## 建议顺序
## 明确不做
## 对上一轮审核的处理
```

## 审核固定标题
```text
## 本轮核对了什么
## 属实
## 不成立或说重了
## 遗漏
## 顺序
## 未核实
## 结论
```
