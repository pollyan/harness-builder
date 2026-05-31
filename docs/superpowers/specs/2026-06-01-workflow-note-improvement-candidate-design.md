# Workflow 补充改进候选设计

## Current State Gap Analysis

事实源快照：
- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/engineering/llm-contracts.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/README.md`、`docs/todos/archive.md`、`docs/evolution-log.md`、`generate_improvements.py`、`maturity_evidence.py`、`experience_index.py`、`interaction_decision.py`、相关 guided init / improve 测试。
- 按需未展开：`docs/engineering/architecture.md` 和 `sensor-and-gate-rules.md`，本轮不调整模块边界、Sensor 或 hard gate 规则。
- Sub agent：按目标模式尝试启动只读 explorer 调研 Workflow 补充链路，但当前返回 `agent thread limit reached`；本轮由主线程完成调研。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Workflow 补充进入 `improve` 改进候选 | Gate / North Star | 用户在 guided `init` 提供 Workflow 补充后，后续维护入口 `improve` 能生成 review-only `workflow_policy_update` 候选，指向 `.ai/harness-config.yaml`，但不修改正式 routing policy | Workflow 补充已写入 `interaction-decisions.yaml`、project-context、human-input-needed，并有 review-only 结构化边界 | `generate_improvements()` 只消费 maturity evidence / workflow recommendation 数量，不消费 `workflow_confirmation.notes` | 让用户输入从“被记录”进入“可治理的改进候选”，形成 init -> improve 的闭环 | 中低；不能生成 `WorkflowPolicyPatch`，不能从自由文本改正式 routing | unit 覆盖 `_candidates()`；integration 覆盖 guided init 后 existing Harness `improve` | 依赖现有 `ImprovementCandidate` schema 和 interaction decisions schema | `.ai/improvement-candidates.yaml` 有稳定 candidate，`harness-config.yaml` 不含 note 文本 | 本轮 |
| B. 从 Workflow note 生成结构化 `workflow_policy` asset candidate | 上轮 Gate | 生成可进入 `review-candidate applied` 的结构化 routing patch | 已有 workflow policy patch / candidate governance | 自由文本 note 无法安全推断完整 routing rule | 更接近自动策略改进 | 高；涉及 LLM / schema / patch 安全和 benchmark | LLM parser、governance、benchmark、acceptance | 需要更完整候选治理设计 | 结构化 patch 通过 schema 且不越权应用 | 后续候选 |
| C. Follow-up Maintainer resolved 状态 | 上轮 Gate | Maintainer 可把 scan follow-up 从 partial / unaddressed 标记为 resolved | 已有 partial / unaddressed 机器状态 | 缺少人工关闭追问的治理动作 | 降低长期 human-input 噪音 | 中；需要新交互和 schema 生命周期 | schema + maintenance action integration | 需要设计 resolved 语义 | 再次 init 能区分 resolved | 后续候选 |
| D. Push 前 full regression / 远端同步 | Gate | 本地 27 个提交形成可推送工作包并通过 full regression | fast 已多轮通过，本地 ahead 27 | 尚未执行 full / push | 降低分叉成本 | 中；依赖真实 acceptance / DeepSeek / 网络 | `scripts/test-full.sh`、push | 需要外部凭证 / 网络 | full 通过并 push | 工作包边界后处理 |

排序结论：
1. 选择 A，因为它直接服务 `init-north-star.md` 的“用户输入必须进入后续决策链路”，并且只生成 review-only improvement candidate，不触碰正式 routing policy，风险明显低于直接生成结构化 patch。
2. B 暂不选，因为自由文本 Workflow note 到 `WorkflowPolicyPatch` 的转换需要 LLM / schema / benchmark / governance 的完整安全设计。
3. C 有价值，但它服务 scan follow-up 治理，不如 A 更贴近最近几轮 Workflow 补充闭环。
4. D 需要 full regression / push 边界；当前目标模式仍应先推进一个独立 init 价值切片。

本轮 milestone：

作为 Harness Maintainer，当我在首次 guided `init` 中输入 Workflow 补充说明后，再次进入已有 Harness 并选择 `improve`，我可以在 `.ai/improvement-candidates.yaml` 和 `.ai/evolution-plan.md` 中看到一个 review-only 的 `workflow_policy_update` 候选，引用 `interaction-decisions.yaml` / `human-input-needed.md`，并明确它不会直接修改正式 routing policy，从而让 Workflow 经验进入可审查改进流，而不是只停留在自由文本记录里。

## 验收标准

1. `generate_improvements()` 读取现有 `.ai/interaction-decisions.yaml`；当 `workflow_confirmation.notes` 非空且 `review_status=pending_harness_maintainer_review`、`routing_policy_effect=review_only_no_direct_policy_change` 时，生成稳定 id 的 `workflow_policy_update` 候选。
2. 候选指向 `.ai/harness-config.yaml`，`human_confirmation_required=true`，`target_dimension=workflow`，evidence / rationale 明确 review-only、不直接应用正式 routing policy。
3. 候选 `evidence_sources` 至少包含 `.ai/maturity-evidence.yaml` 和 `.ai/interaction-decisions.yaml`；当 maturity inputs 包含 `.ai/human-input-needed.md` 时也引用它。
4. 无 Workflow note、note 未处于 pending review、或 routing policy effect 不是 review-only 时，不生成该候选。
5. guided init 后再次进入已有 Harness 执行 `improve`，正式 Guides / Sensors / Workflow Skills / `harness-config.yaml` 不被覆盖，Workflow note 不进入正式 routing policy。
6. `maturity-evidence.yaml` 的 maturity inputs 暴露 `.ai/interaction-decisions.yaml` 和 `.ai/human-input-needed.md`，让后续 LLM review / asset candidate allowlist 可以消费该候选证据。
7. 本轮不生成 `WorkflowPolicyPatch`，不应用 workflow policy candidate，不执行 Runtime，不创建 `.ai/task-runs`。

## 决策 / 取舍

- 采用 `ImprovementCandidate`，不采用 `AssetCandidateDraft(kind="workflow_policy")`，因为后者要求结构化 `workflow_policy_patch`，不适合从自由文本 note 直接生成。
- candidate 表示“需要审查是否调整 routing policy”，不是“已经知道如何调整 routing policy”。
- `improve` 是已有 Harness 的 review-only 改进入口；首次 `init` 仍只记录 Workflow note 和生成基础 Harness，不额外写 `.ai/improvement-candidates.yaml`。

## Assumptions / Risks

- Assumption：Workflow note 的正式策略化应先进入 `workflow_policy_update` improvement candidate，再由 LLM maturity review / asset candidate generation 或人工治理产生结构化 patch。
- Risk：候选 evidence 中包含用户自由文本，不能让后续 reviewer 误以为这是扫描事实；因此文案必须反复标注 review-only / pending review。
- Risk：如果旧 Harness 缺少 `interaction-decisions.yaml`，`improve` 不应失败；它只是不生成该 Workflow note 候选。
