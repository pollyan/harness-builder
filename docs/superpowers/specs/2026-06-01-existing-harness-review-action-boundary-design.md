# Existing Harness Review Action 边界拆分设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、`docs/strategy/Harness Builder — 面向遗留代码库治理的 AI Coding Harness 生成器.md`、`docs/engineering/architecture.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/todos/README.md`、`docs/evolution-log.md`、`src/harness_builder_agent/tools/existing_harness_action_runner.py`、上一轮 Existing Harness 失败 trace spec、当前 git 状态。
- 按需未展开：`llm-contracts.md`、`sensor-and-gate-rules.md`；本轮不修改 LLM、prompt、benchmark check、schema 或 Runtime 产物。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Existing Harness review action 边界拆分 | 上轮 Gate / 架构规则 / 当前代码审查 | `existing_harness_action_runner.py` 负责动作路由，review 类治理动作的 precheck、prompt、governance 调用、trace artifact 和 summary 落在独立模块 | 上轮已统一失败 helper，`existing_harness_action_runner.py` 仍 609 行并直接导入三类 governance schema / tool / summary helper | review-candidate、review-human-input、review-initial-candidate 的细节与 assess / improve / benchmark / self-improve 混在一个函数里，后续维护任一治理动作容易影响其他动作 | 降低已有 Harness 维护入口继续演进的回归风险，给候选治理和人工输入治理保留清晰落点 | 中；主要是行为保持型重构，风险在 import 循环和 trace 语义漂移 | 新增 unit 架构边界测试，现有 guided integration 回归行为 | 上轮失败 trace helper 已稳定 | runner 不再直接依赖 review governance schema / tool，review 模块暴露稳定 delegate，existing Harness integration 通过 | 本轮 |
| B. 首次 init 继续增强某个用户可见预览 / completion gap | init North Star | 首次 guided init 更接近完整成熟度驱动旅程 | 多个写入前预览切片已实现 | 仍可能存在 completion / scan / maturity 细节缺口，但需要重新聚焦具体用户故事 | 直接用户体验价值 | 中；需更多 CLI transcript 审查 | guided init integration | 无 | 新增用户可见断言 | 后续候选 |
| C. full regression / push 工作包 | 用户提醒 / Git 状态 | 独立价值工作完成后同步 GitHub | 本地 ahead 70 / behind 0；fast 通过 | `scripts/test-full.sh` acceptance 因缺 `DEEPSEEK_API_KEY` 和 `.benchmarks` 真实仓库失败，暂不能合规 push | 让远端获得本地提交 | 受外部环境阻塞 | `scripts/test-full.sh` + `git push` | DeepSeek key 和真实仓库 | full 通过后 push | 本轮完成后再次尝试 |

排序结论：

1. 选择 A。它来自上一轮 Gate，直接保护 `init-north-star.md` 的“再次进入已有 Harness”维护入口，也符合架构文档中单文件膨胀时按职责拆分的演进判断。
2. B 暂不选，因为当前已有明确的 review action 技术债，并且上一轮刚稳定失败语义，适合立即收口模块边界。
3. C 不作为功能 milestone，但本轮完成后按用户要求和仓库规则尝试 push；若 full regression 仍因外部前置失败，则不 push 并明确报告。

本轮工程信任故事：

作为 Harness Builder 维护者，当我后续修改已有 Harness 入口中的候选治理、human-input 治理或初始 LLM 候选治理动作时，我可以在独立的 review action 模块里维护这些动作，并由现有 guided integration 回归证明 CLI 行为、trace、review-only 边界不变，从而降低一个动作变更影响整个维护入口的风险。

## 设计

- 新增 `existing_harness_action_failures.py`，承载已有 Harness action-specific 失败出口，避免 runner 和 review 模块复制 trace finish 逻辑。
- 新增 `existing_harness_review_actions.py`，承载：
  - `run_review_candidate_action()`
  - `run_review_human_input_action()`
  - `run_review_initial_candidate_action()`
  - review 类 action 的 candidate summary / lookup / default interaction id helper。
- `existing_harness_action_runner.py` 保留 action dispatch 和非 review 动作实现；遇到 review 类 action 时委托新模块。
- 保持原有 CLI prompt、trace event、trace artifact、summary、failure code、review-only 边界和输出文案不变。
- 新增 unit 架构边界测试，防止 runner 重新直接导入 review governance schema / tool。

## 非目标

- 不新增或修改 CLI 命令。
- 不修改 `review-candidate` / `review-human-input` / `review-initial-candidate` 的业务语义。
- 不修改 schema、benchmark、LLM、prompt、正式资产 writer 或 Runtime 产物。
- 不创建 `.ai/task-runs`。
- 不放宽任何已有 integration 断言。

## 验收标准

- RED：新增 `tests/unit/test_existing_harness_action_boundaries.py`，在新模块不存在或 runner 仍直接持有 review governance 依赖时失败。
- 实现后 unit 边界测试通过。
- `tests/integration/test_init_on_fixture_projects.py` 通过，证明 guided existing Harness 行为、trace、review-only 边界没有漂移。
- `compileall`、`git diff --check`、`scripts/test-fast.sh` 通过。
- `docs/engineering/architecture.md` 记录新模块职责。
- `docs/evolution-log.md` 记录 Gap Analysis、验收和 Self-Harness Gate。
- 完成后运行 `scripts/test-full.sh` 评估是否允许 push；若外部 acceptance 前置缺失，必须停止 push。

## Assumptions / Risks

- Assumption：review 类动作的共同点是都围绕 Maintainer 对 review-only 候选或 human input 的显式治理，适合独立于 assess / improve / benchmark / self-improve 动作。
- Risk：行为保持型重构容易遗漏 trace artifact 或输出顺序；用完整 existing Harness integration 回归覆盖。
- Risk：新增模块后 import 循环可能出现；失败 helper 独立成小模块，review 模块只依赖 summary / governance / schema / triage 类型。

## Sub Agent

按目标模式尝试启动只读 explorer 审查 action runner 拆分边界，当前环境返回 `agent thread limit reached`。主线程继续完成调研、TDD、实现和验证。
