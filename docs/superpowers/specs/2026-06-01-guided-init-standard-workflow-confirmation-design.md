# Guided Init Standard Workflow 确认设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、`docs/strategy/Harness Builder — 面向遗留代码库治理的 AI Coding Harness 生成器.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/engineering/architecture.md`、`docs/todos/README.md`、`docs/evolution-log.md`、`src/harness_builder_agent/tools/interactive_init.py`、`src/harness_builder_agent/tools/prewrite_preview.py`、`src/harness_builder_agent/tools/init_summary.py`、相关 guided init / interaction decisions tests、当前 git 状态。
- 按需未展开：`llm-contracts.md`、`sensor-and-gate-rules.md`；本轮不修改 LLM、prompt、benchmark check、schema 或 Runtime 产物。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Guided init Workflow 确认阶段补齐 `standard` | init North Star / 当前代码审查 | 用户在 Workflow 补充前看到 `lightweight`、`bugfix`、`standard` 三类工作流，以及 standard 的高风险 / 跨模块 / 安全数据升级边界 | 写入前 preview 和正式 `harness-config.yaml` 已包含 `standard` 与 `standard-escalation`；Workflow prompt 只解释 `lightweight` / `bugfix`，`interaction-decisions.yaml` 也只记录这两类 shown workflow | 用户在回答 Workflow 补充时缺少 standard escalation 的上下文，导致补充可能围绕不完整工作流模型产生 | 让渐进式交互在“问用户 Workflow 补充之前”就展示完整工作流基线，强化风险升级和 Runtime 分工说明 | 低；CLI 文案和 machine-readable shown workflow 列表变更，需更新 integration 断言 | unit 覆盖 `_show_workflows()` 输出与返回值；guided integration 覆盖 transcript 和 `interaction-decisions.yaml` | 无外部凭证 | 输出包含 `standard` 高风险说明，decisions `shown_workflows` 包含三类工作流，正式 routing policy 仍不被用户自由文本直接修改 | 本轮 |
| B. 首次 init completion summary 继续细化 | 上轮 Gate / init North Star | 写入后终端摘要进一步减少内部字段，增强下一步行动说明 | completion summary 已覆盖成熟度、下一步、Benchmark、优先文件、资产 ready 概览和用户补充 | 当前没有比 A 更明确的新缺口；进一步细化需要重新审查 transcript | 可能提升交付体验 | 中；容易变成文案打磨 | unit / integration transcript | 无 | 新增更具体用户故事后验收 | 下一轮候选 |
| C. full regression / push 工作包 | 用户提醒 / Git 状态 | 完整工作包同步 GitHub | 本地 ahead 71，上一轮 fast 通过 | `scripts/test-full.sh` acceptance 因缺 `DEEPSEEK_API_KEY` 和 `.benchmarks/RuoYi-Vue` / `.benchmarks/eShopOnWeb` 失败，不能合规 push | 远端同步本地独立价值 | 外部环境阻塞 | `scripts/test-full.sh` + `git push` | DeepSeek key 和真实仓库 | full 通过后 push | 本轮完成后评估 |

排序结论：

1. 选择 A。它直接服务 `init-north-star.md` 的“渐进式协作”和“Workflow Skills / routing 设计预览”目标，且发生在用户输入 Workflow 补充之前，比只在后续预览展示 standard 更符合交互时序。
2. B 暂不选，因为 completion summary 当前已有较完整契约，缺少一个比 A 更清晰的独立用户故事。
3. C 不作为功能 milestone，但本轮完成后按仓库规则评估 push；若 full regression 仍因外部前置失败，则不 push。

本轮用户故事：

作为 Harness Maintainer，当我在首次 guided `init` 中进入“推荐工作流”阶段并准备补充 Workflow 说明时，我可以同时看到 `lightweight`、`bugfix` 和 `standard` 三类工作流及 standard 的高风险升级边界，从而基于完整的工作流模型补充团队约束，而不是只围绕低风险和缺陷修复两个路径作答。

## 设计

- 更新 `_show_workflows()`：
  - 在 CLI 中增加 `standard` 说明，强调复杂、高风险、跨模块、安全 / 数据 / 影响不清任务会升级。
  - `WorkflowConfirmation.shown_workflows` 从 `["lightweight", "bugfix"]` 扩展为 `["lightweight", "bugfix", "standard"]`。
  - 用户输入的 Workflow 补充仍保持 review-only，只进入 interaction decisions / project context / human-input-needed / improvement candidate，不直接修改正式 routing policy。
- 更新 guided init integration 断言，确认 transcript 和 `interaction-decisions.yaml` 都包含 `standard`。
- 更新 README 和 `docs/engineering/init-workflow.md` 的稳定行为说明。

## 非目标

- 不修改 `HarnessConfig.default()`、routing rule、Workflow Skill 模板或 benchmark。
- 不新增 Workflow 类型。
- 不把用户自由文本 Workflow 补充直接应用为正式 routing policy。
- 不修改 schema；`shown_workflows` 已是字符串列表。
- 不执行 Runtime、不创建 `.ai/task-runs`。

## 验收标准

- RED：新增 unit test 先证明 `_show_workflows()` 没有输出 `standard`，返回的 `shown_workflows` 缺少 `standard`。
- 实现后 unit test 通过，输出包含 standard 高风险 / 跨模块 / 安全数据边界。
- guided init integration 通过，并断言 transcript 的“推荐工作流”阶段包含 `standard`，`interaction-decisions.yaml` 的 `shown_workflows` 包含三类工作流。
- `interaction-decisions.md` / project context 中展示的 workflow 列表可自然包含 `standard`，但正式 `harness-config.yaml` routing policy 不受自由文本补充直接修改。
- `compileall`、`git diff --check`、`scripts/test-fast.sh` 通过。

## Assumptions / Risks

- Assumption：`standard` 是当前默认 Harness 的固定 Workflow Skill，也是风险升级主路径；在 Workflow 确认阶段展示它属于产品事实补齐，而非新增能力。
- Risk：部分测试固定断言 `shown_workflows == ["lightweight", "bugfix"]`；本轮更新为三类工作流，并保留 review-only routing boundary。
- Risk：文案变长；但该阶段正是用户补充 Workflow 说明前，补齐 standard 说明比让用户稍后在 preview 才看到更合适。

## Sub Agent

按目标模式尝试启动只读 explorer 审查 Workflow 确认阶段缺口，当前环境返回 `agent thread limit reached`。主线程继续完成调研、TDD、实现和验证。
