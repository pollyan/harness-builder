# 写入前风险路由预览一致性设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景 North Star、`docs/todos/README.md`、`docs/engineering/architecture.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/evolution-log.md`。
- 已对比：`src/harness_builder_agent/tools/interactive_init.py`、`src/harness_builder_agent/tools/prewrite_preview.py`、`src/harness_builder_agent/tools/write_assets.py`、`tests/unit/test_interactive_init_preview.py`、`tests/integration/test_init_on_fixture_projects.py`、既有 prewrite preview 和 risk context consistency specs。
- 按需未展开：`docs/engineering/llm-contracts.md` 和 `sensor-and-gate-rules.md`。本轮不修改 LLM、prompt、scan schema、benchmark check 或 Sensor 规则。
- Sub agent：按目标模式尝试启动只读 explorer 审查用户输入消费链路，当前环境返回 `agent thread limit reached`；本轮由主线程完成调研、TDD、实现和验证。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. 写入前 Workflow 风险路由预览与最终配置一致 | init North Star / 新发现 | 写入前预览展示即将生成的真实 `standard-escalation` 路由，包括 scan risk path 和用户补充 risk 触发的 `risk_area:*` 升级规则 | `write_initial_assets()` 通过 `build_harness_config(inventory)` 把风险路径写入最终 `harness-config.yaml`；Guide / Sensor / benchmark 已围绕 risk context consistency 建立校验 | `show_prewrite_maturity_preview()` 仍用 `HarnessConfig.default()`，preview 只展示静态三条 routing rule，不展示仓库特异性的 `risk_area:<path>` trigger 或 rationale；用户确认前无法看到风险路径会进入 standard routing | 让“用户补充 risk -> 预览 -> 正式 routing policy”闭环可见，避免 preview 像模板说明而不是当前仓库设计 | 低到中：需要让 preview 复用正式 config builder，可能触发成熟度预览阻断项变化；不改 schema / Runtime / benchmark | unit 检查 preview 输出风险 trigger；integration 检查 guided init transcript 和最终 config 一致 | 依赖现有 `build_harness_config()` 风险路由逻辑 | 本轮 |
| B. Existing Harness action execution 进一步抽模块 | 上轮 Gate / 架构债 | 已有 Harness 入口的动作执行、summary、prompt 和 trace 更清晰分层 | action runner / summaries 已存在，但 `interactive_init.py` 仍保留维护入口展示和很多 facade | 工程可维护性仍有改进空间，但本轮用户可见价值弱于 A | 降低后续维护入口迭代冲突 | 中：行为保持型重构需要大量 transcript 回归 | existing Harness unit / integration | 无外部依赖 | 下一轮候选 |
| C. full regression / push 工作包 | Gate / git 状态 | 本地完整工作包通过 full regression 后 push | 当前分支本地领先远端多个提交，fast regression 已用于每轮 commit | push 前需要 `scripts/test-full.sh`，涉及 acceptance / DeepSeek / `.benchmarks` 和网络前置；本轮仍有可本地推进的 init gap | 降低分叉风险 | 外部前置高，不适合作为本轮代码 milestone | full regression 与 push 结果 | `DEEPSEEK_API_KEY`、真实仓库、网络 | 外部前置候选 |

排序结论：

1. 选择 A。它直接服务 `init-north-star.md` 的“成熟度驱动 Harness 设计预览”和“用户补充必须在生成前被后续设计消费”的目标；同时修正 preview 与正式资产之间的可见不一致。
2. B 重要但更偏工程债，且上一轮已有多个 guided init 模块抽取；当前更应先让用户可见预览继续靠近真实生成结果。
3. C 仍受外部前置影响，不作为本轮 milestone；完成有独立价值的工作包后再按 `AGENTS.md` 决定是否 full regression / push。

## 本轮 milestone

作为 Harness Maintainer，当我在首次 guided `init` 的写入前预览中看到 Workflow routing 设计时，我可以看到当前扫描风险或我补充的风险路径会如何进入 `standard-escalation` 的 `risk_area:*` 触发条件，从而在最终确认前确认高风险区域不会只停留在 Guide / Sensor 文案，而会进入实际生成的路由策略。

## 验收标准

1. `show_prewrite_maturity_preview()` 使用与 `write_initial_assets()` 一致的 Harness config 构造逻辑，而不是只使用裸 `HarnessConfig.default()`。
2. 当 inventory 或 scan supplement 中存在 risk area 时，写入前 `Workflow routing` 预览展示 `standard-escalation` 的 `risk_area:<path>` trigger，并说明该风险路径会升级到 `standard`。
3. unit 测试先证明当前 preview 没有 risk trigger；实现后通过。
4. guided init integration 中，用户补充 `risk=frontend/package.json|前端依赖需要单独确认` 后，写入前 preview 和最终 `.ai/harness-config.yaml` 都包含 `risk_area:frontend/package.json`。
5. 不修改 `.ai` schema、LLM prompt、scan reconcile、benchmark check、正式 Runtime 分工或 `.ai/task-runs` 行为。
6. 完成前运行相关 unit、相关 guided init integration、`git diff --check` 和 `scripts/test-fast.sh`。

## 决策与取舍

- 复用正式 Harness config builder 作为 preview 的事实源，避免 preview 和最终 writer 各自维护一套 routing 逻辑。
- 本轮只让 preview 反映即将生成的 routing policy，不新增可编辑 routing DSL，也不把 Workflow 补充自由文本直接应用成正式 policy。
- 风险路径来自当前内存态 `ProjectInventory`，其中包含扫描调和结果和本轮结构化 scan supplement；它仍按用户补充事实边界展示，不声称已由扫描 evidence 验证。

## Assumptions / Risks

- Assumption：`build_harness_config(inventory)` 已经是当前正式资产生成侧的路由事实源；preview 复用它比复制逻辑更可靠。
- Risk：如果 preview 复用正式 config 后成熟度预览的阻断项变化，说明此前 preview 与正式生成确实不一致，应通过测试更新并保留更真实的结果。
- Risk：CLI 输出会多展示风险 trigger。只在已存在风险路径时产生额外可见信息，且它是用户确认前必须知道的设计要点。
