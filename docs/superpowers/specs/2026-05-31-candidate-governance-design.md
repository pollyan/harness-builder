# Candidate Governance MVP Design

## North Star Capability

本轮对应全景规划中的 Experience & Self-Improve、Maturity & Evolution、资产生成与审核接管能力。目标是补齐从 review-only asset candidates 到 Harness Maintainer 可审计采纳动作之间的最小闭环。

## Current State Gap Analysis

| 维度 | 目标态 | 当前已有 | 缺口 | 本轮判断 |
| --- | --- | --- | --- | --- |
| 产品能力 | Maintainer 能审查、采纳、废弃候选并接管 Harness | `improve`、`review-maturity`、`generate-asset-candidates`、`self-improve` 已生成 review-only 候选 | 候选停留在报告里，没有机器契约记录采纳决策 | 本轮优先 |
| 用户工作流 | 候选建议能转成正式 Harness 资产，且有审计链路 | README 说明候选不自动应用 | 没有 CLI 动作表达 accepted / deferred / rejected / applied | 本轮优先 |
| 智能化闭环 | LLM 生成候选，Python 做 schema、验证和可审计应用 | LLM asset candidate schema 已存在 | 没有 governance log、正式资产更新边界和 benchmark 校验 | 本轮优先 |
| 成熟度模型 | 采纳记录成为 Experience / maturity evidence | Experience index 统计 pending、review、asset candidate、runtime task-runs | 不统计候选治理决策 | 本轮纳入最小字段 |
| Runtime 分工 | Builder 不执行 task run，只维护 Harness 资产 | `.ai/task-runs` 明确由宿主 Runtime 生成 | 本轮不能新增 run 或 runtime 执行 | 保持边界 |
| 测试与 benchmark | 可选 review artifacts 存在时必须被 schema 和内容检查 | benchmark 已校验 maturity review / asset candidates / self-improve package | 不校验 candidate governance artifact | 本轮补齐 |

暂缓项：

- Runtime task-run semantic ingestion：价值高，但依赖宿主 Runtime artifact 样例，容易越界成执行器。
- Maturity Model v2：需要更大评分重构；没有候选采纳闭环时，评分更细也难转化为工作流价值。
- Workflow Toolkit 灵活组装：长期重要，但当前固定 workflow 候选先需要可审计采纳动作。

## Scope

新增 `review-candidate` CLI，读取 `.ai/review/asset-candidates.yaml`，对某个 asset candidate 写入 `.ai/review/candidate-governance.yaml` 和 `.ai/review/candidate-governance.md`。

支持决策：

- `accepted`：Maintainer 接受方向，但本次不修改正式资产。
- `deferred`：暂缓候选。
- `rejected`：废弃候选。
- `applied`：仅对 `guide` / `sensor` Markdown 候选，把候选 draft 追加到 `suggested_path` 指向的正式 `.ai/**/*.md` 资产，并记录 applied path。

不做的事：

- 不把 LLM 候选文件本身改成正式状态；候选报告仍保持 review-only。
- 不自动应用 workflow policy YAML 候选。`workflow_policy` 可记录为 accepted / deferred / rejected，应用留给后续更严格的结构化 patch 设计。
- 不创建 `.ai/task-runs`，不执行 Workflow Runtime。
- 不调用 LLM。

## Data Contract

新增 Pydantic schema：

- `CandidateGovernanceLog`
- `CandidateGovernanceDecision`

字段包含 candidate id、kind、suggested path、decision、rationale、reviewer、decided_at、source report、source candidate id、applied paths、acceptance checks、evidence sources。

Experience index 增加：

- `candidate_governance_decision_count`
- source kind `candidate_governance`

Maturity evidence 的 experience 摘要同步暴露该计数。

## Application Boundary

`applied` 只允许：

- `candidate.kind in {"guide", "sensor"}`
- `candidate.suggested_path` 必须在 `.ai/` 下
- 目标文件必须是 Markdown
- 写入内容用稳定 marker 包裹，避免重复应用同一个 candidate

重复应用同一 candidate 必须显式失败，不能静默跳过。

## Error Handling

必须显式失败：

- 缺少 `.ai/review/asset-candidates.yaml`
- candidate id 不存在
- decision 非允许值
- `applied` 指向 `.ai/` 外路径
- `applied` 指向非 Markdown 或非 guide/sensor 候选
- candidate 已经 applied

## Acceptance Criteria

- Unit：schema 能校验合法 governance log，拒绝非法 decision。
- Unit：`review_candidate(..., decision="applied")` 会追加正式 guide/sensor Markdown、写 governance YAML/MD、刷新 experience index。
- Unit：workflow policy candidate 执行 `applied` 明确失败，不修改正式 config。
- Integration：CLI `review-candidate` 生成 trace artifact，正式 guide 更新，原 asset candidate 仍是 `pending_harness_maintainer_review`。
- Benchmark：存在 governance artifact 时校验 schema、Markdown 章节、source candidate 引用、`.ai/` 路径边界和 applied path 存在。
- Docs：README、architecture、init workflow、sensor/gate rules 记录 review-candidate 的边界。

## Risks

- Markdown 追加不是长期最优 patch 机制；本轮只作为 guide/sensor MVP，workflow policy 后续需要结构化 patch。
- 自动化目标模式下没有人工确认；这里的“明确确认”由 CLI 显式 command + decision 参数表达，不由后台自动触发。
- applied 内容质量仍来自候选草案，本轮只提供可审计控制链，不宣称候选一定正确。
