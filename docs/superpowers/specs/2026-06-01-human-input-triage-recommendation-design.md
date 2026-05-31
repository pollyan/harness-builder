# Human Input Triage Recommendation 设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景 North Star、`docs/todos/README.md`、`docs/superpowers/plans/2026-06-01-human-input-backlog-maintenance-entry-migration.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`src/harness_builder_agent/tools/maintenance_triage.py`、`src/harness_builder_agent/tools/interactive_init.py`、`src/harness_builder_agent/schemas/human_confirmation.py` 和相关 maintenance triage / guided init 测试。
- 按需未展开：`docs/engineering/llm-contracts.md`、`docs/engineering/sensor-and-gate-rules.md` 和架构专题。本轮不改 LLM、Sensor、benchmark 检查项、目录结构或 Runtime 契约。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. scan follow-up backlog 进入 Maintenance triage | North Star / 上轮 human-input 迁移后续 | 再次运行 guided `init` 时，未解决或部分回应的 scan follow-up 不只显示计数，还能成为 top action 并推荐 `review-human-input` | 维护入口已展示 questionnaire 状态、scan follow-up resolved / partial / unaddressed 计数，也已有 guided `review-human-input` 动作 | `build_maintenance_triage()` 只读 benchmark 和 Experience index，不读 `questionnaire.yaml`，所以 Maintainer 需要自己从状态行推断下一步 | 补齐“看见问题 -> 推荐动作 -> guided 治理”的闭环，降低已有 Harness 接管成本 | 低；只读 `Questionnaire` schema，新增 deterministic triage，不修改正式资产 | unit 覆盖 action、排序、render、guidance；integration 覆盖 existing Harness 输出和不扫描 / 不覆盖 | 依赖现有 `Questionnaire` schema 和 `review-human-input` 动作 | top action 包含 `review-human-input`、reason、count、detail 和中文 guidance；已有 Harness exit 不扫描不覆盖 | 本轮 |
| B. 首次 init 的用户补充对最终 maturity preview 的可见影响 | init North Star | 用户补充 scan / rules / workflow 后，最终预览更清楚说明这些输入如何改变成熟度差距和推荐 | 当前已有即时复述和最终摘要，且 structured decisions 已落盘 | 仍可能偏“补充已记录”，对“为什么改变推荐优先级”的解释可更强 | 提升首次初始化协作感 | 中；触及较长 guided init transcript 和多处文案 | guided integration CLI transcript | 需要审查现有预览 writer | CLI 输出和 init-summary diff | 下一轮候选 |
| C. push / full regression 同步远端 | Gate / git 状态 | 本地 ahead 提交形成独立工作包后通过 full regression 并 push | 当前本地 `main` 领先 `origin/main`，fast 可作为 commit 前门禁 | full regression 仍依赖 `DEEPSEEK_API_KEY` 和真实 `.benchmarks` 仓库 | 降低长期分叉风险 | 外部前置；不适合本地实现 milestone | `scripts/test-full.sh` 与 push 结果 | 需要凭证、网络和真实仓库 | full 通过后 push | 外部前置候选 |

排序结论：

1. 选择 A。它直接服务 `init-north-star.md` 中“再次进入已有 Harness 时，系统能解释最该先处理什么”的用户旅程；当前状态显示和 guided 动作都已存在，只差 deterministic triage 推荐，是一个完整且可本地验收的纵向切片。
2. B 也符合首次 init 主线，但范围更偏 CLI 叙事扩展，且需要先细读更多 preview 代码；A 的收益更确定，能把最近迁移的人机复核链路闭合。
3. C 受外部凭证和真实仓库前置影响，本轮不作为实现项；保留为 push 前置。

本轮 milestone：

作为 Harness Maintainer，当我再次运行 guided `init` 查看已有 Harness 健康状态时，如果 `.ai/questionnaire.yaml` 中存在未解决或部分回应的 scan follow-up，我可以在 Maintenance triage top actions 中直接看到 `review-human-input` 建议、待处理数量和第一个 interaction id，从而知道下一步应该先复核哪些扫描追问，而不是只看到原始计数后自行推断。

## 验收标准

1. `build_maintenance_triage()` 在 `.ai/questionnaire.yaml` 存在且包含 `unaddressed` 或 `partially_addressed_by_current_scan_supplement` 的 `scan_followup_confirmation` 时，生成 `action=review-human-input`、`reason=human_input_scan_followups_pending`、`source=.ai/questionnaire.yaml`、`count=<待处理数量>`、`detail=<首个待处理 interaction id>`。
2. 排序规则保持：benchmark contract health 优先于 human-input；asset candidate governance 优先于 human-input；human-input 优先于 workflow recommendation 和 pending improvements。benchmark 缺失时 `benchmark` 仍排第一。
3. `render_maintenance_triage_lines()` 输出包含 action、reason、source、count 和 detail。
4. `render_maintenance_triage_guidance_lines()` 用中文建议运行 `review-human-input`，并说明 `resolved` / `reopened` 的复核边界。
5. guided existing Harness integration 展示该 top action / guidance，并保持不扫描、不覆盖正式资产、不创建 `.ai/task-runs`。
6. README 与 `docs/engineering/init-workflow.md` 同步“Maintenance triage 可推荐 review-human-input”的长期规则。
7. 完成前运行目标 unit、目标 integration、完整 guided init integration、`git diff --check` 和 `scripts/test-fast.sh`。

## 决策与取舍

- 只统计 `scan_followup_confirmation`，不把 context confirmation、candidate confirmation 或 scan warning confirmation 混入同一动作。
- 只把 `unaddressed` 和 `partially_addressed_by_current_scan_supplement` 视为待复核；`reviewed_resolved_by_harness_maintainer` 不进入 triage。
- triage 仍只推荐动作，不自动执行治理、不修改正式 Harness 资产、不创建 Runtime 产物。
- 复用 `Questionnaire` Pydantic schema；旧或损坏的 questionnaire 应显式失败，符合 no silent fallback。

## Assumptions / Risks

- Assumption：首个待处理 interaction id 足以作为 top action detail；完整列表仍在 `.ai/questionnaire.yaml` 和 `.ai/human-input-needed.md`。
- Risk：benchmark 未运行时 human-input 可能排第二；这是刻意保留质量门禁优先级。
- Risk：本轮未使用 sub agent 做独立审查，因为 spawn 受当前线程上限阻塞；主线程通过现有测试和文档补足审查。
