# Workflow Policy Candidate Apply

## 问题

`review-candidate --decision applied` 当前只支持 Guide / Sensor Markdown 候选。`workflow_policy` 候选可以记录 `accepted` / `deferred` / `rejected`，但不能自动 patch `.ai/harness-config.yaml`。

## 当前现状

- `.ai/review/asset-candidates.yaml` 可以包含 `kind: workflow_policy` 的草案。
- `.ai/review/candidate-governance.yaml` 可以记录 Maintainer 对该候选的治理决策。
- 为避免无结构 YAML 覆盖风险，MVP 明确拒绝 `workflow_policy` 的 `applied`。

## 理想状态

为 workflow policy candidate 设计结构化 patch schema，例如新增、修改、禁用 routing rule，并通过 Pydantic、benchmark 和 integration 测试验证：

- patch 只能作用于 `.ai/harness-config.yaml` 的 `workflow_routing`。
- selected workflow、rule id、required guides/sensors 必须引用现有正式资产。
- 应用前后 benchmark `content:workflow-routing-policy` 和 `content:maturity-routing-evidence` 必须通过。
- 原始 candidate report 仍保持 review-only，正式应用只由 candidate governance 记录。

## 影响范围

- `docs/engineering/architecture.md`
- `docs/engineering/init-workflow.md`
- `docs/engineering/sensor-and-gate-rules.md`
- `src/harness_builder_agent/schemas/`
- `src/harness_builder_agent/tools/candidate_governance.py`
- `src/harness_builder_agent/tools/benchmark.py`
- integration / e2e tests

## 初步验收标准

- `workflow_policy` candidate 能以结构化 patch 形式应用到 `.ai/harness-config.yaml`。
- 非法 rule id、未知 workflow、`.ai/` 外路径和缺失 skill 引用必须失败。
- benchmark 能发现应用后 routing policy 与 maturity evidence 不一致。
