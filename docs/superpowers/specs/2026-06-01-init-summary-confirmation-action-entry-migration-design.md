# Init Summary 待确认处理入口迁移设计

## Current State Gap Analysis

事实源快照：
- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/engineering/sensor-and-gate-rules.md`、`docs/todos/local-unique-capability-migration.md`。
- 已对比：当前 `init_summary.py`、`human_confirmation.py`、`benchmark.py` 与 `backup/local-61-before-migration` 中 `init-summary` confirmation action entry 旧实现和对应 spec。
- 按需未展开：LLM contracts、acceptance 真实仓库和 scanner internals；本轮不修改 LLM prompt、扫描调和或真实 DeepSeek 链路。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Init Summary 待确认处理入口 | todo / 旧分支 / Gate | `init-summary.md` 作为首次 init 交付入口，能把 `confirm:*` ID 指向 `.ai/human-input-needed.md#处理方式`，并对 scan warning 显示 action hint | `render_init_completion_message()` 会列出 `confirm:*`；`.ai/human-input-needed.md` 已有 `## 处理方式`；已有 Harness 入口能展示 backlog | `build_init_summary_markdown()` 没有 `## 待人工确认`；completion 的待确认区只列问题，不说明处理入口；scan warning ID 与处理动作仍要用户跳转推断 | 把首次 init 交付报告、human input 文件和 questionnaire 连接成可追踪人工确认闭环 | 低到中：只改 Markdown/CLI 摘要和 benchmark 内容检查，不改 schema / LLM / Runtime | unit 覆盖 summary/CLI；integration 覆盖 fixture init 产物；benchmark 内容检查防漂移 | 依赖现有 `Questionnaire` 和 `human-input-needed.md#处理方式` | 本轮 |
| B. Benchmark / quality gate 深层校验迁移 | todo | benchmark 更细检查 risk context、project-context evidence 和 hard gate source path | 已有 Benchmark signals 与 schema detail 展示 | 深层检查尚未全部迁移 | 增强质量门禁真实暴露问题 | 中到高：会改变 benchmark failed 语义 | unit/integration/benchmark fixture | 依赖 signal 展示已稳定 | 下一轮候选 |
| C. Scan evidence 可审计细节 | todo | scan report、project-context、init summary 进一步展示 test/risk/API/doc/LLM requested evidence reason | 当前 scan metadata、evidence expansion 和部分 Guide 已有基础 | 旧分支 evidence reason 可视化仍可能更细 | 强化首次 init 仓库理解深度 | 中：触及 writer / benchmark 多产物 | asset writer、integration、benchmark | 需重新审计旧实现与当前远端实现重叠 | 后续候选 |

排序结论：
1. 选择 A，因为它直接延续刚迁移的 human-input 回访入口，让首次 init 交付摘要也能指向同一个处理闭环；范围小、风险低、可测试，符合 init North Star 的“写入后的交付摘要”。
2. B 暂不选，因为它会扩大 benchmark hard status 变化面，适合作为已有 signal 稳定后的下一轮。
3. C 暂不选，因为它属于 scan / Guide evidence 深度，和本轮 human confirmation 闭环不同旅程。

## Milestone

作为首次运行 `init` 后阅读 `.ai/init-summary.md` 的 Harness Maintainer，当我看到 `## 待人工确认` 时，我可以直接知道这些 `confirm:*` 问题应去 `.ai/human-input-needed.md` 的 `## 处理方式` 处理，并且 scan warning 会显示对应 action hint，从而把交付报告里的风险解释连接到可执行补充动作。

## 验收标准

- `.ai/init-summary.md` 包含稳定 `## 待人工确认` 章节。
- 该章节显示 `.ai/human-input-needed.md#处理方式` 处理入口，并保留 questionnaire 中的前几个 `confirm:*` ID。
- 对 `confirm:scan-warning:<code>`，summary 显示 `scan_warning_action:<code>=...`。
- CLI completion message 的“仍需人工确认”同样显示处理入口，避免终端摘要和 Markdown 摘要漂移。
- Benchmark `content:init-summary` 检查至少要求 `## 待人工确认`、`.ai/human-input-needed.md#处理方式` 和 questionnaire 中的 `confirm:*` ID 出现在 summary，防止三份产物后续漂移。
- Runtime 边界不变：不执行 Runtime、不创建 `.ai/task-runs`、不自动修改正式资产。
- 测试：unit / integration / benchmark 相关测试覆盖；commit 前运行 `scripts/test-fast.sh`。

## 决策 / 取舍

- 不新增 schema，复用现有 `Questionnaire`。
- 将 scan warning action hint 从 human input 逻辑中提取为可复用函数，避免两处文案漂移。
- Summary 只展示前几个问题和 action entry；完整处理建议仍以 `.ai/human-input-needed.md` 为准。
- Benchmark 内容检查只验证稳定入口和 ID 对齐，不强制要求每类 action 文案完全一致。

## Assumptions / Risks

- Assumption：`init-summary.md` 是首次 init 后 Maintainer 最可能先看的入口报告，应能把待确认问题连接到处理方式。
- Risk：旧 Harness 的 init-summary 缺少该章节后 benchmark 会失败；这是内容契约升级，维护入口可通过 benchmark signals 暴露。
- Risk：scan warning action hint 目前是确定性模板，不代表已经自动修正扫描结论。

