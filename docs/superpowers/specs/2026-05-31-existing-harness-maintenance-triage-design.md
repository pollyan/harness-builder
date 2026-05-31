# Existing Harness Maintenance Triage Design

## 用户故事

作为 Harness Maintainer，当我再次运行 guided `init` 进入已有 Harness 维护入口时，我可以直接看到当前最该处理的 3 个维护动作、每个动作的原因、来源文件和对应菜单动作，从而不用从一组 Experience / review signal 计数里自行推断下一步。

## Current State Gap Analysis

- North Star 要求 `init` 是主入口，再次执行 `init` 应进入状态感知维护入口，并“输出下一步，而不是甩文件列表”。
- 当前已有 Harness 入口已展示成熟度、benchmark、Experience / review signals 和可选动作。
- 当前缺口是这些 signals 仍偏计数面板：`pending_improvements=...`、`asset_candidates=...`、`workflow_recommendations=...`、`schema_content_failed_checks=...`。
- Maintainer 仍需要理解计数含义和命令顺序，才能决定是先跑 benchmark、处理候选、生成 self-improve package，还是从 workflow recommendation 推进 routing policy 改进。

## 目标

- 在 existing-Harness guided `init` 状态摘要中新增 `Maintenance triage` 区块。
- 最多展示 3 条 top actions，每条包含：
  - `top_action_N=<menu action>`
  - `reason=<stable reason code>`
  - `source=<.ai path or expected path>`
  - `next=<guided menu action>`
- 第一版优先级规则只基于已存在的结构化产物，不调用 LLM、不写文件：
  1. 缺少 maturity score -> `assess`
  2. 缺少 benchmark report -> `benchmark`
  3. benchmark 中 schema/content failed checks > 0 -> `benchmark`
  4. asset candidates 多于 governance decisions -> `review-candidate`
  5. workflow recommendation count > 0 -> `improve`
  6. pending improvements > 0 -> `self-improve`
  7. 没有待办信号 -> `recommend-workflow`

## 非目标

- 不执行任何维护动作。
- 不新增持久化 `.ai` 机器产物。
- 不改变成熟度评分模型。
- 不把 triage 当作 LLM 智能评审或 benchmark 结果。
- 不解决 workflow policy guided apply；那是后续更大的治理闭环。

## 设计

- 新增 `tools/maintenance_triage.py`：
  - `MaintenanceAction` dataclass。
  - `build_maintenance_triage(ai, score=None) -> list[MaintenanceAction]`。
  - `render_maintenance_triage_lines(actions) -> list[str]`。
- `interactive_init.py` 在 Experience / review signals 后输出 `Maintenance triage:`。
- helper 只读 `.ai/experience/experience-index.yaml`、`.ai/benchmark-report.yaml` 和可选 maturity score 对象。
- schema 错误继续由现有 Pydantic 解析显式失败，不降级成 missing。

## 验收标准

- integration：已有 Harness 首次再次进入 `init -> exit` 时，在没有 benchmark report 的情况下显示 `Maintenance triage` 和 `top_action_1=benchmark`。
- unit：当 benchmark 有 schema/content 失败、asset candidates 未完全治理、workflow recommendations 存在时，triage 按 benchmark -> review-candidate -> improve 排序。
- unit：当没有待办信号时，triage 给出 `recommend-workflow` 作为下一次真实任务入口。
- docs：README、init workflow、todo 和 evolution log 同步说明 existing-Harness 入口会展示 top maintenance actions。

## Decisions / Responses

- 价值切分：本轮服务“回到已有 Harness 后知道下一步做什么”的用户价值，不是单纯增加一个状态字段。
- 智能边界：本轮是结构化信号上的确定性 triage，不引入 LLM；它为后续 LLM-driven improvement proposer 和 workflow policy loop 降低用户入口负担。
- 工程取舍：新增 helper 模块，避免继续扩大 `interactive_init.py`。
- 输出取舍：使用稳定 `reason` 和 `next` 字段，方便测试，也方便未来 IDE / UI 层消费相同逻辑。

## Assumptions / Risks

- 假设 schema/content benchmark 失败比候选治理更优先，因为它说明当前 Harness 契约本身不可信。
- `candidate_governance_decision_count` 不是严格的 unresolved count；第一版用 `asset_candidate_count > governance_count` 作为近似，后续可升级为按 candidate id 计算。
- `workflow_recommendations > 0` 不代表一定要改 routing policy，只表示存在待 review 的 routing signal，因此 next action 是 `improve` 而不是自动 apply。
