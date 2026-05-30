# Remove Run Runtime Boundary Design

## 背景

Harness Builder 的核心职责是为既有代码库生成、评估和验证 AI Coding Harness 资产。当前 `harness-builder-agent run` 会接收一次具体开发任务，生成 `.ai/task-runs/<task-id>/` 下的 `harness-map.yaml`、`sensor-report.yaml`、`runtime-summary.yaml`、`workflow-events.jsonl`、`used-guides.yaml`、`decision-log.md`、`handoff-summary.md` 和 `experience-candidates.md`，并执行 sensor command。

这让 Harness Builder 承担了任务级 runtime 模拟职责。该职责未来应属于 AI Coding 工具或宿主 runtime，例如 InfoCode，而不是 Harness Builder CLI。

同时，原有 runtime 设计中的可观测性原则仍然成立。一次真实 AI Coding workflow 执行后，应留下可追溯、可审计、可调试的过程数据，帮助用户理解 workflow 如何选择 guides、执行 sensors、处理失败和形成交接。

## 目标

删除 Harness Builder 内部的 `run` 功能，同时保留 runtime 可观测性的设计原则，并把过程数据的产出主体转移到 Workflow Skill 和未来 AI Coding Runtime。

完成后：

- `harness-builder-agent` 不再暴露 `run` 命令。
- Harness Builder 不再生成 `.ai/task-runs/<task-id>/`。
- Harness Builder 不再执行任务级 sensor command。
- `benchmark` 不再调用 runtime 模拟，也不再要求 runtime trace 文件存在。
- Workflow Skill 模板继续描述执行 workflow 时应产出的可观测文件契约。
- runtime 过程数据被定义为“宿主 runtime 执行 skill 时应写出的产物”，不是 Harness Builder 当前必须生成的产物。

## 非目标

- 不实现 InfoCode runtime。
- 不新增 `package` 命令或 `.ai/harness-package.yaml`。
- 不设计完整 runtime API。
- 不让 Harness Builder 继续保留任务执行模拟器。
- 不删除 Workflow Skill 资产本身。
- 不删除可观测性原则；只调整其承载主体。

## 方案比较

### 方案 A：保留 `run`，只弱化文档定位

优点是改动少。缺点是 CLI 和 benchmark 仍会依赖 runtime 模拟，产品边界没有真正收缩。

不采用。

### 方案 B：删除 `run`，同时删除全部 runtime artifact 概念

优点是边界最干净。缺点是丢掉了已有设计里有价值的可观测性原则，也无法指导未来 AI Coding Runtime 如何留下审计数据。

不采用。

### 方案 C：删除 `run`，把 runtime artifact contract 移交给 Workflow Skill

Harness Builder 只生成 Workflow Skill 和静态 Harness 资产。Workflow Skill 明确说明宿主 runtime 在执行任务时应写出哪些过程数据，例如 `harness-map.yaml`、`sensor-report.yaml`、`runtime-summary.yaml` 和 `workflow-events.jsonl`。这些文件仍是有价值的 runtime 透明化数据，但不再由 Harness Builder CLI 生成，也不再作为 benchmark 硬验收前提。

采用该方案。

## 目标边界

### Harness Builder 负责

- `init`：扫描目标仓库并生成 `.ai` Harness 资产。
- `assess`：基于当前 Harness 资产生成成熟度评估。
- `improve`：生成待人工确认的改进候选。
- `benchmark`：验证 Harness 资产本身的 schema、章节、引用关系、weapon library 选择、command catalog 可靠性和 generation trace。
- 生成 Workflow Skill 模板，并在模板中记录未来 runtime 可观测性契约。

### Harness Builder 不负责

- 接收一次具体开发任务。
- 判断本次任务属于 bugfix 还是 lightweight。
- 为本次任务选择 workflow。
- 为本次任务生成 `harness-map.yaml`。
- 执行 hard gate sensor command。
- 生成 `sensor-report.yaml`、`runtime-summary.yaml`、`workflow-events.jsonl` 或 `.ai/task-runs/<task-id>/`。
- 模拟 handoff 或 experience candidate。

### 未来 AI Coding Runtime 负责

- 执行 Workflow Skill。
- 根据任务上下文选择 guides、sensors 和 workflow。
- 写出任务级 runtime artifacts。
- 执行或委托执行 sensor command。
- 在失败、跳过、人工确认和 handoff 时保留结构化过程记录。

## Runtime Artifact Contract

Workflow Skill 应描述宿主 runtime 在执行 workflow 时写出以下文件。路径建议仍放在 `.ai/task-runs/<task-id>/`，因为该目录语义清晰，且与历史产物兼容。

```text
.ai/task-runs/<task-id>/
  harness-map.yaml
  sensor-report.yaml
  runtime-summary.yaml
  workflow-events.jsonl
  used-guides.yaml
  decision-log.md
  handoff-summary.md
  experience-candidates.md
```

这些文件的语义：

- `harness-map.yaml`：记录任务类型、风险级别、选中的 workflow skill、必读 guides、相关模块和 sensor policy。
- `sensor-report.yaml`：记录 runtime 实际执行或跳过的 sensor 结果。`failed`、`skipped`、`unresolved` 不能当作成功。
- `runtime-summary.yaml`：记录本次 workflow 的摘要，包括选中 workflow、guide 数量、sensor 状态、未解决风险数量。
- `workflow-events.jsonl`：记录任务分类、guide 选择、workflow 选择、sensor 选择、sensor 执行、handoff 等阶段事件。
- `used-guides.yaml`：记录 runtime 要求本次任务读取的 guide 路径以及文件是否存在。
- `decision-log.md`：记录关键决策、人类确认点和风险接受理由。
- `handoff-summary.md`：记录交接摘要和剩余风险。
- `experience-candidates.md`：记录可回流为 harness 改进候选的经验。

