# Workflow Recommendation History Design

## 用户故事

作为 Harness Maintainer，当我在已有 Harness 上为多个真实任务运行 `recommend-workflow` 时，我可以保留每一次 review-only workflow recommendation 的独立记录和索引，从而审计任务路由判断的演进，并让 Experience / Maturity 能识别重复 routing gap。

## Current State Gap Analysis

- North Star 要求 Recommendation、Experience 和 Maturity 形成持续改进闭环。
- 当前 `recommend_workflow()` 每次覆盖 `.ai/review/workflow-routing-recommendation.yaml` 和 `.md`。
- `experience-index.yaml` 只能把 workflow recommendation 计数为 `1`，无法表达多个任务的推荐历史。
- workflow policy 改进候选可能引用 `.ai/review/workflow-routing-recommendation.yaml`，但无法说明来自哪一次 task brief。
- 这不是 Runtime 阻塞问题；Builder 仍应保持 review-only，不生成 `.ai/task-runs`。

## 目标

- 每次 `recommend-workflow` 写入一条不可覆盖的历史 recommendation。
- 继续写现有 latest 文件，保持现有命令、benchmark 和下游链路兼容。
- 新增机器消费 index，记录 latest id、每条 recommendation 的路径、task id、workflow、risk、confidence 和 review status。
- Experience index 和 maturity evidence 能统计历史 recommendation 数量。
- Benchmark 在 history 存在时校验 index schema、每条 YAML schema、Markdown 配对和 review boundary。

## 非目标

- 不实现 Runtime execution history。
- 不创建 `.ai/task-runs`。
- 不改变 LLM parser、prompt 或 workflow routing 决策逻辑。
- 不实现 UI 历史浏览或 recommendation diff。
- 不删除 latest 兼容文件。

## 设计

### 产物

每次推荐生成：

```text
.ai/review/workflow-routing-recommendation.yaml
.ai/review/workflow-routing-recommendation.md
.ai/review/workflow-routing-recommendations/<recommendation_id>.yaml
.ai/review/workflow-routing-recommendations/<recommendation_id>.md
.ai/review/workflow-routing-recommendations/index.yaml
.ai/review/workflow-routing-recommendations.md
```

`recommendation_id` 使用 task id 的安全化前缀加 UTC 时间戳，避免覆盖。

### Schema

新增 `WorkflowRecommendationHistory`：

- `schema_version`
- `latest_recommendation_id`
- `recommendations[]`

每条 item 包含：

- `recommendation_id`
- `task_id`
- `created_at`
- `yaml_path`
- `markdown_path`
- `recommended_workflow`
- `risk_level`
- `confidence`
- `review_status`

### Experience / Maturity

`experience-index.yaml` 中 `workflow_recommendation_count` 优先读取 history index 数量；没有 history 时保留 legacy latest 文件计数。

source path 优先指向 `.ai/review/workflow-routing-recommendations/index.yaml`，kind 仍为 `workflow_recommendation`，`item_count` 为历史条数。

### Benchmark

现有 latest recommendation check 保留。新增或扩展 check：

- 如果 history index 不存在，不失败。
- 如果 history index 存在，则校验 schema。
- 每条 history item 的 YAML 和 Markdown 必须存在。
- YAML 必须符合 `WorkflowRecommendationReport`。
- Markdown 必须包含 `# Workflow Routing Recommendation` 和 `## Review Boundary`。
- YAML 的 `review_status` 必须是 `pending_harness_maintainer_review`。

## 验收标准

- unit 测试覆盖 history schema。
- unit 测试覆盖 Experience index 两条 recommendation history 计数为 `2`。
- integration 测试覆盖连续两次 `recommend-workflow` 后 history index 有两条，latest 指向第二次，latest 兼容文件仍存在。
- integration 测试覆盖不创建 `.ai/task-runs`。
- benchmark integration 覆盖 history index 缺 markdown 或 schema 错误时失败。
- README、engineering docs、演进记录同步。

## Decisions / Responses

- 用户价值切片：本轮服务 Harness Maintainer 审计多个真实任务的 workflow routing 判断，而不是单纯新增文件或字段。
- 当前问题回应：latest 文件继续作为兼容出口；历史索引成为 Experience / Maturity 的优先计数来源。
- Builder / Runtime 边界回应：历史 recommendation 是 review-only Builder 产物，不是 Runtime execution history，不生成 `.ai/task-runs`。
- 智能化边界回应：LLM 仍只负责生成单次 `WorkflowRecommendationReport` 判断；Python 负责 history id、schema、索引、Markdown 摘要和 benchmark 校验。
- 风险回应：history 存在时 benchmark 必须校验每条配对产物，防止索引看似成功但条目缺失或不可审计。

## Assumptions / Risks

- 假设保留 latest 文件是最低风险兼容策略。
- 风险是 history 产物增加 review 目录复杂度；本轮用 index 和 summary Markdown 控制可读性。
- 风险是 benchmark 检查过重；本轮只在 history 存在时校验，不把 history 设为 baseline required file。
