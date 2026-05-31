# Human Input 待确认回访入口迁移设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/engineering/sensor-and-gate-rules.md`、`docs/todos/local-unique-capability-migration.md`、上一轮 Existing Harness 编号菜单迁移 spec / plan，以及当前 / 备份分支的 `interactive_init.py`、`human_confirmation.py` 和相关测试。
- 按需未展开：`docs/engineering/llm-contracts.md` 和 acceptance 测试。当前 milestone 只迁移确定性 human confirmation 展示与 Markdown 指引，不改 LLM prompt、scan reconcile 或真实 acceptance。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Human Input 待确认回访入口 | 迁移 todo / 上一轮 Gate | 首次 init 生成的 `human-input-needed.md` 有明确 `## 处理方式`；再次进入已有 Harness 时能看到 questionnaire 待确认数量、scan 类确认数量、前几个 interaction id 和处理入口 | 当前会生成 `questionnaire.yaml` 与 `human-input-needed.md`，已有 Harness 入口只显示 `human_input_needed=present/missing` | Maintainer 再次进入时不知道有多少待确认项、哪些 id 最优先，也不知道 `.ai/human-input-needed.md#处理方式` 是处理入口；Markdown 只有下一步建议，没有逐项处理方式 | 补齐渐进式协作的“跳过问题必须可回访”闭环，提升维护入口的可行动性 | 低到中，读取已有 Questionnaire schema；不改正式资产 schema；会改变 human-input Markdown 内容 | unit 覆盖 status helper 与 Markdown `## 处理方式`；integration 覆盖 existing-Harness 输出待确认项状态和 action entry | 依赖当前 Questionnaire schema 和已有 human-input 产物 | CLI 输出 `human_input_confirmations`、`human_input_scan_confirmations`、`human_input_first`、`human_input_action_entry`；Markdown 包含处理方式 | 本轮 |
| B. Benchmark failed preview | 迁移 todo / 上一轮 Gate | 已有 Harness 入口直接展示 benchmark failed check id、中文 label 和 detail | 当前只显示最近 benchmark 和 schema/content failed count | BenchmarkReport 当前 schema 还没有旧分支使用的 `errors/missing/weak_commands` 字段，直接迁移会变成 schema 扩展切片 | 提升质量门禁失败定位效率 | 中到高，涉及 benchmark schema、writer 和报告字段；需同步 sensor/gate rules | unit / integration / benchmark tests | 需要先决定是否扩展 BenchmarkCheck 字段 | 后续按 benchmark 质量门禁切片处理 | 下一轮候选 |
| C. Workflow routing signals | 迁移 todo | 已有 Harness 入口展示 routing default、standard escalation、risk triggers、missing hard gate trigger | 当前只展示 latest workflow recommendation，不展示正式 routing policy 健康信号 | Maintainer 不易区分 review-only recommendation 和正式 routing policy 状态 | 强化 Runtime 分工和 routing 可解释性 | 中，需读取 HarnessConfig 并避免过度解释为 Runtime 证据 | unit / integration | 无外部依赖 | 输出 routing signals 且不执行 Runtime | 后续候选 |

排序结论：

1. 选择 A，因为它与上一轮编号菜单同属已有 Harness 维护入口体验，并且直接服务 `init-north-star.md` 的渐进式协作要求：用户跳过或未处理的问题必须进入可回访、可行动的确认链路。
2. B 价值高，但旧实现依赖当前主线尚未具备的 BenchmarkCheck 扩展字段，适合另立 benchmark schema / quality gate 细化切片。
3. C 也属于已有 Harness 状态增强，但它更多解释 routing policy 健康，优先级略低于 human input 回访闭环。

本轮 milestone：

作为 Harness Maintainer，当我首次 init 后仍有待确认问题，并在之后再次运行 guided `init` 进入已有 Harness 维护入口时，我可以看到待确认项数量、scan 类确认数量、优先处理的 interaction id 和 `.ai/human-input-needed.md#处理方式` 入口，从而知道哪些人工上下文仍需补齐，以及应该用哪个命令或治理动作处理它们。

## 关键决策 / 取舍

- 本轮同时更新 `human-input-needed.md` 的稳定章节和已有 Harness 入口状态，因为它们共享同一条“待确认项回访”用户故事。
- 不新增机器 schema；复用现有 `Questionnaire` Pydantic schema 校验。
- scan 类确认项按当前 schema 类型定义：`scan_warning_confirmation`、`risk_area_confirmation`、`evidence_expansion_confirmation`、`scan_followup_confirmation`。
- scan warning 的处理建议复用 `scan_warning_action_hint()`；其他 interaction type 使用确定性中文指引。
- 不自动处理确认项，不修改 Guides / Sensors / routing policy，不执行 Runtime。

## Assumptions / Risks

- `human-input-needed.md#处理方式` 是 Markdown anchor 约定；不同渲染器 anchor 规则可能不同，但章节名稳定，CLI 同时显示文件路径和章节名。
- 当前 Questionnaire 没有“已处理 / 未处理”状态，本轮用 question count 表示待确认 backlog；候选治理、accepted/applied 等更细状态后续可进入 Experience / governance 证据。
- sub agent 本轮不启用：此前线程 agent 数量达到上限，且当前切片边界清晰，主线程可以完成。

## 可执行验收标准

- Unit：`human_input_markdown()` 输出 `## 扫描待确认摘要`、`## 处理方式`，并对 context、candidate、sensor gate、risk、evidence expansion、scan follow-up、scan warning 给出可行动处理建议。
- Unit：existing-Harness human input status helper 读取 `questionnaire.yaml`，输出 `human_input_questionnaire=present`、`human_input_confirmations=<n>`、`human_input_scan_confirmations=<n>`、最多 3 条 `human_input_first=<id>`、omitted count 和 `human_input_action_entry=.ai/human-input-needed.md#处理方式`。
- Unit：缺少 `human-input-needed.md` 或 `questionnaire.yaml` 时输出 missing / present-but-questionnaire-missing，不静默成功。
- Integration：已有 Harness 再次运行 guided `init` 并输入 `1` 只读退出时，CLI 展示 human input backlog status 和 action entry，不触发 scan、不覆盖正式 Harness 资产。
- 文档：README、`docs/engineering/init-workflow.md`、迁移 todo 和 evolution log 同步本轮稳定契约。
- 验证：targeted unit / integration、`git diff --check` 和 commit 前 `scripts/test-fast.sh` 通过。

## Sub Agent 使用情况

未使用 sub agent。目标模式要求可用时优先考虑，但本线程此前 spawn 已达到 agent 数量上限；本轮迁移范围较小，采用主线程本地对比旧分支实现与当前 schema。
