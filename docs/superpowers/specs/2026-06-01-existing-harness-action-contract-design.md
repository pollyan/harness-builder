# Existing Harness 动作契约同源设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/README.md`、`docs/engineering/architecture.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/engineering/sensor-and-gate-rules.md`、近期 existing Harness 相关 spec / plan / evolution log、`interactive_init.py`、`maintenance_triage.py`、相关 unit / integration tests。
- 按需未展开：`docs/engineering/llm-contracts.md`，本轮不修改 LLM、Prompt、Schema、扫描调和或真实 DeepSeek 行为。
- Sub agent：按目标模式尝试启动 explorer 做只读交叉审查，但当前会话返回 `agent thread limit reached`；本轮由主线程完成调研，并把该限制记录为执行环境约束。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Existing Harness 动作契约同源 | 新发现 / 上轮 Gate 工程债 | 已有 Harness 维护入口的菜单、编号、别名 normalization 和 triage 快捷提示来自同一份动作定义 | 维护入口已有 1-9 菜单；`maintenance_triage.py` 已用编号提示推荐动作 | 菜单定义在 `interactive_init.py`，编号映射在 `maintenance_triage.py`，别名 normalization 也独立维护；未来改编号或新增动作时可能让“建议输入 4”与实际菜单漂移 | 保护“看到维护建议 -> 选择正确动作”的已有 Harness 用户旅程，降低后续菜单迭代风险 | 低到中：新增小模块并调整导入；不改 schema、LLM、Runtime 或动作执行业务 | unit 覆盖菜单行、编号查找、别名 normalization、triage hint 使用共享编号；integration 保持 existing Harness exit transcript | 无外部凭证；依赖当前 1-9 菜单语义稳定 | 测试证明菜单、shortcut 和 normalization 共用同一契约，existing Harness 只读 exit 行为不变 | 本轮 |
| B. 首次 init completion summary 视觉紧凑化 | 上轮 Gate | 写入完成后终端摘要更短、更聚焦，同时保留 benchmark / human-input / maturity 下一步 | completion message 已能优先提示 benchmark、failed checks 和待确认入口 | 内容可能偏长，但没有定义稳定的“紧凑摘要”口径；贸然删减可能削弱主交付说明 | 提升首次 init CLI 体验 | 低：主要文案与测试；但容易反复调文案 | unit / integration transcript 断言 | 需要先建立更明确 transcript 基线 | 下一轮候选 |
| C. Existing Harness 维护入口模块拆分 | 上轮 Gate / 工程架构 | `_handle_existing_harness_entry()` 被拆成清晰模块，便于继续扩展维护入口 | `interactive_init.py` 仍承载已有 Harness 输出和所有动作分支 | 大函数持续增长，后续每轮改动冲突面偏大 | 降低维护风险和后续迭代成本 | 中：纯重构范围更大，容易混入行为变化 | integration 行为等价、unit helper 覆盖 | 最好先稳定动作契约，减少拆分时漂移 | 下一轮候选 |

排序结论：

1. 选择 A，因为它直接保护 `init-north-star.md` 的“再次进入已有 Harness”旅程：Maintainer 依赖 triage 快捷提示选择正确菜单动作，而当前同一编号契约分散在两个模块。
2. B 暂不选，因为 completion summary 刚完成下一步优先级增强；继续压缩前需要先定义更明确的 transcript 体验标准。
3. C 暂不选，因为它是更大的模块拆分；本轮先抽出动作契约，给后续拆分一个稳定低风险基础。

## 本轮 Milestone

作为 Harness Builder 维护者，当我继续增强已有 Harness 维护入口或调整菜单动作时，我可以依赖一份同源动作契约同时驱动菜单、编号快捷提示和用户输入 normalization，从而避免 Maintainer 在 guided `init` 中看到的推荐编号和实际动作发生漂移。

## 验收标准

1. Existing Harness 菜单行、动作编号查询和用户输入 normalization 由同一份动作定义生成。
2. `maintenance_triage` 的 `Maintenance action shortcuts` 不再维护独立编号表，而是通过共享动作契约获取编号；未知 action 仍不能伪造编号。
3. `interactive_init.py` 保持现有 `_existing_harness_action_menu_lines()` 和 `_normalize_existing_harness_action()` 兼容入口，避免测试和内部调用大面积改动。
4. 不改变任何 existing Harness 动作的执行语义、默认值、trace summary、正式资产写入边界或 Runtime 分工；不创建 `.ai/task-runs`。
5. Unit 测试覆盖共享动作契约：菜单行顺序、编号查询、英文 / 中文别名 normalization，以及 triage shortcut 对共享编号的消费。
6. Integration 测试覆盖已有 Harness guided `init -> 1 exit` 仍展示快捷编号、仍不扫描、不覆盖正式资产。
7. 文档记录本轮决策、验证结果和 Self-Harness Gate；无需新增 open todo，除非 Gate 发现更大的后续缺口。

## 关键决策 / 取舍

- 新增 `existing_harness_actions.py` 作为动作契约模块，集中维护 action id、编号、菜单文案和别名。
- `interactive_init.py` 只负责渲染维护入口和执行动作分支；动作菜单和 normalization 委托共享模块。
- `maintenance_triage.py` 只负责排序维护建议；推荐动作编号通过共享模块查询，避免重复编号表。
- 保留现有 underscore helper 作为兼容 facade，不在本轮大面积移动 integration tests。

## Assumptions / Risks

- Assumption：当前 1-9 菜单顺序是已经对用户公开的稳定 CLI 契约，本轮只集中维护，不重新排序。
- Risk：如果未来新增动作但忘记加别名，用户仍可输入 action id；别名只是便利入口。
- Risk：模块抽取可能引入循环导入；本轮只让 `interactive_init.py` 和 `maintenance_triage.py` 依赖新模块，新模块不依赖业务模块。
