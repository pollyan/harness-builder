# Ideas

这里保留 Harness Builder 早期的增强想法记录。

当前这些条目已经完成第一版实现，不再作为待办入口维护。新的优化项统一记录在 `docs/todos/`。

| Idea | 状态 | 来源 | 说明 |
|---|---|---|---|
| [可观测的 Harness 生成过程](observable-harness-generation.md) | implemented | JiuwenSwarm Auto-Harness 调研 | 已落地 `.ai/runs/<run_id>` generation trace |
| [可观测的开发工作流运行过程](observable-harness-runtime-workflow.md) | implemented | JiuwenSwarm Auto-Harness 调研 | 已落地 task-level runtime workflow trace |
| [向导式 Harness 生成与人机确认机制](wizard-style-human-confirmation.md) | implemented | JiuwenSwarm Auto-Harness 调研 / 产品设计讨论 | 已落地 `init --context`、questionnaire 和 human-input assets |
| [武器库底线与模型增强机制](weapon-library-floor-and-llm-enhancement.md) | implemented | 产品设计讨论 | 已落地内置武器库底线和 LLM enhancement candidate 通道 |

后续查看：

- 当前待办：`docs/todos/README.md`
- 已完成归档：`docs/todos/archive.md`
