# Existing Harness LLM 维护动作失败 Trace 设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/README.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/engineering/llm-contracts.md`、近期 spec / plan 列表、`existing_harness_action_runner.py`、`existing_harness_action_failures.py`、`cli.py` 和 existing Harness action integration tests。
- 按需未展开：`docs/engineering/architecture.md`、`docs/engineering/sensor-and-gate-rules.md`。本轮不改架构、benchmark check、Sensor 或 Runtime 契约。
- Sub agent：按目标模式尝试启动只读 explorer 审查 existing Harness LLM action failure，当前环境返回 `agent thread limit reached`；本轮由主线程完成调研、TDD、实现和验证。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. existing Harness LLM 维护动作失败应保留 action-specific trace | 新发现 / 上轮 Gate | Maintainer 在已有 Harness 入口运行 `recommend-workflow` 或 `self-improve`，即使 LLM / schema 失败，也能看到具体动作失败，trace summary 保留 action、错误类型、短错误和关键输入边界 | 空 task brief、review-candidate、review-human-input 等已有 action-specific failure；成功 recommend-workflow / self-improve 有 action summary | `recommend_workflow()` 或 `run_self_improve()` 抛异常时会落到 `cli.py` 顶层 `init failed`，summary 只剩 `error_type`，丢失 action、task id、review-only 边界 | 保护“再次进入已有 Harness -> 运行智能维护动作 -> 失败可审计定位”的用户旅程；符合 LLM 不可用必须显式失败且 no silent fallback | 低到中；只包裹两个同类 LLM/review-only 动作失败，不改成功路径、schema、writer 或 Runtime | integration monkeypatch 动作抛错，断言 CLI、trace summary/events、正式资产不变、无 `.ai/task-runs` | 无外部依赖；不需要真实 DeepSeek | 本轮 |
| B. Existing Harness action runner 模块拆分 | Gate / 工程债 | action runner 按 action family 拆分，降低单文件复杂度和未来冲突 | 已从 `interactive_init.py` 抽出 runner，但仍集中多个动作 | 文件继续变长；失败处理 helper 仍分散 | 降低长期维护成本 | 中；行为等价重构回归面大 | 全量 existing Harness integration | 无外部依赖 | 下一轮候选 |
| C. full regression / push gate 外部 DeepSeek 验收 | Gate | 完整工作包通过 full regression 后 push | fast 能过；`.env` 已配置；真实仓库存在 | sandbox DNS 失败；非 sandbox 因向外部 DeepSeek 发送本地仓库 evidence 被拒 | 解决后可同步远端 | 高；外部服务与审批 | `scripts/test-full.sh` | 网络、外部 DeepSeek、外发审批 | 保留为 push 前置 |

排序结论：

1. 选择 A。它最贴近 `init-north-star.md` 的“再次进入已有 Harness”旅程和 LLM-first 错误边界；范围清晰，能用 mock LLM failure 精确验收，并补齐当前真实可触达的审计漏洞。
2. B 是合理工程债，但没有 A 的直接用户失败风险，不应先做大范围搬迁。
3. C 仍是 push 前外部前置，不作为本轮代码 milestone。

## 本轮 milestone

作为 Harness Maintainer，当我在已有 Harness 维护入口选择 `recommend-workflow` 或 `self-improve`，但底层 LLM、schema 或 review-only 生成过程失败时，我可以看到这是对应维护动作失败，并在 trace summary 中看到 `existing_harness_action`、错误类型、短错误摘要和关键输入边界，从而能定位智能维护动作的外部或契约问题，而不会被泛化成普通 `init` 崩溃。

## 需求

- `recommend-workflow` 在 task brief 非空后，如果 `recommend_workflow()` 或后续 recommendation report 读取 / schema 校验失败：
  - CLI 输出 `recommend-workflow 失败：workflow_recommendation_failed`。
  - trace 记录 `existing-harness failed`。
  - trace summary 包含 `existing_harness_action=recommend-workflow`、`error=workflow_recommendation_failed`、`error_type`、`error_message`、`task_id`。
  - 不额外写入顶层 `init failed` event。
- `self-improve` 如果 `run_self_improve()` 或 self-improve package manifest 读取 / schema 校验失败：
  - CLI 输出 `self-improve 失败：self_improve_failed`。
  - trace summary 包含 `existing_harness_action=self-improve`、`error=self_improve_failed`、`error_type`、`error_message`。
  - 不创建 Runtime 产物，不覆盖正式 Guides / Sensors / Workflow Skills / inventory / config。
- 错误摘要应折叠多行异常，避免把长 LLM / schema 响应作为主要 CLI 输出。

## 非目标

- 不改变 `recommend-workflow` 或 `self-improve` 成功路径。
- 不修改 LLM prompt、schema、review-only 产物结构或 evidence allowlist。
- 不为其他 deterministic maintenance actions 做大范围 try/except 迁移。
- 不解决 full regression 外部 DeepSeek 网络 / 审批前置。

## 决策

- 复用 `fail_existing_harness_action()` 作为统一 action-specific failure 出口。
- 在 `existing_harness_action_failures.py` 增加短错误 helper，避免在 runner 中手写多行折叠逻辑。
- 只包裹 `recommend-workflow` 和 `self-improve` 的 LLM/review-only 生成和 manifest 读取区域；空 task brief 已有 failure 逻辑保持不变。

## Assumptions / Risks

- 这两个动作都属于智能维护动作，失败最常见原因是 LLM / schema / 产物契约，action-specific failure 对用户排查比顶层 `init failed` 更有价值。
- 如果 action 失败前已经写出部分 review-only 产物，本轮不做 rollback；但仍不得修改正式 Harness 资产或创建 Runtime 产物。测试会用正式资产 snapshot 验证边界。
- 未来如果 assess / improve / benchmark 也需要同类 failure helper，应另起更宽的 action runner hardening milestone。

## 验收标准

- 新增 integration RED：
  - `recommend-workflow` 输入有效 task brief 后 monkeypatch `recommend_workflow()` 抛多行 `RuntimeError`，当前 trace 落成泛化 `init failed`，测试先失败。
  - `self-improve` monkeypatch `run_self_improve()` 抛多行 `RuntimeError`，当前 trace 落成泛化 `init failed`，测试先失败。
- 实现后：
  - 两个动作 exit code 非 0，CLI 输出 action-specific failure code，不展示原始多行错误或 traceback。
  - trace summary 保留 action、error code、error type、短错误；recommend-workflow 保留 task id。
  - `events.jsonl` 有 `existing-harness failed`，无 `init failed`。
  - 正式资产 snapshot 不变，不创建 `.ai/task-runs`。
- 回归现有 recommend-workflow success / empty task failure / self-improve success tests。
- 运行 targeted tests、existing Harness integration 切片、`tests/integration/test_init_on_fixture_projects.py`、`compileall`、`git diff --check`、`scripts/test-fast.sh`；push 前尝试 full gate 并记录外部限制。
