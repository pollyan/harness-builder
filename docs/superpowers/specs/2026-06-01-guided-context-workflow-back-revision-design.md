# Guided Init 团队规则与 Workflow 返回修改提示设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/strategy/init-north-star.md`、全景 North Star、`docs/todos/README.md`、近期 `docs/evolution-log.md`、guided init final confirmation / team rules / workflow 代码和测试。
- 按需未展开：`docs/engineering/llm-contracts.md`、`sensor-and-gate-rules.md` 和 `architecture.md`；本轮不修改 LLM、benchmark、Sensor 或模块边界。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. rules / workflow 返回修改替换与清空提示 | 新发现 / 上轮同旅程延伸 | final confirmation 返回修改任一用户补充时，CLI 都说明替换或清空语义，并在清空时给出可见确认 | scan 已有替换 / 清空 / old-current 预览；rules 和 workflow 可以替换最终资产 | rules / workflow 返回修改前不说明新输入替换旧输入；直接回车清空没有确认，用户可能误以为旧规则或旧 note 仍会写入 | 补齐最终确认纠错路径的一致 UX，保护写入前审查信任 | 低；只改 guided CLI 文案和 integration 测试 | guided integration transcript + 资产不含旧输入 | 无外部凭证 | CLI 出现返回修改提示 / 清空确认，最终资产只含新输入或清空 | 本轮 |
| B. Workflow note review-only routing candidate | 上轮 Gate | Workflow note 可转成 review-only workflow policy candidate | Workflow note 已有结构化 review-only impact contract | `workflow_policy` candidate 需要结构化 `WorkflowPolicyPatch`，自由文本 note 不能安全推断 patch | 更强 Workflow Toolkit 闭环 | 中高；涉及 candidate schema、governance、policy patch | candidate/governance integration | 需要单独设计安全边界 | 生成 review-only candidate 且不改正式 routing | 后续候选 |
| C. push 前 full regression / 远端同步 | 工程节奏 | 完整功能批次 full regression 后 push | 本地领先远端 23 个 commit | 尚未运行 full / push | 降低分叉风险 | 中；依赖真实 DeepSeek / `.benchmarks` / 网络 | `scripts/test-full.sh` | 可能缺凭证或真实仓库 | full 通过后 push | 工作包边界处理 |

排序结论：

1. 选择 A。它与刚完成的 scan 返回修改差异预览属于同一 final confirmation 纠错用户旅程，能在一个小型 commit 内补齐 rules / workflow 的替换和清空可见语义。
2. B 暂不选。自由文本 Workflow note 到结构化 routing patch 的转换风险仍然高，不应为了推进候选而引入隐式 policy 推断。
3. C 作为工程节奏候选保留；push 前必须 full regression，本轮继续做一个独立本地切片。

本轮 milestone：

作为 Harness Maintainer，当我在最终确认阶段返回修改团队规则或 Workflow 补充时，我可以在重新输入前看到新输入会替换上一版内容、直接回车会清空上一版内容，并在清空后看到系统确认最终资产不会保留旧内容，从而不用担心旧团队规则或旧 Workflow note 悄悄进入正式 `.ai` 资产。

## 设计

### CLI 行为

新增两个轻量提示：

- `团队规则返回修改`
  - 上一版团队规则非空时输出。
  - 说明将重新填写团队规则，新输入替换上一版，直接回车清空上一版。
  - 展示上一版摘要。
- `团队规则已清空`
  - 上一版非空、返回 rules 后直接回车时输出。
  - 说明后续 preview 和正式资产将不再保留上一版团队规则。
- `Workflow 补充返回修改`
  - 上一版 Workflow note 非空时输出。
  - 说明将重新填写 Workflow 补充，新输入替换上一版，直接回车清空上一版。
  - 展示上一版摘要。
- `Workflow 补充已清空`
  - 上一版非空、返回 workflow 后直接回车时输出。
  - 说明后续 preview 和正式资产将不再保留上一版 Workflow 补充。

### helper

- 新增 `_show_team_rules_back_revision_notice(previous_inline_contexts)`。
- 新增 `_show_team_rules_cleared_summary()`。
- 新增 `_show_workflow_back_revision_notice(previous_workflow_confirmation)`。
- 新增 `_show_workflow_note_cleared_summary()`。
- 摘要使用最多前两条，避免长文本刷屏。

## 决策与取舍

- 不新增 old/current diff，因为 rules / workflow 当前一次只收集一段自由文本；替换 / 清空提示已经足够明确。
- 不修改 `ContextConfirmation` 或 `WorkflowConfirmation` schema；上一轮已经补齐机器契约。
- 不改变正式 `.ai` 资产生成语义，只把当前已存在的替换语义显式化。
- 不修改 candidate governance 或 workflow routing policy。

## Assumptions / Risks

- Assumption：返回 rules / workflow 后重新输入表示替换上一版，而不是累计追加；这与当前代码和 scan 返回修改语义一致。
- Risk：如果未来支持多条团队规则逐项编辑，需要升级为 add/remove/edit 交互；本轮不提前引入复杂状态机。

## 验收标准

1. `back -> rules` 且上一版团队规则非空时，CLI 输出 `团队规则返回修改`、替换 / 清空说明和上一版摘要。
2. `back -> rules` 后输入新规则时，最终 `interaction-decisions.yaml`、project-context 只包含新规则，不包含旧规则。
3. `back -> rules` 后直接回车时，CLI 输出 `团队规则已清空`，最终 `interaction-decisions.yaml` 没有 inline context，project-context / human-input-needed 不包含旧规则。
4. `back -> workflow` 且上一版 note 非空时，CLI 输出 `Workflow 补充返回修改`、替换 / 清空说明和上一版摘要。
5. `back -> workflow` 后直接回车时，CLI 输出 `Workflow 补充已清空`，最终 `interaction-decisions.yaml` 没有 workflow notes，project-context / human-input-needed 不包含旧 note，正式 routing 仍不包含旧 note。
6. 更新 `docs/engineering/init-workflow.md` 和 `docs/evolution-log.md`，记录稳定 CLI 语义。
