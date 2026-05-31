# Scan Follow-up 补充状态标注设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/engineering/llm-contracts.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/README.md`、`docs/evolution-log.md`、相关 scan follow-up / self-check / structured scan supplement specs 与 plans。
- 已核对代码：`interactive_init.py`、`interaction_decisions.py`、`human_confirmation.py`、`write_assets.py`、`interaction_decision.py`、`human_confirmation.py` schema，以及 guided init / human confirmation 相关测试。
- 按需未展开：`sensor-and-gate-rules.md` 和 `architecture.md`。本轮不修改 benchmark / sensor gate 或模块边界。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. scan follow-up 被用户补充后的状态标注 | 上轮 Gate / 新发现 | 用户补充 `module` / `command` / `risk` 后，questionnaire 和 human-input 能说明相关追问已被本轮补充部分回应，但仍需 Maintainer 复核 | follow-up questions、LLM 二次自检、结构化 scan supplement 都已存在 | `build_questionnaire()` 只看 scan metadata，不看 `InteractionDecisions.scan_confirmation`，追问仍像完全未处理 | 避免 Maintainer 误以为系统忽略了刚输入的补充；保留 review-only 边界 | 低到中；只扩展 questionnaire reason，不关闭问题、不改正式事实 | unit + guided integration + schema 校验 | 依赖上一轮 structured scan supplement contract | `questionnaire.yaml` / `human-input-needed.md` 出现补充状态标注，`interaction-decisions.yaml` 保持 pending review | 本轮 |
| B. Workflow note review-only routing candidate 安全设计 | 上轮 Gate | Workflow 自由文本说明可以进入 review-only routing 改进候选，而不是直接改正式 policy | workflow note 已进入 interaction decisions / human-input | 尚无安全候选生成链路；workflow policy candidate 需要结构化 patch | 增强 Workflow routing 自改进闭环 | 中高；涉及 candidate schema、workflow policy patch、LLM / benchmark 边界 | unit / integration / benchmark | 需要更完整候选治理设计 | 生成 review-only 候选且 benchmark 校验 | 下一轮候选 |
| C. push 前 full regression / 远端同步 | Gate / git 状态 | 已完成本地工作包可统一 push，远端基线清晰 | 当前 `main` 本地领先 `origin/main` 25 个 commit | 本轮新功能尚未形成 push 工作包；full 可能依赖 acceptance / 凭证 | 降低分叉风险 | 中；可能受外部 DeepSeek / 网络影响 | `scripts/test-full.sh`、push 结果 | 需要完整工作包边界和凭证 / 网络 | full regression 通过后 push | 后续工作包 |

排序结论：

1. 选择 A，因为它直接补齐 `init-north-star.md` 中“用户补充后必须进入后续决策链路，跳过的问题进入不确定性”的闭环，而且复用已存在的 scan supplement 和 follow-up 契约，能在一个小切片内完成。
2. B 暂不选择，因为它涉及 workflow policy candidate 的安全模型，不能从自由文本 note 直接推断正式 routing patch，需要单独设计。
3. C 暂不选择，因为当前仍在继续目标模式增量演进，本轮完成后未必构成适合 push 的完整工作包；push 前仍必须执行 full regression。

## 本轮 Milestone

作为 Harness Maintainer，当扫描阶段出现深度追问且我在同一次 guided `init` 中用 `module=...`、`command=...` 或 `risk=...` 补充相关信息时，我可以在 `.ai/questionnaire.yaml` 和 `.ai/human-input-needed.md` 看到这些追问已被本轮 scan 补充部分回应、但仍保持 `pending_harness_maintainer_review`，从而知道系统吸收了我的输入，同时不会误以为扫描不确定性已经被自动关闭。

## 设计

### 数据流

当前数据流：

1. `scan_repository()` 生成 `ScanMetadata.followup_questions`。
2. guided CLI 收集 scan supplement，并通过 `accepted_interactive_decisions()` 写入 `InteractionDecisions.scan_confirmation`。
3. `write_initial_assets()` 调用 `build_questionnaire(context_inputs, scan_metadata, risk_areas=...)`。
4. `build_questionnaire()` 将 follow-up question 转成 `scan_followup_confirmation`。

本轮改为：

1. `write_initial_assets()` 将当前 `InteractionDecisions` 传给 `build_questionnaire()`。
2. `build_questionnaire()` 对每个 follow-up question 计算是否有相关 scan supplement。
3. 如果有相关补充，只追加 reason 标注：
   - `本轮 scan 补充可能已部分回应该追问`
   - 补充摘要，例如 `module=...`、`command=...`、`risk=...`
   - `review_status=pending_harness_maintainer_review`
4. follow-up question 仍然保留在 questionnaire 中，不自动 resolved，不删除 human-input。

### 相关性规则

只做保守匹配：

- `unknown_stack`、`stack_claim_without_evidence`：匹配 `primary_stack_override`。
- `module_boundary_unclear`、`coverage_gap`：匹配 structured modules；如果影响 workflow，也可匹配 risk areas。
- `test_evidence_missing`：匹配 test command。
- follow-up affects 包含 `sensors`：匹配 command supplement。
- follow-up affects 包含 `guides`：匹配 module supplement。
- follow-up affects 包含 `workflow`：匹配 risk supplement。
- 自然语言 scan note 只作为低精度补充摘要；不单独关闭任何追问。

### 边界

- 不新增 resolved 状态，不从 questionnaire 删除追问。
- 不把用户补充伪装成扫描 evidence。
- 不修改 `ProjectInventory`、`CommandCatalog` 或 workflow routing 的既有写入语义。
- 不执行 Runtime，不创建 `.ai/task-runs`。
- 不修改 LLM self-check prompt 或 acceptance。

## 验收标准

1. `build_questionnaire()` 在传入 scan follow-up 和相关 `InteractionDecisions` 时，生成的 `scan_followup_confirmation.reason` 包含“本轮 scan 补充可能已部分回应该追问”、补充摘要和 `pending_harness_maintainer_review`。
2. 无相关 scan supplement 时，follow-up reason 保持原语义，不出现部分回应标注。
3. guided init 中，当 mock scan 提供 follow-up 且用户输入结构化 `module` / `command` / `risk` 时：
   - `.ai/questionnaire.yaml` 通过 `Questionnaire` schema 校验。
   - 对应 follow-up reason 包含补充状态标注和具体补充 ID / path / command。
   - `.ai/human-input-needed.md` 的扫描待确认摘要保留相同标注。
   - `.ai/interaction-decisions.yaml` 仍保留 structured scan supplement、`review_status=pending_harness_maintainer_review` 和 `fact_effect=user_supplied_correction_review_required`。
4. 相关 targeted tests、guided init tests 和 `scripts/test-fast.sh` 通过。

## Assumptions / Risks

- Assumption：同一轮 guided scan supplement 是 Maintainer 对当前扫描理解和深度追问的主动补充，适合在 questionnaire reason 中标注为“可能部分回应”。
- Risk：启发式匹配可能无法完美判断每个 follow-up 是否真正解决；因此本轮不关闭追问，只保留 pending review。
- Risk：reason 字符串承载状态不是长期最强契约；如果后续需要机器化 resolved / unresolved 状态，应新增 questionnaire schema 字段并设计迁移。

## Sub Agent

按目标模式尝试启动只读 explorer 审查该链路，但当前环境返回 `agent thread limit reached`，本轮由主线程完成调研、TDD、实现和验证。
