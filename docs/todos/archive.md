# Todo Archive

这里记录已经完成或被合并进当前实现的优化方向。

## 已完成条目

| 条目 | 来源 | 完成状态 | 当前落点 |
| --- | --- | --- | --- |
| [可观测的 Harness 生成过程](../ideas/observable-harness-generation.md) | JiuwenSwarm Auto-Harness 调研 | implemented | `.ai/runs/<run_id>` generation trace、events、artifacts、decision log |
| [可观测的开发工作流运行过程](../ideas/observable-harness-runtime-workflow.md) | JiuwenSwarm Auto-Harness 调研 | implemented | task-level runtime workflow trace、used guides、runtime summary |
| [向导式 Harness 生成与人机确认机制](../ideas/wizard-style-human-confirmation.md) | 调研 / 产品设计讨论 | implemented | `init --context`、`questionnaire.yaml`、`human-input-needed.md` |
| [武器库底线与模型增强机制](../ideas/weapon-library-floor-and-llm-enhancement.md) | 产品设计讨论 | implemented | 内置 weapon library、stack-specific guide/sensor、LLM enhancement candidate 通道 |

## 归档规则

- 归档只表示该方向已经有第一版实现，不代表最终产品形态已经完整。
- 如果后续发现新的缺口，应新增更具体的 todo，不要重新打开过于宽泛的旧 idea。
- 归档条目应尽量指向实际代码、文档或测试落点，方便回溯。

