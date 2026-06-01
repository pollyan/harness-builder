# Guided Final Confirm Invalid Input 设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、`docs/todos/README.md`、`docs/evolution-log.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`src/harness_builder_agent/tools/interactive_init.py` 和相关 guided init integration tests。
- 按需未展开：`docs/engineering/llm-contracts.md`、`docs/engineering/sensor-and-gate-rules.md`、`docs/engineering/architecture.md`；本轮不修改 LLM、benchmark、Sensor gate、模块边界或 Runtime 契约。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. 最终确认非法输入不能写入资产 | 当前代码审查 / init North Star / no silent fallback | 最终写入只能由空回车默认 confirm 或显式 `confirm` 触发；用户输入 typo 或未知命令时，CLI 明确提示有效选项并留在最终确认，不写正式 `.ai` 资产 | `_confirm_summary()` 支持 `back`、`cancel`，空回车默认 `confirm` | 除 `back` / `cancel` 外的任意非空输入都会走默认 `confirm` 分支并写入资产，例如 `cnofirm` 会误写 `.ai` | 保护最终写入边界，避免 typo 导致不可逆的正式资产覆盖；直接服务“最终输入 confirm 前不写入或覆盖正式 Harness 资产” | 低；只改 prompt 解析和 transcript，不改 schema / writer / LLM | guided init integration：先 RED 证明 typo 会写入；修复后断言 typo 输出错误提示、直到后续 `confirm` 才写入 | 无外部凭证 | CLI transcript、`.ai/project-inventory.json` 写入发生在有效 confirm 后、fast regression | 本轮 |
| B. 返回 scan 后自动重新进入候选审查 | 上一轮 Gate | scan 修改后自动要求用户复核当前候选，进一步减少 review-only 候选 stale 风险 | 当前已清空旧 candidate decisions 并提示可 `back -> candidates` | 不自动重新审查；用户可能忘记复核候选而默认 kept | 更强审查，但更重交互 | guided init transcript | 需要 UX 取舍 | 自动重审 transcript / 产物决策 | 下一轮候选 |
| C. full regression / push 工作包 | Git 状态 / 用户 push 规则 | 本地独立价值同步 GitHub | 当前 `main...origin/main [ahead 74]`；上一轮 fast passed | `scripts/test-full.sh` acceptance 因缺 `DEEPSEEK_API_KEY` 和 `.benchmarks/RuoYi-Vue` / `.benchmarks/eShopOnWeb` 失败，不能合规 push | 远端同步本地工作 | 外部环境阻塞 | `scripts/test-full.sh` + `git push` | DeepSeek key 和真实仓库 | full 通过后 push | 本轮完成后评估 |

排序结论：

1. 选择 A。它是最终正式写入边界上的明确 bug，符合 no silent fallback 和 init North Star 的“未确认前不写正式资产”原则，且可以用一个小 integration 切片证明。
2. B 暂不选。上一轮已通过清空旧决策降低 stale 风险；自动重审会增加交互成本，需要单独判断。
3. C 不作为功能 milestone。完成本轮后按仓库规则评估 full regression；外部前置仍缺时不 push。

本轮 milestone：

作为 Harness Maintainer，当我在首次 guided `init` 的最终确认阶段误输入了未知命令或把 `confirm` 拼错时，我可以看到明确的无效输入提示，并且 Harness Builder 不会写入正式 `.ai` 资产，直到我显式输入 `confirm` 或按默认回车确认，从而避免 typo 触发误写入。

## 设计

- 修改 `_confirm_summary()` 的最终确认输入解析：
  - 空输入仍允许走默认 `confirm`，保持现有低负担路径。
  - `confirm`、`back`、`cancel` 保持有效。
  - 其他非空输入输出中文错误提示，说明有效选项，并重新提示。
- 返回目标选择仍保持 `scan` / `rules` / `candidates` / `workflow`；未知返回目标继续回到最终确认，不写资产。
- 不修改 `write_initial_assets()`、schema、trace schema 或 writer。

## 非目标

- 不移除回车默认确认。
- 不修改 guided back stage 的默认值。
- 不引入新的 confirmation schema 字段。
- 不改变非交互模式。
- 不执行 Runtime、不创建 `.ai/task-runs`。

## 验收标准

- RED：新增 guided init integration 先证明最终确认输入未知命令会被当作 confirm，缺少无效提示。
- 实现后：
  - 未知输入输出“未识别的最终确认输入”或等价中文提示。
  - 只有后续有效 `confirm` 才完成写入。
  - `cancel` 和 `back` 既有路径不回归。
  - `tests/integration/test_init_on_fixture_projects.py` 通过。
- `compileall`、`git diff --check`、`scripts/test-fast.sh` 通过。

## Assumptions / Risks

- Assumption：空回车默认确认是当前 CLI 的既有低负担交互，本轮保留。
- Assumption：非空未知输入很可能是 typo，应显式阻止而不是默认确认。
- Risk：脚本化交互如果依赖输入任意字符串触发确认会被破坏；但 guided 模式面向 TTY 人机交互，自动化应使用 `--non-interactive`。

## Sub Agent

按目标模式尝试启动只读 explorer 审查最终确认非法输入风险，当前环境返回 `agent thread limit reached`。主线程继续完成调研、TDD、实现和验证。
