# Workflow 推荐到 Routing Policy 生命周期设计

## 背景

North Star 要求 Workflow Runtime Specification 能根据任务类型、风险等级和历史经验持续调整执行策略；Experience & Self-Improve 应生成可审查的 Workflow 更新候选，并通过人工确认进入正式 Harness。

当前代码已经具备分段能力：

- `recommend-workflow` 生成 review-only `.ai/review/workflow-routing-recommendation.*` 和历史索引。
- `improve` 会把 workflow recommendation 计数转成 `workflow_policy_update` 改进候选。
- `review-maturity` 可对该候选给出 support / revise / defer 判断。
- `generate-asset-candidates` 的 prompt 和 schema 支持 `workflow_policy` 候选与结构化 `workflow_policy_patch`。
- `review-candidate --decision applied` 能按结构化 patch 更新 `.ai/harness-config.yaml`，并记录 candidate governance。

缺口是：这些能力主要分段测试，缺少一条可验收的端到端用户故事，证明一次 recommendation 能进入 policy candidate、被治理应用、被 maturity evidence 和 benchmark 识别。同时 `generate-asset-candidates` 写入 asset candidates 和 Experience index 后，没有立即刷新 maturity evidence，也没有在 CLI trace 中记录 `.ai/experience/experience-index.yaml`。

## Current State Gap Analysis

候选 gap 排序结果：

1. Workflow recommendation 到 routing policy lifecycle：已有智能推荐与候选应用骨架，但缺少纵向闭环和派生证据同步。
2. Self-improve package consumption：需要让下一轮 self-improve 消费已有 package / governance 状态。
3. Acceptance efficiency matrix：可降低循环成本，但产品价值间接。
4. 过程文档中文 gate：保护执行质量，但不直接推进 North Star 能力。

本轮选择第 1 项，因为它直接连接 Workflow Toolkit、Experience / Self-Improve、Maturity & Evolution 和 Governance。

## 工程信任故事

作为 Harness Maintainer，当我先为一个真实任务生成 review-only workflow recommendation，再运行自改进相关命令时，我可以得到一个带结构化 `workflow_policy_patch` 的 routing policy 候选，并通过显式 `review-candidate --decision applied` 把它应用到 `.ai/harness-config.yaml`，随后 benchmark 能验证候选、治理记录和正式 routing policy 一致，从而确信智能推荐不会停留在孤立报告，也不会绕过人工治理直接改正式资产。

## 设计决策

- 不新增命令；复用现有专家命令链路：`recommend-workflow -> improve -> review-maturity -> generate-asset-candidates -> review-candidate applied -> benchmark`。
- `recommend-workflow`、`review-maturity` 和 `generate-asset-candidates` 仍保持 review-only，不应用正式资产。
- 正式 `.ai/harness-config.yaml` 只由 `review-candidate --decision applied` 基于结构化 `workflow_policy_patch` 修改。
- `generate-asset-candidates` 写出 review-only candidates 后，必须刷新 `.ai/experience/experience-index.yaml`，并重新生成 `.ai/maturity-score.yaml` / `.ai/maturity-evidence.yaml`，让 asset candidate 计数和 workflow policy candidate 立即进入后续 maturity / triage / benchmark 证据面。
- CLI trace 必须记录 `experience-index.yaml`、`maturity-score.yaml` 和 `maturity-evidence.yaml`，否则调试时看不到该命令更新了派生证据。
- `workflow_policy` candidate 只有在 `source_review_decision` 为 `support` 或 `revise` 时可以 applied；`defer` / `missing` 只能记录治理决策，不能修改正式 routing policy。
- workflow policy upsert 必须保持既有 routing rule 的相对顺序；替换已有 rule 时原位替换，新增 rule 才追加，避免未来 Runtime 按 first-match 执行时被意外改变优先级。
- asset candidate parser 必须拒绝 `.ai/../...` 这类路径穿越；`workflow_policy` 的 `suggested_path` 必须是 `.ai/harness-config.yaml`。

## 可执行验收标准

- 集成测试使用 mock LLM 跑通完整链路：
  - `recommend-workflow` 生成 pending recommendation，且不创建 `.ai/task-runs`。
  - `improve` 生成 `experience-workflow-recommendation-review`。
  - `review-maturity` 支持该候选。
  - `generate-asset-candidates` 生成 `workflow_policy` candidate，含 `workflow_policy_patch`。
- 生成 asset candidates 后，maturity evidence 中 `experience.asset_candidate_count == 1`。
- `review-candidate --decision applied` 更新 `standard-escalation` routing rule，并记录 governance applied path。
- `workflow_policy` defer / missing 候选不能被 applied。
- workflow policy upsert 替换 `standard-escalation` 时保持 rule 顺序。
- LLM asset candidate parser 拒绝路径穿越和非 `harness-config.yaml` 的 workflow policy target。
- `benchmark` 中 `content:workflow-routing-policy` 通过。
- 非目标：不让 guided `init` 直接应用 workflow policy；它仍提示使用专家命令。
- 非目标：不从 `draft_content` 推断 YAML patch。
- 非目标：不执行 Runtime、不生成 `.ai/task-runs`。

## Assumptions / Risks

- 假设 LLM asset candidate 在真实环境中可能输出不同的 routing patch；parser、schema 和 benchmark 负责兜底。
- 风险：把 recommendation 当成已应用 policy。回应：recommendation、maturity review、asset candidates 都保持 `pending_harness_maintainer_review`；只有 governance applied 才修改正式 config。
- 风险：刷新 maturity evidence 被误解为正式应用候选。回应：maturity evidence 只记录 review-only asset candidate 计数和来源，不改变 routing policy。
