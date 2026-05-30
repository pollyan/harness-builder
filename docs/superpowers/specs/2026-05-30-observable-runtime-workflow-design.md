# Observable Runtime Workflow Design

## 背景

`docs/ideas/observable-harness-runtime-workflow.md` 提出：真实开发任务中，用户不只关心 Harness 文件是否生成，还关心这些文件是否真的被工作流使用。当前 `run` 命令已经会生成 `harness-map.yaml`、`sensor-report.yaml`、`decision-log.md`、`handoff-summary.md` 和 `experience-candidates.md`，但缺少结构化运行事件和 used guides 索引。

## 目标

在每次 `harness-builder-agent run` 任务执行时，生成可审计的 runtime workflow trace，让用户能看到：

- 选择了哪个 workflow skill。
- 本次任务要求读取哪些 guides。
- 执行了哪些 hard gate sensors。
- 每个 sensor 的结果如何影响 handoff 和 improvement candidates。

## 非目标

- 不实现完整 AI Coding IDE runtime。
- 不绑定 InfoCode 或其他 IDE 的私有协议。
- 不自动证明大模型真的阅读了 guide 内容；本轮只记录 Harness Builder 为任务映射出的 runtime contract。
- 不根据 runtime trace 自动改写用户定制过的 Harness 文件。

## 方案比较

### 方案 A：继续扩展 Markdown decision log

优点是简单。缺点是机器不可读，难以作为 benchmark 和后续 improve 的输入。

### 方案 B：在 `.ai/task-runs/<task_id>/` 下新增 runtime 结构化资产

新增：

```text
.ai/task-runs/<task_id>/
  workflow-events.jsonl
  used-guides.yaml
  runtime-summary.yaml
```

优点是和现有 task-run 目录一致，容易被 IDE 或 benchmark 读取。缺点是需要补少量 schema 和测试。

### 方案 C：复用 `.ai/runs/<run_id>` generation trace

优点是统一。缺点是 generation trace 关注 CLI 命令过程，runtime trace 关注任务级 Harness 使用，两者混在一起会降低可读性。

本轮选择方案 B。

## 产物结构

### `workflow-events.jsonl`

每行一个事件：

```json
{
  "schema_version": "1.0",
  "task_id": "demo-task-001",
  "stage": "guide-selection",
  "event_type": "completed",
  "message": "Required guides selected.",
  "details": {
    "guide_count": 3
  }
}
```

关键 stage：

- `task-classification`
- `guide-selection`
- `workflow-selection`
- `sensor-selection`
- `sensor-execution`
- `handoff`
- `experience-candidate`

### `used-guides.yaml`

```yaml
schema_version: '1.0'
task_id: demo-task-001
workflow_skill:
  path: .ai/skills/bugfix/SKILL.md
  source: builtin_template
required_guides:
  - path: .ai/guides/project-context.md
    exists: true
  - path: .ai/guides/architecture.md
    exists: true
  - path: .ai/guides/task-templates/bugfix.md
    exists: true
```

### `runtime-summary.yaml`

```yaml
schema_version: '1.0'
task_id: demo-task-001
task_type: bugfix
selected_workflow: bugfix
hard_gate_count: 1
sensor_statuses:
  unit_test: passed
unresolved_sensor_count: 0
used_guide_count: 3
workflow_skill_path: .ai/skills/bugfix/SKILL.md
```

## 运行流程

`run_task` 在生成 `harness_map` 后：

1. 写 `task-classification` 事件。
2. 写 `guide-selection` 事件和 `used-guides.yaml`。
3. 写 `workflow-selection` 事件。
4. 写 `sensor-selection` 事件。
5. 每个 sensor 执行后写 `sensor-execution` 事件。
6. 写 `runtime-summary.yaml`。
7. 写 `handoff` 和 `experience-candidate` 事件。

## 错误处理

- 没有 hard gate 时，仍写 `sensor-selection` 和 `sensor-execution`，状态为 `skipped`。
- guide 文件不存在时，`used-guides.yaml` 中 `exists=false`，同时 `workflow-events.jsonl` 写 warning。
- sensor failed/skipped 不会阻止 runtime trace 写出；失败会进入 `runtime-summary.yaml.unresolved_sensor_count`。

## 测试策略

单元/集成边界：

- 不单独引入复杂 runtime trace 类；先在 `run_task.py` 内用小函数写三个文件。
- 集成测试验证 `run` 输出的 runtime 文件字段完整。

集成测试：

- bugfix 和 lightweight 两条 run 流程都应生成 runtime trace。
- `workflow-events.jsonl` 每行可解析，且包含关键 stage。
- `used-guides.yaml` 中 required guide 路径和 `harness-map.yaml` 一致。
- `runtime-summary.yaml` 中 workflow、sensor 结果和 `sensor-report.yaml` 一致。

Benchmark 测试：

- benchmark 增加 runtime trace 检查：`schema:runtime-summary`、`content:runtime-workflow-trace`。

## 验收标准

- 默认测试通过。
- 真实开源仓库 e2e 中，`run` 和 `benchmark` 生成的 task run 都包含 runtime trace。
- 用户打开 `.ai/task-runs/demo-task-001/runtime-summary.yaml` 能看懂本次任务的 workflow、guides 和 sensor 执行结果。

