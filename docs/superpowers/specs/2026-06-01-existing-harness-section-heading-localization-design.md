# Existing Harness 维护入口分组标题中文化设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/README.md`、`docs/engineering/init-workflow.md`、`docs/engineering/architecture.md`、`docs/engineering/testing-strategy.md`、近期 `docs/evolution-log.md` 和相关 specs / plans。
- 当前代码 / 测试检查：`src/harness_builder_agent/tools/interactive_init.py` 的 existing Harness 维护入口、`tests/integration/test_init_on_fixture_projects.py` 的 existing Harness transcript 断言。
- 按需未展开：`docs/engineering/llm-contracts.md`、`sensor-and-gate-rules.md`。本轮不修改 LLM、prompt、schema、benchmark 或 Sensor 规则。
- Sub agent：按目标模式尝试启动 explorer 做只读交叉调研，但当前会话达到 `agent thread limit reached`，本轮由主线程完成调研并记录该限制。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Existing Harness 维护入口分组标题中文化 | init North Star / 新发现 | Maintainer 再次进入已有 Harness 时，主要 section header 用中文表达，英文稳定标记只作为括注保留 | 维护入口有分组、signals、triage、guidance、shortcuts 和编号菜单 | 多个 section header 仍以英文为主：`Benchmark signals`、`Workflow routing signals`、`Experience / review signals`、`Maintenance triage`、`Maintenance triage guidance`、`Maintenance action shortcuts`；这和“默认中文、CLI 是产品界面”不完全一致 | 降低维护入口阅读成本，同时保留稳定英文标记给测试、文档和审计 | 低：只改 CLI 文案和测试断言，不改行为 / schema / Runtime | integration transcript 断言中文标题和英文 marker 同时存在 | 依赖现有维护入口输出结构 | guided existing Harness exit transcript 包含中文标题；正式资产不变；英文 marker 仍可搜索 | 本轮 |
| B. Completion summary 视觉紧凑化 | 上轮 Gate | 首次 init 完成摘要短而清晰，不和 `init-summary.md` 过度重复 | completion message 已有主交付说明、用户补充、benchmark 和入口 | 输出可能偏长，但当前缺少明确压缩口径；误删边界信息风险更高 | 改善首次 init 完成体验 | 低到中 | unit / integration transcript | 需要先定义行数和必留信息 | 下一轮候选 |
| C. Existing Harness 维护入口模块拆分 | 上轮 Gate / 工程债 | existing Harness 入口渲染与动作执行从 `interactive_init.py` 拆出，降低后续迭代风险 | prewrite preview 已抽模块；维护入口仍在大文件中 | `_handle_existing_harness_entry()` 仍承载多动作分支和渲染 | 保护已有 Harness 维护旅程的后续迭代质量 | 中；纯工程信任故事，用户可见价值间接 | unit / integration 保行为等价 | 需要谨慎拆分避免冲突 | 下一轮候选 |

排序结论：

1. 选择 A，因为它直接服务 `init-north-star.md` 的 CLI 体验原则，范围极小但用户可见，并且不会扰动已有契约。
2. B 暂不选，因为 completion summary 压缩需要更明确的信息保留标准；当前先修明显的中英文混杂问题。
3. C 暂不选，因为它是工程债，适合在维护入口用户文案继续稳定后再做。

## 本轮 Milestone

作为 Harness Maintainer，当我再次运行 guided `init` 进入已有 Harness 维护入口时，我可以先看到中文分组标题，再按需识别括号中的英文稳定标记，从而更快理解当前健康信号、维护建议和推荐动作。

## 验收标准

1. Existing Harness 维护入口的主要分组标题必须以中文为主，包括质量门禁信号、Workflow 路由信号、经验 / 审查信号、维护优先级、维护建议、推荐动作快捷选择。
2. 每个标题仍保留原英文 marker，例如 `Benchmark signals`，避免破坏现有测试、文档检索和调试习惯。
3. 只改变 CLI 展示文案，不改变 signal 内容、triage 排序、动作执行、默认 exit、schema、LLM、benchmark 或 Runtime 分工。
4. Integration 测试覆盖 existing Harness 只读 exit transcript 中中文标题与英文 marker 同时存在，并证明正式资产不变。
5. 文档记录本轮决策、验证结果和 Self-Harness Gate；无需新增 open todo。

## 关键决策 / 取舍

- 中文标题放在主位置，英文 marker 放在括号中；这样兼顾产品体验和稳定调试标记。
- 不翻译每一行机器信号键值。本轮只处理 section-level navigation，避免大范围改变 existing Harness 信号契约。
- 不改 README / engineering 的长期规则，除非实现后发现当前文档与行为产生事实冲突；现有文档已经允许分项 signals 和稳定 marker。

## Assumptions / Risks

- Assumption：用户主要依靠 section header 进行扫读，先中文化标题能明显降低维护入口的进入门槛。
- Risk：中英混排可能显得稍长；但括号英文 marker 对回归测试和审计仍有价值，本轮接受该取舍。
