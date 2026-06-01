# Guided Final Confirm Chinese Aliases 设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、`docs/strategy/Harness Builder — 面向遗留代码库治理的 AI Coding Harness 生成器.md`、`docs/todos/README.md`、`docs/evolution-log.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`src/harness_builder_agent/tools/interactive_init.py` 和相关 guided init integration tests。
- 按需未展开：`docs/engineering/llm-contracts.md`、`docs/engineering/sensor-and-gate-rules.md`、`docs/engineering/architecture.md`；本轮不修改 LLM、benchmark、Sensor gate、模块边界或 Runtime 契约。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. 最终确认与返回目标支持中文别名 | init North Star / 当前代码审查 | 中文 guided CLI 在最终确认阶段可接受 `确认` / `返回` / `取消`，返回目标也可接受 `扫描` / `团队规则` / `候选` / `工作流`，同时保留英文命令 | CLI 文案是中文，但提示要求输入英文 `confirm` / `back` / `cancel` 和 `scan` / `rules` / `candidates` / `workflow`；未知输入会提示错误 | 中文用户在中文界面下输入 `确认` 或 `返回` 会被当成未知输入；即使安全不误写，也增加交互摩擦 | 降低首次 init 的最终写入和返回修改成本，符合“CLI 中文、低负担、错误恢复清晰”的体验目标 | 低；只改输入解析和提示，不改 schema / writer / LLM / Runtime | guided init integration：中文 `返回 -> 团队规则 -> 确认` 能替换规则并写入；中文 `取消` 可后续另测 | 无外部凭证 | transcript 包含中文别名提示；最终产物只保留中文返回后新规则 | 本轮 |
| B. 返回 scan 后自动重新进入候选审查 | 上一轮 Gate | scan 修改后自动要求用户复核当前候选，进一步减少 review-only 候选 stale 风险 | 当前已清空旧 candidate decisions 并提示可 `back -> candidates` | 不自动重新审查；用户可能忘记复核候选而默认 kept | 更强审查，但更重交互 | guided init transcript | 需要 UX 取舍 | 自动重审 transcript / 产物决策 | 下一轮候选 |
| C. full regression / push 工作包 | Git 状态 / 用户 push 规则 | 本地独立价值同步 GitHub | 当前 `main...origin/main [ahead 75]`；上一轮 fast passed | `scripts/test-full.sh` acceptance 因缺 `DEEPSEEK_API_KEY` 和 `.benchmarks/RuoYi-Vue` / `.benchmarks/eShopOnWeb` 失败，不能合规 push | 远端同步本地工作 | 外部环境阻塞 | `scripts/test-full.sh` + `git push` | DeepSeek key 和真实仓库 | full 通过后 push | 本轮完成后评估 |

排序结论：

1. 选择 A。它是中文 CLI 低负担体验的直接缺口，与上一轮最终确认输入硬化相邻，属于同一个最终确认交互边界；补齐后用户不需要在中文界面记英文控制词。
2. B 暂不选。自动重审候选会增加交互轮次，上一轮已通过清空旧决策降低风险，适合后续单独权衡。
3. C 不作为功能 milestone。完成本轮后按仓库规则评估 full regression；外部前置仍缺时不 push。

本轮 milestone：

作为 Harness Maintainer，当我在中文 guided `init` 的最终确认阶段准备写入或返回修改时，我可以直接输入 `确认`、`返回`、`取消`，并在返回修改时输入 `扫描`、`团队规则`、`候选` 或 `工作流` 选择目标，从而不必在中文界面记住英文控制词，同时仍保留英文命令和未知输入保护。

## 设计

- 为 `_confirm_summary()` 增加轻量归一化 helper：
  - 最终动作：空输入 / `confirm` / `确认` / `写入` -> `confirm`；`back` / `返回` / `修改` -> `back`；`cancel` / `取消` / `退出` -> `cancel`。
  - 返回目标：`scan` / `扫描` / `扫描修正` -> `scan`；`rules` / `团队规则` / `规则` -> `rules`；`candidates` / `候选` / `候选项` -> `candidates`；`workflow` / `工作流` / `Workflow补充` -> `workflow`。
- 更新 prompt 文案和未知输入提示，明确中英文都可用。
- 保持未知非空输入继续等待，不 silent confirm。
- 保留英文命令，避免破坏现有测试和用户习惯。

## 非目标

- 不修改 scan supplement 的结构化格式。
- 不修改 Guide / Sensor candidate 审查选项 `a/r/k/e`。
- 不修改非交互模式。
- 不改变 writer、schema、benchmark、LLM 或 Runtime 分工。

## 验收标准

- RED：新增 guided init integration 先证明 `返回 -> 团队规则 -> 确认` 中文别名不能生效，最终仍保留旧团队规则或无法写入。
- 实现后：
  - 最终确认 prompt 显示中英文别名。
  - 中文 `返回` 能进入返回目标选择。
  - 中文 `团队规则` 能返回团队规则阶段，并用新规则替换旧规则。
  - 中文 `确认` 能完成写入。
  - 英文 happy path 和未知输入保护不回归。
- `tests/integration/test_init_on_fixture_projects.py`、`compileall`、`git diff --check`、`scripts/test-fast.sh` 通过。

## Assumptions / Risks

- Assumption：中文 guided CLI 的控制词应支持中文别名，但 machine-readable 产物仍保留英文枚举值。
- Risk：别名集合过多可能误识别用户自由文本；本轮只在最终确认和返回目标两个明确控制 prompt 生效，不影响 scan/team/workflow 自由文本输入。

## Sub Agent

按目标模式尝试启动只读 explorer 审查中文别名缺口，当前环境返回 `agent thread limit reached`。主线程继续完成调研、TDD、实现和验证。
