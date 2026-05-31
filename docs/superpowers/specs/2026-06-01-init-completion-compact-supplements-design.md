# Init Completion 用户补充紧凑摘要设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/README.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、近期 `docs/evolution-log.md` 与上一轮 completion action-first spec / plan。
- 当前代码 / 测试检查：`src/harness_builder_agent/tools/init_summary.py` 的 `render_init_completion_message()` 与 `_completion_user_supplement_lines()`，以及 `tests/unit/test_init_summary.py`、`tests/integration/test_init_on_fixture_projects.py` 的 completion transcript 断言。
- 按需未展开：`docs/engineering/llm-contracts.md`、`docs/engineering/sensor-and-gate-rules.md` 和完整 benchmark 实现；本轮不修改 LLM、prompt、schema、scan reconciler、Sensor 或 benchmark 规则。
- Todo 状态：`docs/todos/README.md` 当前没有 open todo；本轮从 `init-north-star.md` 和上一轮 Gate 候选继续选择新 gap。
- Sub agent：尝试启动 explorer 做只读调研，但当前会话返回 `agent thread limit reached`；本轮由主线程完成调研、TDD、实现和验证。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Completion 用户补充紧凑摘要 | init North Star / 上轮 Gate | 写入后终端摘要保持短交付说明，同时让 Maintainer 确认 scan / team / workflow 补充已被吸收 | completion message 已展示本次吸收的用户补充、source 和事实边界 | 当前每类最多逐条展示 3 条，合计可达 9 条，再加 source / boundary；它可审计但不像短交付摘要 | 降低终端阅读负担，保留“用户输入已消费”的可见闭环，把完整细节交给 `.ai/init-summary.md` / `.ai/interaction-decisions.yaml` | 低：只改 completion helper 和文档，不改 `.ai` schema / Markdown summary / benchmark / Runtime | unit 覆盖多条补充时只展示计数和示例；integration 保证真实 guided init 仍显示关键示例、source 和事实边界 | 依赖现有 `InteractionDecisions` schema | completion message 每类补充展示条数与首条示例，不逐条展开全部内容；source / boundary 保留 | 本轮 |
| B. Existing Harness 维护入口模块拆分 | 上轮 Gate / 工程债 | existing Harness 入口从 `interactive_init.py` 继续拆出，降低后续维护风险 | 动作契约和状态 overview 已拆出，但入口编排仍偏大 | 工程边界仍偏重；不过本轮 completion 短摘要更直接服务首次 init 用户旅程 | 保护后续迭代 | 中 | 行为等价 unit / integration | 需要控制拆分边界 | 下一轮候选 |
| C. Push 前 full regression / 远端同步 | Gate / 发布节奏 | 完整工作包完成后统一 full regression 并 push | 本地已累积多个 commit，当前领先远端 | 当前没有用户要求 push；full acceptance 依赖真实 DeepSeek / 真实仓库，成本高 | 远端同步价值高，但应以完整工作包为边界 | 高：可能需要凭证 / 网络 / acceptance | `scripts/test-full.sh` + push | 外部服务和真实仓库 | 作为工作包边界候选，不在本轮实现 | 后续工作包 |

排序结论：

1. 选择 A，因为它直接服务 `init-north-star.md` 的“写入后的短交付摘要”，且不破坏渐进式协作闭环：终端仍显示已吸收补充的条数、示例、source 和事实边界。
2. B 暂不选，因为它是工程信任故事，当前首次 init completion 仍有直接用户可见的短摘要缺口。
3. C 暂不选，因为本轮没有形成完整 push 工作包，也没有用户要求同步远端；按规则不为单个小切片触发 full regression / push。

## 本轮 Milestone

作为 Harness Maintainer，当我在首次 guided `init` 中提供多条 scan 修正、团队规则或 Workflow 补充并完成写入后，我可以在终端 `== 初始化完成 ==` 中看到每类补充的条数、一个可读示例、结构化来源和事实边界，从而确认输入已被吸收，同时不用在完成摘要里阅读一长串补充明细。

## 验收标准

1. `_completion_user_supplement_lines()` 对 scan / team / workflow 补充分别输出紧凑摘要：`<类别>：N 条；示例：...`。
2. 多条补充时，completion message 只展示首条示例，不逐条展开第二条、第三条等明细；完整细节仍指向 `.ai/init-summary.md` 和 `.ai/interaction-decisions.yaml`。
3. 无人工补充时，仍显示“本次未提供人工补充”，并保留后续可在已有 Harness 维护入口补齐的提示。
4. 缺少 `.ai/interaction-decisions.yaml` 时仍显式显示 `interaction_decisions=missing`，不静默伪装为无补充。
5. `shown_workflows`、source 和事实边界继续保留。
6. 行为只影响 CLI completion message 的用户补充段，不改变 `init-summary.md`、机器 schema、benchmark、正式资产生成或 Runtime 分工。
7. Unit 和 guided init integration 覆盖 transcript；提交前运行 `scripts/test-fast.sh`。

## 关键决策 / 取舍

- 读取 `InteractionDecisions` schema，不从 Markdown 反向解析。
- 每类补充只展示条数和第一条示例；这是 completion message 的短交付摘要口径，不影响 `init-summary.md` 的完整语义报告。
- 保留 source 和事实边界，防止团队规则或 Workflow 补充被误读为扫描事实或已应用 routing policy。

## Assumptions / Risks

- Assumption：终端完成摘要中“条数 + 示例 + source”足以让 Maintainer 确认补充被吸收；完整审计由 Markdown / YAML 承担。
- Risk：如果用户只看终端，可能想看到所有补充明细；本轮通过明确“完整交付摘要见 `.ai/init-summary.md`”降低风险。
