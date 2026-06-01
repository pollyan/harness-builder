# Existing Harness 智能维护动作抽取设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、`docs/strategy/Harness Builder — 面向遗留代码库治理的 AI Coding Harness 生成器.md`、`docs/engineering/architecture.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/engineering/llm-contracts.md`、`docs/todos/README.md`、`docs/evolution-log.md`。
- 已检查当前代码：`existing_harness_action_runner.py` 335 行，仍同时承接 `exit`、`assess`、`improve`、`benchmark`、`recommend-workflow`、review action 委托、`self-improve`、`reinit` 和 unknown action；`existing_harness_review_actions.py` 与 `existing_harness_entry.py` 已分别抽出 review 治理动作和维护入口编排；`tests/unit/test_existing_harness_action_boundaries.py` 已存在 review action 边界测试。
- Todo 状态：`docs/todos/README.md` 当前没有 open todo，历史 todo 均为 implemented / paused 背景，因此本轮从 Current State Gap Analysis 选题。
- 按需未展开：`docs/engineering/sensor-and-gate-rules.md`；本轮不修改 Sensor、benchmark 检查规则或 hard gate 策略。
- Sub agent：按目标模式尝试启动只读 explorer 调研 action runner 边界，当前环境返回 `agent thread limit reached`；本轮由主线程完成调研、设计、TDD、实现和验证。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Existing Harness 智能维护动作抽取 | Gate / 当前代码 / 架构规则 | `existing_harness_action_runner.py` 负责动作路由与 deterministic 动作编排，LLM / review-only 智能动作在独立模块维护 | 入口、review actions、action failure helper 和 summaries 已拆出；`recommend-workflow` / `self-improve` 已有成功与失败 integration 覆盖 | 两个 LLM / review-only 动作仍在 runner 内直接导入 schema、`yaml`、LLM 工具和 summary，后续改智能动作错误边界或 artifact 容易误伤 deterministic action | 保护“再次进入已有 Harness -> 运行智能维护动作 -> 生成 review-only 产物或显式失败”的用户旅程，降低后续 self-improve / workflow recommendation 迭代风险 | 中低；行为保持型抽取，不改 prompt、schema、产物契约或 Runtime 分工；风险集中在 monkeypatch 路径、trace artifact、失败摘要 | 新增 unit 边界测试；更新 existing Harness LLM failure monkeypatch；recommend-workflow / self-improve targeted integration 与 fast regression | 无外部凭证；真实 DeepSeek acceptance 仍属于 full gate | runner 不再直接依赖 `recommend_workflow`、`run_self_improve`、`WorkflowRecommendationReport`、`SelfImprovePackageManifest`；新模块提供两条 action delegate；现有成功 / 失败 transcript 和 trace 通过 | 本轮 |
| B. 首次 init completion summary 继续紧凑化 | 上轮 Gate / init North Star | 首次初始化完成摘要更短、更行动优先 | completion 已展示成熟度、benchmark、入口文件、用户补充和资产分组 | 仍可能有视觉密度改进空间，但需要重新定义具体 transcript 问题 | 直接改善首次 init 交付阅读体验 | 低到中；需要仔细避免削弱交付说明 | guided init transcript integration | 无 | 新增 transcript 断言和 README / init workflow 同步 | 下一轮候选 |
| C. Push / full regression 同步工作包 | 用户提醒 / Git 状态 | 完整本地工作包通过 full regression 后 push 到 GitHub | 当前 `main` ahead 90；fast 可在本地运行 | full regression acceptance 在沙箱内 DNS 失败，非沙箱会向 DeepSeek 外发本地 fixture / benchmark evidence 且审批被拒 | 降低远端滞后，但不是代码能力 milestone | 高，受外部网络和数据外发审批限制 | `scripts/test-full.sh`、`git push` | 需要外部 DeepSeek 网络与合规授权 | full gate 通过后 push；当前作为 Gate 限制记录 | 后续同步边界 |

排序结论：

