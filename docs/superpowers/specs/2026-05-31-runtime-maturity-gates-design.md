# Runtime 运行证据成熟度门禁设计

## 背景

North Star 将成熟度定义为语义跃迁，而不是文件数量。L3 代表 Guides、Sensors 和 Workflow 形成项目级执行协议，关键门禁不可随意跳过；L4 代表基于任务类型、风险、历史经验和成熟度缺口持续生成可审查改进候选。

当前 Harness Builder 已能只读消费宿主 Runtime 生成的 `.ai/task-runs/<task-id>/`，并把 `harness-map.yaml`、`sensor-report.yaml`、`runtime-summary.yaml`、`decision-log.md` 和 `handoff-summary.md` 纳入 benchmark、Experience index 和 maturity evidence。但成熟度模型仍存在断层：

- `workflow` 维度只要 Workflow Skill 和 `standard-escalation` 存在就可到 L3。
- `observability` 只看 Builder generation trace，未利用 Runtime task-run 证据。
- `repair_loop` 固定为 L0。
- `governance_auditability` 只看 `.ai/runs/`，未利用 Runtime decision log / handoff。
- `overall_level` 只根据命令和 workflow 文件判断，最高基本停在 L2。

这会让用户看到的成熟度结果和真实任务运行证据脱节。

## Current State Gap Analysis

候选 gap 排序结果：

1. Runtime 运行证据成熟度门禁：直接承接刚完成的 Runtime task-run 摄取，把真实任务结果进入 L3 判断。
2. Workflow recommendation 到 policy lifecycle 端到端验收：已有骨架，缺少完整用户故事证明。
3. Self-improve package consumption：已有 review-only package，但下一轮消费治理状态不足。
4. Acceptance efficiency matrix：能降低循环成本，但不直接推进产品 North Star。
5. 过程文档中文 gate：保护流程质量，但用户价值间接。

本轮选择第 1 项，因为它直接提升 Maturity & Evolution 与 Experience / Self-Improve 的真实语义，且可通过本地 fixture 明确验收。

## 用户故事

作为 Harness Maintainer，当宿主 AI Coding Runtime 已经按契约写出 schema-valid `.ai/task-runs/<task-id>/` 运行证据时，我可以运行 `assess` 看到成熟度维度和 overall level 基于真实 Sensor Report、Decision Log、Handoff Summary 和 repair attempts 更新，从而判断当前 Harness 是否真正进入 Workflow-bound L3，而不是只因为文件齐全被误判为成熟。

## 设计决策

- Builder 继续不生成、不执行、不修复 `.ai/task-runs`；只读消费已存在的 Runtime 证据。
- L3 判断必须要求 runtime task-run 证据存在且 sensor 没有 failed / skipped / unresolved。
- failed / skipped / unresolved sensor 不是 Builder 产物校验失败，但会阻止成熟度提升，并写入 blocker。
- `repair_loop` 维度只在存在 Runtime task-run 且 `repair_attempts > 0` 时从 L0 提升到 L2；本轮不声称已达到自动重试 L3。
- `observability` 在存在 Runtime task-run 时从 generation trace 的 L1 提升到 L2，并引用 `.ai/task-runs/<task-id>/`。
- `governance_auditability` 在存在 Runtime decision log / handoff 时从 L1 提升到 L2。
- `workflow` 维度只有在 workflow skill 完整、risk-based routing 存在、并且 Runtime 证据全部 resolved 时才到 L3。
- `overall_level` 可在满足命令、workflow、risk routing、runtime resolved 证据时到 L3；没有 runtime task-run 仍保持 L2 ceiling。
- L4 不在本轮实现；缺少多任务趋势、经验治理闭环和动态策略优化时仍保持阻断。

## 可执行验收标准

- 无 `.ai/task-runs` 时，`assess` 仍不失败，但 `overall_level` 不超过 L2，并包含 runtime evidence blocker。
- 有一个合法且 sensor 全部 passed 的 Runtime task-run 时：
  - `workflow` 维度为 L3。
  - `observability` 维度至少为 L2。
  - `governance_auditability` 维度至少为 L2。
  - `overall_level` 为 L3。
  - evidence 引用 `.ai/task-runs/<task-id>/`。
- 有 Runtime task-run 但 sensor failed / skipped / unresolved 时：
  - `overall_level` 不超过 L2。
  - `workflow` 维度不提升到 L3。
  - blocker 明确说明 unresolved runtime sensors 阻止 L3。
- 有 repair attempts 时，`repair_loop` 维度从 L0 提升到 L2，并保留下一步要求“基于历史优化 repair loop”。
- `maturity-score.yaml` schema 不变；新增逻辑只改变字段值和 evidence/blocker 内容。
- README、engineering docs 和 evolution log 同步说明 Runtime 证据如何影响成熟度。

## Assumptions / Risks

- 假设 Runtime 产物已经通过 `runtime_task_runs.py` schema 与一致性校验；成熟度模型不重复解析原始 YAML。
- 假设单个 passed task-run 足以证明“已有一次 Workflow-bound 运行证据”，但不足以证明 L4 自适应能力。
- 风险：过早把 L3 解释为 Runtime 全面成熟。回应：L3 只代表有 resolved Runtime evidence；L4 仍被 Experience 和趋势闭环阻断。
- 风险：真实 task-run failed 时用户误以为 Builder 失败。回应：benchmark 校验产物结构，maturity 用 failed sensor 作为真实阻断证据，两者语义分开。

## 非目标

- 不新增 `run` 命令。
- 不实现参考 Runtime 或执行器。
- 不修改 Runtime task-run schema。
- 不实现 L4 趋势分析、Dashboard、Workflow Event Store。
- 不改变 `benchmark` 对 Runtime 产物的结构校验语义。

