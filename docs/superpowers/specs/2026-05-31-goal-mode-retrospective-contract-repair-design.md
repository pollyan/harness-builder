# 目标模式回顾与 Workflow Recommendation Benchmark 契约修复设计

## 背景

用户指出前几轮目标模式提示词不完整，需要系统性回顾近期已经执行的内容，找出明显遗漏并补救。

本轮回顾最近本地 8 个目标模式提交：

- `1f96ba1` self-improve acceptance / prompt centralization
- `ff82be9` candidate governance
- `704c459` workflow policy candidate patches / prompt registry
- `af0e111` maturity-driven init summary
- `76d8e15` existing Harness init entry
- `f4f1541` existing Harness assess action
- `b5148bb` existing Harness improve action

## Current State Gap Analysis

| 候选 gap | 目标态要求 | 当前能力 | 缺口 | 用户价值 | 风险 / 复杂度 | 本轮决策 |
| --- | --- | --- | --- | --- | --- | --- |
| 近期 milestone 记录不完整 | 每轮记录 Gate、sub agent 使用、下一轮候选 gap | evolution log 有选题和验收摘要 | 缺少显式 Self-Harness Gate 与 sub agent 使用记录 | 防止后续目标循环丢失上下文 | 文档修补，低风险 | 本轮补回顾记录 |
| `recommend-workflow` Markdown 与 benchmark 契约不一致 | 生成产物应通过 benchmark 可选 review artifact 检查 | producer 写 `Task Brief` / `Required Guides` / `Boundary` | benchmark 要求 `Task` / `Recommended Workflow` / `Required Harness Assets` / `Review Boundary` | 真实 review-only workflow recommendation 可被 benchmark 验收 | 小范围契约修复，可测试 | 本轮实现 |
| existing Harness guided `benchmark` 动作 | 维护入口能运行 benchmark | 底层 benchmark 已存在 | guided init 未接入 | 用户体验价值高 | benchmark 失败路径和耗时更大 | 暂缓 |
| candidate governance 菜单 | 维护入口能处理候选 | 底层 review-candidate 已存在 | 交互菜单缺失 | 接管闭环价值高 | 需要选择候选、rationale、apply 风险 | 暂缓 |

## 目标

- 修复 `recommend-workflow` 生成 Markdown，使实际产物满足 benchmark 的 `content:workflow-recommendation-review` 章节契约。
- 增加 integration 测试，证明真实 `recommend-workflow` 产物能被 benchmark 接受，不只用手写 fixture 产物验证 benchmark。
- 补充演进记录，记录本次提示词不完整后的系统回顾结论、补救内容、Self-Harness Gate 结论和下一轮候选 gap。

## 决策

- 本轮不放宽 benchmark。benchmark 是质量门禁，应该推动 producer 对齐契约。
- Markdown 保留 review-only 边界，不声称 workflow 已执行或 routing policy 已应用。
- 不把 existing Harness guided `benchmark` 混入本轮，避免把契约修复和新 CLI 行为混做。

## 验收标准

- `test_recommend_workflow_writes_review_only_artifacts` 断言 generated Markdown 包含 benchmark 要求章节。
- 同一测试运行 `benchmark`，并断言 `content:workflow-recommendation-review` 通过。
- 既有 benchmark 对缺失章节的失败测试保持有效。
- 文档记录本轮回顾发现、修复、Gate 结论和下一轮候选 gap。

## 风险

- 旧的 Markdown 标题变更可能影响人工阅读习惯。内容语义保持不变，章节名改为 benchmark 契约所需名称。
- 本轮只补最明显的代码契约问题；更完整的近期 milestone 逐条审计可作为后续任务继续深化。