Harness Builder 可以保留已有 `HarnessMap` 和 `SensorReport` schema 作为未来 runtime artifact contract 的参考契约，但这些 schema 不应再被 `benchmark` 当作当前 Harness Builder 生成物校验。

## Benchmark 调整

`benchmark` 继续可以失败，但失败依据必须来自 Harness 资产本身，而不是 task runtime 模拟。

保留或强化的检查：

- 必需 `.ai` 文件存在。
- JSON/YAML 产物符合 Pydantic schema。
- Markdown 产物包含稳定章节。
- Workflow Skill 文件存在，并被 `harness-config.yaml` 的 workflow 配置引用。
- `weapon-library-selection.yaml` 与生成 guides/sensors 内容一致。
- `command-catalog.yaml` 中 hard gate command 有 source、confidence、type 和 gate 证据。
- sensor Markdown 描述已发现命令、缺失验证能力、推荐验证活动和失败处理策略。
- generation trace 存在且可解析。

删除的检查：

- `schema:harness-map`
- `schema:sensor-report`
- `schema:runtime-summary`
- `content:harness-map-workflow-skill`
- `content:runtime-workflow-trace`
- `content:hard-gate-sensors-passed`
- `workflow_quality.runtime_trace_completeness`

替代检查：

- `content:workflow-skill-config-reference`：`harness-config.yaml` 中引用的 workflow skill 路径存在。
- `content:hard-gate-command-evidence`：hard gate command 必须可追溯到 evidence/source，且不能是 low confidence。
- `workflow_quality.skill_reference_integrity`：基于 `harness-config.yaml`，不再基于 `harness-map.yaml`。
- `sensor_quality.executable_gate`：基于 command catalog 的 hard gate 可靠性，不再基于 sensor execution result。

## 模块调整

删除：

- `src/harness_builder_agent/tools/run_task.py`
- `src/harness_builder_agent/tools/run_sensor.py`
- CLI 中的 `run` command。
- 依赖 `run` 的 integration/e2e/acceptance 测试。

保留：

- Workflow Skill 模板。
- `HarnessMap` / `SensorReport` schema，作为未来 runtime artifact contract 的 schema 参考。若后续确认没有任何内部引用，可在单独清理任务中迁移到更明确的 `runtime_contracts` 命名。

修改：

- `benchmark.py`：删除 `run_task` 调用和 runtime trace 检查，改为静态 Harness 资产检查。
- `assess_maturity.py`：observability 维度基于 `.ai/runs/` generation trace，不再基于 `.ai/task-runs/`。
- Workflow Skill 模板：把 task-run 产物描述为“宿主 runtime 执行本 skill 时必须维护的过程记录”，避免暗示 Harness Builder 会生成它们。
- README 和 engineering docs：移除 `run` 作为核心命令的描述，并明确 runtime artifacts 的新承载主体。
- tests：用 TDD 改写 benchmark、CLI、assess/improve、e2e 和 acceptance 断言。

## 错误处理

- 调用 `harness-builder-agent run` 应表现为不存在该命令，由 Typer 返回命令解析错误。
- benchmark 缺少 runtime artifacts 不应失败。
- benchmark 缺少 Harness 必需资产、schema 错误、guide/sensor 章节缺失、workflow skill 引用错误或 hard gate command 证据不足时应失败。
- 缺少 generation trace 仍应失败，因为它是 Harness Builder 自身命令可观测性，不是任务 runtime 可观测性。

## 测试策略

遵循 TDD：

1. 先改 CLI import/help 测试，断言 `run` 不再出现，直接调用 `run` 返回错误。
2. 改 benchmark 测试，断言 benchmark 不生成 `.ai/task-runs/`，报告中不包含 runtime check id，仍包含新的静态资产检查 id。
3. 改 benchmark 失败路径测试，断言 low confidence 或 source 缺失的 hard gate command 会失败。
4. 改 assess/improve 测试，删除预先执行 `run` 的准备步骤，断言 observability 基于 `.ai/runs/`。
5. 改 e2e/acceptance 测试，流程从 `init -> run -> assess -> improve -> benchmark` 改为 `init -> assess -> improve -> benchmark`。
6. 改 Workflow Skill 模板测试或 snapshot 断言，确认模板包含 runtime artifact contract，但不声称 Harness Builder 会生成 task-run。

## 验收标准

- `harness-builder-agent --help` 不显示 `run`。
- `harness-builder-agent run ...` 失败，且没有业务逻辑执行。
- `benchmark` 不导入、不调用 `run_task`。
- 默认 benchmark 不生成 `.ai/task-runs/`。
- benchmark report 不包含 runtime trace 或 sensor execution result 检查。
- benchmark 仍能基于静态 Harness 资产发现缺失文件、schema 错误、workflow skill 引用错误、hard gate command 证据不足。
- `assess` 的 observability 评分不依赖 `.ai/task-runs/`。
- Workflow Skill 模板保留 runtime artifact contract，并明确产出主体是宿主 AI Coding Runtime。
- README、engineering docs、tests 不再把 `run` 作为 Harness Builder 核心工作流。
- 默认快速回归通过。

