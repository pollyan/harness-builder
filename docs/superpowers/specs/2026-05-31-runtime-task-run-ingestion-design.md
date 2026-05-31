# Runtime Task-Run 只读摄取设计

## North Star 对齐

- 能力模块：Experience & Self-Improve、Maturity & Evolution、Sensors、Governance & Auditability。
- 产品目标：Harness Builder 不执行 Runtime，不生成 `.ai/task-runs`，但当宿主 AI Coding Runtime 按 Workflow Skill 契约产出任务级过程数据后，Builder 应能只读校验、汇总并把这些数据交给 Experience / Maturity / Benchmark。

## Current State Gap Analysis 摘要

| 维度 | 目标态 | 当前能力 | 缺口 | 价值 | 风险 | 验收方式 |
|---|---|---|---|---|---|---|
| Experience | 真实任务结果可进入经验闭环 | `experience-index.yaml` 只统计 `.ai/task-runs` 目录数量 | 不解析 harness-map、sensor-report、runtime-summary、handoff | 让自改进不只看候选计数 | 锁死 Runtime 格式 | schema + unit |
| Maturity | 成熟度能看到 Runtime 证据质量 | `maturity-evidence.yaml` 只记录 has_runtime_task_runs | 缺少 task count、failed/skipped sensor、repair signal | 为后续真实晋级语义提供硬证据 | 过早改整体评分 | maturity evidence test |
| Benchmark | 可选 Runtime 产物存在时必须可验 | benchmark 明确不要求 task-runs | 存在坏 task-run 时不会失败 | 防止脏 Runtime 证据污染闭环 | 不应让缺失 task-runs 失败 | benchmark integration |
| Experience Summary | LLM 摘要可读真实任务内容 | 只把 run 目录文件名注入 prompt | LLM 看不到 sensor failed/skipped、handoff 摘要 | 让智能总结具备语义输入 | prompt 体积膨胀 | source collection test |

## 用户故事

作为 Harness Maintainer，当外部 Runtime 已经在 `.ai/task-runs/<task-id>/` 写出 `harness-map.yaml`、`sensor-report.yaml`、`runtime-summary.yaml` 和 handoff / decision 文档时，我可以让 Harness Builder 只读校验这些过程数据，并在 Experience index、maturity evidence、benchmark 和 experience summary 输入中看到真实任务结果，从而让后续 self-improve 基于可审计的运行证据，而不是只基于候选文件计数。

## 方案选择

### 方案 A：直接把成熟度 overall 晋级到 L3/L4

拒绝。当前 Runtime 证据还没有被结构化校验；先改评分会把成熟度变成主观判断。

### 方案 B：恢复 Builder 自己生成 `.ai/task-runs`

拒绝。当前边界已经确认 Builder 不提供 `run` 命令，Runtime 产物由宿主 AI Coding 工具或 Workflow Skill 承载。

### 方案 C：只读摄取外部 Runtime 产物

采用。Builder 只在 `.ai/task-runs` 已存在时校验和汇总，不创建、不执行、不修复 Runtime 产物。缺失 task-runs 仍是可接受状态；存在但 schema 无效、跨文件不一致或 failed/skipped sensor 未被显式记录时，benchmark 必须暴露问题。

## 设计

新增 Runtime task-run 只读契约层：

- `schemas/runtime_task_run.py`
  - `RuntimeSummary`：读取 `.ai/task-runs/<task-id>/runtime-summary.yaml`。
  - `RuntimeTaskRunSummary`：Builder 汇总后的只读摘要，不作为 Runtime 必写产物。
- `tools/runtime_task_runs.py`
  - `iter_runtime_task_runs(ai)`：列出 task-run 目录。
  - `load_runtime_task_run(run_dir)`：校验 harness-map、sensor-report、runtime-summary 和关键 Markdown 产物。
  - `summarize_runtime_task_runs(ai)`：返回 task 数、failed/skipped/passed sensor 数、unresolved sensor 数、repair attempt 数、风险数量和源路径。

Runtime 必需文件第一版定义为：

- `harness-map.yaml`：用现有 `HarnessMap` schema 校验。
- `sensor-report.yaml`：用现有 `SensorReport` schema 校验。
- `runtime-summary.yaml`：用新增 `RuntimeSummary` schema 校验。
- `decision-log.md`：必须存在且非空。
- `handoff-summary.md`：必须存在且非空。

