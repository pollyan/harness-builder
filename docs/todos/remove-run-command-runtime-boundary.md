# 删除 run 命令并收缩 Runtime 职责边界

## 状态

- 状态：implemented
- 优先级：high
- 发现日期：2026-05-31
- 相关命令：`harness-builder-agent run`、`harness-builder-agent benchmark`
- 相关工程规则：`docs/engineering/architecture.md`、`docs/engineering/init-workflow.md`、`docs/engineering/sensor-and-gate-rules.md`、`docs/engineering/testing-strategy.md`

## 完成说明

- 设计文档：`docs/superpowers/specs/2026-05-31-remove-run-runtime-boundary-design.md`
- 实施计划：`docs/superpowers/plans/2026-05-31-remove-run-runtime-boundary.md`
- 完成结果：`harness-builder-agent run` 已从 Harness Builder CLI 中移除，`run_task.py` 和 `run_sensor.py` 已删除；benchmark 不再生成或检查 `.ai/task-runs/` runtime trace，而是验证静态 Harness 资产、Workflow Skill 引用和 hard gate command 证据。
- 可观测性承载：`harness-map.yaml`、`sensor-report.yaml`、`runtime-summary.yaml` 等任务过程数据仍作为未来宿主 AI Coding Runtime 执行 Workflow Skill 时的 runtime artifact contract 保留在 Skill 模板中。

## 背景

Harness Builder 的核心职责应是为目标代码库生成、打包和验证 AI Coding Harness 资产。真正的 Harness 执行和任务级 runtime 应属于未来的 AI coding 工具或宿主环境，例如 InfoCode，而不是 Harness Builder 本身。

当前仓库存在 `harness-builder-agent run` 命令。它会基于任务文本生成 `.ai/task-runs/<task-id>/`，选择 workflow skill，执行 hard gate sensor，并写出 runtime summary、workflow events、decision log、handoff summary 和 experience candidates。

这让 Harness Builder 从“构建 Harness 的工具”扩展成了“模拟 Harness runtime 的工具”，容易搅乱产品边界和代码职责。

## 当前现状

当前 `run` 相关实现主要包括：

- `src/harness_builder_agent/cli.py` 中的 `run` command。
- `src/harness_builder_agent/tools/run_task.py`。
- `src/harness_builder_agent/tools/run_sensor.py` 中被任务运行调用的 sensor execution。
- `.ai/task-runs/<task-id>/` 任务级产物。
- benchmark 中对 runtime summary、workflow events、harness map 和 hard gate sensor 的检查。
- integration/e2e/acceptance 测试中对 `run` 链路的覆盖。

## 问题

当前需要重新审视 `run` 命令是否应该存在。当前倾向不是继续增强 `run`，而是将它从 Harness Builder 的正式职责中移除。

初步判断：

- `run` 接收具体开发任务，这已经是 runtime 输入，而不是 harness generation 输入。
- `run` 选择 workflow skill 和 guide，这应由宿主 AI coding runtime 在执行任务时完成。
- `run` 执行 sensor command，这更像一次任务验证行为，而不是构建 Harness 的行为。
- `.ai/task-runs/` 是 runtime trace，不应由 Harness Builder 作为正式产物维护。
- benchmark 依赖 `run_task` 会让质量验收和 runtime 模拟耦合。

如果这些判断成立，应彻底删除 `run` 命令，而不是继续增强它。实施时需要同步改造 benchmark，避免质量验收继续依赖 task runtime 模拟。

## 理想状态

Harness Builder 的边界应收缩为：

- `init`：扫描目标仓库并生成 `.ai` Harness 资产。
- `assess` / `improve`：评估和生成待确认改进候选。
- `benchmark`：验证 Harness 资产本身的完整性、schema、引用关系、sensor 定义和 package 质量。
- 可选新增 `package` 类命令：生成可被 InfoCode 或其他 runtime 消费的 Harness package manifest。

Harness Builder 不负责：

- 接收一次具体开发任务。
- 选择本次任务 workflow。
- 执行任务级 hard gate。
- 生成 runtime trace。
- 维护 `.ai/task-runs/`。
- 模拟 handoff。

Sensor 相关能力可以保留，但应转成 asset/package validation，而不是 task runtime execution。例如 benchmark 可以检查命令是否有证据、路径是否存在、schema 是否正确，必要时可以有显式的 validation mode 来验证命令可执行性。

## 初步验收标准

实现该 todo 时，至少应满足：

- 删除 CLI 的 `run` 命令；如需兼容旧文档，可先在 changelog 或 README 中说明该命令被移除。
- 删除 `run_task.py` 或将其逻辑迁移为非 runtime 的资产验证能力。
- benchmark 不再调用 `run_task`。
- benchmark 检查项从 runtime trace 改为 harness/package asset validation。
- README、engineering docs、tests 中不再把 `run` 作为核心工作流。
- 删除或重写依赖 `.ai/task-runs/` 的 integration/e2e/acceptance 测试。
- `assess` 的 observability 评分不再依赖 `.ai/task-runs/`。
- Workflow Skill 模板不再引用 `.ai/task-runs/<task-id>/` 作为 Harness Builder 生成的正式运行产物。
- 默认测试通过。

## 待澄清点

- `run_sensor.py` 是否保留为 benchmark 的命令验证工具，还是只保留 schema/content 检查，不实际执行命令。
- 是否要先引入 `.ai/harness-package.yaml`，再删除 benchmark 中的 runtime trace 检查。
- InfoCode 未来消费 Harness 时需要的最小 manifest 字段有哪些。

## 非目标

第一版不要求：

- 实现 InfoCode runtime。
- 设计完整 runtime API。
- 在 Harness Builder 内部保留任务执行模拟器。
- 删除 Workflow Skill 资产本身。

Workflow Skill 仍可以作为 Harness 资产生成，但其执行应属于未来宿主 AI coding runtime。
