# 扫描补充结构化决策契约设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/strategy/init-north-star.md`、全景 North Star、`docs/todos/README.md`、近期 `docs/evolution-log.md`、`interactive_init.py`、`interaction_decisions.py`、`interaction_decision.py`、guided init integration tests。
- 按需未展开：`docs/engineering/architecture.md`、`sensor-and-gate-rules.md`；本轮不改模块边界、benchmark 或 Sensor gate 规则。`docs/engineering/llm-contracts.md` 未展开，因为本轮不改 LLM prompt、DeepSeek、scan self-check 或 schema 解析边界。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. 扫描补充结构化决策契约 | 新发现 / init North Star | 用户用 `module` / `command` / `risk` 修正扫描理解后，`interaction-decisions.yaml` 能机器读取这些结构化修正、影响范围和待审事实边界 | 结构化补充已进入 project inventory、command catalog、Guides、Sensors 和 CLI summary；`interaction-decisions.yaml` 只记录 notes 和 primary stack override | 交互决策文件无法稳定区分用户补充的模块、命令、风险，也无法声明这些修正是 user-supplied / review-required，而不是已验证扫描事实 | 补齐“用户补充进入 machine-readable decisions”的 North Star 验收口径，降低后续 self-improve / 审计解析自由文本的风险 | 中低；Pydantic schema 扩展需默认兼容旧文件，需保持正式 routing 不被自由文本污染 | schema unit、decision writer unit、guided init integration | 无外部凭证；依赖现有 `GuidedScanOverrides` | `interaction-decisions.yaml` 包含 modules / commands / risk_areas / impact_scopes / review_status / fact_effect；无补充时默认不制造 pending review | 本轮 |
| B. Workflow note review-only routing candidate | 上轮 Gate | Workflow 补充可生成 review-only workflow policy candidate，由维护者治理后才应用 | Workflow note 已有结构化 impact contract 和返回修改语义 | 自由文本 note 尚不能安全转换为 `WorkflowPolicyPatch` | 增强 Workflow Toolkit 闭环 | 中高；涉及候选 schema、LLM/确定性转换边界和治理 apply | candidate/governance integration | 需要安全设计，避免从自由文本推断正式 routing | 生成候选且不改正式 routing | 后续候选 |
| C. push 前 full regression / 远端同步 | 工程节奏 | 累积本地独立价值后运行 full regression 并 push | 本地领先远端 24 个 commit，fast 回归最近通过 | 尚未运行 full / push；可能受 DeepSeek、真实仓库或网络影响 | 降低分叉和远端同步风险 | 中；可能有凭证/真实仓库依赖 | `scripts/test-full.sh` + push 状态 | 需要本地 `.benchmarks` 和 DeepSeek 配置 | full 通过后 push | 工作包边界处理 |

排序结论：

1. 选择 A。它直接服务 init North Star 的“用户补充能被写入 machine-readable decisions 并改变后续决策链路”，比继续做纯 CLI 提示更接近 Self-Improve / 审计的长期能力。
2. B 暂不选。从自由文本 Workflow note 生成 routing candidate 仍需单独治理边界，不能在本轮顺手推断正式策略。
3. C 保留为工程节奏候选；本轮继续做一个独立本地切片，不 push。

本轮 milestone：

作为后续 Self-Improve / 审计链路维护者，当 Harness Maintainer 在 guided `init` 中用 `module=...`、`command=...` 或 `risk=...` 修正扫描理解时，我可以在 `interaction-decisions.yaml` 中读取结构化的模块、验证命令、风险区域、影响范围和“用户补充待审，不是已验证扫描事实”的边界，从而稳定消费这些输入，而不是解析自由文本 notes 或误判它们已经由扫描证据验证。

## 设计

### Schema

扩展 `ScanConfirmation`：

- `modules: list[dict[str, str]]`
- `commands: list[CommandDefinition]`
- `risk_areas: list[dict[str, str]]`
- `impact_scopes: list[ScanImpactScope]`
- `review_status: ScanReviewStatus`
- `fact_effect: ScanFactEffect`

新增枚举：

- `ScanImpactScope`
  - `interaction_decisions`
  - `project_inventory`
  - `command_catalog`
  - `project_context`
  - `sensors`
  - `workflow_routing_review`
  - `human_input_needed`
  - `maturity_preview`
- `ScanReviewStatus`
  - `pending_harness_maintainer_review`
  - `not_required`
- `ScanFactEffect`
  - `user_supplied_correction_review_required`
  - `not_applicable`

默认值保持兼容：空列表、`not_required`、`not_applicable`。

### 写入规则

`accepted_interactive_decisions()` 接收 `scan_modules`、`scan_commands`、`scan_risk_areas`：

- 没有 scan 补充时：`status=accepted`，影响字段为空 / not required。
- 有 primary stack / note / module / command / risk 任一补充时：`status=amended`，`review_status=pending_harness_maintainer_review`，`fact_effect=user_supplied_correction_review_required`。
- `impact_scopes` 根据补充类型追加：
  - 所有补充：`interaction_decisions`、`project_context`、`human_input_needed`、`maturity_preview`
  - primary stack / module / risk：`project_inventory`
  - command：`command_catalog`、`sensors`
  - risk：`workflow_routing_review`

guided `init` 把 `GuidedScanOverrides.modules`、`commands`、`risk_areas` 传入决策写入。

### Markdown

`interaction_decisions_markdown()` 展示：

- `scan_impact_scopes`
- `scan_review_status`
- `scan_fact_effect`
- scan modules / commands / risk areas 小节

## 决策与取舍

- 不新增独立 `ScanCorrection` schema；直接扩展 `ScanConfirmation`，因为这些字段属于同一交互决策。
- 不把用户补充标记为已验证事实；它们可以更新本轮生成资产，但仍保留 `pending_harness_maintainer_review` 和 `user_supplied_correction_review_required`。
- 不修改 formal `harness-config.yaml` routing policy；风险补充只标记 `workflow_routing_review`，正式策略仍由现有写入和候选治理边界控制。
- 不改变 `project-inventory.json` / `command-catalog.yaml` 现有写入行为，本轮只补齐 interaction decisions 审计契约。

## Assumptions / Risks

- Assumption：`module` / `command` / `risk` 是维护者在 guided init 中提供的高信号修正，应比自由文本 notes 更适合机器消费。
- Risk：字段增加会让新生成的 `interaction-decisions.yaml` 更详细；旧文件通过默认值兼容。
- Risk：自然语言 note 仍无法被结构化分类；本轮只记录 notes 和 review-required 边界，不做 NLP 分类。

## 验收标准

1. schema unit：`ScanConfirmation` 接受 structured modules / commands / risk areas、scan impact scopes、review status 和 fact effect。
2. writer unit：`accepted_interactive_decisions()` 在有结构化 scan 补充时写入结构化字段、影响范围和 review-required 边界。
3. writer unit：无 scan 补充时保持空 impact、`not_required` 和 `not_applicable`。
4. Markdown unit：`interaction_decisions_markdown()` 展示 scan impact、fact effect、模块、命令和风险。
5. guided integration：输入 `module=...;command=...;risk=...` 后，`.ai/interaction-decisions.yaml` 包含结构化字段；同时现有 project inventory、command catalog、project-context、Sensor 等行为保持不退化。
6. 文档：`docs/engineering/init-workflow.md` 和 `docs/evolution-log.md` 记录稳定契约和本轮 Gate 结论。
