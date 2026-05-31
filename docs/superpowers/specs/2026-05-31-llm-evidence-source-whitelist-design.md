# LLM Evidence Source Whitelist Hardening Design

## 背景

上一轮目标模式回顾发现，多个 LLM review-only 产物虽然要求 `evidence_sources` 使用 `.ai/` 路径，但并未统一验证这些路径是否来自提供给 LLM 的 evidence source map、maturity inputs、Experience sources 或上游候选的 evidence sources。

这会削弱 Experience & Self-Improve 的可审查性：模型可以返回 `.ai/review/fake.yaml` 这类看似在 Harness 内、实际不可追溯的路径，后续 maturity review、asset candidates 或 benchmark 仍可能接受。

North Star 要求 Experience / Self-Improve 产物“可审查、可版本化、可反哺 Harness”，正式规则修改必须可追溯。证据路径白名单是该闭环的基础防线。

## Current State Gap Analysis

| 候选 gap | 目标态要求 | 当前能力 | 缺口 | 用户 / 工程价值 | 风险 / 复杂度 | 可测试性 | 本轮决策 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LLM evidence source 白名单 | LLM review-only 产物只能引用已提供或结构化可追溯的证据路径 | Experience summary parser 已校验 unknown sources；其它 parser 多为 `.ai/` 前缀校验 | workflow recommendation、maturity review、asset candidates 可引用未知 `.ai/` 路径 | 提升智能候选可信度，防止幻觉证据进入自改进闭环 | 中等，需跨 3 个 LLM 工具和 benchmark | unit + benchmark integration | 本轮实现 |
| guided apply diff / summary | guided init 可安全应用候选前展示 diff | standalone applied 已存在，guided 仍 review-only | 用户仍要使用专家命令 | 用户体验强 | 高，涉及正式资产修改 | integration + snapshot | 暂缓 |
| recommendation history | 多次 workflow recommendation 可累积 | 当前只保留最新推荐 | 经验趋势不足 | 中 | 需新存储模型 | schema + benchmark | 暂缓 |
| acceptance 分级优化 | 提高目标模式循环效率 | fast 很快，full/acceptance 重 | push 前 full 成本高 | 工程效率 | 中 | scripts/docs | 暂缓，另轮处理 |

## 目标

用户故事：

> 作为 Harness Maintainer，我在审查 workflow recommendation、maturity review、asset candidates 或 experience summary 时，能确认每个 LLM 引用的 `evidence_sources` 都来自 Builder 明确提供的证据集合，因此这些智能建议可追溯、可复核、不会把幻觉路径伪装成 Harness 事实。

- 为 workflow recommendation、maturity review 和 asset candidate parser 增加显式 `allowed_evidence_sources` 参数。
- 在 orchestration 层从 `MaturityEvidencePack`、`ExperienceSource`、`ImprovementCandidate`、上游 maturity review 和可选 Experience Summary 中构造 allowlist。
- 保留并复用 experience summary 已有 unknown source 语义。
- 在 benchmark 中校验落盘 review-only artifacts 的 evidence source 可追溯性，不能只看 `.ai/` 前缀。

## 非目标

- 不把所有 `.ai/**` 文件自动当成合法证据；allowlist 必须来自结构化契约或明确核心输入。
- 不要求非 LLM 的 candidate governance 决策在本轮做同样白名单升级。
- 不把空 `evidence_sources` 升级为 hard fail；本轮只处理“引用了未知路径”的情况。
- 不实现 guided apply、recommendation history 或 acceptance 分级。

## 设计决策

### 共享 Allowlist

新增轻量 helper 模块，负责：

- `maturity_evidence_source_allowlist(evidence_pack)`
  - 固定核心输入：`.ai/maturity-evidence.yaml`、`.ai/maturity-score.yaml`、`.ai/improvement-candidates.yaml`、`.ai/harness-config.yaml`、`.ai/project-inventory.json`、`.ai/command-catalog.yaml`、`.ai/experience/experience-index.yaml`。
  - `evidence_pack.maturity_inputs`
  - `evidence_pack.experience.sources[*].path`
- `review_evidence_source_allowlist(evidence_pack, candidates, maturity_review=None, experience_summary=None)`
  - 包含 maturity allowlist。
  - 包含 `ImprovementCandidate.evidence_sources`。
  - 包含上游 `MaturityReviewReport.candidate_reviews[*].evidence_sources`。
  - 包含可选 `ExperienceSummaryReport.findings[*].evidence_sources` 和 `.ai/experience/experience-summary.yaml`。

Helper 只校验，不修正、不过滤、不替换。

### Parser 行为

直接调用 parser 时必须传入 `allowed_evidence_sources`。这避免测试或后续代码绕开 orchestration 层的白名单。

错误语义：

- 非 `.ai/`：继续报 `evidence_sources must be under .ai/`。
- `.ai/` 下但不在 allowlist：报 `referenced unknown evidence_sources`。

### Benchmark 行为

Benchmark 读取已存在的结构化产物构造 `allowed_evidence_sources`，并在以下可选 artifact 存在时校验：

- workflow recommendation
- maturity review
- asset candidates
- experience summary

未知 `.ai/` evidence source 使对应 content check 失败，并返回 `unknown_evidence_source`。

## Assumptions / Risks

- `.ai/maturity-evidence.yaml` 是当前多个候选的事实证据源，即使它不总在 `maturity_inputs` 中，也必须作为核心来源允许。
- 旧 artifact 如果引用了任意 `.ai/` 路径但未被结构化 evidence 输入声明，本轮会让 benchmark 失败。这是有意的显式失败，不是兼容回退。
- 空 `evidence_sources` 暂不 hard fail，避免把“缺证据”和“伪造证据路径”混成一类问题。

## 验收标准

- Workflow recommendation parser 拒绝 `.ai/review/missing.yaml` 这类未知 evidence source。
- Maturity review parser 拒绝未知 evidence source。
- Asset candidate parser 拒绝未知 evidence source。
- `recommend_workflow_with_llm`、`review_maturity_with_llm`、`generate_asset_candidates_with_llm` 自动从输入对象构造 allowlist。
- Benchmark 对 workflow recommendation、maturity review、asset candidates 和 experience summary 的未知 evidence source 报 `unknown_evidence_source`。
- 既有合法 review-only 流程测试仍通过。
- README / engineering docs / todo / evolution log 记录本轮稳定规则与完成状态。
