# Guided Candidate Apply Design

## 用户故事

作为 Harness Maintainer，当我在已有 Harness 上再次运行 guided `init` 并查看 self-improve 生成的 Guide / Sensor 候选时，我可以在向导中审查单个候选的目标路径、证据、风险和验收检查，并明确选择 `applied` 将它写入正式 Guide / Sensor Markdown，从而完成一条可审计的自改进接管闭环。

## Current State Gap Analysis

- North Star 目标态要求 Maintainer 能在“审查接管”和“持续演进”阶段审核、采纳、废弃自改进候选。
- 当前 guided `init` 已支持 `improve`、`self-improve`、`recommend-workflow` 和 `review-candidate`，但 guided `review-candidate` 只允许 `accepted` / `deferred` / `rejected`，显式拒绝 `applied`。
- standalone `review-candidate` 已支持安全 `applied`：Guide / Sensor Markdown 追加候选块，workflow policy 依赖结构化 patch，治理日志和 Experience index 会刷新。
- 缺口是直接用户必须离开主向导并记住专家命令，才能把已审查候选正式接管；这削弱成熟度驱动维护入口的闭环价值。

## 目标

- guided existing-Harness `review-candidate` 支持单个 Guide / Sensor 候选的 `applied` 决策。
- 应用前在 CLI 输出候选详情：id、kind、title、suggested path、risk、evidence sources、acceptance checks 和即将应用的边界。
- 成功后复用现有 `review_candidate(..., decision="applied")`，写入正式 Markdown、candidate governance、Experience index 和 trace artifacts。
- workflow policy 候选在 guided 入口仍不支持 `applied`，提示使用专家命令。

## 非目标

- 不批量应用多个候选。
- 不开放 guided workflow policy apply。
- 不从自由文本推断 `harness-config.yaml` patch。
- 不执行 Runtime，不创建 `.ai/task-runs`，不生成 harness map 或 sensor report。
- 不实现自动回滚、freshness / expiry 或组织级 dashboard。

## 设计

### CLI 行为

在 existing-Harness `review-candidate` 动作中，读取 `.ai/review/asset-candidates.yaml` 后展示候选列表。用户输入候选 id 后，系统展示该候选的详细审查摘要。

允许的决策变为：

- `accepted`
- `deferred`
- `rejected`
- `applied`，仅当候选 `kind` 是 `guide` 或 `sensor`

如果用户对 `workflow_policy` 候选输入 `applied`，guided 入口显式失败，错误说明该类型只能通过专家命令应用，因为需要更完整的结构化 patch 审核。

### 数据和产物

复用现有 `CandidateGovernanceLog` 和 `review_candidate()`，不新增 schema。成功应用后：

- 正式目标 Markdown 追加带 candidate marker 的候选块。
- `.ai/review/candidate-governance.yaml` 记录 `decision=applied` 和 `applied_paths`。
- `.ai/review/candidate-governance.md` 保留 review boundary。
- `.ai/experience/experience-index.yaml` 刷新 candidate governance source。
- 当前 init trace 记录 candidate governance artifact、experience index 和 `applied_path_count`。

### 错误与边界

- 空 rationale 继续由 `review_candidate()` 显式失败。
- 未知 candidate id 继续显式失败。
- 非 `.ai/` suggested path 继续显式失败。
- 已应用候选重复应用继续显式失败。
- guided `applied` 只允许 `guide` / `sensor`，避免主向导过早承担 workflow policy 正式配置变更风险。

## 验收标准

- integration 测试覆盖 guided `init -> review-candidate -> applied` 对 Guide 候选成功应用。
- 测试断言不重新扫描、不创建 `.ai/task-runs`、不覆盖 inventory / config / skills / 非目标 Guide/Sensor。
- 测试断言正式目标 Markdown 追加 candidate marker，治理日志记录 `decision=applied` 和 `applied_paths`。
- 测试断言 trace summary 和 artifacts 记录 `review-candidate`、candidate id、decision、applied path count、governance 和 experience index。
- 测试覆盖 guided `applied` 对 workflow policy 候选显式失败，且不写 governance。
- README、`docs/engineering/init-workflow.md`、演进记录同步说明新的 guided apply 边界。

## Assumptions / Risks

- 假设 Guide / Sensor Markdown 追加式应用是当前最小可接管闭环，风险低于 workflow policy 配置变更。
- 风险是用户可能误以为所有候选都可在 guided 入口应用；CLI 文案和文档必须明确 workflow policy 仍走专家命令。
- 风险是错误经验进入正式 Harness；本轮通过单候选、显式 id、候选详情展示、rationale 必填和底层路径校验降低风险。
