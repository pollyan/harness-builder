# Existing Harness Candidate Governance Action Design

## North Star 能力模块

- CLI Experience：`init` 是已有 Harness 后续维护的主入口。
- Experience & Self-Improve：review-only 候选需要进入可审计治理闭环。
- Maturity & Evolution：候选治理决策应进入 Experience index，作为后续成熟度和改进信号。

## Current State Gap Analysis

| 候选 gap | 目标态要求 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 排序 |
|---|---|---|---|---|---|---|---|
| guided candidate governance | 维护入口能处理待确认候选 | standalone `review-candidate` 已支持 accepted/deferred/rejected/applied | 用户仍需记住专家命令和参数 | 高，补齐候选接管闭环 | 中；`applied` 会改正式资产 | 高，可先只支持非 applied 决策 | 1 |
| guided self-improve | 维护入口生成 self-improve package | standalone 已存在 | 需要解释何时触发深度 LLM 自改进 | 中 | 中到高，LLM 链路更多 | 中 | 2 |
| recommendation history | 多次 workflow recommendation 不互相覆盖 | 当前单份 latest artifact | 需要新 schema/存储模型 | 中 | 中到高 | 中 | 3 |

本轮只做 guided candidate governance 的非 applied 决策切片。`accepted`、`deferred`、`rejected` 能让 Maintainer 进入可审计接管闭环，同时避免本轮自动修改正式 Guides、Sensors 或 routing policy。

## 设计

当 guided `init` 检测到已有 Harness 后，在菜单新增：

```text
- review-candidate：记录候选 accepted / deferred / rejected 决策，不应用正式资产；applied 请使用专家命令。
```

用户选择 `review-candidate`、`candidate`、`governance`、`候选` 或 `治理` 后：

1. 如果 `.ai/review/asset-candidates.yaml` 不存在，现有 `review_candidate` 会显式失败。
2. 展示最多 10 个候选摘要，包括 candidate id、kind、suggested path、risk level 和标题。
3. 提示输入 candidate id。
4. 提示输入 decision，允许 `accepted`、`deferred`、`rejected`，默认 `deferred`。
5. 如果用户输入 `applied`，显式失败并提示使用 standalone `review-candidate` 专家命令，因为 applied 会修改正式资产，需要更完整的 diff / summary UX。
6. 提示输入 rationale，不能为空。
7. 提示输入 reviewer，默认 `harness-maintainer`。
8. 调用 `review_candidate(repo, candidate_id, decision, rationale, reviewer)`。
9. 记录 `.ai/review/candidate-governance.*` 和 `.ai/experience/experience-index.yaml` 到 init trace，打印中文摘要。

## 边界与失败模式

- 本轮不支持 guided `applied`；正式资产应用继续由 standalone `review-candidate --decision applied` 承担。
- 不重新扫描、不调用 LLM、不执行 Runtime、不创建 `.ai/task-runs`。
- 不覆盖正式 Harness 资产：inventory、command catalog、harness config、Guides、Sensors、Workflow Skills、scan metadata、LLM proposal、weapon selection。
- candidate id 不存在、asset-candidates 缺失、rationale 为空或 decision 非法时必须显式失败。
- 原始 `.ai/review/asset-candidates.yaml` 保持 review-only，不因治理记录而改写候选状态。

## Assumptions / Risks

- Assumption：记录 accepted/deferred/rejected 已能形成“处理待确认候选”的第一步闭环，后续再补 guided apply。
- Risk：用户可能期待 accepted 自动应用。菜单与输出必须明确“记录决策，不应用正式资产”。
- Risk：候选列表展示仍较弱。本轮先要求输入 candidate id，后续可以做候选浏览和编号选择。

## Sub Agent 使用

已启动 explorer 子代理只读审计 candidate governance 切片，重点确认是否适合排除 applied、需要触碰的文件和验收标准。主线程并行完成 RED 测试和设计；子代理结论将在实现或 Self-Harness Gate 中吸收。

## 可执行验收标准

- guided existing-Harness 菜单包含 `review-candidate`。
- 输入 candidate id、accepted/deferred/rejected、rationale 和 reviewer 后，生成 `.ai/review/candidate-governance.yaml` / `.md`。
- `CandidateGovernanceLog` schema 校验通过，决策记录 reviewer、rationale、evidence 和空 `applied_paths`。
- Experience index 的 `candidate_governance_decision_count` 变为 1。
- trace summary 包含 `existing_harness_action: review-candidate`、candidate id 和 decision。
- 不扫描、不覆盖正式 Harness 资产、不创建 `.ai/task-runs`。
