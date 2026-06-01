# Existing Harness Signal Renderer 抽取设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/README.md`、`docs/engineering/architecture.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、近期 completion specs / plans 与 `docs/evolution-log.md`。
- 当前代码 / 测试检查：`src/harness_builder_agent/tools/interactive_init.py` 中 `_handle_existing_harness_entry()`、`_benchmark_signal_lines()`、`_workflow_routing_status_lines()`、`_experience_status_lines()` 等 helper，已拆出的 `existing_harness_actions.py`、`existing_harness_status.py`，以及 existing Harness 相关 integration / unit tests。
- 按需未展开：`docs/engineering/llm-contracts.md` 和 `sensor-and-gate-rules.md`；本轮不修改 LLM、prompt、schema、scan reconciler、Sensor 或 benchmark 规则。
- Todo 状态：`docs/todos/README.md` 当前没有 open todo；本轮从上一轮 Gate 候选和当前代码结构选择工程信任故事。
- Sub agent：尝试启动 explorer 做只读调研，但当前会话返回 `agent thread limit reached`；本轮由主线程完成调研、TDD、实现和验证。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Existing Harness signal renderer 抽取 | 上轮 Gate / 架构规则 | 已有 Harness 维护入口的 benchmark / workflow routing / experience signals 有独立模块和 unit，主向导只负责流程编排 | actions contract 和 status overview 已拆出；integration 覆盖 existing Harness 入口 | signal 读取 / 渲染 helper 仍堆在 `interactive_init.py`，与主向导、动作执行混在一起 | 保护再次进入已有 Harness 的状态感知维护入口，降低后续维护入口体验迭代风险 | 低到中：行为等价抽取，不改 schema / LLM / Runtime | 新 unit 直接覆盖 signal module；existing Harness integration 验证 transcript 不漂移；fast regression | 依赖现有 `BenchmarkReport`、`HarnessConfig`、`ExperienceIndex`、`Questionnaire` schema | 新模块可直接返回 benchmark / workflow / experience signals；CLI 输出保持不变 | 本轮 |
| B. Completion 生成清单进一步紧凑化 | 上轮 Gate | 写入后终端摘要更短 | completion 已行动优先，用户补充已紧凑 | 生成清单仍列 8 类资产，但它是交付摘要中的核心确认信息，压缩收益低于现有维护入口工程风险 | 降低终端长度 | 低 | unit / integration transcript | 需要定义哪些资产可以合并展示 | 下一轮候选 |
| C. Push 前 full regression / 远端同步 | Gate / 发布节奏 | 完整工作包完成后统一 full regression 并 push | 本地已领先远端多个 commit | 当前没有用户要求 push；full acceptance 依赖真实 DeepSeek / 真实仓库，成本高 | 远端同步价值高，但应以完整工作包为边界 | 高 | `scripts/test-full.sh` + push | 外部服务和真实仓库 | 不在本轮 | 后续工作包 |

排序结论：

1. 选择 A，因为 recent init 体验已经把首次 completion 打磨到更短，下一步应降低已有 Harness 维护入口继续演进的代码风险；这直接保护 `init-north-star.md` 的“再次进入已有 Harness”旅程。
2. B 暂不选，因为生成清单仍是首次交付摘要的核心内容，压缩收益小于已有 Harness 入口模块边界收益。
3. C 暂不选，因为本轮不是完整 push 工作包，且 push 前 full regression 有外部依赖成本。

## 本轮 Milestone

作为 Harness Builder 维护者，当我继续打磨已有 Harness 维护入口的健康状态、signals 和 triage 体验时，我可以在独立 signal renderer 模块中修改和单测 benchmark / workflow routing / experience signals，从而降低触碰主 guided init 编排文件的风险，并确保 Maintainer 再次运行 `init` 时看到的维护信号不漂移。

## 验收标准

1. 新增 `existing_harness_signals.py`，集中提供 benchmark status、benchmark signals、workflow routing signals 和 experience / review signals。
2. `interactive_init.py` 不再内联这些 signal helper，只调用新模块；existing Harness CLI transcript 和动作语义不变。
3. 新 unit 覆盖 benchmark 缺失 / failed detail、workflow routing risk trigger、experience index / human-input / workflow recommendation signals。
4. Existing Harness integration 至少覆盖只读 exit transcript，证明维护入口输出不漂移且不触发 scan / 覆盖正式资产。
5. 不修改 `.ai` schema、LLM、benchmark 规则、正式资产生成或 Runtime 分工。
6. 提交前运行 `scripts/test-fast.sh`。

## 关键决策 / 取舍

- 本轮只抽取 signals，不搬动作执行分支；`_handle_existing_harness_entry()` 仍负责选择动作和 trace。
- 保持旧 underscore facade `_benchmark_signal_lines()` 等兼容内部调用的可能性，避免一次性大改 tests。
- 复用 `harness_builder_agent.tools.human_confirmation.SCAN_CONFIRMATION_TYPES`，避免继续在 `interactive_init.py` 重复维护 scan confirmation 类型集合。

## Assumptions / Risks

- Assumption：signals helper 是现有维护入口中最容易继续膨胀、且最适合纯函数单测的部分。
- Risk：行为等价抽取可能遗漏一个 schema import 或 helper 依赖；本轮用 direct unit、existing Harness integration 和 fast regression 兜住。
