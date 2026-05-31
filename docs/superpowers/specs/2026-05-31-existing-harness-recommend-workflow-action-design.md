# Existing Harness Recommend Workflow Action Design

## North Star 能力模块

- CLI Experience：`init` 是后续维护入口，普通用户不应记住专家命令顺序。
- Workflow Runtime Specification：根据任务 brief 和 routing policy 推荐 Workflow、Guides、Sensors 和人工确认点。
- Experience & Self-Improve：workflow recommendation 是 review-only 信号，应进入 Experience index、maturity evidence 和后续 improvement 候选链路。

## Current State Gap Analysis

| 候选 gap | 目标态要求 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 排序 |
|---|---|---|---|---|---|---|---|
| existing-Harness guided `recommend-workflow` | 维护入口能围绕一个任务生成 review-only workflow recommendation | standalone `recommend-workflow` 已有 schema、prompt、benchmark 和 Experience/Maturity 刷新 | 普通用户仍需记住专家命令和参数 | 高，补齐“向导组织底层能力”和智能路由体验 | 中，涉及 LLM、review-only 边界和 task brief UX | 高，可 mock LLM 并验 schema / benchmark | 1 |
| candidate governance menu | 从维护入口处理候选 accepted/deferred/rejected/applied | standalone `review-candidate` 已存在 | 需要候选选择、rationale、apply 边界 | 高 | 高，可能修改正式资产 | 高但范围更大 | 2 |
| guided `self-improve` | 从维护入口生成 self-improve package | standalone 能力存在 | 需要解释何时触发深度智能改进 | 中 | 中到高，LLM 链路更多 | 中 | 3 |

本轮只选择 guided `recommend-workflow`。它是可独立验收的小步智能化切片：用户输入任务说明，系统用 LLM + 当前 Harness routing policy 生成可审查推荐，不执行任务、不修改正式 policy。

## 设计

当 guided `init` 检测到已有 Harness 后，在维护菜单新增：

```text
- recommend-workflow：输入一个任务说明，生成 review-only Workflow 推荐，不执行任务或修改正式 routing policy。
```

用户选择 `recommend-workflow`、`recommend`、`workflow`、`工作流` 或 `路由` 后：

1. 提示输入任务说明 `task_brief`。为空则显式失败并终止本次 guided action，不调用 LLM。
2. 提示输入稳定 `task_id`，默认 `manual-task`。
3. 调用现有 `recommend_workflow(repo, task_brief=..., task_id=...)`，复用已存在的 LLM prompt、schema 校验、review-only artifact 写入和 Experience/Maturity 刷新。
4. 从 `.ai/review/workflow-routing-recommendation.yaml` 读取 `WorkflowRecommendationReport`，打印中文摘要：推荐 workflow、risk、confidence、是否需要人工确认、review-only 文件路径。
5. 在 init trace 中记录 action、task id、recommended workflow、risk/confidence 和相关 artifacts。

## 边界与失败模式

- LLM 不可用、返回非法 JSON、schema 无效或引用未知 workflow/routing rule 时，必须显式失败；不添加 fallback。
- 该动作只写 review-only recommendation 和派生 evidence，不执行 Runtime、不生成 `.ai/task-runs`、不生成 Harness Map、不应用 `.ai/harness-config.yaml` routing policy 变更。
- 不重新扫描已有 Harness；测试会替换扫描函数为失败函数。
- 不覆盖正式资产：inventory、command catalog、harness config、Guides、Sensors、Workflow Skills、scan metadata、LLM scan proposal、weapon library selection。
- 对高风险或低置信度 recommendation 仍保持 `pending_harness_maintainer_review`，后续由 `improve` / `self-improve` / candidate governance 处理。

## Assumptions / Risks

- Assumption：guided 维护入口可以收集 `task_brief`，因为 workflow recommendation 必须有任务语义输入，不能凭空推荐。
- Assumption：`task_id` 默认 `manual-task` 足以用于人工探索；自动化场景继续使用 standalone command 明确传参。
- Risk：真实 LLM 可能失败或无 key；本轮不掩盖失败，只在 mock integration 中验证 orchestration，真实 acceptance 仍由现有 LLM/acceptance 策略承担。

## Sub Agent 使用

本轮启动 explorer 子代理审查 guided `recommend-workflow` 的边界、测试和风险；主线程并行读取现有实现和先写 RED 测试。若子代理返回新的风险，会在实现或 Self-Harness Gate 中吸收。

## 可执行验收标准

- guided existing-Harness 菜单包含 `recommend-workflow`。
- 输入任务说明和 task id 后生成 `.ai/review/workflow-routing-recommendation.yaml` 和 `.md`。
- YAML 通过 `WorkflowRecommendationReport` schema；Markdown 保留 `## Review Boundary` 和 `pending_harness_maintainer_review`。
- `.ai/experience/experience-index.yaml` 的 `workflow_recommendation_count` 变为 1；`.ai/maturity-evidence.yaml` 同步该计数。
- benchmark 对 guided 生成的 recommendation artifact 的 `content:workflow-recommendation-review` 检查通过。
- 不扫描、不覆盖正式 Harness 资产、不创建 `.ai/task-runs`。
- trace summary 包含 `existing_harness_action: recommend-workflow` 和 `recommended_workflow`。

