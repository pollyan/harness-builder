# 已有 Harness 维护入口焦点前置设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划前段、`docs/todos/README.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/engineering/architecture.md`、`docs/evolution-log.md`。
- 已检查代码：`interactive_init.py` 的 existing Harness 入口、`existing_harness_status.py`、`existing_harness_signals.py`、`maintenance_triage.py`、相关 unit / integration tests。
- 按需未展开：LLM prompt、scanner、benchmark 细节和 acceptance；本轮只调整已有 Harness 入口 CLI 呈现顺序与文案，不修改 LLM、scan、schema、benchmark 或 Runtime。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. 已有 Harness 维护焦点前置 | 上一轮 Gate / init North Star | Maintainer 再次进入已有 Harness 时，第一屏先看到中文维护摘要、建议动作和可输入编号；机器字段作为审计明细保留但不抢占第一决策焦点 | 当前已有 `Maintenance overview`、raw Benchmark / Workflow / Experience signals、triage、guidance 和 shortcuts | guidance / shortcuts 排在 raw signals 后面；用户需要先扫过 `benchmark_failed_checks=`、`routing_default=` 等内部字段，才能看到建议动作 | 提升已有 Harness 入口的 CLI 视觉焦点和低内部字段暴露，直接服务“再次进入已有 Harness”旅程 | 低；只调整输出顺序与分组，不改动作执行、schema 或产物 | integration transcript 可验证顺序；unit 可验证 helper 不变 | 无外部依赖 | 输出中 `Maintenance triage guidance` 和 shortcuts 出现在 raw signal sections 前，raw sections 前有审计明细说明，exit 不扫描不覆盖资产 | 本轮 |
| B. 首次 guided init 深度追问与 self-check 再审 | init North Star / 新发现 | 首次 init 对 scan follow-up 和 LLM self-check 的 CLI 展示更聚焦，帮助用户理解哪些不确定性必须补 | 当前已展示 scan followup/self-check 并写入 questionnaire | 可能仍有文案密度和优先级问题，需要更系统 transcript 审查 | 提升首次 init 理解深度，但范围更大，可能触碰 scan presentation 多处 | 中等；需要多条 guided integration | 无外部依赖，但需更长调研 | transcript / questionnaire / human-input-needed 验证 | 下一轮候选 |
| C. Full regression / push 工作包 | Gate / git 状态 | 累积本地目标模式提交形成完整同步批次后，运行 full regression 并 push | 当前 `main` ahead origin 59；每个本地 commit 已跑 fast regression | push 前需要 `scripts/test-full.sh`，可能依赖真实 DeepSeek、`.benchmarks` 和网络 | 同步远端，但不直接推进 init North Star 体验 | 高；外部凭证 / 真实仓库可能阻塞 | full regression + git push | 外部服务可用性 | full regression 通过后 push | 工作包完成后处理 |

排序结论：

1. 选择 A，因为它直接服务 init North Star 的“再次进入已有 Harness”场景和“CLI 视觉焦点清晰、低内部字段暴露”原则；同时改动边界小，可在一个 commit 内通过 transcript 验收。
2. B 更贴近首次 init 深度，但需要重新审 scan presentation / follow-up / self-check，范围比本轮更大。
3. C 是同步节奏，不是本轮产品体验切片；仍按 AGENTS 在完整 push 工作包前运行 full regression。

本轮 milestone：

作为 Harness Maintainer，当我再次运行 guided `init` 进入已有 Harness 维护入口时，我可以在 raw 审计字段之前先看到中文维护建议和对应菜单编号，从而立刻知道下一步该选哪个动作，同时仍保留 Benchmark / Workflow / Experience raw signals 供排查和测试定位。

## 验收标准

1. Existing Harness 入口输出顺序调整为：维护状态摘要 -> 维护建议 -> 推荐动作快捷选择 -> 审计明细说明 -> raw Benchmark / Workflow / Experience signals -> raw triage lines -> 菜单。
2. `Maintenance triage guidance` 和 shortcut 行只输出一次，不在 raw signals 后重复出现。
3. raw signals 仍保留原有 section 和字段，保证测试和审计定位能力不丢失。
4. exit / numbered exit 仍是只读动作，不扫描、不覆盖正式 Harness 资产、不追加首次初始化完成摘要。
5. README 与 `docs/engineering/init-workflow.md` 同步说明维护入口先展示焦点动作，再展示审计明细。

## 决策

- 不删除 raw signals，因为它们已经被 README / engineering docs 作为审计和测试定位能力记录；本轮只把它们明确降级为“审计明细”。
- 不新增 CLI flag 或隐藏模式，避免让测试和用户路径分叉。
- 不修改 `maintenance_triage.py` 的排序语义，只调整 existing Harness 入口渲染顺序。

## Assumptions / Risks

- 输出顺序变化可能影响 transcript 测试；本轮用 integration 测试显式锁定关键顺序，避免后续又把 raw signals 放回第一屏。
- sub agent 按 playbook 尝试用于只读审查，但当前环境返回 `agent thread limit reached`；主线程完成调研、TDD、实现和验证。
