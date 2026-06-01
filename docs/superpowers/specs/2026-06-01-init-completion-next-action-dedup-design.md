# Init Completion 下一步动作去重设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/README.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、既有 completion specs / plans、`docs/evolution-log.md` 近期记录。
- 当前代码 / 测试检查：`src/harness_builder_agent/tools/init_summary.py` 的 `render_init_completion_message()` 与 `_completion_next_action_lines()`，`tests/unit/test_init_summary.py`，以及 `tests/integration/test_init_on_fixture_projects.py` 中 guided init completion transcript 断言。
- 按需未展开：`docs/engineering/llm-contracts.md`、`docs/engineering/sensor-and-gate-rules.md`、`docs/engineering/architecture.md`，本轮不修改 LLM、Sensor、benchmark 规则、schema 或模块边界。
- Todo 状态：`docs/todos/README.md` 标记当前没有 open todo；历史 todo 均为 implemented / paused 背景参考。
- Sub agent：尝试启动 explorer 做 completion message 只读调研，但当前会话返回 `agent thread limit reached`；本轮由主线程完成调研、TDD 和验证。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Completion 下一步动作去重 | init North Star / 当前代码审查 | 写入后终端摘要给出 3 条以内互不重复的优先动作：基础治理先行，成熟度建议补充不同动作 | completion summary 已把 benchmark 未运行 / failed 和 human-input 处理放到 `建议下一步` 前两位 | 当 `score.recommended_next_steps` 也建议运行 benchmark 时，输出会重复 benchmark，占掉一个行动位；failed benchmark 场景也可能重复“运行 benchmark”类建议 | 让 Maintainer 完成 init 后看到更有效的行动列表，不需要自己过滤重复建议 | 低；只调整 completion helper 和 transcript 测试，不改机器契约、正式资产或 Runtime | unit 覆盖 not_run / failed benchmark 的语义去重；integration 覆盖 guided init completion transcript | 依赖现有 `MaturityReport`、`BenchmarkReport`、`Questionnaire` schema | `建议下一步` 中 benchmark / failed-report / human-input 不重复；distinct maturity step 仍保留；最多 3 条 | 本轮 |
| B. Completion 资产概览进一步压缩 | 上轮 Gate / 当前代码 | 完成摘要更短，只保留最关键资产和入口 | 当前已按 4 个资产组展示 ready/missing，且每组最多 3 个 missing detail | 仍然偏长，但它承担交付审计功能；缺少新的稳定压缩标准 | 改善终端阅读负担 | 低到中；容易误删审计信息 | unit / integration transcript | 需要先定义不损失审计的压缩口径 | 下一轮候选 |
| C. Existing Harness action dispatch registry | Self-Harness Gate / 工程债 | 菜单动作与 runner handler 在一个可测试 registry 中保持一致，新增动作不容易漏接 | runner 已拆到 79 行，动作实现已分到 deterministic / intelligent / review 模块 | 仍靠 if/elif 和菜单常量人工同步，缺少 handler coverage 断言 | 降低已有 Harness 维护入口扩展漂移风险 | 低到中；工程信任故事，用户可见价值弱于 A | unit source/registry coverage + existing harness integration | 无外部依赖 | runner handler keys 覆盖菜单可执行动作 | 下一轮候选 |

排序结论：

1. 选择 A。它直接服务 `init-north-star.md` 的“写入后的交付摘要”和“用户知道下一步该干什么”，并修正当前测试已经固化的重复建议问题。
2. B 暂不选。Completion 资产概览虽可继续压缩，但当前信息承担审计价值；先消除重复行动比删减内容更明确。
3. C 暂不选。runner 已显著瘦身，dispatch registry 是合理的下一轮工程信任候选，但本轮应优先处理首次 init 用户可见体验。

## 本轮 Milestone

作为 Harness Maintainer，当我完成首次 guided `init` 后，我可以在 `== 初始化完成 ==` 的 `建议下一步` 中看到不重复的优先动作：先运行 benchmark 或处理 failed checks，再处理待人工确认，最后展示不同的成熟度后续建议，从而不会被重复 benchmark 提示占掉关键行动空间。

## 验收标准

1. 当 benchmark 尚未运行且 maturity recommended next steps 也包含 benchmark 语义时，completion summary 只展示一条运行 benchmark 的基础治理动作。
2. 当 benchmark failed 且 maturity recommended next steps 包含 benchmark / 重新运行 benchmark 语义时，completion summary 只展示一条 failed-report 处理动作。
3. 当存在待确认 questionnaire 时，human-input 处理入口仍排在成熟度建议之前，且不会被去重误删。
4. 当 maturity recommended next steps 中存在与基础治理不同的建议时，仍会补到最多 3 条行动中。
5. 行为只影响 CLI completion message；不修改 `.ai/init-summary.md` 章节、Pydantic schema、benchmark 判断、正式资产生成或 Runtime 分工。
6. Unit、guided init integration、`git diff --check` 和 `scripts/test-fast.sh` 通过。

## 关键决策 / 取舍

- 去重按 completion action 的语义类别处理，而不是简单字符串相等；`benchmark`、质量门禁、failed check、重新运行 benchmark 属于同一基础治理类别。
- 去重只用于 completion message 的短行动列表，不改动 maturity report 原始 recommended next steps，避免丢失机器审计信息。
- 保持最多 3 条行动，优先级仍为 benchmark / failed checks、human-input、distinct maturity recommendation。

## Assumptions / Risks

- Assumption：首次 init 后的 benchmark / failed check 处理是基础治理动作，重复出现时不应占用额外行动位。
- Risk：自由文本 maturity 建议可能用非常规表述表达 benchmark，简单语义分类不能覆盖所有写法；本轮覆盖当前中文 / 英文 benchmark、质量门禁、failed check、重新运行 benchmark 等稳定表达，不引入复杂 NLP。
