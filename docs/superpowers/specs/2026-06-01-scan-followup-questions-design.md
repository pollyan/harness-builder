# Scan Follow-up Questions 设计

## 背景

`guided-init-ai4se-real-repo-findings.md` 中剩余的核心问题是 LLM-planned deep scan 仍未形成足够完整的补救闭环。最近几轮已经完成：

- 全量轻量 manifest 带 bucket / priority / reason。
- LLM evidence planner 可请求未采样文件。
- planner 计划和实际读取结果进入 `scan-metadata.yaml`。
- guided CLI 展示 LLM 深度补充，并把 planner low confidence 转成待确认项。

但 coverage gap、unsupported stack claim、unknown stack、模块边界缺失这类问题仍主要停留在 warning 或散落的 CLI 文案里。系统还没有形成一组机器可读、可展示、可进入 `questionnaire.yaml` / `human-input-needed.md` 的“扫描补救追问”。这会让大仓库里“抽样不足 / claim 冲突 / unknown”继续表现为“提示一下然后继续生成”。

本轮做 P0 的 targeted 追问部分：把这些问题转成结构化 follow-up questions。真正的二次 LLM self-check、targeted scan 再读取、claim-level support matrix 扩展留给后续独立切片。

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/engineering/init-workflow.md`、`docs/engineering/llm-contracts.md`、`docs/engineering/testing-strategy.md`、`docs/todos/guided-init-ai4se-real-repo-findings.md`、近期 evolution log、`scan.py`、`scan_repo.py`、`scan_reconciler.py`、`interactive_init.py`、`human_confirmation.py`、相关 unit / integration 测试。
- 按需未展开：`sensor-and-gate-rules.md` 和已有 Harness 维护入口代码，本轮不改 benchmark hard gate、Runtime 或维护入口。

候选 gap：

| 候选 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. 扫描补救追问清单 | coverage gap、unsupported stack claim、unknown stack、模块缺失进入结构化 follow-up，并在 CLI / questionnaire / human-input 中可见 | coverage warning、stack warning、unknown / no module CLI 文案已有；planner low confidence 已进入待确认 | warning 与用户追问没有统一机器契约，不能稳定驱动后续成熟度和生成前补充 | 大仓库不会只是“提示抽样不足后继续”，Maintainer 可在补充输入前看到应修正什么 | 中低，新增 scan metadata 可选字段和 questionnaire 类型，不新增 LLM 调用 | schema、reconciler、human confirmation、guided transcript | 依赖现有 coverage / stack validation | CLI 展示“深度追问”；`scan-metadata.yaml` 有 `followup_questions`；questionnaire / human-input 有稳定 id |
| B. 二次 LLM self-check | conflict / unknown 后自动带着 warning 和 evidence 再请求 LLM 自查 | 当前只有 planner -> final scan 单轮 | 需要新 prompt / parser / retry 策略和结果调和 | 更接近智能扫描目标态 | 高，涉及 LLM 调用次数、成本、失败语义、acceptance | 需要 unit + LLM contracts + acceptance | 需要设计新 schema 与 prompt | self-check 输出进入 metadata 并改变 proposal 或 confirmation |
| C. claim-level validation 扩展 | module / risk / config / CI / architecture signal 均有 support / conflict / unknown | 只有 stack 和 command 有较明确验证 | 风险 / module 可能被当作事实写入资产 | 提升资产可信度 | 中高，涉及 schema、writer、benchmark | unit / integration / benchmark | 需要定义每类 claim 的 evidence rule | validation report 驱动 warnings、CLI、asset rendering |

排序结论：

1. 选择 A。它直接回应 open todo 的“coverage gap / conflict / unknown 不能静默继续”，且能在一个纵向切片内打通 metadata -> CLI -> questionnaire -> human-input。
2. B 暂不选，因为它需要新增 LLM self-check prompt 和失败语义。当前先把“何时需要补救、问什么”结构化，后续 self-check 可以消费同一 follow-up 契约。
3. C 暂不选，因为它是更大范围的 claim validation hardening，容易和本轮 targeted 追问混在一起。

## Milestone

用户故事：

作为 Harness Maintainer，当我在大型或多栈仓库运行首次 guided `init`，并且扫描存在源码覆盖不足、LLM 栈判断缺少证据、主要技术栈未知或模块边界不清时，我可以在 CLI、`.ai/scan-metadata.yaml`、`.ai/questionnaire.yaml` 和 `.ai/human-input-needed.md` 中看到明确的补救追问，从而知道应该补充哪些关键路径、技术栈、模块边界或验证线索，而不是让系统带着不确定性继续生成一份看似完整的 Harness。

## 设计

### 新增 Scan Follow-up 契约

在 `ScanMetadata` 中新增可选字段：

```python
followup_questions: list[ScanFollowupQuestion]
```

每个 follow-up question 包含：

- `interaction_id`：稳定 id，例如 `confirm:scan-followup:coverage-source-java`。
- `trigger`：`coverage_gap`、`stack_claim_without_evidence`、`unknown_stack`、`module_boundary_unclear`、`test_evidence_missing`。
- `question`：面向 Maintainer 的中文问题。
- `reason`：为什么需要这个补救输入。
- `evidence`：关联 bucket、stack、path 或 warning code。
- `confidence`：默认 `low`。
- `affects`：说明影响哪些后续决策，例如 `maturity`、`guides`、`sensors`、`workflow`。

字段是可选新增，旧 `.ai/scan-metadata.yaml` 仍可解析。

### 生成规则

`reconcile_scan()` 在已有 warning / validation 基础上生成 follow-up：

- `source_sampling_truncated` -> `coverage_gap`：询问哪些目录、入口文件或高风险路径必须补充。
- `llm_stack_claim_without_evidence` -> `stack_claim_without_evidence`：询问是否存在该技术栈对应模块，或应忽略该 LLM claim。
- `proposal.primary_stack == "unknown"` -> `unknown_stack`：询问真实主技术栈和入口目录。
- `proposal.modules` 为空 -> `module_boundary_unclear`：询问主要模块路径、职责和入口文件。
- `test_evidence_not_found` -> `test_evidence_missing`：询问真实 test / integration / lint / typecheck 入口。

这些问题不改变 scan proposal，不自动修正 inventory，不伪装成已验证事实。

### CLI 与 human confirmation

首次 guided `init` 的扫描关注点中新增 `深度追问` 分组。只有 `followup_questions` 非空时展示，放在 `LLM 深度补充` 后、`风险区域` 前。

`build_questionnaire()` 读取 `scan_metadata.followup_questions` 并转成：

- `interaction_type`: `scan_followup_confirmation`
- `interaction_id`: 使用 follow-up 原始 id
- `question`: 使用 follow-up question
- `reason`: 包含 follow-up reason 和 affects

`human-input-needed.md` 通过现有 questionnaire markdown 自动列出这些问题。

### 非目标

- 不新增二次 LLM self-check prompt。
- 不修改 `LLMScanProposal` schema。
- 不把 follow-up 回答自动解析成正式资产变更。
- 不扩大 evidence 读取预算。
- 不调整 benchmark scoring。

## 验收标准

1. `ScanMetadata` schema 接受 `followup_questions`，旧 metadata 无该字段仍兼容。
2. `reconcile_scan()` 对 source sampling truncation、unsupported stack claim、unknown stack、空 modules 和缺少测试 evidence 生成稳定 follow-up question。
3. guided CLI 在 follow-up 存在时展示 `深度追问` 分组，包含问题、原因和影响范围。
4. `.ai/questionnaire.yaml` 包含 `scan_followup_confirmation` 类型问题，且通过 schema 校验。
5. `.ai/human-input-needed.md` 包含这些 follow-up 的稳定 `interaction_id` 和中文问题。
6. 文档和 todo 明确：本轮完成 targeted follow-up，不等于完成二次 LLM self-check。

## Assumptions / Risks

- Assumption：follow-up 是补救入口，不是自动修复机制；用户回答的结构化消费可由后续 milestone 接入。
- Risk：follow-up 与既有 scan warning confirmation 可能有一定重复。当前保留 scan warning confirmation 作为低层审计问题，同时让 follow-up 提供更面向用户的补救问题；后续可做去重或优先级排序。
- Risk：问题数量可能变多；本轮先限制每类 trigger 生成少量稳定问题，避免问卷膨胀。

## Sub Agent 使用

本轮启动 explorer 子代理做只读调研，重点确认 coverage warning、planner low confidence、stack conflict / unknown 的产生和消费路径。主线程先按当前已知路径推进 spec / plan；子代理结果如指出更低风险落点，会在实现前整合。
