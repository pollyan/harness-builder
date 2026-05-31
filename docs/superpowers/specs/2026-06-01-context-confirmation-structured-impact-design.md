# 团队规则结构化影响契约设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/strategy/init-north-star.md`、全景 North Star、`docs/todos/README.md`、近期 evolution log、`ContextConfirmation` / `WorkflowConfirmation` schema、guided init 与 interaction decisions 测试。
- 按需未展开：`docs/engineering/llm-contracts.md` 和 `sensor-and-gate-rules.md` 本轮不修改 LLM prompt、扫描、benchmark 或 Sensor 规则；`architecture.md` 本轮不调整模块边界。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. 团队规则结构化影响契约 | 上轮 Gate / 新发现 | 团队规则补充不仅进入文本，还以机器字段说明影响范围、review 状态和不直接改正式 policy 的边界 | CLI 已即时复述团队规则，preview 已展示团队规则约束；`inline_contexts` 进入语义资产 | `ContextConfirmation` 只有文本和路径，后续 self-improve / 审计不能稳定判断它影响哪些资产、是否待审、是否改 policy | 补齐用户输入消费链路的机器契约，和 Workflow note 保持一致，为后续候选治理 / self-improve 复用打基础 | 低到中；schema 扩展需兼容旧文件，不能暗示自动修改正式 routing | schema unit、Markdown unit、guided init integration | 无外部凭证；依赖现有 interaction decisions 写入链路 | `interaction-decisions.yaml` 有 context impact 字段；无团队规则时默认不要求 review；正式 routing 不含自由文本团队规则 | 本轮 |
| B. Workflow note review-only routing candidate | 上轮 Gate | Workflow 补充可进入 review-only workflow policy 候选，并由治理流程审核 | Workflow note 已有结构化 impact/review/policy boundary | 自由文本 note 尚不能变成可审查 routing patch | 更强 Workflow Toolkit 闭环 | 中高；`workflow_policy` candidate 需要结构化 patch，自由文本推断 patch 有误改风险 | candidate schema / governance / integration | 需要先设计自由文本到结构化 patch 的安全边界 | 生成 review-only candidate 且不改正式 routing | 下一轮候选 |
| C. Scan correction diff preview | 上轮 Gate | 返回 scan 修改时展示旧补充和新补充差异 | 已支持替换 / 清空语义和提示 | 无逐项 diff，用户仍需自行对比 | 增强纠错信任感 | 低；纯 CLI 文案 | guided transcript integration | 无 | CLI 展示 old/new diff，资产只保留最新补充 | 下一轮候选 |
| D. Push 前 full regression / 远端同步 | 工程节奏 | 完整工作包形成独立价值后执行 full 并 push | 本地领先远端 21 个 commit | 尚未运行 push 前 full；但当前仍在继续演进 init 主线 | 降低本地积压风险 | 中；acceptance 依赖 DeepSeek / `.benchmarks` / 网络 | `scripts/test-full.sh` | 可能缺凭证或真实仓库 | full 通过后 push | 工作包完成后处理 |

排序结论：

1. 选择 A。团队规则是首次 guided `init` 中最关键的人类上下文输入之一，当前已有用户可见闭环，但机器契约弱于 Workflow note；本轮可以在一个小切片内补齐 schema、写入、Markdown 和 integration 验收。
2. B 暂不选，因为从自由文本 Workflow note 直接生成 `workflow_policy_patch` 容易越过候选治理边界；应在 context / workflow review-only contract 稳定后单独设计。
3. C 是好体验，但只改善返回修改时的可见对比；A 更直接服务后续 Self-Improve 和审计消费。
4. D 应在形成完整可 push 工作包后处理；本轮只做本地 commit。

本轮 milestone：

作为后续 Self-Improve / 审计链路维护者，当 Harness Maintainer 在首次 guided `init` 中输入团队规则、架构约束或测试策略时，我可以在 `interaction-decisions.yaml` 和 `human-input-needed.md` 的 interaction decision 摘要中读取机器可验证的影响范围、review-only 状态和“不直接修改正式 policy”的边界，从而稳定消费团队规则补充，而不是解析自由文本或误以为它已经改变正式 workflow routing。

## 设计

### Schema

在 `ContextConfirmation` 上新增兼容字段：

- `impact_scopes`
  - 可选值：`interaction_decisions`、`project_context`、`human_input_needed`、`guide_context`、`review_only_team_context`
  - 默认空列表，兼容旧文件和无上下文路径 / 无 inline 规则场景。
- `review_status`
  - `pending_harness_maintainer_review` 或 `not_required`
  - 默认 `not_required`。
- `policy_effect`
  - `context_only_no_direct_policy_change` 或 `not_applicable`
  - 默认 `not_applicable`。

### 写入规则

- guided `init` 或带 `--context` 的 interactive decisions 只要存在 `confirmed_paths` 或 `inline_contexts`，就写入：
  - `impact_scopes=[interaction_decisions, project_context, human_input_needed, guide_context, review_only_team_context]`
  - `review_status=pending_harness_maintainer_review`
  - `policy_effect=context_only_no_direct_policy_change`
- 无团队规则 / 无 context path 时保持默认值。
- 非交互模式继续保留 `status=not_confirmed` 或 `not_provided`，默认 impact 字段为空，不把未确认 context 误标为 review-only 已消费。

### Markdown 摘要

`interaction_decisions_markdown()` 增加：

- `context_impact_scopes`
- `context_review_status`
- `context_policy_effect`

这些字段进入 `human-input-needed.md`，让语义审计入口和机器 YAML 契约保持一致。

## 决策与取舍

- 本轮不让团队规则自动修改 `harness-config.yaml`、workflow routing 或正式 policy。
- 本轮不从团队规则生成 asset candidate；后续可以基于结构化 review-only context contract 设计候选生成。
- `policy_effect` 用泛化的 policy，而不是只写 routing policy，因为团队规则可能影响 Guides、Sensors、review 或未来治理；但当前明确是 context-only，不做直接正式 policy 变更。
- 默认值保持旧文件兼容，不要求迁移旧 `interaction-decisions.yaml`。

## Assumptions / Risks

- Assumption：提供 `--context` 文件或 inline 团队规则都属于 Harness Maintainer 提供的团队上下文，应进入 review-only 审计边界。
- Risk：`pending_harness_maintainer_review` 可能让人以为团队规则尚未写入语义资产；CLI / docs 需要继续强调它已进入 context assets，但不等于正式 policy 已被修改。
- Risk：未来如果团队规则需要成为正式 policy，应走候选治理或结构化 patch，不应复用本轮字段直接应用。

## 验收标准

1. `ContextConfirmation` schema 接受并输出新增字段；非法 impact / review / policy 值会被 Pydantic 拒绝。
2. `accepted_interactive_decisions()` 在存在 context path 或 inline 团队规则时写入结构化 impact/review/policy 字段；无团队规则时保持默认值。
3. `default_non_interactive_decisions()` 不把未确认 context path 误标为 pending review 或 policy effect。
4. `interaction_decisions_markdown()` 展示 context impact/review/policy 字段。
5. guided init integration 证明团队规则进入 `interaction-decisions.yaml` 的结构化字段，并且正式 `harness-config.yaml` workflow routing 不包含自由文本团队规则。
6. 更新 `docs/engineering/init-workflow.md` 和 `docs/evolution-log.md`，记录稳定契约和本轮取舍。
