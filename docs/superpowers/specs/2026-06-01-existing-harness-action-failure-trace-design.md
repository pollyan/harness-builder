# Existing Harness 维护动作失败 Trace 保真设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、`docs/strategy/Harness Builder — 面向遗留代码库治理的 AI Coding Harness 生成器.md`、`docs/engineering/architecture.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/todos/README.md`、`src/harness_builder_agent/cli.py`、`src/harness_builder_agent/tools/existing_harness_action_runner.py`、`tests/integration/test_init_on_fixture_projects.py`、当前 git 状态。
- 按需未展开：`llm-contracts.md`、`sensor-and-gate-rules.md`；本轮不修改 LLM、benchmark check、schema 或 Runtime 产物。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Existing Harness 维护动作失败 trace 保真 | 上一轮 Gate / 当前代码审查 | 已有 Harness guided action 失败时，trace summary 保留 `existing_harness_action`、相关 id / decision 和 error | `review-candidate` 缺 report / unknown id 早期失败已用 `typer.Exit` 保留 action trace | 其他分支仍在 `trace.finish("failed", ...)` 后抛 `typer.BadParameter`，会被顶层 `init` 泛化覆盖为 `error_type=BadParameter` | 让 Maintainer 和测试能判断失败属于哪个维护动作，保护审计和排障 | 中；触碰 guided init 失败退出语义和 integration tests | 新增 guided failure-path integration，检查 trace summary、stages、无 scan、无 `.ai/task-runs` | 无外部凭证 | `recommend-workflow` 空 brief、`review-human-input` unknown id、`review-initial-candidate` 缺 report 等失败保留 action summary | 本轮 |
| B. Existing Harness action runner 模块拆分 | 技术债 / 架构规则 | runner 按动作拆模块，降低单文件复杂度 | 已有 summary renderer / action runner 抽取 | `existing_harness_action_runner.py` 仍承载所有动作和重复失败 trace 逻辑 | 降低后续维护成本 | 中高；重构范围更大，易和行为测试耦合 | 全量 existing Harness integration regression | 依赖 A 先稳定失败语义 | 拆分后行为无变更，测试通过 | 下一轮候选 |
| C. full regression / push 工作包 | 用户提醒 / Git 状态 | 独立价值工作包完成后同步 GitHub | 本地 ahead 69 / behind 0；fast 通过 | `scripts/test-full.sh` acceptance 因缺 `DEEPSEEK_API_KEY` 和 `.benchmarks` 真实仓库失败 | 让远端获得本地迁移和增强 | 受外部环境阻塞 | `scripts/test-full.sh` + `git push` | DeepSeek key 和真实仓库 | full 通过后 push | 外部前置满足后处理 |

排序结论：

1. 选择 A。它直接服务 `init-north-star.md` 的“再次进入已有 Harness”旅程，保护失败后的审计可信度；范围比 B 小，但能为后续拆分提供稳定契约。
2. B 暂不选，因为当前更适合先统一失败语义，再做模块拆分。
3. C 暂不选，因为 push 前 full acceptance 前置仍未满足，不能绕过仓库规则。

本轮 milestone：

作为 Harness Maintainer，当我在已有 Harness guided 维护入口执行 `recommend-workflow`、`review-human-input`、`review-candidate` 或 `review-initial-candidate` 等动作但输入缺失、候选不适用或治理失败时，我可以获得明确失败，并且 generation trace 保留所选维护动作、相关 id / decision 和错误原因，从而后续排查不需要猜测这是普通 init 失败还是具体维护动作失败。

## 设计

- 在 `existing_harness_action_runner.py` 中增加一个小型失败出口 helper，统一写入：
  - `trace.event("existing-harness", "failed", ...)`
  - `trace.finish("failed", {"existing_harness_action": action, ...})`
  - 面向 CLI 的简短失败输出
  - `raise typer.Exit(code=1)`
- 对已经写入 action-specific failed trace 的 guided maintenance 分支，不再继续抛 `typer.BadParameter`。
- 覆盖代表性失败路径：
  - `recommend-workflow` 空 task brief。
  - `review-candidate` workflow policy guided `applied` 禁止路径。
  - `review-candidate` 不支持 decision。
  - `review-candidate` 执行治理失败。
  - `review-human-input` 治理失败。
  - `review-initial-candidate` 缺候选 report。
  - `review-initial-candidate` 治理失败。
- 不改变 standalone `review-candidate` / `review-human-input` 命令的异常语义。
- 不改变 benchmark failed 的当前行为；benchmark 本身会把 failed status 当作 action-specific failed trace。

## 非目标

- 不修改候选治理 schema。
- 不改变成功路径、正式资产应用规则或 review-only 边界。
- 不创建 `.ai/task-runs`。
- 不做 action runner 大拆分。
- 不绕过 push 前 full regression 要求。

## 验收标准

- 新增 integration RED tests 先证明当前 `recommend-workflow` 空 brief、`review-human-input` unknown id、`review-initial-candidate` 缺 report 会退化为泛化 `BadParameter` summary。
- 实现后这些测试通过，trace summary 包含 `existing_harness_action` 和对应 error / id / decision。
- 相关 `review-candidate` workflow policy guided apply 禁止路径保留 `existing_harness_action=review-candidate` 和 `error=workflow_policy_applied_requires_expert_command`。
- 失败路径不重新扫描，不覆盖正式 Harness 资产，不创建 `.ai/task-runs`。
- `tests/integration/test_init_on_fixture_projects.py` 通过。
- `compileall`、`git diff --check`、`scripts/test-fast.sh` 通过。

## Assumptions / Risks

- Assumption：guided maintenance action 失败属于用户可修复的动作失败，应以非零 exit 结束，同时保留 action trace，而不是让顶层 init 捕获泛化。
- Risk：`typer.Exit` 会让异常输出更短；本轮 helper 会先 `typer.echo` 失败原因，保证 CLI 仍有可读信息。
- Risk：统一失败出口可能改变既有 tests 对 `BadParameter` 文案的依赖；本轮保留核心错误字符串并更新 tests 到更有价值的 trace 断言。

## Sub Agent

按目标模式要求尝试启动只读 explorer 审查 action runner 失败路径，当前环境返回 `agent thread limit reached`。主线程继续完成调研、TDD、实现和验证。
