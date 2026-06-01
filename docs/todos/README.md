# Harness Builder Todos

这里存放 Harness Builder 后续需要优化、深化或重新设计的事项。

判断“当前是否有 open todo”时，以本文件的“当前待办”表为准。目录中保留的 `implemented` / `paused` 历史文件用于回溯背景和完成说明，不等同于当前待执行事项。

它和 `docs/superpowers/specs/` 的区别：

- `todos`：记录已经发现但尚未进入详细设计和实施计划的问题。
- `specs`：记录已经决定要做、并进入设计阶段的方案。
- `plans`：记录已经可以执行的实施步骤。

它和旧的 `docs/ideas/` 的区别：

- `ideas` 曾用于记录早期增强方向，目前其中条目已经完成。
- 新增优化项统一记录在 `docs/todos/`。
- 已完成条目统一进入 `archive.md` 索引；原始 todo 文件可以保留在本目录，但必须在文件顶部标明 `implemented` 或其他明确状态。

## 当前待办

| Todo | 状态 | 优先级 | 说明 |
| --- | --- | --- | --- |
| 暂无 | - | - | 当前没有 open todo。后续目标模式按 `docs/strategy/init-north-star.md` 和 Current State Gap Analysis 重新选择具体 gap。 |

`local-unique-capability-migration.md` 已归档为 implemented，用于记录本地 61 个提交迁移收口过程、已迁移切片和未迁移取舍。`guided-init-ai4se-real-repo-findings.md` 与 `maturity-driven-init-wizard.md` 暂停为背景参考；如果后续仍有价值，应基于最新代码和 North Star 拆成新的具体 gap，而不是直接重新打开旧宽泛 todo。

## 保留的历史事项状态索引

### Paused 背景参考

| Todo | 状态 | 说明 |
| --- | --- | --- |
| [guided init 在 ai4se 真实仓库上的体验与扫描深度问题](guided-init-ai4se-real-repo-findings.md) | paused | 多个切片已落入当前实现；剩余方向不作为 open todo，后续如仍有价值需基于最新代码重拆具体 gap。 |
| [成熟度驱动的 init 主向导与命令信息架构重构](maturity-driven-init-wizard.md) | paused | 大部分主向导能力已实现；剩余体验缺口需重新进入 Current State Gap Analysis。 |

### Implemented / 归档

| Todo | 状态 | 当前落点 |
| --- | --- | --- |
| [全局交互式 CLI 与强引导式 Harness 生成](interactive-guided-cli.md) | implemented | 默认 guided `init`、`--non-interactive`、interaction decisions 和 context 输入链路。 |
| [面向用户的 guided init 交互体验增强](guided-init-human-centered-cli.md) | implemented | 中文解释式 guided `init`、开放补充、逐项 Guide / Sensor 决策和 summary / back / confirm。 |
| [测试覆盖深度与 Acceptance 策略增强](testing-coverage-and-acceptance-strategy.md) | implemented | fast / full / acceptance 脚本、hooks 策略和分层测试规则。 |
| [Benchmark 质量评分细化](benchmark-quality-scoring.md) | implemented | `quality_status`、`quality_scores` 和 degraded / failed 质量评分。 |
| [Asset Writer 拆分重构](asset-writer-refactor.md) | implemented | `asset_writers/` 分层 writer 和 `write_initial_assets` 编排入口。 |
| [删除 run 命令并收缩 Runtime 职责边界](remove-run-command-runtime-boundary.md) | implemented | 移除 Builder 的任务执行职责，Runtime 产物由宿主 AI Coding Runtime 生成。 |
| [旧 scanner v2 实现审查与迁移评估](scanner-v2-review-and-migration.md) | implemented | 旧 scanner v2 的 claim validation 思路已迁移到当前 scan validation。 |
| [Workflow Policy Candidate Apply](workflow-policy-candidate-apply.md) | implemented | 结构化 `WorkflowPolicyPatch` 和 `review-candidate --decision applied` routing policy 审核应用。 |
| [LLM Evidence Source Whitelist Hardening](llm-evidence-source-whitelist.md) | implemented | LLM review-only 产物 evidence source allowlist 校验。 |
| [本地独有 / 更细能力合并与迁移](local-unique-capability-migration.md) | implemented | 本地 61 个旧提交中的高价值独有 / 更细能力已按最新主线迁移收口。 |

完整已完成条目索引见 [archive.md](archive.md)。

## 管理规则

1. 每个 todo 必须说明问题、当前现状、理想状态、影响范围和初步验收标准。
2. todo 不等于承诺立即开发；进入开发前需要升级为 spec 和 plan。
3. 已完成 todo 应进入 `archive.md` 索引；原文件可以保留，但必须在文件顶部标明 `implemented` 并保留完成说明。
4. 新增 todo 时优先用中文描述，路径、命令、字段名保持英文原样。
5. 如果 todo 影响 `init` 主链路、LLM、测试或 sensor，要在条目中明确对应的工程规则文档。
