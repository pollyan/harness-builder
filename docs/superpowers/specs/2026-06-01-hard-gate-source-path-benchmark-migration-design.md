# Hard Gate Source Path Benchmark 迁移设计

## Current State Gap Analysis

事实源快照：
- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/engineering/sensor-and-gate-rules.md`、`docs/todos/local-unique-capability-migration.md`。
- 已对比：当前 `benchmark.py`、`BenchmarkReport` schema、benchmark integration tests，以及 `backup/local-61-before-migration` 中 hard gate source path、risk context consistency、project-context evidence context 旧实现。
- 按需未展开：LLM contracts、scanner internals 和真实 acceptance；本轮只修改确定性 benchmark gate，不改 LLM prompt、扫描调和或真实仓库验收链路。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Hard gate source path 校验 | todo / 旧分支 / Gate | benchmark 不只检查 hard gate command 有 source，还要确认 source 指向仓库内真实文件，并在 `weak_commands.reason` 中说明 `source_path_missing` 或 `source_path_outside_repo` | 当前 `_hard_gate_command_evidence_check()` 会检查 hard gate 数量、source 非空和 low confidence；schema 可保留 `weak_commands.reason` | 人工编辑或旧 Harness 可能留下不存在 / 越界 source，benchmark 仍可能通过，Maintainer 无法信任 hard gate 来源证据 | 保护 Sensor / hard gate 质量底线，防止不可追溯命令被当作可执行质量门禁 | 低到中：只增强确定性检查和测试，不执行命令，不改 Runtime | integration 负向测试 source missing/outside；成功 fixture 继续通过；schema 已能保存 reason | 无外部凭证；依赖现有 `CommandCatalog` | 本轮 |
| B. Risk context consistency | todo / 旧分支 | scan risk paths 在 project-context、verification sensor 和 standard routing 中一致 | 当前 Guide/Sensor/Workflow routing 各自有基础检查；Maintenance triage 已能识别该 check id | 当前 main 没有 `content:risk-context-consistency` check，本轮若直接迁入会触碰 Guide/Sensor/Routing 三方语义 | 更强地证明风险叙事不是模板拼接 | 中：涉及多产物语义和 routing rationale，负向 fixture 较多 | integration 正/负向三类缺失 | 依赖当前风险路径渲染稳定 | 下一轮候选 |
| C. Project-context evidence context gate | todo / 旧分支 / Scan evidence | benchmark 检查 project-context 是否保留 inventory evidence path 和 LLM evidence expansion 摘要 | 当前 `content:guides-quality` 只检查章节；Guide 已有 `## 来源证据` | 缺少对 evidence path / expansion 细节的内容门禁 | 直接提升仓库理解深度和可审计性 | 中：和 Scan evidence 可审计细节强相关，可能要求 writer 先补齐细节 | unit / integration / benchmark | 依赖 evidence writer 审计内容 | 后续与 Scan evidence 切片合并评估 |

排序结论：
1. 选择 A，因为它是 Benchmark / quality gate 迁移中最小、最可验证、最少跨模块的工程信任故事；它直接服务 hard gate 可信度，不依赖 LLM 或资产 writer 改造。
2. B 暂不选，因为它跨 Guide、Sensor 和 Workflow routing 三个语义资产，适合在 hard gate source path 稳定后单独做。
3. C 暂不选，因为它和 Scan evidence 可审计细节耦合，若当前只加 gate 可能逼迫 writer 一起大改。

## Milestone

作为 Harness Maintainer，当我运行 `benchmark` 验收已有 Harness 时，如果 hard gate command 的 `source` 指向不存在文件或逃出目标仓库，我可以在 `benchmark-report.yaml` 的 `content:hard-gate-command-evidence` 中看到失败和 `weak_commands.reason`，从而知道该 hard gate 缺少可信来源证据，不能被当作已验证质量门禁。

## 验收标准

- `content:hard-gate-command-evidence` 对 hard gate command source 为空、low confidence、source path missing 和 source path outside repo 都会失败。
- `weak_commands` 保留 command id、source、confidence 和 reason，reason 至少覆盖 `missing_source`、`low_confidence`、`source_path_missing`、`source_path_outside_repo`。
- 正常 fixture 中 source 指向真实仓库文件时 benchmark 仍通过。
- 不执行命令、不访问外部服务、不创建 `.ai/task-runs`。
- 测试：benchmark integration 覆盖 missing / outside source；commit 前运行 `scripts/test-fast.sh`。

## 决策 / 取舍

- 复用现有 `content:hard-gate-command-evidence` check id，不新增新的 benchmark check，避免让维护入口和历史报告出现重复语义。
- 不把 source path 校验变成命令执行；它只证明来源文件可追溯，不证明命令一定可运行。
- `BenchmarkReport` schema 保持对旧报告兼容，仍允许旧 weak command 缺少 reason，但新生成报告必须写 reason。

## Assumptions / Risks

- Assumption：`CommandDefinition.source` 是相对目标仓库的 evidence path，不应指向仓库外文件。
- Risk：某些旧 Harness 可能把 source 写成 URL、说明文本或组合路径；本轮会将其视为不可追溯 hard gate source，要求 Maintainer 修正为仓库内 evidence 文件。
- Sub agent：尝试启动 explorer 做只读方案审查，但当前 agent thread limit reached；本轮由主线程对比旧分支实现。
