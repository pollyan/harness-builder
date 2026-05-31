# Init Completion 优先下一步设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/README.md`、`docs/engineering/init-workflow.md`、`docs/engineering/architecture.md`、`docs/engineering/testing-strategy.md`、近期 `docs/evolution-log.md` 与相关 specs / plans。
- 当前代码 / 测试检查：`src/harness_builder_agent/tools/init_summary.py` 的 `render_init_completion_message()`、`_benchmark_readiness()`、`_pending_confirmation_lines()`，以及 `tests/unit/test_init_summary.py`、`tests/integration/test_init_on_fixture_projects.py` 的 completion summary 断言。
- 按需未展开：`docs/engineering/llm-contracts.md` 和 `sensor-and-gate-rules.md`，本轮不修改 LLM、prompt、schema、scan reconciler、Sensor 或 benchmark 规则。
- Sub agent：尝试启动 explorer 做只读调研，但当前会话返回 `agent thread limit reached`；本轮由主线程完成调研、TDD 和验证。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Completion 优先下一步 | init North Star / Gate | 首次 init 完成后，终端主交付摘要直接告诉 Maintainer 现在最应该先做什么 | completion message 已展示生成资产、成熟度、证据 / 缺口、用户补充、`建议下一步`、Benchmark 健康度、优先查看、待确认 | `建议下一步` 只来自 maturity report；benchmark 未运行和待确认处理分别散落在 Benchmark / 待确认区块，用户要自己合成优先顺序 | 把“写入后知道下一步该干什么”做成明确闭环，降低首次交付后的行动成本 | 低：只改 completion summary helper 和测试，不改 `.ai` schema / benchmark / Runtime | unit 覆盖 benchmark not_run、failed report、pending confirmation 优先动作；integration 覆盖 guided init completion transcript | 依赖现有 `BenchmarkReport` 和 `Questionnaire` schema | completion summary 的 `建议下一步` 第一项优先运行 benchmark；有待确认时包含 human-input 处理入口；benchmark failed 时先查看 report | 本轮 |
| B. Completion summary 视觉紧凑化 | 上轮 Gate | 完成摘要更短、更少重复 | completion summary 已包含所有主交付信息 | 当前缺少“哪些信息可以删”的稳定口径；直接压缩可能误删事实边界 | 改善终端可读性 | 低到中 | unit / integration transcript | 需要先定义短摘要标准 | 下一轮候选 |
| C. Existing Harness 维护入口模块拆分 | 上轮 Gate / 工程债 | existing Harness 入口从 `interactive_init.py` 拆出，降低后续维护风险 | 维护入口体验近期持续增强，但仍在大函数中 | 工程边界仍偏重；不过本轮首次 init completion 有更直接用户价值 | 保护后续迭代 | 中 | 行为等价 unit / integration | 需要控制拆分边界 | 下一轮候选 |

排序结论：

1. 选择 A，因为它直接服务 `init-north-star.md` 的“写入后的交付摘要”和“用户知道下一步该干什么”，且能通过现有 schema 和测试明确验收。
2. B 暂不选，因为压缩摘要需要先有优先级语义；本轮先让摘要更可行动。
3. C 暂不选，因为它是工程信任故事，当前没有比首次 completion 下一步动作更高的用户可见价值。

## 本轮 Milestone

作为 Harness Maintainer，当我完成首次 guided `init` 后，我可以在终端 `== 初始化完成 ==` 的 `建议下一步` 中直接看到按优先级排序的下一步动作：先运行 benchmark 或查看失败报告，再处理待人工确认，最后参考成熟度建议，从而不用在多个区块之间自己推断行动顺序。

## 验收标准

1. 当 `.ai/benchmark-report.yaml` 缺失时，completion summary 的 `建议下一步` 第一项必须建议运行 `harness-builder-agent benchmark --repo <repo>`。
2. 当 benchmark report 存在且 failed checks 非零时，completion summary 的第一项必须建议查看 `.ai/benchmark-report.yaml` 并处理失败项。
3. 当 `questionnaire.yaml` 有待确认问题时，completion summary 必须在 `建议下一步` 中提示 `.ai/human-input-needed.md#处理方式`。
4. maturity report 的 recommended next steps 仍作为后续建议保留，但不能排在 benchmark / human-input 基础治理动作之前。
5. 行为只影响 CLI completion message，不改变 `init-summary.md` 章节、机器 schema、benchmark 语义、正式资产生成或 Runtime 分工。
6. Unit 和 guided init integration 覆盖新 transcript；提交前运行 `scripts/test-fast.sh`。

## 关键决策 / 取舍

- 复用现有 `BenchmarkReport` 和 `Questionnaire` schema，不从 Markdown 反向解析。
- `建议下一步` 最多保持 3 条，避免 completion summary 继续膨胀。
- 缺少 `questionnaire.yaml` 时不静默假装无待确认；优先动作只在 schema 可读取时加入 human-input 提示，详细缺失仍由 `仍需人工确认` 区块显式展示。

## Assumptions / Risks

- Assumption：首次 init 后最可靠的第一步是运行 benchmark，因为它验证生成资产质量，而不是直接进入 self-improve。
- Risk：如果 maturity report 的 recommended next steps 已包含 benchmark，可能出现语义重复；本轮会用去重逻辑避免同一句重复进入优先动作。
