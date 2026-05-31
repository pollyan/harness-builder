# Existing Harness 维护状态人话摘要设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/README.md`、`docs/engineering/architecture.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、近期 existing Harness / completion summary 相关 spec、plan、evolution log、`interactive_init.py`、`init_summary.py`、existing Harness integration tests。
- 按需未展开：`docs/engineering/llm-contracts.md`，本轮不修改 LLM、Prompt、扫描调和或真实 DeepSeek 行为；`sensor-and-gate-rules.md` 未完整重读，因为本轮不改 benchmark / Sensor 检查。
- Sub agent：尝试启动只读 explorer 做交叉审查，但当前会话返回 `agent thread limit reached`；本轮由主线程完成调研并记录该限制。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Existing Harness 维护状态人话摘要 | init North Star / 当前代码新发现 | Maintainer 再次运行 `init` 时先看到面向人的维护状态摘要，再按需查看 raw signals | 维护入口已有中文分组标题、Benchmark / Workflow / Experience raw signals、triage guidance 和编号 shortcut | 关键状态仍以 `benchmark_failed_checks=...`、`routing_default=...`、`asset_candidates=...` 等内部字段为主，用户需要自行翻译含义和优先级 | 符合“CLI 是产品界面”和“默认中文、解释性表达”原则，让用户更快理解当前健康状态和下一步动作 | 低到中：只读渲染摘要，不改 schema、LLM、benchmark 或动作执行；需避免与 raw signals / triage 重复过重 | unit 覆盖 benchmark not_run / failed / passed、Experience candidate / human-input 摘要；integration 覆盖 existing Harness `exit` transcript | 依赖现有 BenchmarkReport、ExperienceIndex、Questionnaire、MaintenanceAction schema | 输出包含 `维护状态摘要` 和 3-4 条中文摘要；raw signals 仍保留；只读 exit 不扫描、不覆盖资产 | 本轮 |
| B. 首次 init completion summary 视觉紧凑化 | 上轮 Gate | 首次 init 完成摘要更短、更聚焦 | completion message 已优先列 benchmark、human-input 和 maturity next steps | 摘要仍偏长，但已有明确下一步；缺少更细的 transcript 体验标准 | 提升首次初始化交付体验 | 低：文案改动；但容易误删主交付边界 | unit / integration transcript 行数与关键内容断言 | 需要先定义“紧凑”的稳定口径 | 下一轮候选 |
| C. Existing Harness 维护入口模块拆分 | 上轮 Gate / 工程债 | `_handle_existing_harness_entry()` 拆分清晰，后续维护入口迭代更稳 | 已抽出 action contract，但状态渲染和动作分支仍在 `interactive_init.py` | 大函数仍很长；但纯拆分用户价值不如本轮摘要直接 | 降低后续迭代冲突与回归风险 | 中：纯重构范围较大，需大量等价测试 | integration 行为等价、helper unit 覆盖 | 更适合在用户可见摘要稳定后再拆 | 下一轮候选 |

排序结论：

1. 选择 A，因为它直接推进 `init-north-star.md` 中“再次进入已有 Harness”的成功体验：用户应能理解健康状态和最该先处理的问题，而不是只读内部字段。
2. B 暂不选，因为首次 completion 的下一步优先级刚增强；继续压缩需要更明确的 transcript 标准，避免削弱交付摘要。
3. C 暂不选，因为它主要是工程结构优化；本轮先把状态页的人类摘要稳定下来，后续拆模块时有更清楚的输出边界。

## 本轮 Milestone

作为 Harness Maintainer，当我再次运行 guided `init` 进入已有 Harness 维护入口时，我可以先看到一组中文维护状态摘要，理解质量门禁、Workflow 路由、Experience / review backlog 和推荐下一步，从而不用先阅读 raw `key=value` signals 才知道当前应该处理什么。

## 验收标准

1. Existing Harness 维护入口在 raw `Benchmark signals` 前展示 `维护状态摘要（Maintenance overview）`。
2. 摘要必须用中文解释：
   - Benchmark 未运行、失败或通过时的质量门禁状态。
   - Workflow routing 是否具备 standard escalation、risk triggers 和 missing hard gate trigger。
   - Experience / review 是否有待治理候选、pending improvements、workflow recommendations、human-input 待确认或 Runtime task-run 证据。
   - 当前 triage 第一优先动作及可输入的菜单编号。
3. 摘要只读，不执行 benchmark / improve / review / self-improve，不修改正式 Harness 资产，不创建 `.ai/task-runs`。
4. Raw signals、Maintenance triage lines、中文 guidance 和 shortcuts 仍保留，作为审计与测试入口。
5. Unit 测试覆盖无 benchmark report、failed benchmark、有 pending human input / asset candidates、no pending signal 等状态组合。
6. Integration 测试覆盖 existing Harness `1` exit transcript 包含中文摘要，且正式资产快照不变。
7. 文档记录本轮决策、验证结果和 Self-Harness Gate；长期 README / init-workflow 若已有维护入口状态说明，不为轻量摘要重复扩写。

## 关键决策 / 取舍

- 新增只读渲染 helper，优先复用现有 schema 文件读取；不解析 raw signal 字符串作为事实源。
- 摘要放在 raw signals 前，解决“先读懂再审计”的 CLI 顺序问题。
- 每个摘要分组控制为短句，避免替代完整 raw signals、triage guidance 和 `.ai/*` 报告。
- 维护动作编号通过上一轮共享 `existing_harness_actions` 契约查询，避免再次引入编号漂移。

## Assumptions / Risks

- Assumption：Maintainer 仍需要 raw signals 做审计和测试定位，因此本轮不删除 `key=value` 输出。
- Risk：摘要与 raw signals 表达可能重复；本轮把摘要限定为概览，不展开每个 failed check 或每个 candidate。
- Risk：读取 schema 文件做摘要可能因旧 Harness schema 无效而显式失败；这符合已有维护入口规则，不引入 fallback。
