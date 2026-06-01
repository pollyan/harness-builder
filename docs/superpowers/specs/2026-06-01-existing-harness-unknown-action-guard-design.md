# Existing Harness 维护动作未知输入保护设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、`docs/strategy/Harness Builder — 面向遗留代码库治理的 AI Coding Harness 生成器.md`、`docs/todos/README.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、已有 related specs / plans 列表、`src/harness_builder_agent/tools/interactive_init.py`、`existing_harness_actions.py`、`existing_harness_action_runner.py` 和 existing Harness integration tests。
- 按需未展开：`docs/engineering/llm-contracts.md`、`docs/engineering/sensor-and-gate-rules.md`、`docs/engineering/architecture.md`；本轮不修改 LLM、benchmark checks、Sensor gate、schema 或模块边界。
- open todo：`docs/todos/README.md` 显示当前没有 open todo。
- sub agent：尝试启动只读 explorer 审查已有 Harness 维护入口未知动作，当前环境返回 `agent thread limit reached`；主线程继续。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. 已有 Harness 维护入口未知动作不能默认退出 | 新发现 / no silent fallback / init North Star 已有 Harness 维护入口 | Maintainer 输入未知菜单项时，CLI 明确提示有效动作并重新等待输入；内部 runner 收到未知 action 时显式失败，不伪装成 exit | 菜单支持编号、英文命令和中文别名；默认回车为 `1` exit | `normalize_existing_harness_action()` 返回未知字符串，runner 末尾输出“默认退出且不覆盖现有 Harness”，trace 记录 completed exit；这会把 typo 伪装成有意退出 | 保护已有 Harness 维护入口的操作可信度，符合 no silent fallback，避免用户以为已触发建议动作实际只是退出 | 低；只改交互解析和 fallback，不改正式资产、schema、LLM、Runtime | integration 输入未知动作后再输入 `1`，断言先提示未知并重新等待；trace 最终只有显式 exit；runner unknown fallback 可用 unit 或 integration 间接覆盖 | 无 | CLI transcript、trace summary、正式资产快照 | 本轮 |
| B. 已有 Harness 菜单继续降低输入成本 | init North Star 交互低负担 | 维护入口可根据 triage top action 提供默认推荐动作或更短别名 | 当前默认 `1` exit，避免自动执行 | 如果 top action 是 benchmark，用户仍需输入 `4`；但把默认改成推荐动作会违反“默认只读退出” | 可能提升效率，但风险是误执行维护动作 | 中；涉及产品取舍和多 action 流程 | integration 覆盖默认行为、推荐 shortcut | 需要产品取舍 | 保留为候选，不进入本轮 |
| C. full regression / push 工作包 | Git 状态 / 提交规则 | 本地 ahead commit 通过 full 并 push GitHub | fast 可通过，`.env` 和 `.benchmarks` 已具备 | sandbox 下 DeepSeek acceptance 无法解析 `api.deepseek.com`；非 sandbox full 会外发 fixture / benchmark evidence，权限申请被策略拒绝 | 远端同步本地工作 | 外部网络和数据外发权限阻塞 | `scripts/test-full.sh` + push | 需要用户明确授权外发 evidence | full 通过并 push | 继续作为 push gate，不作为本轮功能 milestone |

排序结论：

1. 选择 A。它直接修复已有 Harness 维护入口的 no-silent-fallback 风险，保护 `init` 再次进入时的维护动作选择可信度；改动小、可用 CLI transcript 和 trace 明确验收。
2. B 暂不选。维护入口默认只读退出是已确认边界，提升快捷性不能牺牲安全默认。
3. C 仍受外部服务和数据外发权限阻塞；本轮完成后继续按规则评估 push gate。

本轮 milestone：

作为 Harness Maintainer，当我再次运行 guided `init` 进入已有 Harness 维护入口并误输入不存在的维护动作时，我可以看到明确的未知输入提示并重新选择有效菜单项，从而不会把一次 typo 静默记录成有意退出，也不会误以为推荐维护动作已经执行。

## 设计

- 在 `existing_harness_actions.py` 增加 `is_existing_harness_action()`，复用稳定 action table。
- `_handle_existing_harness_entry()` 的维护动作 prompt 改为循环：
  - 空输入仍按默认 `1` 归一化为 `exit`。
  - 命中编号 / action / alias 时才调用 runner。
  - 未命中时输出有效输入提示并继续等待。
- `run_existing_harness_action()` 的末尾 unknown fallback 从“默认退出”改为显式 action failure，避免未来绕过 prompt 的调用继续 silent fallback。

## 非目标

- 不改变默认回车 `1 exit`。
- 不改变现有 action 编号、英文命令或中文别名。
- 不改变任何已有 Harness action 的产物、schema 或 trace summary。
- 不执行 Runtime、不创建 `.ai/task-runs`。
- 不解决 full regression / push 外部权限问题。

## 验收标准

- RED：新增 integration 先证明未知维护动作会默认退出，不会要求用户重新选择。
- 实现后：
  - 输入 `not-a-real-action` 后 CLI 输出未知维护动作提示和有效菜单说明。
  - 随后输入 `1` 才退出，正式 Harness 资产不变。
  - trace summary 记录 `existing_harness_action=exit`，且这是用户第二次显式选择 `1` 的结果。
  - 输出不再包含“默认退出且不覆盖现有 Harness”。
  - existing Harness exit / numbered action 回归通过。
  - `tests/integration/test_init_on_fixture_projects.py`、`compileall`、`git diff --check`、`scripts/test-fast.sh` 通过。

## Assumptions / Risks

- Assumption：已有 Harness 维护入口是 TTY guided UI，未知输入更可能是 typo，应重新提示而不是退出。
- Risk：如果有人依赖输入任意字符串退出，该行为会变严格；应改用直接回车、`1`、`exit`、`quit`、`q` 或 `退出`。
