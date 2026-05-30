# 可观测的开发工作流运行过程

状态：implemented

落地记录：

- Spec：`docs/superpowers/specs/2026-05-30-observable-runtime-workflow-design.md`
- Plan：`docs/superpowers/plans/2026-05-30-observable-runtime-workflow-plan.md`
- 产物：`.ai/task-runs/<task_id>/workflow-events.jsonl`、`used-guides.yaml`、`runtime-summary.yaml`

来源：JiuwenSwarm Auto-Harness 调研 / 2026-05-30

相关范围：InfoCode 集成、AI Coding 工作流、Harness 运行效果评估

## 一句话

当 InfoCode 或 AI Coding IDE 使用 `.ai/guides`、`.ai/sensors`、`.ai/skills` 执行真实开发任务时，记录哪些规则被读取、哪些 sensor 被执行、哪些 workflow 步骤真的产生了效果。

## 为什么重要

- 区分“文件生成了”和“规则真的被工作流使用了”。
- 帮助判断 guide、sensor、skill 的实际价值。
- 为持续改进提供真实信号，而不是只依赖静态扫描或模型判断。
- 让用户能看到一次开发任务中 Harness 到底参与了哪些关键决策。

## 暂时不做什么

- 不要求 Harness Builder 自己实现完整 AI Coding runtime。
- 不绑定单一 IDE 的私有协议。
- 不自动根据运行日志改写用户定制过的 Harness 文件。

## 可能形态

- `.ai/runs/<task_id>/workflow-events.jsonl`
- `.ai/runs/<task_id>/sensor-results.yaml`
- `.ai/runs/<task_id>/used-guides.yaml`
- `.ai/experience/pending-improvements.md`

## 触发执行的信号

当 InfoCode 侧有明确的 Harness 加载和执行接口，或者我们开始做真实任务级 E2E 验收时，再把这个 idea 提升为 spec 或 implementation plan。
