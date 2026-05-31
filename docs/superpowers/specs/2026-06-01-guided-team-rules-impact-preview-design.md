# Guided Init 团队规则影响与预览设计

## 事实源快照

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/todos/README.md`、上一轮 scan supplement spec、`interactive_init.py`、`asset_writers/guides.py`、guided init integration tests。
- 按需未展开：`docs/engineering/llm-contracts.md`、`sensor-and-gate-rules.md`、`architecture.md`。本轮不修改 LLM、benchmark gate、架构边界或 Runtime 契约。
- sub agent：按目标模式尝试启动只读 explorer 审查团队规则/context 链路，但当前返回 `agent thread limit reached`；主线程继续完成分析、实现和验证。

## Current State Gap Analysis

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. 团队规则输入后的即时影响说明和写入前预览 | 上一轮 Gate / init North Star | 用户输入团队规则后，CLI 立即说明这些规则如何进入 Guides / human-input-needed / 后续审查，并在写入前 preview 中把规则作为 Harness 设计约束展示 | `inline_contexts` 会进入 `interaction-decisions.yaml`、`project-context.md`、`human-input-needed.md` 和最终确认摘要 | 团队规则输入后直接进入候选审查；用户直到最终确认才看到影响，写入前设计预览也不展示团队规则如何约束本次 Harness | 补齐“隐性工程约束转成 AI 可读 Guides”的核心体验，让用户确认团队规则不是只被记录，而是作为设计约束进入后续资产 | 低；CLI helper 和 integration 断言，不改 schema / LLM | guided init transcript、现有资产断言、fast regression | 无外部凭证 | 断言团队规则输入后、建议生成规则前出现 `团队规则理解 / 团队规则影响`；写入前 preview 出现 `团队规则约束` 并包含具体规则 | 本轮 |
| B. `InteractionDecisions.context_confirmation` 结构化 impact 字段 | init North Star / 新发现 | context decisions 机器记录每条规则影响 guides/sensors/workflow/risk | 目前只记录 inline_contexts 文本 | 下游智能审查无法直接消费规则影响分类 | 有利于后续 self-improve / LLM reviewer | 中；schema 迁移、writer 与测试更新 | schema unit、integration | 需兼容旧 decisions | 新字段 schema 校验并进入 trace/summary | 后续候选 |
| C. 团队规则参与候选生成或 weapon selection | 全景规划 / 深度推荐 | 团队规则能影响候选 Guide / Sensor 优先级或 LLM enhancement candidate | 当前 candidate report 只基于 inventory / commands | 团队规则没有改变候选生成，只进入正式语义资产 | 更强的“规则驱动推荐” | 中高；涉及 candidate generator、LLM prompt 或 weapon scoring | unit + integration + acceptance 风险 | 需要设计规则分类和 prompt 契约 | 团队规则改变候选 rationale / priority | 后续较大 milestone |
| D. Push 前 full regression 先决条件 | 当前仓库状态 | 本地 ahead commits 能推送远端 | 当前缺 DeepSeek key 和真实 `.benchmarks`，full 会失败 | 无法 push | 同步远端 | 依赖外部凭证/网络 | `scripts/test-full.sh` | 外部依赖 | full 通过后 push | 暂不处理 |

排序结论：

1. 选择 A，因为它直接服务 init North Star 中“用户补充后复述理解、说明影响，并在设计预览前形成协作闭环”的体验，而且当前数据流已经存在，只差用户可见反馈。
2. B/C 更接近长期智能化，但会扩大 schema 或 LLM 设计面；本轮先不把低风险 CLI 闭环升级成数据契约迁移。
3. D 不推进 init 主体验，且依赖外部条件。

## 本轮 Milestone

作为 Harness Maintainer，当我在 guided `init` 中输入团队代码规范、架构约束或测试策略时，我可以在进入候选审查前立即看到系统如何理解这些规则、它们会进入哪些 Harness 资产，并在写入前设计预览中看到这些规则作为 Guides / human-input-needed / 后续审查的约束，从而确认团队隐性规则已经进入本次 Harness 设计，而不是只在最终确认阶段被动记录。

## 验收标准

- CLI transcript：在团队规则输入之后、`建议生成的规则` 之前，出现稳定 `团队规则理解` 和 `团队规则影响` 区块。
- CLI transcript：即时说明必须包含具体团队规则文本，并说明会进入 `interaction-decisions.yaml`、`project-context.md`、`.ai/human-input-needed.md`，且不会伪装成扫描事实。
- CLI transcript：写入前 `Harness 设计预览` 中出现 `团队规则约束`，并列出团队规则及对 Guides / Sensors / Workflow 后续审查的影响边界。
- 产物契约：既有 `interaction-decisions.yaml`、`project-context.md`、`human-input-needed.md` 对团队规则的持久化保持不退化。
- 边界：不修改 LLM prompt/schema，不修改 candidate generator，不默认运行 benchmark，不执行 Runtime，不创建 `.ai/task-runs`。
- 测试：先更新 guided init integration 测试形成失败断言，再实现；提交前运行 `scripts/test-fast.sh`。
- 文档：更新 `docs/engineering/init-workflow.md` 和 `docs/evolution-log.md`。

## 决策与取舍

- 本轮不声称团队规则已经改变 maturity score。它们会进入团队上下文 Guide、human-input-needed 和后续人工审查；正式评分仍由已有 maturity model 和资产写入后评估负责。
- 本轮不把自然语言团队规则分类成安全、架构、测试等结构化字段；避免轻率 schema 迁移。
- 预览展示只读影响边界，不自动修改正式 routing policy；Workflow policy 变更仍走候选治理或结构化 patch。

## Assumptions / Risks

- Assumption：当前 `accepted_interactive_decisions()` 已把 `inline_contexts` 写入 `context_confirmation.inline_contexts`，Guide writer 和 human-input writer 已消费该字段。
- Risk：CLI 输出继续变长；本轮只在有团队规则时输出短区块，未提供规则时保持现有流程。
- Risk：用户可能以为团队规则已经被验证；文案必须明确这是用户提供的团队约束，不是扫描事实。

## 非目标

- 不新增 context impact schema。
- 不改 LLM candidate generation。
- 不改 benchmark 或 acceptance。
- 不处理已有 Harness 维护入口。
