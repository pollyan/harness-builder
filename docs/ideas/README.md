# Ideas

这里存放 Harness Builder 的未来增强想法。这里不是详细计划，也不代表已经进入开发排期。

这些文档只记录原始方向、价值判断和暂时不做的边界。等某个 idea 真正进入实现，再升级为 spec 和 implementation plan。

| Idea | 状态 | 来源 | 说明 |
|---|---|---|---|
| [可观测的 Harness 生成过程](observable-harness-generation.md) | implemented | JiuwenSwarm Auto-Harness 调研 | 已落地 `.ai/runs/<run_id>` generation trace |
| [可观测的开发工作流运行过程](observable-harness-runtime-workflow.md) | implemented | JiuwenSwarm Auto-Harness 调研 | 已落地 task-level runtime workflow trace |
| [向导式 Harness 生成与人机确认机制](wizard-style-human-confirmation.md) | implemented | JiuwenSwarm Auto-Harness 调研 / 产品设计讨论 | 已落地 `init --context`、questionnaire 和 human-input assets |
| [武器库底线与模型增强机制](weapon-library-floor-and-llm-enhancement.md) | implemented | 产品设计讨论 | 已落地内置武器库底线和 LLM enhancement candidate 通道 |
