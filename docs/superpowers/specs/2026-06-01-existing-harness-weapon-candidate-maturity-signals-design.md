# 已有 Harness 初始候选成熟度信号

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划第 1-4 节、`docs/engineering/architecture.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/todos/README.md`、`docs/todos/local-unique-capability-migration.md`、上一轮 candidate maturity impact spec / plan、`interactive_init.py`、`existing_harness_signals.py`、`existing_harness_status.py`、`maintenance_triage.py`、`weapon_library_candidate.py` 和相关测试。
- 按需未展开：`docs/engineering/llm-contracts.md`、`docs/engineering/sensor-and-gate-rules.md`。本轮不修改 LLM prompt / schema、benchmark hard gate 或 Sensor 规则。
- Todo 状态：`docs/todos` 当前无 open todo；本轮来自上一轮 Self-Harness Gate 的候选 gap。
- Sub agent：尝试启动只读 explorer 审计该 gap，当前会话返回 `agent thread limit reached`，因此由主线程完成调研、实现和验证。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. 已有 Harness 入口展示初始 LLM 候选成熟度影响 | 上一轮 Gate / init North Star | Maintainer 再次运行 `init` 时能看到 `.ai/experience/weapon-library-candidates.yaml` 中仍待确认的初始 Guide / Sensor 候选、成熟度维度、下一阶段贡献和 review-only 边界 | candidate YAML 已有 `maturity_dimensions` / impact 字段；首次 guided review 能展示成熟度影响 | existing Harness 维护入口只展示 asset candidates 数量，不读取初始 weapon-library candidates；非交互 init 生成的 pending 初始候选在维护入口不可见 | 把上一轮机器契约接到主入口，减少 Maintainer 忽略初始候选的风险，继续服务 Maturity-driven init 主线 | 低到中；只读信号和 triage，不新增应用动作，不改正式资产 | unit 覆盖 signals / triage / overview；integration 覆盖 guided existing Harness exit transcript | 依赖上一轮 schema 字段，已有 | 终端输出包含 pending count、maturity dimensions、top candidate、review boundary；triage detail 指向初始候选 report | 本轮 |
| B. 为初始 weapon-library candidates 增加 guided 治理动作 | 新发现 | Maintainer 可在已有 Harness 入口后续修改初始候选 accepted / rejected / kept 状态 | 首次 init 过程已有候选逐项审查；后续无专门治理入口 | 需要设计 interaction-decisions 与 candidate report 的后续治理语义，可能和 asset candidate governance 重叠 | 闭环更完整，但会扩大命令边界和 schema 语义 | 中到高；涉及新动作、状态写入和文档 | integration / schema / benchmark | 需要产品边界确认 | 作为后续更大候选，当前不做 | 下一轮候选 |
| C. Candidate maturity impact 进入 benchmark 质量评分 | Gate / 新发现 | benchmark 能提醒候选缺少成熟度影响或 review-only 边界 | schema 允许默认空字段兼容旧资产 | 强制检查可能让旧 Harness 因历史候选报告失败 | 可提升契约硬度，但与兼容策略冲突 | 中；会影响已有资产验收 | benchmark integration | 需要迁移策略 | 暂不处理，先用维护入口消费字段 | 保留 |

排序结论：

1. 选择 A，因为它直接把上一轮新增的机器契约接入 `init` 维护入口，用户可见、风险低、可独立验收。
2. B 虽然更完整，但需要新增候选治理语义；如果本轮顺手做，会把只读状态展示和正式状态变更混在一起。
3. C 会强化 benchmark，但上一轮已明确新增字段保持向后兼容；不应立刻让旧候选报告失败。

本轮 milestone：

作为 Harness Maintainer，当我再次运行 guided `init` 进入已有 Harness 维护入口时，我可以看到初始 LLM Guide / Sensor 候选是否仍待确认、它们影响哪些成熟度维度、最优先候选是什么以及它仍是 review-only 边界，从而不会把首次初始化留下的候选审查债误认为已经进入后续自改进闭环。

## 验收标准

1. `existing_harness_signals.experience_status_lines()` 在 `.ai/experience/weapon-library-candidates.yaml` 存在且 schema 有效时展示：
   - `weapon_library_candidates=<total>`
   - `weapon_library_candidates_pending=<pending>`
   - `weapon_candidate_maturity_dimensions=<dimensions>`
   - `weapon_candidate_top=<id> type=<type> dimensions=<dimensions> boundary=<boundary>`
2. 初始 candidate pending 的判断只使用 `status == "candidate"` 或 `human_confirmation_required == true`，confirmed / rejected 不计入 pending。
3. `render_existing_harness_status_overview_lines()` 的 Experience / review 摘要包含初始 LLM 候选待确认数量，避免只显示 asset candidates。
4. `build_maintenance_triage()` 在没有更高优先级 benchmark / schema 失败时，把 pending 初始 LLM 候选作为 review-only triage action，source 指向 `.ai/experience/weapon-library-candidates.yaml`，detail 包含 top candidate 和 maturity dimensions。
5. triage guidance 明确这是初始 LLM enhancement candidate，需要先查看 candidate report 和 review-only 边界；不调用 `review-candidate`、不应用正式资产、不执行 Runtime、不创建 `.ai/task-runs`。
6. guided existing Harness `init -> exit` transcript 能展示上述信号、overview 和 triage guidance。
7. 不修改 `WeaponLibraryCandidate` schema、不修改首次 init 的 candidate generation、不修改 asset candidate governance、不新增正式资产写入动作。

## 决策 / 取舍

- 本轮只做只读状态与 triage 暴露，不新增“review initial candidates”治理动作。原因是初始 weapon-library candidates 与 `.ai/review/asset-candidates.yaml` 的候选治理模型不同，混用 `review-candidate` 会误导用户。
- triage action 使用 `next_action="manual-review"`，让 action shortcuts 明确没有维护菜单编号，避免伪造一个不能执行的菜单项。
- Pending 计算优先看候选自身状态，而不是重新解释 `interaction-decisions.yaml`。落盘后的 candidate report 是维护入口可审计事实源。

## Assumptions / Risks

- Assumption：非交互 init 或用户 kept / edited 的初始候选是维护入口应提醒的审查债。
- Risk：只读提示不能完成治理闭环。通过 guidance 明确 report 入口、review-only 边界和后续更大候选 B，避免把它包装成已解决问题。
- Risk：旧 candidate report 通过 schema 兼容可能缺少 maturity impact 字段；本轮信号应显示 `none` / 空摘要，而不是失败或 silent success。
