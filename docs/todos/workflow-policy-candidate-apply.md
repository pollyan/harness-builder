# Workflow Policy Candidate Apply

## 完成状态

已完成第一版实现，并归档到 `docs/todos/archive.md`。本文保留问题背景，方便后续回溯。

## 问题

`review-candidate --decision applied` 原来只支持 Guide / Sensor Markdown 候选。`workflow_policy` 候选可以记录 `accepted` / `deferred` / `rejected`，但不能自动 patch `.ai/harness-config.yaml`。

## 已实现现状

- `.ai/review/asset-candidates.yaml` 可以包含 `kind: workflow_policy` 的草案。
- `workflow_policy` candidate 必须携带结构化 `workflow_policy_patch`，自由文本 `draft_content` 只作为人类说明。
- `.ai/review/candidate-governance.yaml` 可以记录 Maintainer 对该候选的治理决策。
- `review-candidate --decision applied` 能通过 `WorkflowPolicyPatch` upsert `.ai/harness-config.yaml` 的 routing rule，并刷新 `.ai/maturity-score.yaml` 与 `.ai/maturity-evidence.yaml`。

## 实现边界

- patch 只能作用于 `.ai/harness-config.yaml` 的 `workflow_routing.rules`。
- selected workflow、rule id、required guides/sensors 必须引用现有正式资产。
- `standard-escalation` 必须保留核心 escalation triggers 和 human confirmation。
- 原始 candidate report 仍保持 review-only，正式应用只由 candidate governance 记录。

## 影响范围

- `docs/engineering/architecture.md`
- `docs/engineering/init-workflow.md`
- `docs/engineering/sensor-and-gate-rules.md`
- `src/harness_builder_agent/schemas/workflow_policy_patch.py`
- `src/harness_builder_agent/tools/candidate_governance.py`
- `src/harness_builder_agent/tools/benchmark.py`
- integration / e2e tests

## 验收标准

- `workflow_policy` candidate 能以结构化 patch 形式应用到 `.ai/harness-config.yaml`。
- 非法 rule id、未知 workflow、`.ai/` 外路径和缺失 guide/sensor 引用必须失败。
- benchmark 能发现应用后 routing policy 与 source candidate patch 不一致。
