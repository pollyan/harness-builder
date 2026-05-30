---
name: standard
description: 用于复杂功能、高风险变更、跨模块改造、安全/数据/架构影响任务的项目级 AI Coding 工作流。
---

# 标准开发工作流

## 使用条件

当任务影响范围不清楚、涉及高风险模块、跨模块设计、安全/权限/金额/数据迁移/核心业务状态，或 lightweight workflow 覆盖不足时使用本 Skill。

## 必读资产

- `.ai/guides/project-context.md`
- `.ai/guides/architecture.md`
- `.ai/guides/coding-rules.md`
- `.ai/sensors/verification.md`
- `.ai/sensors/test-strategy.md`
- `.ai/experience/experience-summary.md`

## 执行步骤

1. Requirement Alignment：澄清需求、边界、不做范围和验收标准。
2. Harness Mapping：由宿主 AI Coding Runtime 创建或更新 `.ai/task-runs/<task-id>/harness-map.yaml`，映射影响模块、Guides、Sensors、风险区域和 restricted paths。
3. Solution Design：形成方案、取舍、风险和需要人工确认的问题。
4. Implementation Plan：拆成可验证小步骤，并明确每步对应的 Sensors。
5. Test-first Build & Verify Loop：优先补测试或验证证据，再实施变更，运行 hard gate Sensors。
6. Repair Loop / Human Escalation：Sensor 失败时修复并重跑；多次失败或高风险决策升级人工。
7. Review / Decision Log / Handoff：输出验证结果、残余风险、经验候选和交付摘要。

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

- 方案和实现必须引用项目事实、Guides、Sensors 或 Experience Summary。
- 不把单次经验直接写入正式 Guides / Sensors / Workflow。
- 高风险、低置信度或违反 restricted paths 的情况必须进入人工确认。
- 所有经验候选先进入待确认区，不自动升级为正式规则。
