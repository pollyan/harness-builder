# Guided Scan Back Candidate Summary 设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、`docs/strategy/Harness Builder — 面向遗留代码库治理的 AI Coding Harness 生成器.md`、`docs/todos/README.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`src/harness_builder_agent/tools/interactive_init.py`、`src/harness_builder_agent/tools/interaction_decisions.py` 和 guided init integration tests。
- 按需未展开：`docs/engineering/llm-contracts.md`、`docs/engineering/sensor-and-gate-rules.md`、`docs/engineering/architecture.md`；本轮不修改 LLM、Sensor gate、benchmark 检查、模块边界或 Runtime 契约。
- sub agent：按目标模式尝试启动只读 explorer 交叉审查本轮 gap，当前环境返回 `agent thread limit reached`；主线程继续。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. 返回 scan 后最终确认准确展示候选待复核状态 | 上一轮 Gate / 当前代码审查 | 当用户返回 scan 修改扫描理解后，最终确认摘要能说明候选已刷新、旧决策已清空、当前有多少候选待重新审查且默认保持候选 | `back -> scan` 已刷新 `candidate_report`、清空 `candidate_decisions`，并输出一次“如需重新审查候选，请 back -> candidates”提示；最终写入会用 `candidate_ids` 生成 kept 决策 | `_confirm_summary()` 只统计 `candidate_decisions`；scan 返回后该列表为空，最终确认显示“保持候选 0 条”，与最终产物中 3 条 kept 候选不一致，容易让用户误以为没有候选需要审查 | 修正写入前审查摘要的可信度，不增加交互负担，保护“最终确认前理解即将写入什么”的 init North Star 主体验 | 低；只改 CLI summary 文案和函数参数，不改 schema、writer、candidate 生成或 Runtime | integration 可覆盖 `back -> scan` 后最终确认摘要、`interaction-decisions.yaml` kept 决策和 candidate report 状态 | 无外部凭证 | CLI transcript 包含 `待重新审查 3 条` 和默认保持候选边界；产物仍为 kept / candidate | 本轮 |
| B. 返回 scan 后自动重新进入候选审查 | 上一轮 Gate | scan 修改后自动逐项复核刷新后的候选，避免用户忘记手动返回 candidates | 当前已清空旧决策并提示可手动 `back -> candidates` | 仍可能忘记重审；但自动重审会增加流程长度并改变已有低负担交互 | 更强审查闭环 | 中；影响输入序列、候选审查 UX 和多条测试 | integration transcript | 需要产品取舍 | 自动重审后可记录新决策 | 下一轮候选 |
| C. full regression / push 工作包 | Git 状态 / 用户 push 规则 | 本地独立价值同步 GitHub | 当前 `main...origin/main [ahead 76]`；上一轮 fast passed | `scripts/test-full.sh` acceptance 因缺 `DEEPSEEK_API_KEY` 和 `.benchmarks/RuoYi-Vue` / `.benchmarks/eShopOnWeb` 失败，不能合规 push | 远端同步本地工作 | 外部环境阻塞 | full regression + push | DeepSeek key 和真实仓库 | full 通过后 push | 本轮后评估 |

排序结论：

1. 选择 A。它直接修正最终确认阶段的用户可见事实错误，属于 init North Star 的“写入前能理解即将得到什么”和“候选 / 待确认边界清晰”要求；它也消化了上一轮 Gate 的 candidate 审查风险，但不引入强制自动重审的交互成本。
2. B 暂不选。自动重审有价值，但会改变用户流程，适合在 A 先把状态讲清楚后继续观察是否仍需要。
3. C 不作为功能 milestone。完成本轮后按仓库规则评估 full regression；外部前置仍缺时不 push。

本轮 milestone：

作为 Harness Maintainer，当我在首次 guided `init` 最终确认阶段返回 scan 修改扫描理解后，我可以在下一次最终确认摘要中看到候选已刷新、旧决策已清空、当前仍有多少候选待重新审查且默认保持候选，从而不会把“候选决策 0 条”误解为“没有候选需要审查”。

## 设计

- `_confirm_summary()` 增加 `candidate_count` 输入，用刷新后的 `candidate_ids` 数量表达当前候选总数。
- 候选摘要规则：
  - 有逐项决策时，保留现有确认 / 拒绝 / 备注 / 保持候选统计。
  - 没有逐项决策但 `candidate_count > 0` 时，显示待重新审查数量，并说明最终确认会默认保持候选，用户可 `back` / `返回` 到 `candidates` / `候选` 复核。
  - 没有候选时，明确显示暂无候选决策。
- 保持 `accepted_interactive_decisions()` 的默认 kept 行为不变，避免改变 schema 和写入契约。

## 非目标

- 不自动重新进入候选审查。
- 不改变 candidate report schema、candidate 生成逻辑或 review-only 状态。
- 不修改已有 Harness 的 `review-initial-candidate` / `review-candidate` 维护入口。
- 不执行 Runtime、不创建 `.ai/task-runs`。

## 验收标准

- RED：guided init integration 先证明 `back -> scan` 后最终确认摘要仍显示 `保持候选 0 条` 或缺少待复核候选说明。
- 实现后：
  - `back -> scan` 后最终确认摘要展示候选已刷新、待重新审查 3 条和默认保持候选边界。
  - 最终 `interaction-decisions.yaml` 仍为 3 条 kept 决策，且旧候选备注不进入产物。
  - 初次逐项审查候选时现有确认 / 拒绝 / 备注 / 保持候选统计不回归。
  - guided init integration、`compileall`、`git diff --check` 和 `scripts/test-fast.sh` 通过。

## Assumptions / Risks

- Assumption：清空候选决策后，默认 kept 是当前写入契约；本轮只把这个事实讲清楚，不改变默认策略。
- Risk：提示文案过长会增加最终确认噪声；因此只在无逐项决策但存在候选时展示待复核提示。
