# Existing Harness Benchmark / Routing Signals 迁移设计

## Current State Gap Analysis

事实源快照：
- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/engineering/sensor-and-gate-rules.md`、`docs/todos/local-unique-capability-migration.md`。
- 已对比：当前 `interactive_init.py` / `maintenance_triage.py` / `benchmark_report.py`，以及 `backup/local-61-before-migration` 中 Benchmark signals、Workflow routing signals 和 hard gate weak command triage 的旧实现。
- 按需未展开：LLM prompt 与 acceptance 真实仓库文档；本轮不修改 LLM 调用、真实 DeepSeek 链路或 Runtime 产物。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Existing Harness Benchmark / Routing signals | todo / 旧分支 / README 契约 | 再次运行 guided `init` 时，Maintainer 能独立看到 benchmark failed count、failed id、人类可读解释、error/missing/weak command detail，以及 workflow routing default、rule count、standard escalation、risk trigger 和 missing hard gate trigger | 当前入口展示成熟度、Experience / review signals、Maintenance triage；`schema_content_failed_checks` 混在 Experience 中；README 已描述 Benchmark / Workflow signals，但代码没有独立小节 | 文档事实源和 CLI 不一致；Maintainer 仍要打开 YAML 才能理解质量门禁和 routing 策略卡点 | 补齐已有 Harness 维护入口的健康状态视图，降低迁移旧本地能力的冲突风险，也让后续 hard gate / routing policy 迁移有稳定观察面 | 中：涉及 `BenchmarkReport` schema 增量字段、guided init 输出和 triage 排序；不触碰 LLM / Runtime | unit 覆盖 signal helper、schema 字段和 triage；integration 覆盖 `init -> exit` 输出且不扫描不覆盖 | 无外部凭证；依赖现有 BenchmarkReport YAML 中 `missing/errors/weak_commands` 字段 | 本轮 |
| B. Benchmark / quality gate 深层校验迁移 | todo | benchmark 能更细检查 risk context、project-context evidence 和 hard gate source path | 当前 benchmark 已检查多类 schema/content 与 hard gate command evidence | 部分旧分支更细检查尚未完全迁移 | 提升质量门禁真实暴露问题的能力 | 中到高：会改变 benchmark failed 语义，影响多层测试 | unit / integration / benchmark fixture | 需要先有维护入口 signal 承接失败详情 | 后续候选 |
| C. Scan evidence 可审计细节 | todo | scan report / project-context / init summary 展示 test/risk/API/doc/LLM requested evidence reason | 当前已有 evidence expansion、scan followup、自检和部分 CLI 展示 | 旧分支里 evidence reason preservation 可能还有可吸收细节 | 提升首次 init 仓库理解深度 | 中：触及 scanner / writer 多文件 | fixture init、asset writer、benchmark | 需要重新审计旧实现和当前 scan metadata | 后续候选 |

排序结论：
1. 选择 A，因为它是 open todo 中尚未迁移的 Existing Harness 维护入口能力，且 README / engineering 文档已经把 Benchmark signals 和 Workflow routing signals 写成当前契约；先修正代码与测试能消除事实源漂移。
2. B 暂不选，因为它会改变 benchmark 判定范围，应该在 signal 展示和 schema detail 已稳定后再做。
3. C 暂不选，因为它属于首次 init scan 深度旅程，和本轮已有 Harness 维护入口不同旅程，避免横向发散。

## Milestone

作为 Harness Maintainer，当我再次运行 guided `init` 进入已有 Harness 维护入口时，我可以直接看到最近 benchmark 失败项的数量、ID、中文解释、可行动错误详情，以及当前 workflow routing 的 default / standard escalation / risk trigger 状态，从而不用先打开多个 YAML 文件也能判断应该先修质量门禁还是调整 routing 策略。

## 验收标准

- CLI：已有 Harness 入口输出独立 `Benchmark signals` 和 `Workflow routing signals` 小节。
- Benchmark signals：无 report 时显示 `benchmark_failed_checks=not_available`；有 failed check 时显示 count、最多 3 个 failed id、中文 detail；携带 `error`、`errors`、`missing` 或 `weak_commands` 时显示 `benchmark_failed_check_error=<id>|<detail>`。
- Workflow routing signals：基于 `HarnessConfig` schema 显示 `routing_default`、`routing_rule_count`、`standard_escalation`、`standard_human_confirmation`、`standard_risk_triggers`、最多 3 个 `risk_trigger` 和 `missing_hard_gate_trigger`。
- Schema：`BenchmarkReport` 保留 `errors`、`missing` 和 `weak_commands` 字段，不再在 schema validate 后丢失这些机器可消费失败详情。
- Triage：hard gate weak command 失败优先生成 `reason=hard_gate_command_evidence`，带 detail 和中文 guidance；project-context evidence missing 能生成专属 detail。
- Runtime 边界：本轮只读 benchmark / config 信号，不执行 Runtime、不创建 `.ai/task-runs`、不修改正式 Harness 资产。
- 测试：新增或更新 unit / integration；commit 前运行 `scripts/test-fast.sh`。

## 决策 / 取舍

- 保留现有 `schema_content_failed_checks` Experience 行以兼容已有测试，同时新增独立 Benchmark signals 小节。
- `BenchmarkWeakCommand.reason` 做宽松字符串字段，兼容当前 benchmark 只写 `id/source/confidence` 的报告，也兼容旧分支带 `reason` 的报告；展示时缺失 reason 会按 source/confidence 推断为 `missing_source` 或 `low_confidence`。
- Workflow routing signals 只解释 `.ai/harness-config.yaml` 当前策略，不进行任务路由推荐，也不修改 routing policy。

## Assumptions / Risks

- Assumption：当前 `harness-config.yaml` 的 `standard-escalation` 是已有 Harness routing 健康度的关键观察点。
- Risk：BenchmarkReport schema 变宽后可能暴露历史报告中的更多 detail；这是可审计信息增强，不改变 benchmark pass/fail 计算。
- Risk：CLI 仍有部分机器式 `key=value` 输出；本轮先迁移旧分支的稳定契约，后续可继续把 detail 翻译成更自然的中文状态卡片。

