# Guided Human Input Review Action 设计

## Current State Gap Analysis

事实源快照：
- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景 North Star、`docs/todos/README.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/evolution-log.md`、现有 `interactive_init.py` / `cli.py` / integration tests。
- 按需未展开：LLM prompt 与 benchmark 专题文档。本轮不修改 LLM、benchmark、Sensor 或 Runtime 契约。

候选 gap：
| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. existing Harness 菜单化 `review-human-input` | 上轮 Gate / 新发现 | Maintainer 再次运行 guided `init` 时，可在维护入口直接处理 scan follow-up resolved / reopened | standalone `review-human-input` 已有 schema、CLI、governance log、Markdown 刷新；维护入口已展示 resolved / partial / unaddressed 计数 | 菜单没有该动作，用户仍需记住专家命令和 interaction id 参数 | 把 human-input 待确认从“看见状态”推进到“入口内可治理”，降低接管成本，补齐已有 Harness 维护旅程 | 低到中；只接入 existing Harness 动作，不改扫描、LLM、正式资产或 Runtime | unit 覆盖 action normalization；integration 覆盖 guided action、trace、产物和正式资产不变 | 依赖 `review_human_input()` 稳定行为和现有 questionnaire schema | guided `init` 选择 human-input review 后写 governance、更新 questionnaire / human-input Markdown、trace artifact，无 `.ai/task-runs`，正式资产快照不变 | 本轮 |
| B. push 前 full regression / 远端同步 | 上轮 Gate / 本轮验证 | 本地 30 个 ahead 提交通过 full regression 后同步远端 | `git fetch` 后确认远端没有新提交；fast 通过 402 tests | full regression acceptance 因缺 `DEEPSEEK_API_KEY` 与 `.benchmarks` 失败，按规则不能 push | 降低长期分叉风险 | 外部依赖；当前环境无法补齐凭证和真实仓库 | `scripts/test-full.sh`、`git status`、push 结果 | DeepSeek key 与真实 benchmark 仓库 | full 通过后 push；当前只能保留为下一轮/外部前置 | 下一轮候选，需外部前置 |
| C. 真实 DeepSeek targeted acceptance 验证 Workflow note asset candidate | 上轮 Gate | 真实 LLM 能按 prompt 把 Workflow note 转成 review-only workflow policy candidate | mock integration 已覆盖 self-improve 生成 workflow policy candidate | 缺真实 DeepSeek acceptance 证据 | 提升 LLM prompt 可信度 | 外部凭证与真实仓库依赖 | targeted acceptance | `DEEPSEEK_API_KEY` / `.benchmarks` | targeted acceptance 通过 | 外部前置候选 |

排序结论：
1. 选择 A，因为它直接服务 `init-north-star.md` 的“再次进入已有 Harness”维护入口，把已展示的 human-input 信号连接到可执行治理动作；范围清晰、可用本地 mock integration 验收，不需要外部凭证，也不改变 Runtime 边界。
2. B 暂不选为实现 milestone，因为本轮已再次确认 full regression 的阻塞是缺少外部凭证和真实 benchmark 仓库；在补齐前继续尝试 push 不会产生新价值。
3. C 暂不选，因为它同样依赖真实 DeepSeek / benchmark 前置条件，适合作为有凭证后的 acceptance 工作。

本轮 milestone：
作为 Harness Maintainer，当我再次运行 guided `init` 并看到 human-input-needed 中存在 scan follow-up 待复核项时，我可以在已有 Harness 维护菜单中选择 `review-human-input`，输入 interaction id、resolved/reopened 决策和理由后，让系统写入可审计治理日志并刷新 human-input 状态，从而不离开 init 维护入口也能关闭或重新打开扫描追问。

## 验收标准

1. 菜单与别名：existing Harness 菜单新增稳定 `review-human-input` 编号，`_normalize_existing_harness_action()` 支持数字、英文和中文别名。
2. Guided 行为：选择该动作后提示 interaction id、decision、rationale、reviewer，调用既有 `review_human_input()`，输出治理摘要。
3. 产物契约：只写 `.ai/questionnaire.yaml`、`.ai/human-input-needed.md`、`.ai/review/human-input-governance.yaml`、`.ai/review/human-input-governance.md`，并记录 trace artifacts。
4. 边界：不重新扫描、不覆盖正式 Guides / Sensors / Workflow Skills / `harness-config.yaml` / inventory / command catalog，不执行 Runtime，不创建 `.ai/task-runs`。
5. 错误：未知 interaction id、非法 decision 或空 rationale 沿用 `review_human_input()` 显式失败；guided action 在 trace summary 中记录失败原因。
6. 测试：先写失败 unit / integration 测试，再实现；完成后运行目标测试、相关 guided init integration、`git diff --check` 和 `scripts/test-fast.sh`。
7. 文档：同步 README、`docs/engineering/init-workflow.md`、本 plan 和 `docs/evolution-log.md`；`docs/todos/` 仍无 open todo。

## 决策与取舍

- 复用 standalone `review_human_input()`，不新增第二套治理逻辑。
- `resolved` 仍只表示 Maintainer 人工复核完成，不表示 Builder 自动重扫或验证事实。
- 该 guided action 不自动选择第一个待处理 item；用户仍需输入稳定 interaction id，避免误关错误追问。
- 不把 human-input review 合并进 `review-candidate`，两者治理对象不同，分别保留审计日志。

## Assumptions / Risks

- Assumption：Maintainer 可以从维护入口状态行或 `.ai/human-input-needed.md#处理方式` 读取 interaction id。
- Risk：菜单动作过多可能增加选择成本；本轮用中文说明和别名降低记忆成本，后续可考虑 triage action 直接推荐 `review-human-input`。
- Risk：resolved 被误解为扫描事实已验证；README 和工程规则继续强调这是人工复核边界。
