# Guided review-candidate 失败 trace 设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景 North Star、`docs/todos/README.md`、`docs/engineering/architecture.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/evolution-log.md`。
- 已对比：`src/harness_builder_agent/tools/interactive_init.py`、`src/harness_builder_agent/tools/existing_harness_action_runner.py`、`tests/integration/test_init_on_fixture_projects.py`、既有 Existing Harness action runner spec。
- 按需未展开：`docs/engineering/llm-contracts.md` 与 `sensor-and-gate-rules.md`。本轮不修改 LLM、scan、benchmark check、Sensor 或正式资产 writer。
- Sub agent：尝试启动只读 explorer 审查 existing Harness action runner，当前环境返回 `agent thread limit reached`；本轮由主线程完成调研、TDD、实现和验证。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. guided `review-candidate` 失败 trace | 新发现 / Gate | Maintainer 在已有 Harness 入口选择 `review-candidate` 时，即使候选报告缺失或候选 ID 不存在，trace 也要明确记录 `existing_harness_action=review-candidate`、candidate id 和失败原因 | 成功治理、workflow policy 禁止应用、治理命令失败都有 action-specific trace；standalone `review-candidate` 也有失败 trace | `show_asset_candidate_summary()` 和 `find_asset_candidate()` 在 action-specific trace 前执行，缺文件或未知候选会落成泛化 `init` failure，缺少维护动作上下文 | 保护“再次运行 init -> 选择候选治理 -> 失败后可审计定位”的用户旅程，避免治理失败看起来像普通 init 崩溃 | 低：只补错误路径 trace，不改成功路径、schema、writer、Runtime | integration RED 覆盖缺失 report 和未知 candidate；trace summary / stages 可验证 | 无外部依赖 | 本轮 |
| B. Existing Harness action runner 继续按动作拆模块 | 上轮 Gate / 架构债 | action runner 进一步拆分 governance / assessment / recommendation 动作，降低文件复杂度 | 当前 runner 已从 `interactive_init.py` 抽出，但仍有 646 行、多个动作分支 | 工程债存在，但不是直接用户失败；可放到更完整重构 milestone | 降低后续维护入口改动风险 | 中：行为等价重构覆盖面大 | unit / integration 回归 | 无外部依赖 | 下一轮候选 |
| C. full regression / push 工作包 | Gate / git 状态 | 本地多个已验证 commit 在完整工作包边界通过 full regression 后 push | 当前分支本地领先远端 67 个提交 | push 前需要 `scripts/test-full.sh`，涉及真实 acceptance / DeepSeek / `.benchmarks` / 网络；本轮仍有本地可实施维护入口 gap | 降低分叉风险 | 高：外部前置多 | full regression / push 结果 | `DEEPSEEK_API_KEY`、真实仓库、网络 | 外部前置候选 |

排序结论：

1. 选择 A。它是用户可触达的 existing Harness 维护入口错误路径，范围小、可测试，并且强化 trace / 可观测边界。
2. B 继续保留为工程债候选，但不应在没有具体用户风险时做大范围搬迁。
3. C 不进入本轮；当前不 push。

## 本轮 milestone

作为 Harness Maintainer，当我在已有 Harness 维护入口选择 `review-candidate` 但 `.ai/review/asset-candidates.yaml` 缺失或输入了不存在的候选 ID 时，我可以获得明确失败，并且 generation trace 会记录这是 `review-candidate` 维护动作失败、失败的 candidate id 和原因，从而后续排查不需要猜测这是普通 init 失败还是候选治理失败。

## 验收标准

1. guided `review-candidate` 在候选报告缺失时，trace stage 记录 `existing-harness` failed，summary 包含 `existing_harness_action=review-candidate` 和错误信息。
2. guided `review-candidate` 在候选 ID 不存在时，trace 同样记录 action-specific failure，并保留用户输入的 candidate id。
3. 成功 `review-candidate`、applied、workflow policy 禁止应用等既有路径行为不变。
4. 不修改正式 Guides、Sensors、Workflow Skills、`harness-config.yaml`、inventory、command catalog，也不创建 `.ai/task-runs`。
5. 完成前运行相关 integration、`compileall`、`git diff --check` 和 `scripts/test-fast.sh`。

## 决策与取舍

- 只补 `review-candidate` action 的早期失败路径，因为它当前存在明确 trace 漏洞。
- 不抽取整个 action runner，也不改变 prompt 顺序或用户输入格式。
- 抛给 Typer 的异常仍使用 `typer.BadParameter`，但在抛出前先写 action-specific trace。

## Assumptions / Risks

- Assumption：缺失候选报告和未知候选 ID 都属于 Maintainer 可修复的治理前置问题，应显式记录为维护动作失败。
- Risk：错误输出中可能仍包含 Typer 的参数错误格式；本轮只要求 trace 和消息包含可定位原因，不重做全局异常渲染。
