# Human Input Follow-up 人工复核设计

## Current State Gap Analysis

事实源快照：
- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/engineering/architecture.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/engineering/llm-contracts.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/README.md`、`docs/evolution-log.md`、`human_confirmation.py`、`interactive_init.py`、`cli.py`、`candidate_governance.py` 和相关 questionnaire / guided init 测试。
- 按需未展开：`sensor-and-gate-rules.md`，本轮不新增 benchmark check、不修改 Sensor / hard gate 规则。
- Sub agent：按目标模式尝试启动只读 explorer 调研 scan follow-up resolved 状态，但当前返回 `agent thread limit reached`；本轮由主线程完成调研。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. scan follow-up 人工复核 resolved 状态 | 上轮 Gate / 新发现 | Maintainer 复核 scan follow-up 后，可以显式标记为 resolved / reopened，`questionnaire.yaml`、`human-input-needed.md` 和已有 Harness 入口都能反映状态 | follow-up 已有 `unaddressed` / `partially_addressed_by_current_scan_supplement`，维护入口显示 partial / unaddressed 计数 | 没有显式人工复核动作；partial 永远停留为 pending，维护入口无法区分“已复核解决”和“仍待确认” | 完成 human-input 回访闭环，降低长期待确认噪音，同时保留审计 | 中；新增 CLI、schema、review log，但不改正式资产、不用 LLM | schema/unit/CLI integration/guided init maintenance preview | 依赖现有 Questionnaire schema 和 human-input 产物 | 命令更新 status、写 review log、刷新 Markdown、维护入口显示 resolved count | 本轮 |
| B. Workflow note -> 结构化 workflow policy asset candidate | 上轮 Gate | Workflow note 可在 LLM review 后生成带 `WorkflowPolicyPatch` 的 review-only asset candidate | 已有 improvement candidate，asset candidate prompt 支持 workflow_policy patch | prompt 尚未针对 `interaction-workflow-note-review` 注入上下文；自由文本到 patch 需要安全边界 | 推进 Workflow Toolkit 自演进 | 高；涉及 LLM prompt、patch、benchmark、governance | LLM parser / prompt / integration / benchmark | 需要更完整安全设计 | schema-valid patch 且不越权应用 | 后续候选 |
| C. push 前 full regression / 远端同步 | Gate | 本地 28 个提交形成可推送工作包并通过 full regression | fast 多轮通过，本地 ahead 28 | 尚未运行 full / push | 降低长期分叉成本 | 中；依赖 DeepSeek、真实仓库、网络 | `scripts/test-full.sh` + push | 外部凭证 / 网络 | full 通过并 push | 工作包边界后处理 |

排序结论：
1. 选择 A，因为它直接延续最近几轮 scan follow-up partial / unaddressed 契约，把“系统吸收了补充”推进到“Maintainer 可以审计并关闭追问”，符合 `init-north-star.md` 的 human-input 闭环和已有 Harness 维护入口目标。
2. B 暂不选，因为它会进入 LLM prompt 和结构化 `WorkflowPolicyPatch`，比本轮更高风险。
3. C 有工程价值，但当前仍有可实施的 init 用户价值切片；push 前 full regression 适合作为完整工作包同步时处理。

本轮 milestone：

作为 Harness Maintainer，当我在 `.ai/questionnaire.yaml` 或已有 Harness 维护入口看到 scan follow-up 已被当前 scan supplement 部分回应后，我可以运行显式人工复核命令把该 interaction 标记为 resolved，并留下 `.ai/review/human-input-governance.*` 审计记录；再次运行 guided `init` 时，我可以看到 resolved / partial / unaddressed 计数，从而知道哪些扫描追问已经人工关闭、哪些仍待补充。

## 验收标准

1. `QuestionnaireQuestion.response_status` 支持 `reviewed_resolved_by_harness_maintainer`，旧 payload 默认仍为 `unaddressed`。
2. 新增 `review-human-input` CLI 命令，要求 `--repo`、`--interaction-id`、`--decision resolved|reopened`、`--rationale` 和可选 `--reviewer`。
3. 命令只能治理 `.ai/questionnaire.yaml` 中存在的 `scan_followup_confirmation`；未知 id、缺少 rationale、缺少 questionnaire、非 scan follow-up 必须显式失败。
4. `resolved` 将对应问题写成 `reviewed_resolved_by_harness_maintainer`；`reopened` 根据是否保留 `response_sources` 回到 partial 或 unaddressed。
5. 命令写入 `.ai/review/human-input-governance.yaml` 和 `.ai/review/human-input-governance.md`，并刷新 `.ai/human-input-needed.md`；不修改正式 Guides、Sensors、Workflow Skills、`harness-config.yaml`、inventory、command catalog 或 Runtime 产物。
6. 已有 Harness 维护入口读取 questionnaire 时展示 resolved / partially addressed / unaddressed scan follow-up 计数。
7. `human-input-needed.md#处理方式` 对 resolved follow-up 显示已复核边界，对 partial follow-up 建议复核或运行 `review-human-input` 标记。
8. README 和 `docs/engineering/init-workflow.md` 说明该命令是 human-input 治理动作，不代表扫描事实被自动验证，不会修改正式 Harness 资产。

## 决策 / 取舍

- 新增独立 `human-input-governance` schema，而不是复用 `candidate-governance`，因为被治理对象是 `questionnaire.yaml` 中的 human input interaction，不是 review-only asset candidate。
- `resolved` 只表示 Maintainer 已复核该追问，不表示 Builder 重新扫描或验证了事实；正式资产变更仍需 reinit、review-candidate 或人工编辑后 benchmark。
- 本轮不新增 guided init 菜单项，先提供专家命令和 human-input 处理入口；维护入口会显示 resolved 计数。

## Assumptions / Risks

- Assumption：Maintainer 可以基于当前补充、上下文和团队知识人工决定某个 scan follow-up 已解决。
- Risk：resolved 状态可能被误读为扫描证据已经自动补齐；因此 Markdown 和工程文档必须明确它是人工复核状态。
- Risk：reopened 从 resolved 回到 partial/unaddressed 需要保守处理；如果仍有 `response_sources`，恢复 partial，否则恢复 unaddressed。
