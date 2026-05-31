# Workflow 补充结构化影响契约设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/README.md`、`docs/evolution-log.md`、上一轮 Workflow 补充即时影响 / 返回修改 spec、`interaction_decision.py`、`interaction_decisions.py`、`interactive_init.py`、相关 writer 和 guided init / schema tests。
- 按需未展开：`llm-contracts.md`、`sensor-and-gate-rules.md`、`architecture.md`，因为本轮不修改 LLM prompt、benchmark gate、Sensor 内容或模块边界。
- 当前 todo 状态：`docs/todos/README.md` 显示没有 open todo；本轮从 init North Star 和上一轮 Gate 候选中重新选择。
- Sub agent：按目标模式尝试启动只读 explorer 调研 Workflow 补充链路，但当前返回 `agent thread limit reached`；本轮由主线程完成调研。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Workflow 补充结构化 impact 契约 | 上轮 Gate / 新发现 | Workflow 补充不仅是自由文本 note，还在 `interaction-decisions.yaml` 中记录影响范围、review-only 状态和 routing policy 边界 | CLI 已即时复述 Workflow 补充影响，preview 也说明不直接修改正式 routing policy；资产持久化 note | 这些影响只存在于文案，后续 self-improve / audit 只能解析自由文本，难以稳定消费 | 把用户补充的决策边界变成机器可读契约，保护 Workflow routing 不被自由文本静默修改，也为后续智能改进提供稳定输入 | 中低：新增 Pydantic 默认字段和 guided init 写入，不改正式 routing policy / writer 生成策略 | unit schema tests + integration 断言 `interaction-decisions.yaml` 字段 | 无外部依赖 | 本轮 |
| B. Scan correction diff preview | 上轮 Gate | 返回 scan 时展示旧补充与新补充差异 | 已有替换 / 清空提示和资产语义 | 没有逐项 diff | 更强 CLI 可解释性 | 中：CLI 复杂度增加 | CLI transcript tests | 无 | 下一轮候选 |
| C. Workflow note 生成 review-only routing candidate | North Star / Workflow Toolkit | 高价值 workflow 补充可转成候选 routing policy patch，等待治理 | 当前 note 只进入说明和人工确认 | 用户的工作流策略经验不能进入候选治理 | 更深 workflow 定制 | 高：涉及候选 schema、LLM/确定性判断、benchmark 和 review-candidate 边界 | schema + integration + benchmark tests | 需要先有结构化 impact 契约 | 后续较大 milestone |
| D. Push 前 full regression / 远端同步 | 工程治理 | 完整工作包完成后 full regression 并 push | 本地领先远端 20 commits | full 依赖 DeepSeek key 和 `.benchmarks`，当前未重新满足 push 条件 | 降低本地堆积风险 | 中：外部凭证 / 真实仓库 | `scripts/test-full.sh` + push 状态 | 外部前置条件 | 后续工作包 |

排序结论：

1. 选择 A，因为它把已经稳定的用户可见 Workflow 补充边界升级为机器契约，直接服务 `init-north-star.md` 中“关键用户输入必须留下可消费结果”的要求，并且风险可控。
2. B 是纯 CLI 可解释增强，价值明确但不如 A 对后续 self-improve 和审计链路的基础性强。
3. C 更接近目标态，但会触碰正式 routing policy 候选治理边界，应建立 A 的 review-only contract 后再设计。
4. D 暂不作为本轮功能切片；push 前仍必须 full regression。

本轮 milestone：

作为后续 Self-Improve / 审计链路维护者，当 Harness Maintainer 在 guided `init` 中输入 Workflow 补充说明时，我可以在 `interaction-decisions.yaml` 中读取机器可验证的影响范围、review-only 状态和“不直接修改正式 workflow routing policy”的边界，从而让后续智能改进和人工审查稳定消费这条输入，而不是解析自由文本或误以为它已经改变正式路由策略。

## 验收标准

1. `WorkflowConfirmation` Pydantic schema 增加默认兼容字段：`impact_scopes`、`review_status`、`routing_policy_effect`。
2. 有 Workflow note 的 guided `init` 会在 `interaction-decisions.yaml` 写出：
   - `impact_scopes` 包含 `interaction_decisions`、`project_context`、`human_input_needed`、`review_only_workflow_note`。
   - `review_status=pending_harness_maintainer_review`。
   - `routing_policy_effect=review_only_no_direct_policy_change`。
3. 没有 Workflow note 的默认 / 非交互决策仍 schema-valid，并保持 `review_status=not_required`、`routing_policy_effect=not_applicable`。
4. `interaction_decisions_markdown()` 展示 workflow impact / review status / routing policy effect，供 trace / decision-log 审计。
5. 不修改正式 `harness-config.yaml` routing policy，不生成 `.ai/task-runs`，不执行 Runtime。
6. 测试先失败再实现；运行目标 unit / integration tests、相关 guided init tests 和 `scripts/test-fast.sh`。

## 决策与取舍

- 字段放入现有 `WorkflowConfirmation`，不新增独立文件或 questionnaire 类型，保持影响范围集中在交互决策契约。
- 自由文本 Workflow note 仍然是 review-only 输入，不直接生成 routing policy candidate；后续候选化需要独立 schema 和治理流程。
- 使用默认字段保持旧决策文件和非交互路径兼容。
- CLI 文案复用现有说明，不在本轮继续增加 transcript 长度。

## Assumptions / Risks

- Pydantic 新默认字段会让新生成的 `interaction-decisions.yaml` 更详细；旧文件读取仍可通过默认值兼容。
- 后续如果 workflow note 需要影响候选治理，应根据这些结构化字段筛选 review-only note，再生成候选，不应从自由文本直接修改正式 routing policy。