可选文件第一版只检查存在性，不做 hard fail：

- `workflow-events.jsonl`
- `used-guides.yaml`
- `experience-candidates.md`

Runtime consistency 规则：

- run directory name、`HarnessMap.task_id`、`SensorReport.task_id`、`RuntimeSummary.task_id` 必须一致。
- `RuntimeSummary.selected_workflow` 必须与 `HarnessMap.selected_workflow` 一致。
- `RuntimeSummary.sensor_status` 必须能由 `SensorReport.sensor_results` 推导：有 failed 则 failed；否则有 skipped 则 degraded；否则 passed；无结果则 unresolved。
- `RuntimeSummary.unresolved_sensor_count` 必须等于 failed + skipped 结果数。
- failed/skipped sensor 必须有非空 summary，不能伪装成 passed。

Maturity / Experience 集成：

- `ExperienceIndex.sources` 继续记录 `.ai/task-runs/`，但 item_count 来自 schema-valid task-run 数。
- `MaturityEvidencePack.observability` 增加 runtime task-run 统计字段。
- `MaturityEvidencePack.experience.runtime_task_run_count` 继续保留。
- `_warnings()` 在 task-runs 存在时不再写 absent warning，但 invalid task-runs 应显式失败于 benchmark 或调用方。
- `summarize_experience._collect_sources()` 对 task-run 注入结构化摘要文本，而不是目录文件名列表。

Benchmark 集成：

- 新增 `content:runtime-task-run-artifacts`。
- `.ai/task-runs` 缺失时该 check passed 且 `present=false`。
- `.ai/task-runs` 存在且所有 task-run schema/consistency 合法时 passed。
- 缺文件、schema 错、task id 不一致、sensor 状态不一致、failed/skipped summary 为空时 failed。

## 关键决策 / 取舍

- 不把 `.ai/task-runs` 加入 REQUIRED_FILES；Runtime 产物仍是可选外部输入。
- 不修改成熟度整体等级算法；本轮只补可信证据面。
- 不让 LLM 解析 Runtime YAML；Python 先 schema 校验和汇总，再把安全摘要交给 LLM experience summary prompt。
- 不执行任何 sensor command，不读取仓库外路径，不生成 task-runs。

## Assumptions / Risks

- 假设宿主 Runtime 会按 Workflow Skill 中已有契约写出 `runtime-summary.yaml`。如果未来 Runtime 格式变化，本层需要通过 schema 版本演进。
- 旧的历史 task-runs 可能缺少 `runtime-summary.yaml`；一旦存在就失败是刻意设计，避免不可信证据进入成熟度。
- 本轮不会证明 LLM 能从真实任务中生成高质量经验，只证明真实任务数据可进入受控上下文。

## 边界情况与失败模式

- `.ai/task-runs` 不存在：Experience index 警告 absent，benchmark optional passed。
- task-run 目录为空：benchmark failed。
- YAML schema invalid：benchmark failed，直接暴露 schema error。
- `sensor-report.yaml` 有 failed/skipped 但 `runtime-summary.yaml` 声称 passed：benchmark failed。
- `decision-log.md` 或 `handoff-summary.md` 为空：benchmark failed。

## Sub Agent 使用情况

- Hume 只读调研 North Star 与当前代码 gap，建议 Runtime Task-Run Ingestion 作为优先 milestone。
- Epicurus 只读审查测试覆盖，指出 E2E 和 self-improve 纵向验收还有缺口；这些会作为 Self-Harness Gate 后续候选，不混入本轮。

## 可执行验收标准

1. Unit：合法 task-run 汇总能得到 task count、sensor passed/failed/skipped、repair attempts、source path。
2. Unit：缺少 `runtime-summary.yaml`、task id 不一致、sensor 状态不一致会显式失败。
3. Unit：Experience index 对 schema-valid task-runs 记录 `.ai/task-runs/` source，并移除 absent warning。
4. Unit：Maturity evidence 的 observability 包含 runtime task-run 统计。
5. Unit：Experience summary source collection 注入 sensor failed/skipped 和 handoff 摘要内容。
6. Integration：benchmark 缺少 task-runs 时 `content:runtime-task-run-artifacts` passed 且 `present=false`。
7. Integration：benchmark 对合法 task-run passed，对非法 task-run failed。
8. 文档：README、engineering runtime / sensor gate 规则和演进记录同步说明“Builder 只读消费，不生成 Runtime 产物”。
