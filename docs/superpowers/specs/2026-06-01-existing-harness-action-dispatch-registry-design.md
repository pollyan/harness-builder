# Existing Harness Action Dispatch Registry 设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/engineering/architecture.md`、`docs/todos/README.md`、近期 existing Harness action / completion specs 与 `docs/evolution-log.md`。
- 当前代码 / 测试检查：`src/harness_builder_agent/tools/existing_harness_actions.py`、`existing_harness_action_runner.py`、`existing_harness_entry.py`、`tests/unit/test_existing_harness_actions.py`、`tests/unit/test_existing_harness_action_boundaries.py`。
- 按需未展开：`docs/engineering/llm-contracts.md`、`docs/engineering/sensor-and-gate-rules.md`，本轮不修改 LLM、Prompt、Schema、benchmark check、Sensor 或 Runtime 契约。
- Todo 状态：`docs/todos/README.md` 标记当前没有 open todo；历史 todo 均为 implemented / paused 背景参考。
- Sub agent：尝试启动 explorer 做 existing Harness action 同步风险只读调研，但当前会话返回 `agent thread limit reached`；本轮由主线程完成调研、TDD 和验证。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Existing Harness action dispatch registry | 上轮 Gate / 当前代码审查 | 菜单中每个可选维护动作都有 runner handler 覆盖，新增或改名动作时测试能立即发现漂移 | 菜单动作集中在 `EXISTING_HARNESS_ACTIONS`，runner 已降到 79 行并委托 deterministic / intelligent / review action 模块 | runner 仍靠 `if action == ...` 手写分支；没有测试证明菜单动作集合与 runner 可处理动作集合一致 | 保护“再次运行 init -> 选择维护动作 -> 获得可审计结果”的核心维护入口，降低后续增加动作时漏接或编号/handler 漂移风险 | 低；行为等价重构，不改 CLI 文案、schema、LLM、writer 或 Runtime | unit 先 RED 断言 handler registry 覆盖菜单动作；targeted existing Harness action unit 回归；fast regression | 无外部依赖 | `EXISTING_HARNESS_ACTION_HANDLERS` 覆盖 `EXISTING_HARNESS_ACTIONS` 全部 action；runner 不再手写每个 action if/elif；现有 delegation tests 仍通过 | 本轮 |
| B. Completion 资产概览进一步压缩 | 上轮 Gate / init North Star | 写入完成摘要更短，资产概览不压过行动建议 | completion summary 已行动优先、下一步去重、资产按 4 组 ready/missing 展示 | 资产概览仍占几行，但缺少新的稳定压缩标准；当前信息承担审计价值 | 改善首次 init 终端阅读负担 | 低到中；容易误删审计信息 | unit / integration transcript | 需要定义不损失审计的压缩口径 | 下一轮候选 |
| C. Push / full regression 同步远端 | Git / Gate | 本地完整工作包通过 full regression 后同步 GitHub | 当前 main 领先 origin/main 93 个本地提交；fast 可通过 | push 前 full regression 需要真实 DeepSeek acceptance；沙箱 DNS 失败，非沙箱运行会外发本地 fixture / benchmark evidence，已被策略拒绝 | 降低长期分叉风险 | 高；外部服务与数据外发审批阻塞 | `scripts/test-full.sh` + git push | 需要网络和合规外发授权 | full 通过后 push | 外部前置，当前不作为代码 milestone |

排序结论：

1. 选择 A。它直接保护 `init-north-star.md` 中“再次进入已有 Harness”的维护动作选择旅程；相比继续压缩 completion 文案，它降低未来功能迭代时的真实漂移风险，并且范围小、可单元验收。
2. B 暂不选。completion 资产概览虽然还可打磨，但上一轮已修正行动重复；压缩标准需要进一步定义，避免为了短而损失审计信息。
3. C 暂不选。远端同步仍受 full regression 外部 DeepSeek 网络 / 数据外发审批阻塞，本轮继续做可本地验证的工程信任切片。

## 本轮 Milestone

作为 Harness Builder 维护者，当我继续给已有 Harness 维护入口新增或调整菜单动作时，我可以通过一个显式 dispatch registry 和覆盖测试确认每个菜单动作都有 runner handler，从而降低“菜单显示可选但实际执行落到 unknown 或漏 trace”的回归风险。

## 验收标准

1. `existing_harness_action_runner.py` 暴露稳定的 `EXISTING_HARNESS_ACTION_HANDLERS`，覆盖 `EXISTING_HARNESS_ACTIONS` 中全部 action。
2. `run_existing_harness_action()` 通过 registry 派发动作；未知 action 仍调用 `fail_existing_harness_action()`，记录 `unknown_existing_harness_action`。
3. `exit`、`reinit` 和所有委托动作保持原有返回值、trace event、trace summary、正式资产 / Runtime 边界不变。
4. Unit 测试证明菜单 action 集合与 handler registry 一致，并保留现有 deterministic / intelligent / review action delegate 边界测试。
5. 不修改 CLI 菜单文案、action 编号、别名、Pydantic schema、LLM prompt、benchmark check、writer 或 Runtime 分工。

## 关键决策 / 取舍

- 使用 runner 内部 registry，而不是把 handler 放入 `existing_harness_actions.py`，避免菜单定义模块依赖执行模块。
- 保持所有 handler 使用统一签名 `(repo, ai, inventory, trace, maintenance_actions)`，用小 wrapper 适配各 action 的不同参数。
- 本轮只做行为等价 hardening，不把 action implementation 再拆新模块。

## Assumptions / Risks

- Assumption：外部调用者只依赖 `run_existing_harness_action()`，不直接依赖 runner 内部 if/elif 结构。
- Risk：source-inspection 类测试可能过脆；本轮以 handler registry 集合一致性为主要断言，source 检查只保留“runner 不持有业务实现依赖”的边界测试。
