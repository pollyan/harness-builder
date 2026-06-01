# Review Human Input 默认待处理项设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/README.md`、`docs/engineering/architecture.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`。
- 当前代码 / 测试检查：`interactive_init.py` 中已有 Harness 入口、`maintenance_triage.py` 的 `human_input_scan_followups_pending` detail、`tests/integration/test_init_on_fixture_projects.py` 的 guided existing Harness `review-human-input` 覆盖。
- Todo 状态：`docs/todos/README.md` 当前没有 open todo；本轮从当前 existing Harness 维护入口的用户体验 gap 中选择。
- Sub agent：按目标模式尝试启动 explorer，但当前会话返回 `agent thread limit reached`；本轮由主线程完成调研、TDD、实现和验证。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. review-human-input 默认待处理 interaction id | init North Star / 当前代码 | Maintainer 选择 `review-human-input` 后，可以直接回车处理 triage 推荐的首个 scan follow-up | triage 已展示 count 和首个 interaction id；guided action 能治理指定 interaction id | 用户仍需从上方输出手动复制 interaction id，CLI 没有把 triage detail 带入下一步 prompt | 降低 existing Harness 维护入口的操作负担，强化“状态信号 -> 推荐动作 -> 治理执行”闭环 | 低：只改 prompt 默认值，不改 schema / 治理语义 / Runtime | integration 改成回车接受默认 id；unit 可覆盖默认 id helper | 依赖 `MaintenanceAction.detail` 继续承载首个待处理 id | guided `init` 输入 `review-human-input` 后 interaction id 直接回车仍成功治理首个待处理项 | 本轮 |
| B. Existing Harness action execution 抽模块 | 上轮 Gate / 架构 | 主向导只负责入口展示和动作派发，动作执行逻辑有独立模块 | signals、actions、status overview 已拆出 | assess / improve / benchmark / recommend-workflow / review governance / self-improve 分支仍在 `interactive_init.py` | 降低后续维护动作扩展风险 | 中：跨多动作、trace artifact 和 prompt，容易触碰集成测试 | 多个 existing Harness integration + new unit | 无外部依赖 | 可作为后续工程信任切片 | 下一轮候选 |
| C. 首次 init completion 生成清单进一步紧凑化 | 上轮 Gate | 完成摘要更短、更行动优先 | completion 已行动优先，用户补充已紧凑 | 生成清单仍稍长，但它是交付确认信息 | 改善首次 init 终端可读性 | 低 | unit / integration transcript | 需要定义压缩规则 | 暂不处理 |

排序结论：

1. 选择 A，因为它直接改善 Harness Maintainer 再次运行 `init` 后的实际操作：系统已经知道建议先处理哪个 interaction id，就不应要求用户再手动复制。
2. B 暂不选，因为上一轮刚完成 signals 抽取；动作执行抽模块更大，适合作为后续工程信任切片。
3. C 暂不选，因为 completion 当前已经行动优先，用户收益小于 A 的操作成本降低。

## 本轮 Milestone

作为 Harness Maintainer，当我再次运行 guided `init` 并选择 `review-human-input` 处理待确认 scan follow-up 时，我可以直接回车接受维护入口推荐的首个 interaction id，从而不用手动复制上方 triage detail，也能完成显式人工复核治理。

## 验收标准

1. existing Harness 入口仍先展示 human-input triage count 和首个 interaction id。
2. 选择 `review-human-input` 后，如果 triage 中存在首个待处理 scan follow-up，interaction id prompt 使用该 id 作为默认值。
3. 用户在 interaction id prompt 直接回车时，`review-human-input` 治理该默认 id，并刷新 `.ai/questionnaire.yaml`、`.ai/human-input-needed.md` 和 `.ai/review/human-input-governance.*`。
4. 没有默认待处理 id 时，行为保持原样：空 id 仍显式失败，不 silent fallback。
5. 不修改 schema、正式 Harness 资产、Runtime 分工、review-human-input 治理语义或 benchmark 规则。
6. 提交前运行 `scripts/test-fast.sh`。

## 关键决策 / 取舍

- 默认 id 只来自当前 `build_maintenance_triage()` 计算出的 `human_input_scan_followups_pending` action detail，不重新扫描、不重新推断。
- 默认 id 只是 prompt 默认值；Maintainer 仍可以输入其他 interaction id 覆盖。
- 本轮不抽取整段 action execution，避免把低风险用户体验增强变成跨动作重构。

## Assumptions / Risks

- Assumption：triage detail 已由 `Questionnaire` schema 读取，足够作为默认 interaction id 的事实来源。
- Risk：Typer prompt 默认值输出可能影响 transcript；本轮只断言回车可成功治理默认 id，不依赖具体 prompt 字符串样式。
