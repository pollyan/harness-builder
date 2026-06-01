# Human Input 处理方式 Benchmark 深度校验设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划前半部分、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/engineering/sensor-and-gate-rules.md`、`docs/todos/README.md`、近期 evolution log、相关 benchmark / human confirmation 代码与测试。
- 按需未展开：`docs/engineering/llm-contracts.md`，本轮不改 LLM prompt、DeepSeek 配置、scan proposal schema 或 LLM 调和逻辑；`docs/engineering/architecture.md`，本轮只在既有 benchmark / helper 模块内增强契约。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Human Input 处理方式 benchmark 深度校验 | 上一轮 Gate / init workflow | `benchmark` 能防止 `.ai/human-input-needed.md#处理方式` 丢失章节、scan follow-up 具体示例、`review-human-input` 显式治理和 Runtime 边界 | `human-input-needed.md` 已生成深度追问处理建议；README / init workflow 已声明稳定契约 | `_human_confirmation_checks()` 只校验基础 question id 和 `# Human Input Needed`，Markdown 丢掉 `## 处理方式` 或具体 `module/command/risk/stack` 示例也可能通过 | 保护“动态追问 -> 会后处理 -> 显式复核”的渐进式协作闭环，避免文档事实源和质量门禁漂移 | 中低；只增强 benchmark content check，不改 `.ai` schema、LLM、Runtime 或 writer 主行为 | integration 直接篡改 generated `.ai/human-input-needed.md` 后运行 `_human_confirmation_checks()` / `run_benchmark()`；unit 可覆盖 guidance snippet helper | 无外部凭证；依赖现有 `Questionnaire` schema 和 scan followup guidance helper | `content:human-confirmation` 对合法 generated artifact 通过；缺章节、缺处理入口、缺 per-id 示例或 Runtime 边界时失败并列出 `missing` detail | 本轮 |
| B. Self-check suggested action 结构化约束 | 上一轮 Gate | LLM 二次自检建议动作可被 schema / parser 约束，避免自由文本难以消费 | `self_check` 已展示 suggested action 并进入 questionnaire reason | 建议动作仍偏自由文本，未形成可机器审计的 action 类型 | 提升 scan self-check 到后续治理链路的可消费性 | 中高；涉及 schema、LLM output、prompt、兼容旧数据和测试 | schema/unit/integration/LLM contract tests | 需要读 `llm-contracts.md` 并设计迁移 | 后续单独 milestone |
| C. Full regression / push 工作包 | Git / Gate | 已形成完整批次后运行 full regression 并 push | 当前 `main` ahead origin 62，本地 commits 均已 fast 验证 | push 前必须运行 `scripts/test-full.sh`，可能依赖真实 DeepSeek、`.benchmarks` 和网络 | 降低长期远端分叉 | 高；外部服务和真实仓库可能阻塞 | `scripts/test-full.sh`、git push 结果 | DeepSeek key、真实仓库、网络 | 完整工作包形成后处理 | 暂缓 |
| D. Existing Harness action execution 抽模块 | 既有 spec Gate / 架构债 | 主向导只负责编排，维护动作执行由独立模块承接 | summaries / signals 已逐步抽出 | action execution 分支仍在 `interactive_init.py` | 降低维护入口后续演进成本 | 中高；跨多个 guided actions 和 trace artifacts | unit + existing Harness integration | 无外部依赖 | 后续工程信任故事 | 下一轮候选 |

排序结论：

1. 选择 A，因为它直接保护上一轮刚建立的 human-input 持久化处理入口。当前 README / init workflow 已把具体 scan follow-up 示例写成稳定契约，但 benchmark 还停留在标题级检查，属于“文档和测试门禁弱于产品承诺”的断点。
2. B 暂不选，因为它会触碰 LLM/schema 契约，设计面更大，且用户会后处理入口的质量门禁应先补齐。
3. C 暂不选，因为它依赖 full regression 的外部前置，不直接增强 init North Star 能力；等一个完整工作包形成后再统一处理。
4. D 暂不选，因为它是工程结构优化，不如 A 对当前已交付用户故事的信任闭环直接。

## 本轮 Milestone

作为 Harness Maintainer，当我运行 `benchmark` 验收首次 `init` 生成的人工确认材料时，我可以确认 `.ai/human-input-needed.md#处理方式` 保留了必要章节、scan follow-up 的具体回答示例、`review-human-input` 显式治理入口和 Runtime 边界；如果这些内容漂移，`benchmark-report.yaml` 会给出精确 missing detail，从而让我信任会后追问处理不会退化成泛化提醒。

## 验收标准

1. `content:human-confirmation` 继续校验 `Questionnaire` schema 和基础 `confirm:*` 问题。
2. `content:human-confirmation` 必须校验 `.ai/human-input-needed.md` 的稳定章节：`## 已提供上下文`、`## 扫描待确认摘要`、`## 待确认问题`、`## 处理方式`、`## 下一步建议`。
3. 对未解决或部分回应的 `scan_followup_confirmation`，benchmark 必须校验 Markdown 中包含该 interaction id、`review-human-input --interaction-id <id> --decision resolved`、不会自动关闭追问 / 不伪装为已验证 evidence 的边界，以及 trigger 对应的关键示例 snippet。
4. 对 `reviewed_resolved_by_harness_maintainer` 的 scan follow-up，benchmark 不强制要求重新补充示例，但必须允许 resolved 边界文案通过。
5. 缺失章节、处理入口、示例、review-human-input 命令或 Runtime 边界时，check `passed=false`，并在 `missing` 中保留可行动 detail；完整 `run_benchmark()` 的 `status` 应随之 failed。
6. 不修改 `.ai` 机器 schema、LLM prompt、正式资产 writer 主契约或 Runtime 分工；Builder 仍不创建 `.ai/task-runs`。
7. 更新 README / engineering docs 中 benchmark 对 human-input 处理方式的质量门禁说明，并在 evolution log 记录本轮决策和验证结果。

## 设计决策

- 复用 `scan_followup_guidance.py` 作为 trigger 到示例的单一事实源；为 benchmark 暴露稳定 required snippet helper，避免在 benchmark 里复制中文长文。
- Benchmark 检查只锁定稳定 marker、命令片段和边界语义，不要求整段 Markdown 逐字一致。
- `resolved` follow-up 表示人工复核完成；benchmark 不再要求它保留重新补充示例，避免把已治理状态误判为待补充状态。
- 本轮不新增 todo；这是上一轮 Gate 候选的直接消化。

## Assumptions / Risks

- Assumption：`QuestionnaireQuestion.trigger` 当前不是显式 schema 字段，但已允许 extra 信息；benchmark 可通过 interaction id fallback 推断 trigger，与现有 helper 一致。
- Risk：锁定中文 snippet 过细会让未来文案调整成本变高；因此只校验示例片段和边界关键词，不校验完整句子。
- Risk：旧 Harness 的 human-input 文档如果缺少新章节会 benchmark failed；这是有意暴露质量漂移，不做 silent fallback。

## Sub Agent 使用

按 playbook 尝试启动 explorer 做只读审查，当前环境返回 `agent thread limit reached`。本轮由主线程完成代码路径审查、TDD、实现、验证和提交。
