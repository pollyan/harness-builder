# Existing Harness 确定性维护动作抽取设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、`docs/strategy/Harness Builder — 面向遗留代码库治理的 AI Coding Harness 生成器.md`、`docs/engineering/architecture.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/todos/README.md`、`docs/evolution-log.md`。
- 已检查当前代码：`existing_harness_action_runner.py` 197 行，已经委托 review actions 与 intelligent actions，但仍直接持有 `assess`、`improve`、`benchmark` 的业务调用、trace artifact、summary 与 `BenchmarkReport` 依赖；`existing_harness_intelligent_actions.py` 和 `existing_harness_review_actions.py` 已分别承接 LLM / review-only 智能动作与治理动作。
- Todo 状态：`docs/todos/README.md` 当前没有 open todo；历史 todo 均为 implemented / paused 背景。
- 按需未展开：`docs/engineering/llm-contracts.md` 与 `docs/engineering/sensor-and-gate-rules.md`；本轮不修改 LLM、prompt、schema、benchmark 检查规则、Sensor 或 hard gate 策略。
- Sub agent：按目标模式尝试启动只读 explorer 审查 runner 剩余职责，当前环境返回 `agent thread limit reached`；主线程完成调研、设计、TDD、实现和验证。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Existing Harness 确定性维护动作抽取 | Gate / 当前代码 / 架构规则 | `existing_harness_action_runner.py` 只负责动作路由和 exit / reinit / unknown 控制流；确定性维护动作在独立模块维护 | entry、review actions、intelligent actions、failure helper 和 summaries 已拆出；assess / improve / benchmark integration 已覆盖正式资产边界 | `assess`、`improve`、`benchmark` 仍在 runner 内直接导入 maturity / benchmark / improvement 业务模块和 `BenchmarkReport`，runner 仍承担过多动作实现细节 | 保护“再次进入已有 Harness -> 运行确定性维护动作”的旅程，降低后续改 maturity / benchmark / improvement 维护动作时误伤路由、review 或 LLM action 的风险 | 中低；行为保持型抽取，不改 schema / writer / benchmark check；风险集中在 artifact 和 trace summary 漂移 | 新增 unit 边界测试；assess / improve / benchmark targeted integration；完整 init integration；fast regression | 无外部凭证；full acceptance 仍受 DeepSeek 网络 / 数据外发审批限制 | runner 不再直接依赖 `assess_maturity`、`generate_improvements`、`run_benchmark`、`BenchmarkReport`；新模块提供三个 delegate；现有 CLI 和 trace 通过 | 本轮 |
| B. 首次 init completion summary 继续紧凑化 | 上轮 Gate / init North Star | 初始化完成摘要更短、更行动优先 | completion 已展示成熟度、benchmark、入口文件、用户补充和资产分组 | 仍可能有视觉密度改进空间，但需要重新定义具体 transcript 问题 | 改善首次 init 交付阅读体验 | 低到中；主要是 transcript 改动 | guided init integration / snapshot-like transcript 断言 | 无 | 新增用户可见断言和文档同步 | 下一轮候选 |
| C. Push / full regression 同步工作包 | 用户提醒 / Git 状态 | 完整本地工作包通过 full regression 后 push 到 GitHub | 当前 `main` ahead 91；fast 可运行 | full regression acceptance 在沙箱内 DNS 失败，非沙箱会向 DeepSeek 外发本地 fixture / benchmark evidence 且审批被拒 | 让远端同步本地工作，但不是代码能力 gap | 高，受外部网络和数据外发审批限制 | `scripts/test-full.sh`、`git push` | 需要外部 DeepSeek 网络与合规授权 | full gate 通过后 push；当前作为 Gate 限制记录 | 后续同步边界 |

排序结论：

1. 选择 A。它承接上一轮 intelligent action 抽取，是已有 Harness 维护入口模块化的自然收口；完成后 runner 会更接近“只做路由”，后续迭代可以在 action 家族模块内演进。
2. B 暂不选，因为当前代码结构仍有明确的维护动作实现混杂，先降低工程风险更利于后续用户可见切片。
3. C 不作为本轮 milestone。push 需要 full regression；当前环境对真实 DeepSeek acceptance 的外部访问与数据外发未获许可，不能把它伪装成可完成代码切片。

## 本轮 Milestone

作为 Harness Builder 维护者，当我继续演进已有 Harness 入口中的 `assess`、`improve` 和 `benchmark` 确定性维护动作时，我可以在独立 deterministic action 模块中维护 maturity refresh、improvement candidate generation、benchmark validation 的调用、trace artifact 和 summary 输出，从而让 action runner 保持清晰路由职责，并降低改确定性维护动作时影响 review / LLM actions 或 reinit 控制流的风险。

## 验收标准

1. 新增 `src/harness_builder_agent/tools/existing_harness_deterministic_actions.py`，暴露 `run_assess_action()`、`run_improve_action()` 与 `run_benchmark_action()`。
2. `existing_harness_action_runner.py` 对 `assess`、`improve` 和 `benchmark` 只做 delegate，不再直接导入或调用 `assess_maturity()`、`generate_improvements()`、`run_benchmark()`，也不直接依赖 `BenchmarkReport`。
3. CLI 行为保持：`assess` 仍只刷新 maturity / init summary 产物，trace summary 保留 `existing_harness_action=assess` 和 `artifact_count=4`。
4. CLI 行为保持：`improve` 仍先刷新 experience index / maturity，再生成 review-only improvement candidates，trace summary 保留 `existing_harness_action=improve` 和 `artifact_count=8`。
5. CLI 行为保持：`benchmark` 仍输出 benchmark summary，trace summary 保留 benchmark status、quality status、check count 与 failed check count；benchmark failed 仍以 failed trace 结束但不覆盖正式 Guides / Sensors / Workflow Skills / config / inventory。
6. 新增或增强 unit 边界测试，证明 runner 委托 deterministic actions，且确定性动作模块承接 maturity / benchmark / improvement 依赖。
7. 不修改 `.ai` schema、LLM prompt、benchmark 检查规则、正式资产 writer、Sensor 或 Runtime 分工。
8. 提交前运行 `scripts/test-fast.sh`；full regression / push 按 Gate 记录外部限制。

## 关键决策 / 取舍

- 本轮只抽取 `assess`、`improve`、`benchmark` 这三个确定性维护动作；`exit`、`reinit` 和 unknown action 仍留在 runner，因为它们是路由控制流而非业务动作家族。
- 新模块继续复用 `existing_harness_action_summaries.py` 的 benchmark / improvement 摘要，避免文案漂移。
- 不改变 existing Harness action 编号、菜单、prompt、trace event、artifact kind 或输出文件。
- 不为 hidden tests 保留 runner 上的 direct `assess_maturity` / `run_benchmark` / `generate_improvements` alias；模块边界即新事实源，公开 CLI 契约保持不变。

## Assumptions / Risks

- Assumption：外部用户通过 CLI 使用这些 guided action，不依赖 runner 的内部导入符号。
- Risk：行为保持型抽取可能遗漏 artifact 或 trace summary 字段；用 targeted integration 与完整 init integration 覆盖。
- Risk：`benchmark` action 的 failed status 是刻意语义，本轮必须保持 failed trace 而不是改成 success 或异常。
- Risk：full regression 仍可能因真实 DeepSeek / 网络 / 数据外发审批失败；本轮不将 push 作为完成条件。
