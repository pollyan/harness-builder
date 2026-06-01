# Guided Scan Back Candidate Review Reset 设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、`docs/strategy/Harness Builder — 面向遗留代码库治理的 AI Coding Harness 生成器.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/todos/README.md`、`docs/evolution-log.md`、`src/harness_builder_agent/tools/interactive_init.py`、`src/harness_builder_agent/tools/interaction_decisions.py`、`src/harness_builder_agent/tools/llm_enhancement_candidates.py`、`src/harness_builder_agent/tools/guided_candidate_review.py`、`src/harness_builder_agent/tools/write_assets.py` 和相关 guided init integration tests。
- 按需未展开：`docs/engineering/llm-contracts.md`、`docs/engineering/sensor-and-gate-rules.md`、`docs/engineering/architecture.md`；本轮不修改 LLM prompt/schema、benchmark 检查、Sensor gate 或模块边界。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. 返回 scan 修改后清空旧候选审查决策 | 上轮 Gate / 当前代码审查 / init North Star | 用户在最终确认输入 `back -> scan` 后，后续 Harness 写入只使用当前生效扫描补充和当前候选状态；旧 candidate accept/reject/edit 不会静默套用到修改后的 scan 结果 | `back -> scan` 已重算 `inventory`、`commands`、`weapon_selection`、`candidate_report`，并能替换或清空旧 scan supplement | `candidate_decisions` 没有同步清空或重新审查；如果用户在旧 scan 状态下接受 / 拒绝候选，再返回 scan 修改后直接 confirm，最终 `interaction-decisions.yaml` 与 `weapon-library-candidates.yaml` 仍会保留旧决策 | 保护渐进式交互可信度，避免“返回修改”只修正部分状态，导致 review-only 候选治理被旧上下文污染 | 低；只改 guided init 状态机和 transcript，不改 schema / writer / LLM | guided init integration：先 RED 证明旧 candidate decisions 泄漏，修复后断言旧 accept/reject/edit 不进入最终产物，并输出清空提醒 | 无外部凭证 | 输出候选审查重置提示；最终 candidate decisions 全为当前候选默认 kept；candidate report 不出现旧 confirmed/rejected/decision_notes | 本轮 |
| B. 返回 scan 后自动重新进入候选审查 | 同一缺口的更激进方案 | scan 修改后系统自动让 Maintainer 重新逐项审查当前候选，保证用户显式复核 | 当前用户可以手动 `back -> candidates` 重新审查 | 自动重审会增加交互轮次，并可能打断用户只想快速修正 scan 的路径 | 更强复核，但交互成本更高 | guided init transcript 可测 | 需要 UX 决策 | 自动二次审查 transcript 和产物决策 | 暂不选 |
| C. full regression / push 工作包 | Git 状态 / 用户 push 规则 | 本地独立价值同步 GitHub | 当前 `main...origin/main [ahead 73]`；上一轮 fast passed | `scripts/test-full.sh` acceptance 因缺 `DEEPSEEK_API_KEY` 和 `.benchmarks/RuoYi-Vue` / `.benchmarks/eShopOnWeb` 失败，不能合规 push | 远端同步本地工作 | 外部环境阻塞 | `scripts/test-full.sh` + `git push` | DeepSeek key 和真实仓库 | full 通过后 push | 本轮完成后评估 |

排序结论：

1. 选择 A。它直接修复上一轮 Gate 提到的 `back -> scan` 候选审查风险，并且属于同一条首次 guided init “返回修改后只使用当前生效理解”的用户旅程。
2. B 暂不选。自动重新审查候选能更强保证显式复核，但会增加交互负担；当前更稳妥的小步是清空旧决策并提示用户可以返回 candidates 重新审查。
3. C 不作为功能 milestone。完成本轮独立价值后会按仓库规则运行 full regression；如果仍缺外部前置，则不 push。

本轮 milestone：

作为 Harness Maintainer，当我在首次 guided `init` 的最终确认阶段返回 scan 修改扫描理解后，我可以看到候选审查决策已随 scan 状态刷新而清空，并且最终写入不会把上一版 scan 状态下的 accept / reject / edit 决策静默套用到当前候选，从而相信“返回修改”真的只使用当前生效的扫描理解和审查状态。

## 设计

- 在 `run_guided_init()` 的 `action == "scan"` 分支中，重算 `weapon_selection` 与 `candidate_report` 后同步清空 `candidate_decisions`。
- 输出简短中文提醒：
  - 候选项已根据新的扫描状态刷新。
  - 上一轮候选审查决策已清空。
  - 如果需要重新审查，可在最终确认输入 `back` 并选择 `candidates`。
- 不自动重新进入候选审查，避免每次 scan 修改都强制用户重复回答全部候选。
- 最终 `accepted_interactive_decisions()` 在 `candidate_decisions=[]` 时会用当前 `candidate_ids` 生成默认 `kept` 决策，保持当前候选可审查但不带旧确认。

## 非目标

- 不修改 `CandidateDecision` schema。
- 不修改 LLM enhancement candidate 生成逻辑。
- 不把用户 scan supplement 直接转成 LLM enhancement candidate。
- 不改变 `back -> rules`、`back -> workflow`、`back -> candidates` 的现有行为。
- 不执行 Runtime、不创建 `.ai/task-runs`。

## 验收标准

- RED：新增 guided init integration 先证明旧行为会在 `back -> scan` 后保留旧 candidate accept / reject / edit 决策。
- 实现后：
  - CLI 输出候选审查决策清空提醒。
  - `interaction-decisions.yaml` 中当前候选只有默认 `kept`，不包含旧 `accepted` / `rejected` / `edited`。
  - `.ai/experience/weapon-library-candidates.yaml` 中候选保持 `candidate` / `human_confirmation_required=true`，不出现旧 `confirmed`、`rejected` 或旧 `decision_notes`。
  - 现有 scan back replacement tests、candidate review tests、guided init integration 继续通过。
- `compileall`、`git diff --check`、`scripts/test-fast.sh` 通过。

## Assumptions / Risks

- Assumption：返回修改 scan 代表用户改变了候选审查所依赖的上游理解，因此旧 candidate 决策不应继续生效。
- Assumption：清空旧决策比自动重新审查更符合当前 CLI 的低负担原则；用户仍可通过 `back -> candidates` 显式重新审查。
- Risk：如果用户只是微调 scan supplement，旧候选决策也会被清空，需要重新审查；这是为了避免旧上下文污染正式审计记录。

## Sub Agent

按目标模式尝试启动只读 explorer 审查 `back -> scan` 候选链路，当前环境返回 `agent thread limit reached`。主线程继续完成调研、TDD、实现和验证。
