# 写入前 Workflow Skills 预览设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景 North Star、`docs/todos/README.md`、`docs/engineering/architecture.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/evolution-log.md`。
- 已对比：`src/harness_builder_agent/tools/prewrite_preview.py`、`src/harness_builder_agent/schemas/harness_config.py`、`src/harness_builder_agent/templates/skills/*/SKILL.md`、`tests/unit/test_interactive_init_preview.py`、`tests/integration/test_init_on_fixture_projects.py`、既有写入前 preview / workflow routing specs。
- 按需未展开：`docs/engineering/llm-contracts.md` 和 `sensor-and-gate-rules.md`。本轮不修改 LLM、prompt、scan schema、benchmark check 或 Sensor 规则。
- Sub agent：尝试启动只读 explorer 审查 Workflow Skills preview 覆盖，当前环境返回 `agent thread limit reached`；本轮由主线程完成调研、TDD、实现和验证。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. 写入前 Workflow Skills 预览 | init North Star / 新发现 | 写入前 preview 明确展示将生成 `lightweight`、`bugfix`、`standard` Workflow Skills，并说明每个 Skill 的路径、关键阶段、引用的 Guides / Sensors 和对应 routing rule | `harness-config.yaml` 已有 workflows 与 routing rules；写入会复制三个 Skill 模板；completion summary 会概览 Workflow Skills | `show_prewrite_maturity_preview()` 只展示 Guides、Sensors 和 Workflow routing，没有展示 Workflow Skills 作为即将生成的核心资产，也没有说明它们如何引用 Guides / Sensors | 让 Maintainer 在确认写入前理解“哪些工作流会被生成、何时使用、依赖哪些上下文与验证”，补齐 North Star 的设计预览闭环 | 低：纯 preview 文案和测试，不改 schema / writer / Runtime | unit + guided integration transcript；config schema 已覆盖 skill paths | 无外部依赖 | 本轮 |
| B. Existing Harness action execution 进一步抽模块 | 上轮 Gate / 架构债 | 已有 Harness action runner 进一步按动作分层，降低后续维护入口迭代成本 | `interactive_init.py` 已降到约 558 行，但 `existing_harness_action_runner.py` 约 646 行，仍聚合多个动作 | 工程可维护性仍有改善空间，但本轮用户可见价值弱于 A | 降低未来改 action 的冲突和回归风险 | 中：行为保持型重构需大量 existing Harness 回归 | unit / integration 行为等价 | 无外部依赖 | 下一轮候选 |
| C. full regression / push 工作包 | Gate / git 状态 | 本地完整工作包通过 full regression 后 push | 当前分支本地领先远端 65 个提交 | push 前需要 `scripts/test-full.sh`，涉及 acceptance / DeepSeek / `.benchmarks` 和网络前置；本轮仍有可本地推进的 init gap | 降低分叉风险 | 外部前置高，不适合作为本轮代码 milestone | full regression 与 push 结果 | `DEEPSEEK_API_KEY`、真实仓库、网络 | 外部前置候选 |

排序结论：

1. 选择 A。它直接命中 `init-north-star.md` 中“将生成哪些 Workflow Skills，以及它们如何引用 Guides / Sensors”的目标态，且可在一个清晰用户可见切片内完成。
2. B 是真实工程债，但当前 preview 仍缺少核心用户信息，优先级低于 A。
3. C 仍受外部前置影响，不作为本轮 milestone。

## 本轮 milestone

作为 Harness Maintainer，当我在首次 guided `init` 的最终确认前查看 Harness 设计预览时，我可以看到将生成的 `lightweight`、`bugfix`、`standard` Workflow Skills、它们的文件路径、关键阶段、对应 routing rule，以及会加载哪些 Guides / Sensors，从而在写入前理解即将得到的不是孤立文件，而是一套可被 Runtime 消费的工作流控制资产。

## 验收标准

1. `show_prewrite_maturity_preview()` 在 `将生成的 Sensors` 与 `Workflow routing` 之间输出稳定的 `将生成的 Workflow Skills` section。
2. section 至少展示 `lightweight`、`bugfix`、`standard` 三个 workflow、各自 `.ai/skills/*/SKILL.md` 路径和关键阶段摘要。
3. section 根据 `workflow_routing.rules` 展示每个 workflow 对应的 routing rule，并说明会引用哪些 Guides / Sensors。
4. 有风险路径时，`standard` 的 Skill preview 与 routing preview 都能体现高风险任务升级语义；本轮不重复展示所有 `risk_area:*` trigger，只保持上一轮 routing 预览负责 trigger 明细。
5. 不修改 `.ai` schema、Skill 模板、writer、benchmark、LLM 或 Runtime 分工。
6. 完成前运行相关 unit、相关 guided init integration、`compileall`、`git diff --check` 和 `scripts/test-fast.sh`。

## 决策与取舍

- Workflow Skills preview 以 `HarnessConfig` 为事实源，避免硬编码路径和 routing 引用。
- 只展示前几个 stage / guide / sensor，完整契约仍以 `.ai/skills/*/SKILL.md` 和 `harness-config.yaml` 为准。
- 本轮不修改 Skill 模板内容，也不动态生成 Workflow Skills；它只是让写入前设计预览更接近即将落盘的真实资产。

## Assumptions / Risks

- Assumption：三个固定 Skill 是当前产品边界内的稳定基线，写入前展示它们有助于 Maintainer 形成完整 Harness 结构心智。
- Risk：preview 输出会略长。通过每个 workflow 只展示路径、关键阶段和 routing 引用，避免变成完整 `harness-config.yaml` 展开。
