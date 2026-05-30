# Todo Archive

这里记录已经完成或被合并进当前实现的优化方向。

## 已完成条目

| 条目 | 来源 | 完成状态 | 当前落点 |
| --- | --- | --- | --- |
| [可观测的 Harness 生成过程](../ideas/observable-harness-generation.md) | JiuwenSwarm Auto-Harness 调研 | implemented | `.ai/runs/<run_id>` generation trace、events、artifacts、decision log |
| [可观测的开发工作流运行过程](../ideas/observable-harness-runtime-workflow.md) | JiuwenSwarm Auto-Harness 调研 | implemented | task-level runtime workflow trace、used guides、runtime summary |
| [向导式 Harness 生成与人机确认机制](../ideas/wizard-style-human-confirmation.md) | 调研 / 产品设计讨论 | implemented | `init --context`、`questionnaire.yaml`、`human-input-needed.md` |
| [武器库底线与模型增强机制](../ideas/weapon-library-floor-and-llm-enhancement.md) | 产品设计讨论 | implemented | 内置 weapon library、stack-specific guide/sensor、LLM enhancement candidate 通道 |
| [全局交互式 CLI 与强引导式 Harness 生成](interactive-guided-cli.md) | 当前 todo | implemented | 默认 guided `init`、显式 `--non-interactive`、interaction decisions、context 进入 guide、candidate 决策落盘 |
| 大仓库 Evidence 扫描深度增强 | 当前 todo | implemented | 分桶采样、priority evidence、coverage metadata、scan warnings、LLM prompt coverage context |
| [测试覆盖深度与 Acceptance 策略增强](testing-coverage-and-acceptance-strategy.md) | 当前 todo | implemented | fast/full/acceptance 脚本、hooks 策略、schema/writer/benchmark/run task/init/e2e/acceptance 覆盖增强 |
| [Benchmark 质量评分细化](benchmark-quality-scoring.md) | 当前 todo | implemented | `quality_status`、`quality_scores`、`quality_summary`、degraded/failed 质量评分测试 |
| [Asset Writer 拆分重构](asset-writer-refactor.md) | 当前 todo | implemented | `asset_writers/` 分层 writer、`write_initial_assets` 编排入口、独立 writer 单元测试 |
| [删除 run 命令并收缩 Runtime 职责边界](remove-run-command-runtime-boundary.md) | 当前 todo | implemented | 删除 `run` CLI/runtime 模拟；benchmark 改为静态 Harness 资产验证；runtime 可观测性契约转移到 Workflow Skill / 未来 AI Coding Runtime |

## 归档规则

- 归档只表示该方向已经有第一版实现，不代表最终产品形态已经完整。
- 如果后续发现新的缺口，应新增更具体的 todo，不要重新打开过于宽泛的旧 idea。
- 归档条目应尽量指向实际代码、文档或测试落点，方便回溯。
