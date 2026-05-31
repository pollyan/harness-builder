# Workflow Policy Candidate Apply Design

## North Star Capability

本轮对应 Experience & Self-Improve、Workflow Toolkit Evolution、资产生成与审核接管能力。目标是让 Harness Maintainer 能把已审核的 `workflow_policy` asset candidate 以结构化、可验证、可审计的方式应用到正式 `.ai/harness-config.yaml`，继续补齐“智能建议 -> 治理决策 -> 正式 Harness 资产 -> benchmark 验证”的闭环。

## Current State Gap Analysis

| 维度 | 目标态 | 当前已有 | 缺口 | 本轮判断 |
| --- | --- | --- | --- | --- |
| 产品能力 | Workflow policy 候选可被明确采纳并进入正式 Harness | `review-candidate` 已记录 accepted/deferred/rejected/applied；Guide/Sensor Markdown 可 applied | `workflow_policy` applied 被拒绝，只能停留在 accepted | 本轮优先 |
| 用户工作流 | Maintainer 不需要手工编辑 YAML 即可应用一个安全 routing rule patch | governance log、benchmark 和 routing policy check 已存在 | 缺少结构化 patch schema 和应用器 | 本轮优先 |
| 智能化闭环 | LLM 产出候选，Python 只接受 schema-valid patch 并验证正式契约 | `llm_asset_candidate_v2` 能生成 workflow_policy draft | draft_content 只是自由文本 YAML snippet，不能安全应用 | 本轮优先 |
| Benchmark / Review Intelligence | 应用后 benchmark 能证明 routing policy 和 maturity evidence 一致 | 已有 `content:workflow-routing-policy`、`content:maturity-routing-evidence`、`content:candidate-governance` | governance 不检查结构化 workflow patch，应用后未刷新 maturity evidence | 本轮补齐 |
| Runtime 边界 | Builder 只更新项目级 Harness 策略，不执行任务 | 当前无 `run` 命令，不创建 `.ai/task-runs` | 本轮不得执行 workflow recommendation 或 task runtime | 保持边界 |

暂缓项：

- Runtime task-run ingestion：仍依赖宿主 Runtime artifact 语义样例，风险更大。
- Maturity Model v2：评分重构范围较大，本轮先让 workflow 改进能进入正式资产。
- 多操作 patch（delete/disable/reorder/default workflow）：容易扩大为配置迁移系统；本轮只做 `upsert_routing_rule`。

## Design

新增机器契约 `WorkflowPolicyPatch`。它作为 `AssetCandidateDraft.workflow_policy_patch` 的结构化字段出现；`draft_content` 仍可作为人类可读说明，但不作为机器应用来源：

```yaml
schema_version: "1.0"
operation: upsert_routing_rule
target: workflow_routing.rules
rule:
  id: standard-escalation
  selected_workflow: standard
  rationale: ...
  task_type_hints: [...]
  triggers: [...]
  required_guides: [...]
  required_sensors: [...]
  human_confirmation_required: true
```

`review-candidate --decision applied` 遇到 `candidate.kind == "workflow_policy"` 时：

1. 要求 `candidate.suggested_path == ".ai/harness-config.yaml"`。
2. 要求 `candidate.workflow_policy_patch` 存在，并通过 `WorkflowPolicyPatch` schema 校验。
3. 只允许 `operation: upsert_routing_rule` 和 `target: workflow_routing.rules`。
4. 校验 `selected_workflow` 已存在于 `harness-config.yaml`。
5. 校验 `required_guides` 和 `required_sensors` 都是存在的 `.ai/` 正式资产。
6. 按 rule id 替换已有 routing rule 或追加新 rule。
7. 重新校验 `HarnessConfig` 和 routing policy 不变式：默认 workflow 仍为 `lightweight`，必需基础规则仍存在，`standard-escalation` 仍保留关键触发条件和 human confirmation。
8. 写回 `.ai/harness-config.yaml`。
9. 写入 candidate governance log，刷新 Experience index，并重新评估 maturity assets 让 `.ai/maturity-evidence.yaml` 与 config 同步。
10. `benchmark` 在已有 `.ai/` Harness 上运行时不得重写正式资产；它应验证当前资产状态，避免把刚应用的 routing policy 覆盖回默认值。

## Decisions

- 不支持删除规则、禁用规则或修改 default workflow；这些属于后续更大配置治理。
- 不从自由文本 `draft_content` 中推断 patch。LLM 如果没有输出合法 `workflow_policy_patch`，应用必须显式失败。
- 原始 `.ai/review/asset-candidates.yaml` 仍保持 review-only，不把 candidate status 改成 applied。
- 应用 workflow policy 不执行 `recommend-workflow`，也不创建 `.ai/task-runs`。

## Acceptance Criteria

- Unit：`WorkflowPolicyPatch` schema 接受合法 `upsert_routing_rule`，拒绝未知 operation / target。
- Unit：`review_candidate(... decision="applied")` 能应用 workflow_policy patch 到 `.ai/harness-config.yaml`，并记录 governance / refresh maturity evidence。
- Unit：非法 workflow、缺失 guide/sensor 引用、`.ai/` 外引用、破坏 required standard escalation 的 patch 必须显式失败且不改写 config。
- Integration：CLI `review-candidate --decision applied` 可应用 workflow policy candidate，trace 记录 governance、experience index、maturity assets。
- Benchmark：应用后的 `content:workflow-routing-policy`、`content:maturity-routing-evidence`、`content:candidate-governance` 均通过，且 benchmark 不覆盖已有 `.ai/harness-config.yaml`。
- Prompt：`llm_asset_candidate_v2` 明确要求 workflow_policy 候选提供结构化 `workflow_policy_patch`；`draft_content` 只保留人类说明。
- Docs：README、architecture、init workflow、sensor/gate rules、todo/evolution log 同步更新。

## Risks

- LLM 真实输出可能仍给自由文本 draft；这是应显式失败的 contract violation，不做 fallback。
- Routing policy 不变式与 benchmark 存在重复校验；本轮接受少量重复，以避免应用后生成必然失败的正式配置。
- Upsert 可能覆盖现有 rule 字段；这是显式 candidate governance 动作，必须有 rationale 和 governance log。
