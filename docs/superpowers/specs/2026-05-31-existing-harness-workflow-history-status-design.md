# Existing Harness Workflow History Status Design

## 用户故事

作为 Harness Maintainer，当我再次运行 guided `init` 查看已有 Harness 状态时，我可以直接看到 workflow recommendation 历史中的最新任务、推荐 workflow、风险和待审核状态，从而判断是否需要进入 `improve` 或 `review-candidate` 处理 routing policy gap。

## Current State Gap Analysis

- North Star 要求再次执行 `init` 是状态感知维护入口，持续演进阶段要从任务经验和评审反馈中提升 Harness。
- 当前 `recommend-workflow` 已保留 `.ai/review/workflow-routing-recommendations/index.yaml` 历史，Experience / Maturity 能统计历史数量。
- guided `init` 的 Existing Harness 状态摘要仍只显示 `workflow_recommendations=<count>`，没有解释最新 recommendation 的 task、workflow、risk、review status 或 history index 路径。
- guided `recommend-workflow` 调用底层 `recommend_workflow()` 后会写 history artifacts，但 trace/output 仍只列 latest YAML/Markdown 和 Experience/Maturity 派生产物。
- 这会让 Maintainer 看到“有 recommendation”，但不知道最近一个待审核 routing signal 是什么，降低审查接管体验。

## 目标

- Existing Harness 状态摘要在有 history index 时展示：
  - `workflow_recommendations=<count>`
  - latest recommendation id
  - task id
  - recommended workflow
  - risk level
  - review status
  - source index path
- 没有 history index 但有 legacy latest recommendation 时，保持兼容，展示 latest 文件中的 task/workflow/risk/status。
- guided `recommend-workflow` 成功后，输出和 trace artifact 同步包含 history index 与 history summary。
- 所有新增显示必须来自 Pydantic schema 校验后的机器产物；schema 错误显式失败，不 silent fallback。

## 非目标

- 不实现 interactive history browser 或 diff。
- 不改变 LLM workflow router prompt/parser。
- 不自动应用 workflow policy。
- 不生成 `.ai/task-runs`。
- 不改变 Experience / Maturity 计数模型。

## 设计

### 状态摘要

新增小 helper 读取 workflow recommendation review signal：

- 优先读取 `.ai/review/workflow-routing-recommendations/index.yaml`，使用 `WorkflowRecommendationHistory` schema。
- 如果 history 存在且有 recommendation，展示 latest entry。
- 如果 history 不存在，读取 `.ai/review/workflow-routing-recommendation.yaml`，使用 `WorkflowRecommendationReport` schema。
- 如果都不存在，只保留 `workflow_recommendations=0`。

Existing Harness 状态仍输出平铺行，便于当前测试和 CLI 扫描：

```text
workflow_recommendations=2
latest_workflow_recommendation=task-2-... task=task-2 workflow=standard risk=high status=pending_harness_maintainer_review source=.ai/review/workflow-routing-recommendations/index.yaml
```

### Guided Recommend Trace

guided `recommend-workflow` 继续写 latest compatibility files，同时记录：

- `.ai/review/workflow-routing-recommendations/index.yaml`
- `.ai/review/workflow-routing-recommendations.md`

输出摘要补充 history index 和 summary 路径，告诉 Maintainer 这次推荐已进入历史。

## 验收标准

- integration 覆盖已有 Harness 有两条 recommendation history 时，guided `init -> exit` 状态摘要展示 count、latest id、task id、recommended workflow、risk、review status 和 history index path。
- integration 覆盖 legacy latest recommendation 存在但 history index 缺失时，guided `init -> exit` 状态摘要仍展示 latest task/workflow/risk/status。
- integration 覆盖 guided `recommend-workflow` 输出 history index / summary 路径，trace artifacts 包含 history artifacts，且不创建 `.ai/task-runs`、不覆盖正式 Harness 资产。
- README 和 init workflow 文档同步维护入口会展示 latest workflow recommendation signal。

## Decisions / Responses

- 价值切分：本轮把上一轮新增的 history 数据接入 Maintainer 的主入口状态体验，避免“只有机器计数、没有人类可审查信号”。
- 边界回应：只展示 review-only signal，不执行 Runtime、不应用 routing policy。
- 兼容回应：旧 Harness 只有 latest 文件时仍展示一条 latest signal。
- 失败回应：如果 history schema 无效，guided status 应显式失败，暴露契约问题，不能伪装成 missing。

## Assumptions / Risks

- 假设一行 latest signal 足以支持第一步维护入口判断；完整浏览历史留给后续。
- 风险是状态输出继续变长；本轮只添加一行 latest signal，保持可扫描。
- 风险是旧 latest 文件与新 history 同时存在但不一致；优先信任 history index，因为它是多任务审计契约。
