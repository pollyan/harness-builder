# Workflow Note 资产候选闭环设计

## Current State Gap Analysis

事实源快照：
- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/engineering/architecture.md`、`docs/engineering/init-workflow.md`、`docs/engineering/llm-contracts.md`、`docs/engineering/testing-strategy.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/README.md`、`generate_improvements.py`、`review_maturity.py`、`generate_asset_candidates.py`、`llm_maturity_reviewer.py`、`llm_asset_candidate_generator.py`、`llm_maturity_review_v2.md`、`llm_asset_candidate_v2.md`、相关 schema 与 unit / integration 测试。
- 按需未展开：`sensor-and-gate-rules.md`，本轮不新增 benchmark 检查、不修改 Sensor / hard gate 规则。
- Sub agent：按目标模式尝试启动只读 explorer 调研 Workflow note 到 asset candidate 链路，但当前返回 `agent thread limit reached`；本轮由主线程完成调研。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Workflow note -> review-only workflow_policy asset candidate | 上轮 Gate / 新发现 | guided `init` 收到的 Workflow 补充可以经过 `improve -> review-maturity -> generate-asset-candidates` 形成可审核的 `workflow_policy` 候选，并保持结构化 patch / review-only / 不自动应用边界 | `improve` 已生成 `interaction-workflow-note-review`；workflow recommendation candidate 已有 prompt 指引和 workflow_policy patch 契约 | maturity review / asset candidate prompt 尚未专门指引 `interaction-workflow-note-review`，真实 LLM 可能忽略或只产出泛化 Guide/Sensor；缺少端到端测试证明 Workflow note 能进入 asset candidate | 完成“用户 Workflow 补充 -> 自演进候选”的闭环，让渐进式交互输入真正进入后续 Harness 演进 | 中；涉及 LLM prompt 和 workflow policy patch，但不修改正式资产、不执行 Runtime | prompt unit、LLM parser unit、guided integration / self-improve integration | 依赖现有 `WorkflowPolicyPatch` schema、candidate governance 和 review-only 边界 | prompt 包含明确指引；integration 证明 Workflow note 生成 review-only workflow_policy candidate 且正式资产不变 | 本轮 |
| B. Push 前 full regression / 远端同步 | 上轮 Gate | 本地 29 个提交形成可推送工作包并通过 full regression | fast 多轮通过，本地 ahead 29 | 尚未运行 full / push | 降低长期分叉成本 | 中；依赖 DeepSeek、真实仓库、网络 | `scripts/test-full.sh` + push | 外部凭证 / 网络 | full 通过并 push | 工作包边界后处理 |
| C. Human input review guided 菜单化 | 上轮 Gate | Maintainer 可在 existing Harness 入口直接选择处理 human-input review，而不是记 standalone 命令 | 已有 standalone `review-human-input` 和状态计数 | 维护入口菜单没有专门动作 | 降低 CLI 记忆成本 | 低到中；涉及 guided menu 和输入流 | guided integration | 依赖上一轮命令稳定 | 菜单动作写 governance，不覆盖正式资产 | 后续候选 |

排序结论：
1. 选择 A，因为它直接服务 `init-north-star.md` 的“用户补充进入后续推荐和自演进”的主线，且当前代码已经有 improvement candidate 和 workflow policy patch 基础，适合做一个完整但可审查的纵向切片。
2. B 暂不选，因为它是同步工程动作，适合完整工作包 / push 边界处理；当前仍有可实施的 init 用户价值缺口。
3. C 暂不选，因为上一轮 standalone 命令已经形成独立价值；菜单化是易用性增强，但不如 A 对自演进闭环关键。

本轮 milestone：

作为 Harness Maintainer，当我在首次 guided `init` 中留下 Workflow 补充说明，并在已有 Harness 入口运行 self-improve 或专家链路时，我可以得到一个以该 Workflow note 为 evidence 的 review-only `workflow_policy` asset candidate，且它必须携带结构化 `WorkflowPolicyPatch`、保持 `pending_harness_maintainer_review`、不修改正式 routing policy，从而把交互式 Workflow 经验推进到可审核的 Harness 演进候选。

## 验收标准

1. `llm_maturity_review_v2.md` 明确指导 `interaction-workflow-note-review`：读取 `.ai/interaction-decisions.yaml` / `.ai/human-input-needed.md` 中 review-only Workflow notes，对照 `maturity_evidence.harness_assets.workflow_routing_rules`，仅给 review-only judgment，不声称已应用。
2. `llm_asset_candidate_v2.md` 明确指导 `interaction-workflow-note-review`：当 maturity review 为 support / revise 时，优先生成目标为 `.ai/harness-config.yaml` 的 `workflow_policy` 候选，必须带 `workflow_policy_patch`，并保持 review-only。
3. LLM prompt unit 测试覆盖 Workflow note candidate 的 prompt 指引、evidence source、review-only 边界和 patch 结构。
4. parser / schema 仍拒绝未知 source candidate、未知 evidence source、非法 workflow policy target 和缺失 patch；本轮不放宽契约。
5. integration 测试覆盖 guided `init` 输入 Workflow note 后，existing Harness `self-improve` 生成 `interaction-workflow-note-review` 对应的 workflow_policy asset candidate；正式 Guides、Sensors、Workflow Skills、`harness-config.yaml`、inventory 和 Runtime 产物不被修改。
6. README 和 `docs/engineering/init-workflow.md` 同步说明 Workflow note 进入 review-only self-improve / asset candidate 链路，正式 routing policy 仍需候选治理显式应用。

## 决策 / 取舍

- 本轮不新增确定性 free-text-to-patch 逻辑。Workflow note 到 patch 的语义判断仍由 LLM asset candidate generator 完成，Python 负责 schema、allowlist、path、patch 和 review-only 校验。
- `workflow_policy` candidate 仍必须携带结构化 `WorkflowPolicyPatch`；自由文本 `draft_content` 只能是人类说明。
- 本轮不自动 apply `.ai/harness-config.yaml`，也不把 guided `review-candidate` 扩展到 workflow_policy apply；正式 routing policy 仍走专家 `review-candidate --decision applied`。

## Assumptions / Risks

- Assumption：Workflow note 是用户提供的 review-only routing signal，适合作为 LLM 生成候选的 evidence，但不是已应用配置。
- Risk：LLM 可能从自由文本 note 生成过度宽泛的 routing rule；缓解方式是保持候选 review-only、要求结构化 patch、review-candidate 应用时校验 baseline routing invariants，并由 benchmark 校验。
- Risk：prompt-only 改动真实效果需要 acceptance 才能完全证明；本轮用 prompt unit 和 mock LLM integration 证明契约与链路，真实 DeepSeek 留到 push/full 或 targeted acceptance 边界。
