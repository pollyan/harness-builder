# Guided Init Scan 返回修改替换补充设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/README.md`、`interactive_init.py`、`project_inventory.py`、`command_catalog.py` 和相关 guided init integration tests。
- 按需未展开：`llm-contracts.md`、`sensor-and-gate-rules.md`、`architecture.md`，因为本轮不修改 LLM prompt/schema、benchmark gate 或模块边界。
- 当前 todo 状态：`docs/todos/README.md` 显示没有 open todo，旧本地独有能力迁移包已 `implemented`。
- Sub agent：尝试启动只读 explorer 审查 back->scan 流程，但当前环境返回 `agent thread limit reached`，本轮由主线程完成调研。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. 返回 scan 后替换旧补充而不是叠加 | 新发现 / Gate | 用户在最终确认返回 scan 重新输入补充后，最终资产只包含最新 scan correction | `back -> scan` 已支持重新收集补充，最终 decisions 只记录最新 `scan_overrides` | `_apply_scan_overrides()` 直接追加到已变异 inventory / command catalog，旧 module / command / risk 仍可能残留进正式 `.ai` 资产 | 防止用户已撤销的扫描事实污染 project inventory、Guides、Sensors 和 init summary，保护渐进式协作的可信度 | 中低：需调整内存态应用方式，不改 schema / writer | integration 测试可断言旧 module / command / risk 不落盘，新补充落盘 | 无外部依赖 | 本轮 |
| B. 返回 scan 后清空所有补充 | 同类边界 | 用户返回 scan 直接回车可撤销旧 scan note / module / command / risk | 当前 latest `scan_overrides` 会变空 | 旧变异仍残留，和 A 同根 | 与 A 同价值 | 中低 | 可作为 A 的后续边界测试或同实现覆盖 | 无 | 后续可补 |
| C. Scan overrides 结构化 diff / reset preview | North Star / 可解释性 | 返回 scan 时展示“将移除旧补充、应用新补充”的差异 | 当前只有即时理解 / 影响说明 | 用户不清楚哪些旧补充被替换 | 更强可解释性 | 中：CLI 复杂度增加 | CLI transcript tests | 需先修正替换语义 | 后续候选 |
| D. Workflow note 结构化 impact schema / routing candidate | 上轮 Gate | Workflow note 进入更强机器契约或候选治理 | 当前是 review-only note | 仍是自由文本说明 | 更深 workflow 定制 | 中到高 | schema / governance tests | 需要独立设计 | 后续候选 |

排序结论：

1. 选择 A，因为它影响正式资产正确性：用户返回 scan 重新修改后，旧补充不应继续进入 project inventory、command catalog、project-context、verification sensor 或 init-summary。相比 workflow impact schema，这个缺口更直接破坏“用户输入被正确消费”的 North Star 要求。
2. B 与 A 同根，但本轮先覆盖“旧补充替换为新补充”的纵向路径；实现会自然支持清空，是否单独加测试由后续 Gate 决定。
3. C 属于更强 CLI diff 解释，等替换语义正确后再做。
4. D 与本轮 scan 资产正确性不同旅程，留作后续。

本轮 milestone：

作为 Harness Maintainer，当我在最终确认阶段发现扫描补充写错并返回 `scan` 重新输入模块、验证命令或风险区域时，我可以确信最终生成的 project inventory、command catalog、Guides、Sensors 和 init summary 只包含最新补充，而不会继续保留已经撤销的旧补充，从而避免错误扫描事实污染正式 Harness 资产。

## 验收标准

1. Integration 测试先失败：首次输入 `legacy` module / command / risk，最终确认 `back -> scan` 后输入 `final` module / command / risk；当前代码会把旧补充残留到资产。
2. 修复后，`project-inventory.json` 只包含 `final` module / risk，不包含 `legacy`。
3. `command-catalog.yaml` 只包含 `final_test`，不包含 `legacy_test`。
4. `interaction-decisions.yaml` 的 `scan_confirmation` 只记录最新 scan notes。
5. `project-context.md`、`verification.md` 和 `init-summary.md` 包含 final 补充，不包含 legacy 补充。
6. 返回 scan 后的 weapon selection / candidate generation / maturity preview 基于最新 inventory / commands。
7. 不修改 schema、LLM、asset writer 或 benchmark；只修正 guided init 内存态应用语义。
8. 运行目标测试、相关 guided init tests 和 `scripts/test-fast.sh`。

## 决策与取舍

- 在扫描完成后保存一份 clean baseline `ProjectInventory` / `CommandCatalog`。
- 每次应用 scan overrides 时，从 baseline 深拷贝生成新的内存态，再应用最新 overrides，避免旧补充叠加。
- `back -> scan` 展示和收集基于 clean baseline，而不是已变异的 inventory。
- 不在本轮新增“将移除哪些旧补充”的 diff 文案；语义正确性优先。

## Assumptions / Risks

- `ProjectInventory` 和 `CommandCatalog` 是 Pydantic model，可用 `model_copy(deep=True)` 保留扫描基线。
- 用户返回 scan 后重新输入补充应表达“替换上一版 scan corrections”，与 rules / workflow 返回修改保持一致。
- 如果未来需要多轮累计补充，应显式设计 add/remove/diff 语义，不能继续靠隐式追加。
