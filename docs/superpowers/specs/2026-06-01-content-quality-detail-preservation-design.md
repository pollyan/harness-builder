# Content Quality Detail Preservation 迁移设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/local-unique-capability-migration.md`。
- 已读取相关工程文档：`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/engineering/sensor-and-gate-rules.md`。
- 已对比当前代码与测试：`benchmark.py` 中 `content:workflow-skills`、`content:guides-quality`、`content:sensors-quality`、`content:stack-specific-guides`，以及 `tests/integration/test_benchmark_command.py` 中已有负向测试。
- 按需未展开：`llm-contracts.md` 不展开，因为本轮不改 LLM；architecture 不展开，因为不改模块边界；acceptance 不运行，因为不触碰真实 LLM / 真实仓库。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Content quality detail preservation | todo / 上轮 Gate | Guide、Sensor、Workflow Skill 内容质量失败时，benchmark report 保留具体 missing detail | 多数 schema / routing / evidence check 已保留 errors/missing；维护入口可展示 detail | `content:guides-quality`、`content:sensors-quality`、`content:workflow-skills` 目前只返回 passed=false，没有 missing/errors | Maintainer 能从 benchmark report 和维护入口知道哪个章节或 Skill 标记缺失，不必手工 diff Markdown | 低：只增强 check payload 和测试，不改生成逻辑 | integration 负向测试断言 missing detail | 不依赖外部服务 | 本轮 |
| B. Stack-specific guide detail | todo / Gate | `content:stack-specific-guides` 失败时说明缺少哪个 weapon id | 当前只返回 stack 和 passed | 与 A 相近，但需要按 stack 组织 expected ids | 增强栈特定 Guide 诊断 | 低 | integration 单测可覆盖 | 可并入 A，仍属同一内容质量用户故事 | 本轮并入 |
| C. Full failed check audit | todo | 所有 failed checks 都有 action detail | 已覆盖很多重点 check | 需要完整清单、兼容策略和文档 | 全面诊断 | 中 | 大量测试 | A/B 之后再做系统审计 | 后续 |
| D. Evidence helper 去重 | Gate 技术债 | evidence helper 统一 | 多处 helper 重复 | 与 failed detail 无直接关系 | 降低维护成本 | 中 | 回归测试 | 不服务本轮用户故事 | 后续 |

排序结论：

1. 选择 A+B，因为它们共享同一用户故事：老的内容质量 check 失败时缺少可行动 detail；变更边界小、价值直接、测试清晰。
2. C 保留为后续系统审计，避免本轮变成无边界 checklist。
3. D 保留为技术债候选。

## 本轮 milestone

作为 Harness Maintainer，当我运行 `benchmark` 发现 Guide、Sensor、Workflow Skill 或 stack-specific Guide 内容质量失败时，我可以在 `benchmark-report.yaml` 中看到具体缺失章节、缺失 workflow skill marker 或缺失 weapon id，从而知道应该修哪份语义资产，而不是只看到 `passed=false`。

## 验收标准

- `content:workflow-skills` 失败时返回 `missing`，至少包括缺失文件或缺失 marker。
- `content:guides-quality` 失败时返回 `missing`，列出缺失章节名。
- `content:sensors-quality` 失败时返回 `missing`，列出缺失章节名或 `missing_hard_gate_marker`。
- `content:stack-specific-guides` 失败时返回 `missing`，列出当前 stack 缺失的 weapon id；unknown stack 仍要求人工确认 marker。
- 现有 benchmark pass/fail 语义不变，不执行 Runtime，不创建 `.ai/task-runs`。
- 迁移 todo 和 evolution log 同步记录该 failed detail preservation 小切片。

## 决策 / 取舍

- 不新增 BenchmarkReport schema；复用现有 `missing` 字段。
- 本轮不改变 writer 生成内容，只增强失败报告的可诊断性。
- 不把所有 benchmark check 一次性审计完；只处理最常见且当前测试已覆盖失败路径的内容质量 check。

## Assumptions / Risks

- Assumption：`missing` 字段是维护入口和 benchmark report 已支持的稳定 detail 承载方式。
- Risk：部分旧报告没有这些 missing detail；新生成 report 会更可诊断，旧报告仍按现有 schema 兼容。
- Sub agent 使用：尝试启动只读 explorer 审查本轮候选，但当前环境返回 `agent thread limit reached`，本轮由主线程完成分析、TDD、实现和验证。
