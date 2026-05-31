# Guided Init 高风险发现确认链路设计

## 背景

本轮继续消化 `docs/todos/guided-init-ai4se-real-repo-findings.md`，并采用新的 milestone 粒度规则：把同一用户故事下、共享风险数据流且可一次验收的小问题合并为一个工作包。

真实 `ai4se` 试跑中，扫描发现 `docs/a.json` 可能包含明文 API key。当前 guided `init` 会把它放进普通“风险区域”，后续 Guide / Sensor 也会泛化写入风险映射，但用户在 CLI 中看不到这是疑似凭证类高影响风险，也没有专门的人工确认问题或 Workflow escalation 说明。

## Current State Gap Analysis

- 产品能力：`init` 已能展示风险区域，并把 risk areas 写入 Guides / Sensors，但还没有区分普通风险与疑似密钥、权限、安全、支付、数据迁移等高影响风险。
- init 用户旅程：问题发生在“扫描结果友好呈现”“深度追问”“设计预览前的人工确认”之间；高风险线索必须在写入正式资产前显著进入用户视野。
- CLI 体验：`_risk_attention_lines()` 只输出 `path: reason`，没有高风险视觉标记、确认状态或后续影响说明。
- 渐进式交互：用户可通过 `risk=路径|原因` 补充风险，但系统没有将疑似 secret / credential 风险转成强确认问题。
- Harness 推荐质量：Guide / Sensor 文档已经提到风险区域，但没有说明疑似高风险内容需保持待确认，命中后应进入 standard workflow / human escalation。
- Runtime 分工：Builder 不执行 Runtime、不清理密钥；它只应生成需要 Runtime / Maintainer 消费的确认问题、风险叙事和升级建议。
- schema / 数据：`risk_areas` 当前是自由 dict，不适合本轮大 schema 迁移。可以用确定性 helper 从 path/reason/name/summary 中识别 high impact category，并通过现有 questionnaire schema 小幅扩展 `interaction_type`。
- 测试：已有 guided CLI 风险分组 integration、human confirmation unit、Guide / Sensor writer unit 可扩展为一个纵向风险确认链路。

## 用户故事

作为 Harness Maintainer，当首次 guided `init` 扫描到疑似 API key、凭证、安全、支付、权限或数据迁移等高影响风险时，我可以在 CLI 中立即看到它被标记为“高风险，需人工确认”，并在 `.ai/questionnaire.yaml` / `.ai/human-input-needed.md` / Guides / Sensors 中看到它如何影响人工确认、Sensor 验证和 Workflow escalation，从而不会把未确认的敏感风险当作普通扫描事实或模板化规则。

## 设计

采用轻量高风险分类 helper，不做 risk schema 迁移：

1. 新增 `harness_builder_agent.tools.risk_signals`：
   - `classify_risk_area(risk: dict) -> RiskSignal` 返回 `is_high_impact`、`category`、`confirmation_reason`。
   - 关键词覆盖 secret / api key / token / password / credential / private key / security / auth / permission / payment / money / data migration / migration / PII，以及对应中文词。
   - helper 只基于扫描线索分类，不把风险确认为事实。
2. Guided CLI：
   - 普通风险保持现有表达。
   - 高风险风险项输出 `【高风险，需人工确认】`，说明疑似类别、原因、以及“建议进入 Guide / Sensor / Workflow standard escalation 或 human-input-needed”。
   - “建议补充”区如果存在高风险项，增加一句让用户确认是否确认为风险边界、是否需要 standard workflow / human escalation。
3. 人工确认资产：
   - `build_questionnaire()` 增加可选 `risk_areas` 参数。
   - 对高风险项生成 `risk_area_confirmation` 问题，`interaction_id` 使用稳定 slug，如 `confirm:high-risk:docs-a-json`。
   - `.ai/human-input-needed.md` 通过现有 questionnaire 渲染自然出现该问题。
4. Guide / Sensor：
   - `project-context.md` 的“风险区域”对高风险项标记“待确认高风险”，说明不能自动当作已确认团队规则。
   - `verification.md` 的“风险与验证映射”对高风险项说明命中时应优先 standard workflow / human escalation，缺少验证环境时记录 skipped 和人工下一步。

## 验收标准

- guided init transcript 中，疑似 API key / secret 风险被标记为 `高风险，需人工确认`，并说明会影响 Guide / Sensor / Workflow escalation。
- `questionnaire.yaml` 通过 schema 校验，并包含 `risk_area_confirmation` 问题，问题文本指向具体风险路径。
- `human-input-needed.md` 包含该高风险确认问题。
- `project-context.md` 和 `verification.md` 对高风险项使用待确认表达，不把疑似 secret 自动写成已确认事实。
- 本轮不清理密钥、不执行 Runtime、不修改正式 workflow routing policy、不引入大 risk schema 迁移。
- 测试覆盖 CLI transcript、questionnaire schema、Guide / Sensor 文档内容和现有 fast regression。

## 决策与取舍

- 合并理由：CLI 突出、人工确认和资产叙事都服务同一个用户故事，并共享 `risk_areas` 数据流；拆成多个 milestone 会重复读取同一上下文和重复生成过程文档。
- 不做多栈建模和成熟度英文修复：它们分别属于 stack schema / maturity text 的不同用户故事。
- 不自动写入正式 workflow policy：高风险升级先在 preview / Guide / Sensor / human-input 中表达，正式 routing policy 变更仍走候选治理。

## Assumptions / Risks

- 关键词分类可能误报，因此所有高风险表达都使用“疑似 / 需确认”，不声称事实已验证。
- 部分风险来自用户补充而非 LLM scan，也应进入相同确认链路。
- 如果后续需要更强准确性，应由 LLM-planned deep scan 和 detector validation 支撑，本轮只建立用户可见确认闭环。