1. 选择 A。它紧接已有 Harness 入口、review actions、failure trace 和 entry extraction 的架构收口，直接服务 init North Star 中“再次进入已有 Harness”的维护旅程；同时抽取范围小、可测试、不改变用户契约。
2. B 暂不选，因为首次 init completion 已有多轮用户可见增强，本轮更适合先降低已有 Harness 维护入口继续演进的工程风险。
3. C 不作为本轮 milestone。push 需要 full regression；当前环境对真实 DeepSeek acceptance 的外部访问与数据外发未获许可，不能把它伪装成可完成代码切片。

## 本轮 Milestone

作为 Harness Builder 维护者，当我继续演进已有 Harness 入口里的 `recommend-workflow` 和 `self-improve` 智能维护动作时，我可以在独立的 intelligent action 模块中维护 LLM / review-only 动作的输入、schema 读取、trace artifact、成功摘要和 action-specific 失败边界，从而让 action runner 保持路由清晰，并降低改智能动作时影响 `assess`、`improve`、`benchmark`、review governance 或 `reinit` 的风险。

## 验收标准

1. 新增 `src/harness_builder_agent/tools/existing_harness_intelligent_actions.py`，暴露 `run_recommend_workflow_action()` 与 `run_self_improve_action()`。
2. `existing_harness_action_runner.py` 对 `recommend-workflow` 和 `self-improve` 只做 delegate，不再直接导入或调用 `recommend_workflow()`、`run_self_improve()`，也不直接依赖 `WorkflowRecommendationReport`、`SelfImprovePackageManifest` 或 `yaml`。
3. CLI 行为保持：`recommend-workflow` 仍收集 task brief / task id，空 task brief 显式失败；成功时仍记录 latest recommendation、history、experience、maturity artifacts；失败时仍使用 action-specific trace，不写顶层 `init failed`，不创建 `.ai/task-runs`。
4. CLI 行为保持：`self-improve` 成功时仍记录 self-improve package、maturity、candidate、review artifacts；失败时仍记录 `existing_harness_action=self-improve`、短错误、错误类型，不覆盖正式资产、不创建 `.ai/task-runs`。
5. 新增或增强 unit 边界测试，证明 runner 委托 intelligent actions，且智能动作模块承接 LLM / review-only schema 依赖。
6. 更新 integration monkeypatch 路径到新模块，并回归 recommend-workflow / self-improve 成功与失败切片。
7. 不修改 `.ai` schema、LLM prompt、benchmark 检查规则、正式资产 writer、Sensor 或 Runtime 分工。
8. 提交前运行 `scripts/test-fast.sh`；full regression / push 按 Gate 记录外部限制。

## 关键决策 / 取舍

- 本轮只抽取 `recommend-workflow` 和 `self-improve`，因为它们共同属于已有 Harness 入口中的 LLM / review-only 智能动作；`assess`、`improve`、`benchmark` 仍保留在 runner，避免把 deterministic 动作也一并大拆。
- 新模块可以继续使用 `typer.prompt`，因为 guided existing Harness 动作本身需要交互式输入；runner 只负责选择后委托。
- 不为隐藏测试保留 runner 上的 `recommend_workflow` / `run_self_improve` monkeypatch alias；本轮把测试路径迁到新模块，模块边界即新事实源。
- 不改变错误文案、trace summary、artifact kind 或 Runtime 边界。

## Assumptions / Risks

- Assumption：当前外部用户只通过 CLI 使用这些 guided action，不依赖 `existing_harness_action_runner.py` 内部导入符号。
- Risk：行为保持型抽取可能遗漏 artifact 或 trace 字段；用 targeted integration 锁住成功和失败路径。
- Risk：monkeypatch 路径迁移可能暴露隐藏测试对内部实现的依赖；这是可接受的内部边界调整，公开 CLI 契约不变。
- Risk：full regression 仍可能因真实 DeepSeek / 网络 / 数据外发审批失败；本轮不将 push 作为完成条件。
