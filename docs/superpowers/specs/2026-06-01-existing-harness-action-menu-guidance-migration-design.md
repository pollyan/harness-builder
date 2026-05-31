# Existing Harness 编号菜单与维护指引迁移设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/todos/local-unique-capability-migration.md`、已有 `2026-05-31-existing-harness-maintenance-triage-*` spec / plan，以及当前 / 备份分支的 `interactive_init.py`、`maintenance_triage.py` 和相关测试。
- 按需未展开：`docs/engineering/llm-contracts.md`、`sensor-and-gate-rules.md`、acceptance 测试。当前 milestone 只改已有 Harness guided 入口的只读 CLI 路由体验，不改 LLM、Sensor、benchmark 规则或正式资产 schema。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Existing Harness 编号菜单与维护指引 | 迁移 todo / 旧分支 | Maintainer 再次运行 `init` 时，可以按编号选择维护动作，并看到 top actions 对应的中文处理建议 | 当前主线已展示成熟度、Experience signals、Maintenance triage 和命令名动作 | 用户仍要记英文命令；`top_action_*` 只有 reason/source/next，缺少“该先怎么处理”的中文 guidance；旧分支已有编号菜单和 guidance 基础 | 直接改善已有 Harness 维护入口的 CLI 友好性，降低误选和认知负担，不改变 Runtime 边界 | 低到中，只改只读入口输出和 action normalization；不写正式 Harness 资产 | unit 覆盖 action normalization / guidance；integration 覆盖输入 `1` 只读退出且不扫描、不覆盖 | 依赖当前已有 Maintenance triage 和旧分支参考实现 | CLI 输出含 `1. exit` 与 `Maintenance triage guidance`；输入 `1` trace 记录 exit；formal assets 不变 | 本轮 |
| B. Benchmark failed preview 与更细失败 detail | 迁移 todo / 旧分支 | 已有 Harness 入口直接展示 benchmark 失败项中文标签、weak command、missing detail | 当前主线只展示最近 benchmark 和 schema/content failed count；benchmark 命令本身会输出失败摘要 | 入口状态面板不能快速解释具体失败项；旧分支有 `_benchmark_signal_lines` 和更细 labels | 提升维护入口问题定位效率 | 中，涉及 BenchmarkReport 扩展字段渲染和多个失败类型 | unit 构造 BenchmarkReport；integration 构造失败 report 再进入 guided init | 无外部凭证；但与后续 benchmark quality gate 细化相关 | 输出失败项 label/detail 且 triage reason 更具体 | 下一轮候选 |
| C. Human-input-needed backlog 状态 | 迁移 todo / 旧分支 | 已有 Harness 入口展示 questionnaire 待确认数量、scan confirmation 数量和处理入口 | 当前主线只显示 `human_input_needed=present/missing` | Maintainer 不知道还有哪些确认项待处理，也不知道 `.ai/human-input-needed.md#处理方式` 是入口 | 补齐渐进式协作的维护回访链路 | 中，涉及 Questionnaire schema 读取和缺失文件边界 | unit 读 questionnaire；integration 输出确认项状态 | 依赖当前 human confirmation 产物 | 输出 `human_input_confirmations`、`human_input_first`、action entry | 后续候选 |
| D. Workflow routing signals | 迁移 todo / 旧分支 | 已有 Harness 入口展示 routing default、standard escalation、risk trigger 等路由健康信号 | 当前主线展示 latest workflow recommendation，但不展开正式 routing policy 健康 | Maintainer 不易判断推荐动作和正式 routing policy 的关系 | 强化 Runtime 分工与 routing 可解释性 | 中，读取 HarnessConfig，需避免伪装为 Runtime 执行结果 | unit helper；integration 输出 routing signals | 无外部依赖 | 输出 routing signals 且保持不执行 Runtime | 后续候选 |

排序结论：

1. 选择 A，因为它是迁移 todo 推荐的 Existing Harness 维护入口第一组能力中风险最低、最直接用户可感知的一刀。当前主线已经有 triage 数据，缺的是低负担选择和可行动中文解释；实现不触碰 LLM、benchmark 评分或正式资产写入。
2. B、C、D 也有价值，但分别进入 benchmark detail、human confirmation backlog 和 routing health。它们更像下一批状态信号增强，适合在菜单 / guidance 这个入口交互稳定后继续迁移。

本轮 milestone：

作为 Harness Maintainer，当我再次运行 guided `init` 进入已有 Harness 维护入口时，我可以看到带编号的维护动作菜单，并按编号选择只读退出或后续维护动作，同时从 Maintenance triage guidance 中理解 top actions 应该如何处理，从而不用记英文命令或自行解读 reason code。

## 关键决策 / 取舍

- 本轮只迁移“编号菜单 + triage guidance + action normalization”，不迁移 benchmark failed preview、routing signals 或 human input backlog。
- 继续保留英文命令和中文别名，保证已有脚本化输入和用户习惯不被破坏。
- 未识别输入仍走当前“默认退出且不覆盖正式资产”的保守边界。
- guidance 只解释当前 `MaintenanceAction.reason`，不新增持久化 `.ai` 文件，不重新排序 triage。

## Assumptions / Risks

- 假设编号菜单对 guided CLI 是独立价值；它不会改变非交互模式，也不会影响首次 init。
- 旧分支的更细 benchmark detail 依赖额外字段，本轮暂不迁移，避免把小入口体验切片扩大成 benchmark 质量门禁切片。
- sub agent 原计划用于只读对比，但当前线程 agent 数量已达上限，本轮在 spec 中记录为不可用。

## 可执行验收标准

- Unit：`_normalize_existing_harness_action()` 接受 `1` 到 `8`、英文命令、常见中文别名，并对未知输入返回原始 normalized action。
- Unit：`render_maintenance_triage_guidance_lines()` 针对 benchmark 缺失、候选待处理、无待办信号等 reason 输出中文下一步建议。
- Integration：已有 Harness 再次运行 guided `init`，输入 `1` 可以只读退出，不触发 scan，不覆盖 `project-inventory.json`、`harness-config.yaml`、`init-summary.md`。
- CLI transcript：维护入口输出 `Maintenance triage guidance`、`1. exit`、`2. assess` 等编号动作。
- 文档：README、`docs/engineering/init-workflow.md`、迁移 todo 和 evolution log 同步说明本轮已迁移的能力与后续候选。
- 验证：targeted unit / integration 测试通过，`git diff --check` 通过，commit 前 `scripts/test-fast.sh` 通过。

## Sub Agent 使用情况

尝试使用只读 explorer 对比当前 main 与 `backup/local-61-before-migration`，但当前线程 sub agent 数量达到上限，无法 spawn。本轮改为主线程本地对比旧分支实现、当前代码和测试。
