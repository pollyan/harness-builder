# Init Completion 行动优先交付摘要设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/README.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、近期 `docs/evolution-log.md` 与 completion summary 相关 spec / plan。
- 当前代码 / 测试检查：`src/harness_builder_agent/tools/init_summary.py` 的 `render_init_completion_message()`、`_completion_next_action_lines()`、`_benchmark_readiness()`、`_completion_user_supplement_lines()`，以及 `tests/unit/test_init_summary.py`、`tests/integration/test_init_on_fixture_projects.py` 的 completion transcript 断言。
- 按需未展开：`docs/engineering/llm-contracts.md`、`docs/engineering/sensor-and-gate-rules.md` 和完整 benchmark 实现；本轮不修改 LLM、prompt、schema、scan reconciler、Sensor 或 benchmark 规则。
- Todo 状态：`docs/todos/README.md` 当前没有 open todo；`local-unique-capability-migration.md` 已归档为 implemented，本轮不继续迁移旧 61 个提交。
- Sub agent：尝试启动 explorer 做只读调研，但当前会话返回 `agent thread limit reached`；本轮由主线程完成调研、TDD、实现和验证。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Completion 行动优先交付摘要 | init North Star / Gate | 首次 init 完成后，终端摘要先告诉 Maintainer 当前成熟度、下一步命令、benchmark 状态和优先入口，再补充生成清单与审计细节 | completion message 已包含生成资产、成熟度、证据 / 缺口、用户补充、优先下一步、Benchmark、优先查看和待确认 | 信息顺序仍以“本次已生成”开头，`建议下一步` 被用户补充和生成清单压在中后段；用户要读完整段才知道先做什么 | 把“写入后知道下一步该干什么”作为第一屏主体验，降低首次交付后的行动成本 | 低：只改 completion summary 渲染顺序和文档，不改 `.ai` schema / benchmark / Runtime | unit 断言 section 顺序；integration 覆盖 guided init transcript | 依赖现有 completion helper、`BenchmarkReport` 和 `Questionnaire` schema | `建议下一步`、`Benchmark 健康度`、`优先查看` 出现在 `本次已生成` 前；next action 优先级不退化 | 本轮 |
| B. Completion 用户补充进一步压缩 | 上轮 Gate | 完成摘要更短，用户补充只展示计数、示例和事实边界 | 当前已展示前 3 条 scan / team / workflow 补充和 source / boundary | 直接压缩可能削弱“用户输入已被吸收”的可见闭环，且需要更明确的摘要格式契约 | 改善终端长度 | 低到中 | unit / integration transcript | 需要定义完整细节仍在 Markdown / YAML 的展示口径 | 下一轮候选 |
| C. Existing Harness 维护入口模块拆分 | 上轮 Gate / 工程债 | existing Harness 入口从 `interactive_init.py` 继续拆出，降低后续维护风险 | 动作契约和状态 overview 已拆出，但入口编排仍偏大 | 工程边界仍偏重；不过本轮首次 init completion 有更直接用户价值 | 保护后续迭代 | 中 | 行为等价 unit / integration | 需要控制拆分边界 | 下一轮候选 |

排序结论：

1. 选择 A，因为它直接服务 `init-north-star.md` 的“写入后的交付摘要”和“用户知道下一步该干什么”，且当前所有数据已存在，只需调整 CLI 信息架构即可验收。
2. B 暂不选，因为现有用户补充可见性刚建立，贸然压缩可能削弱渐进式协作闭环；可在行动优先顺序稳定后再做。
3. C 暂不选，因为它是工程信任故事，当前没有比首次 completion 主体验更高的用户可见价值。

## 本轮 Milestone

作为 Harness Maintainer，当我完成首次 guided `init` 后，我可以在终端 `== 初始化完成 ==` 的前半段先看到当前成熟度、建议下一步、Benchmark 健康度和优先查看入口，从而不用先读完整生成清单和补充审计也能知道下一步应该做什么。

## 验收标准

1. `render_init_completion_message(ai)` 输出仍保留 `== 初始化完成 ==`、输出目录、CLI-first 边界、`本次已生成`、`当前成熟度`、`主要证据 / 缺口`、`本次吸收的用户补充`、`建议下一步`、`Benchmark 健康度`、`优先查看` 和 `仍需人工确认`。
2. `当前成熟度` 必须出现在 `本次已生成` 前，先建立 L0-L4 叙事。
3. `建议下一步`、`Benchmark 健康度` 和 `优先查看` 必须出现在 `本次已生成` 前，让终端前半段先完成行动交接。
4. `建议下一步` 的优先级保持上一轮契约：benchmark 未运行时先建议运行 benchmark；benchmark failed 时先建议查看 report；待确认问题进入 human-input 处理入口。
5. 行为只影响 CLI completion message 顺序，不改变 `init-summary.md` 章节、机器 schema、benchmark 语义、正式资产生成或 Runtime 分工。
6. Unit 和 guided init integration 覆盖 transcript 顺序；提交前运行 `scripts/test-fast.sh`。

## 关键决策 / 取舍

- 不新增新的机器消费文件，不改 `.ai/init-summary.md`，因为本轮目标是终端主交付说明的信息架构。
- 保留所有现有 section 名称，避免破坏用户和测试对稳定标题的识别。
- `本次吸收的用户补充` 仍保留在 completion message 中，但放在生成清单和证据缺口之后，作为审计细节而不是第一行动焦点。

## Assumptions / Risks

- Assumption：首次 init 完成后用户最需要先知道“当前 L 等级”和“下一步命令”，其次才是完整生成清单。
- Risk：调整顺序会影响依赖 transcript 顺序的测试；本轮通过 unit 和 integration 明确锁定新顺序。
