# Scan Follow-up Self-check 设计

## 背景

上一轮已经把 coverage gap、LLM stack claim 缺少 evidence、unknown stack、模块边界不清和测试 evidence 缺失转成 `ScanMetadata.followup_questions`，并在 guided CLI、`questionnaire.yaml` 和 `human-input-needed.md` 中展示为“深度追问”。

这个切片解决了“系统应该问什么”，但还没有解决“系统是否会基于这些问题再自检一次”。这会让大型或多栈仓库里的扫描不确定性仍停留在待办清单，离 `init-north-star.md` 要求的渐进式深入和智能化闭环还有差距。

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/engineering/init-workflow.md`、`docs/engineering/llm-contracts.md`、`docs/engineering/testing-strategy.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/guided-init-ai4se-real-repo-findings.md`、`docs/todos/maturity-driven-init-wizard.md`、`docs/evolution-log.md`。
- 已检查代码：`scan_repo.py`、`scan_reconciler.py`、`schemas/scan.py`、`llm_scan_analyzer.py`、`llm_evidence_planner.py`、`prompts/registry.py`、`interactive_init.py`、`human_confirmation.py` 和相关测试。
- 按需未展开：benchmark scoring 细节和已有 Harness 维护入口候选治理实现；本轮不改 benchmark 规则、不改维护入口动作。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. follow-up 二次 LLM self-check | 上一轮 Self-Harness Gate / ai4se todo | 深度追问被 LLM 基于当前 evidence 和 scan metadata 二次审查，形成 review-only resolution | 已有 `followup_questions`、CLI“深度追问”、questionnaire 和 human input | 追问只是待办，没有被智能扫描链路消费 | 让扫描不确定性进入“LLM 判断 + Python schema/validation”的闭环，提升首次 init 信任 | 中；新增 LLM prompt/schema/调用阶段，但不自动修改正式 inventory | schema unit、LLM parser unit、scan repo unit、guided CLI transcript | 依赖现有 follow-up 契约和 LLM 调用配置 | `scan_metadata.self_check` 有 schema；CLI 展示自检摘要；questionnaire reason 带自检建议；无 follow-up 时不调用 | 本轮 |
| B. 用户自然语言补充更强消费 | init North Star / todo | 用户自由补充能更明确影响成熟度、推荐和资产 | 结构化补充已能影响 inventory/catalog/risk；自然语言进入 decisions 和语义资产 | 自由文本仍偏记录，未进行语义归因或 LLM 解析 | 提升渐进式协作感 | 中高；若解析成事实，容易把补充伪装成已验证扫描结论 | guided integration、asset writer unit、maturity preview transcript | 需要先明确 scan resolution 与人工补充的边界 | 作为后续“用户补充 + self-check resolution 消费链路”候选 | 下一轮候选 |
| C. 维护入口候选列表/历史浏览 | maturity-driven wizard todo | 再次运行 init 时可以浏览更多候选和 workflow recommendation history | 维护入口已有 triage、latest recommendation 和主要动作 | 候选列表浏览仍不完整 | 改善已有 Harness 维护体验 | 中；主要是 CLI UX 和 schema 读取 | integration transcript | 依赖现有 review artifacts | 归入已有 Harness 维护入口 UX 工作包 | 后续工作包 |
| D. claim-level support/conflict/unknown validation | ai4se todo / LLM contracts | module/risk/config/CI/architecture claims 都有 support/conflict/unknown 证据矩阵 | 当前只对 stack claim 做验证，follow-up 能覆盖部分缺口 | 风险、模块和配置 claim 仍可能缺少统一支持关系 | 长期信任基础强 | 高；涉及 schema、reconciler、CLI、benchmark 和资产 writer | unit + integration + benchmark | 需要先定义 claim map 契约 | 拆成后续 hardening milestone | 后续候选 |

排序结论：

1. 选择 A，因为它直接消费上一轮新增的 `followup_questions`，服务首次 `init` 的“深度追问”和“智能化闭环”，且可以用 review-only 报告降低误改正式扫描结论的风险。
2. D 更底层但范围更大，适合在 self-check report 有落点后拆成 claim map hardening。
3. B 需要更谨慎地区分“人工补充说明”和“扫描事实”，适合在 self-check resolution 可被展示后再推进。
4. C 属于再次进入已有 Harness 的维护体验，不应打断短中期首次 `init` 深度扫描主线。

本轮 milestone：

作为 Harness Maintainer，当我首次 guided `init` 一个大型或多栈仓库且系统生成深度追问时，我可以看到 Builder 基于当前 evidence 对这些追问执行了一轮 LLM self-check，并把每个追问的 review-only 结论、风险和下一步写入 scan metadata、CLI 和人工确认链路，从而知道哪些问题仍需人工补充、哪些需要后续 targeted scan，而不是只拿到一组未消费的问题。

## 设计

### 数据契约

在 `schemas/scan.py` 中新增：

- `ScanSelfCheckResolution`
  - `interaction_id`
  - `trigger`
  - `status`: `supported_by_current_evidence`、`needs_human_confirmation`、`needs_targeted_scan`、`conflict_detected`
  - `rationale`
  - `evidence_sources`
  - `suggested_next_action`
  - `confidence`
- `ScanSelfCheckReport`
  - `schema_version`
  - `prompt_version`
  - `review_status`: 固定 `pending_harness_maintainer_review`
  - `overall_risk`: `low`、`medium`、`high`
  - `summary`
  - `resolutions`

`ScanMetadata` 新增可选 `self_check`。旧 metadata 没有该字段仍兼容。

### LLM 调用边界

新增 `llm_scan_self_checker.py`：

- 使用 `src/harness_builder_agent/prompts/llm_scan_self_check_v1.md` 和 prompt registry。
- 输入包含 `EvidenceBundle`、`ScanMetadata` 和 `followup_questions`。
- parser 要求合法 JSON、Pydantic schema、已知 `interaction_id` 和允许的 evidence source。
- 未知 interaction id 或未知 evidence source 必须显式失败。

`scan_repository()` 在 `reconcile_scan()` 之后判断：

- 如果没有 `followup_questions`，不运行 self-check。
- 如果有 `scan_self_check_caller`，运行 self-check，便于 mock 测试。
- 如果是真实 LLM 路径，也就是未传入 `llm_caller`，运行 self-check。
- 如果 mock `llm_caller` 存在但没有显式 self-check caller，不自动调用，避免现有 mock scan 测试被第三次 LLM 响应破坏。

self-check 失败时不 fallback，不吞异常。self-check 结果只写入 `ScanMetadata.self_check` 和 `inventory.stack_extensions["scan_metadata"]`，不自动修改 `ProjectInventory`、`CommandCatalog`、正式 Guides、Sensors 或 Workflow policy。

### CLI 与人工确认

首次 guided `init` 的扫描关注点中，如果存在 `self_check`：

- 在“深度追问”后展示“LLM 二次自检”。
- 展示 summary、overall risk 和前 5 条 resolution。
- 文案必须明确这是 review-only 结论，不代表正式扫描结论已自动修正。

`build_questionnaire()` 在生成 `scan_followup_confirmation` 时，如果存在同 interaction id 的 self-check resolution，就把 status、suggested next action 和 rationale 追加到 reason 中，帮助 `human-input-needed.md` 告诉用户为什么仍需要确认。

### 进度反馈

`scan_repository()` 新增 `scan-self-check` progress event。guided CLI 翻译为“请求 LLM 二次自检深度追问”。

只有实际运行 self-check 时才发事件，避免无 follow-up 的普通项目输出多余阶段。

## 验收标准

1. schema unit：`ScanMetadata` 接受 `self_check`，resolution 保留稳定 interaction id、status、evidence source 和 review-only 状态。
2. LLM parser unit：合法 self-check JSON 能解析；未知 interaction id、未知 evidence source、非法 JSON 或 schema 错误会显式失败。
3. scan repo unit：有 follow-up 且传入 `scan_self_check_caller` 时，`scan_repository()` 在 reconcile 后调用 self-check，并把结果写入 `inventory.stack_extensions["scan_metadata"]["self_check"]`；无 follow-up 时不调用。
4. guided CLI transcript：存在 `self_check` 时输出“LLM 二次自检”、review-only 边界、resolution status 和下一步建议。
5. questionnaire unit：`scan_followup_confirmation` 的 reason 包含对应 self-check 的 status 和 suggested next action。
6. 文档：同步 `init-workflow.md`、`llm-contracts.md`、todo 和 evolution log，说明 follow-up self-check 是 review-only，不自动修正正式扫描结论。

## Assumptions / Risks

- self-check 只做 review-only 判断，不自动改变 inventory、commands 或成熟度评分，避免把 LLM 二次判断升级为事实。
- 真实 guided init 在有 follow-up 时会增加一次 LLM 调用，耗时增加但只发生在扫描有明显不确定性时。
- mock LLM 测试默认不触发 self-check，只有显式传入 `scan_self_check_caller` 的测试覆盖新链路。
- 后续仍需要 claim-level support/conflict/unknown validation，本轮只为它建立可审计的 self-check 落点。
