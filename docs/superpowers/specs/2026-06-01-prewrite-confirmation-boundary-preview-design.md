# 写入前待确认边界预览设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景 North Star、`docs/todos/README.md`、`docs/engineering/architecture.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/engineering/sensor-and-gate-rules.md`、`docs/evolution-log.md`。
- 已对比：`src/harness_builder_agent/tools/prewrite_preview.py`、`src/harness_builder_agent/tools/guided_scan_presentation.py`、`src/harness_builder_agent/tools/interactive_init.py`、`src/harness_builder_agent/schemas/scan.py`、`src/harness_builder_agent/schemas/command_catalog.py`、`tests/unit/test_interactive_init_preview.py`、`tests/integration/test_init_on_fixture_projects.py`、近期写入前 preview / scan follow-up / self-check specs。
- 按需未展开：`docs/engineering/llm-contracts.md`。本轮不修改 LLM prompt、LLM schema、scan reconciler 或 DeepSeek acceptance 行为。
- Sub agent：尝试启动只读 explorer 审查 prewrite preview 的待确认边界覆盖，当前环境返回 `agent thread limit reached`；本轮由主线程完成调研、TDD、实现和验证。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. 写入前待确认边界预览 | init North Star / 新发现 | 写入前 Harness 设计预览明确展示低置信度命令、scan follow-up、LLM self-check 和 scan warning 等仍需人工确认的内容，并说明确认写入不会自动关闭追问或验证事实 | 扫描结果阶段已展示深度追问、LLM 二次自检和回答建议；questionnaire / human-input 会持久化待确认项；completion summary 会提示仍需人工确认 | 最终确认前的 `show_prewrite_maturity_preview()` 只展示成熟度、扫描补充、团队规则、Workflow、Guides、Sensors、Workflow Skills 和 routing，没有集中说明“哪些内容仍是低置信度或待人工确认” | 让 Maintainer 在输入 `confirm` 前再次看到可信度边界，避免把“生成资产”误解为“追问已关闭 / 低置信度已验证” | 低：纯 preview renderer 和 transcript 测试，不改 schema、writer、benchmark 或 Runtime | unit + guided integration transcript；可用 mocked scan metadata 和 low-confidence command 验证 | 无外部凭证；不依赖真实 DeepSeek | 本轮 |
| B. Existing Harness action execution 进一步抽模块 | 上轮 Gate / 架构债 | 已有 Harness action runner 按动作分层，降低后续维护入口迭代成本 | 维护入口已经有 action runner，但仍聚合多个动作 | 工程债存在，但用户可见价值弱于 A，且本轮 North Star 更直接指向首次 init 写入前 preview | 降低未来改 action 的冲突风险 | 中：行为保持型重构需大量回归 | existing Harness unit / integration 回归 | 无外部依赖 | 下一轮候选 |
| C. full regression / push 工作包 | Gate / git 状态 | 本地完整工作包通过 full regression 后 push | 当前分支仍领先远端多个本地提交 | push 前需要 `scripts/test-full.sh`，涉及真实 acceptance / DeepSeek / `.benchmarks` / 网络前置；当前仍有可本地推进的 init gap | 降低分叉风险 | 高：外部前置多，不适合作为本轮代码 milestone | full regression 与 push 结果 | `DEEPSEEK_API_KEY`、真实仓库、网络 | 外部前置候选 |

排序结论：

1. 选择 A。它直接命中 `init-north-star.md` 中“写入前设计预览展示哪些内容标记为低置信度或需要人工确认”的目标态，并且补齐的是用户输入最终确认前的可信度闭环。
2. B 是真实工程债，但不直接改善本轮首次 `init` 的用户确认质量。
3. C 适合作为完整工作包同步动作，但仍有外部前置；本轮继续不 push。

## 本轮 milestone

作为 Harness Maintainer，当我在首次 guided `init` 的最终确认前查看 Harness 设计预览时，我可以看到当前仍待人工确认或低置信度的 scan follow-up、LLM self-check、scan warning 和验证命令，并理解确认写入只会生成可审计 Harness 基线，不会自动关闭追问、验证用户补充或执行 Runtime，从而在写入前做出更可信的确认。

## 验收标准

1. `show_prewrite_maturity_preview()` 在写入前 Harness 设计预览中输出稳定的 `待确认与低置信度边界` section。
2. section 在存在 `scan_metadata.followup_questions` 时展示待处理数量、示例 `confirm:*` interaction id、trigger、影响范围和置信度。
3. section 在存在 `scan_metadata.self_check.resolutions` 时展示 review-only 自检结论数量、示例 interaction id、status、`suggested_action_type` 和边界。
4. section 在存在低置信度命令时展示命令 id、命令、gate、source，并说明它仍需人工确认或 benchmark / 后续验证。
5. section 在没有待确认项时也明确说明没有额外低置信度追问，但写入后仍需 benchmark 和 Runtime 证据验证。
6. 不修改 scan schema、LLM prompt、questionnaire schema、正式 writer、benchmark check 或 Runtime 分工；不创建 `.ai/task-runs`。
7. 完成前运行相关 unit、相关 guided init integration、`compileall`、`git diff --check` 和 `scripts/test-fast.sh`。

## 决策与取舍

- 预览从 `ProjectInventory.stack_extensions["scan_metadata"]` 和 `CommandCatalog` 读取已有结构化信息，不新增长期 schema。
- 只展示摘要和前几个示例，完整治理仍由 `.ai/questionnaire.yaml`、`.ai/human-input-needed.md` 和 `.ai/scan-metadata.yaml` 承担。
- `confirm` 的语义保持不变：确认写入 Harness 资产，不代表关闭 follow-up、验证低置信度命令或执行 Runtime。
- 本轮不把 self-check 结果应用到 inventory / command catalog / routing policy，也不新增 targeted scan 执行器。

## Assumptions / Risks

- Assumption：早段 scan presentation 的深度追问信息可能被长流程冲淡，最终确认前重述边界能显著降低误确认风险。
- Risk：preview 输出会变长。通过最多展示少量示例并把完整细节指向持久化产物控制长度。
