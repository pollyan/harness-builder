---
name: lightweight
description: 用于低风险、小范围功能、文案、配置或文档调整的项目级 AI Coding 工作流。
---

# 轻量级开发工作流

## 使用条件

当任务影响范围较小、风险较低，并且不需要完整设计评审时使用本 Skill。

## 必读资产

- `.ai/guides/project-context.md`
- `.ai/guides/architecture.md`
- `.ai/guides/coding-rules.md`
- `.ai/sensors/verification.md`

## 执行步骤

1. 复述任务目标和不做范围。
2. 由宿主 AI Coding Runtime 创建或更新 `.ai/task-runs/<task-id>/harness-map.yaml`，确认影响模块、必读 Guides 和 Sensors。
3. 只做最小必要变更；如果当前 POC 不修改业务代码，则输出实施建议。
4. 执行 hard gate Sensor；缺少运行环境时记录 skipped 和原因。
5. 对失败 Sensor 做一次有限分析，输出人工下一步。
6. 写入 Decision Log、Sensor Report、Handoff Summary 和 Experience Candidate。

## Runtime Artifact Contract

当宿主 AI Coding Runtime 执行本 Workflow Skill 时，必须维护任务级可观测产物。Harness Builder 不负责生成这些任务运行产物；它只生成本 Skill 和静态 Harness 资产。This section is the runtime artifact contract for host runtimes.

建议产物路径：

- `.ai/task-runs/<task-id>/harness-map.yaml`
- `.ai/task-runs/<task-id>/sensor-report.yaml`
- `.ai/task-runs/<task-id>/runtime-summary.yaml`
- `.ai/task-runs/<task-id>/workflow-events.jsonl`
- `.ai/task-runs/<task-id>/used-guides.yaml`
- `.ai/task-runs/<task-id>/decision-log.md`
- `.ai/task-runs/<task-id>/handoff-summary.md`
- `.ai/task-runs/<task-id>/experience-candidates.md`

## 交付要求

- 不扩大任务范围。
- 不静默忽略失败的 Sensor。
- 所有经验候选先进入待确认区，不自动升级为正式规则。
