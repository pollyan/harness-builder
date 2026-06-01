# Guided 初始 LLM 候选治理

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划第 1-3 节、`docs/engineering/architecture.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/todos/README.md`、上一轮初始候选成熟度信号 spec / plan、`existing_harness_actions.py`、`existing_harness_action_runner.py`、`maintenance_triage.py`、`weapon_candidate_status.py`、`llm_enhancement_candidates.py`、`candidate_governance.py` 和相关 unit / integration tests。
- 按需未展开：`docs/engineering/llm-contracts.md`、`docs/engineering/sensor-and-gate-rules.md`。本轮不修改 LLM prompt / parser，不调整 benchmark hard gate。
- Todo 状态：`docs/todos` 当前无 open todo；本轮来自上一轮 Self-Harness Gate 的候选 gap。
- Sub agent：尝试启动只读 explorer 审计“初始 LLM candidates 后续治理动作”，当前会话返回 `agent thread limit reached`。本轮由主线程完成调研、TDD、实现和验证。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. guided 初始 LLM candidate 治理动作 | 上一轮 Gate / init North Star / 全景规划审查接管 | Maintainer 再次运行 `init` 时，可以对 `.ai/experience/weapon-library-candidates.yaml` 中的初始 Guide / Sensor 候选记录 accepted / rejected / kept，并留下治理日志 | 维护入口能展示 pending 初始候选、top candidate 和 maturity dimensions | 用户只能手动查看报告；没有主入口动作记录后续决策，pending 信号无法被消除或审计 | 补齐“看见审查债 -> 留下治理决策”的接管闭环，继续服务 existing Harness 可持续维护体验 | 中；涉及新 guided action、机器治理产物、report 状态更新，但不改正式资产 | schema unit、tool unit、action runner unit、guided integration transcript | 依赖上一轮只读信号和 `WeaponLibraryCandidateReport` | 菜单出现 `review-initial-candidate`，triage shortcut 可指向编号；执行后候选 report 状态更新、governance log 落盘、正式资产不变 | 本轮 |
| B. Candidate maturity impact 进入 benchmark 检查 | 上一轮 Gate / 工程信任 | benchmark 能提醒旧或损坏候选缺少 maturity impact / review boundary | schema 默认兼容旧字段；benchmark 只校验 schema 与候选状态 | 强制检查可能让历史 Harness 失败；软检查语义还未设计 | 可提升质量门禁，但用户可见接管价值不如 A | 中；涉及 benchmark 兼容策略 | benchmark integration | 需要迁移策略 | 暂缓，等治理链路稳定后再评估 | 下一轮候选 |
| C. existing Harness 维护入口文案结构化瘦身 | 新发现 / 技术债 | 维护入口在信号增多后仍能保持低噪声、面向人优先 | 当前同时展示 overview、raw signals、triage、guidance、shortcuts 和菜单 | raw signals 越来越多，用户可能难以扫描 | 体验价值高，但更偏 UI 整理，容易和功能变更混杂 | 中；主要 transcript tests | 需先稳定新 action 输出 | 单独做 CLI transcript UX 切片 | 保留 |

排序结论：

1. 选择 A，因为上一轮已经让 pending 初始候选可见；如果没有治理动作，Maintainer 仍无法从主入口完成接管闭环。
2. B 先不选，因为 benchmark hardening 需要兼容策略，且不能替代用户可见的治理动作。
3. C 是合理 UX 债，但应该在新信号和新 action 稳定后再做，避免一轮里同时改功能和重排 CLI。

本轮 milestone：

作为 Harness Maintainer，当我再次运行 guided `init` 看到初始 LLM Guide / Sensor 候选仍待确认时，我可以在同一个维护入口中选择 `review-initial-candidate`，对单个初始候选记录 accepted / rejected / kept 决策，并留下机器可读治理日志，从而完成一条不修改正式 Harness 资产的候选接管闭环。

## 验收标准

1. 新增机器消费 schema：`.ai/review/weapon-candidate-governance.yaml` 必须能通过 Pydantic schema 校验，记录 candidate id、type、source report、decision、rationale、reviewer、timestamp、maturity dimensions、review boundary、previous/new status。
2. 新增 deterministic tool：
   - 读取 `.ai/experience/weapon-library-candidates.yaml`。
   - `accepted` 把候选置为 `status=confirmed`、`human_confirmation_required=false`。
   - `rejected` 把候选置为 `status=rejected`、`human_confirmation_required=false`。
   - `kept` 保持 `status=candidate`、`human_confirmation_required=true`。
   - rationale 不能为空；未知 candidate id、非法 decision、缺 report 必须显式失败。
   - 重新生成 `.ai/review/llm-enhancement-candidates.md`、`.ai/review/candidate-guides.md` 和 `.ai/review/candidate-sensors.md`，让 Markdown 与 YAML 状态一致。
3. existing Harness 菜单新增 `review-initial-candidate`，maintenance triage 对 `weapon_library_candidates_pending` 应映射到该编号，而不是 `manual-review`。
4. guided action 执行后写入 `.ai/review/weapon-candidate-governance.yaml/.md`，trace 记录 governance artifact，不重新扫描、不运行 LLM、不执行 Runtime、不创建 `.ai/task-runs`。
5. guided action 不修改正式 Guides、Sensors、Workflow Skills、`harness-config.yaml`、project inventory 或 command catalog。
6. accepted / rejected 后，再次进入 existing Harness 维护入口时 pending 初始候选数量减少；kept 后仍保持 pending。
7. README 与 `docs/engineering/init-workflow.md` 同步描述该 action 的边界。

## 决策 / 取舍

- 不复用 `.ai/review/asset-candidates.yaml` 的 `review-candidate` 命令和 governance schema。初始 LLM candidates 是首次 init 的增强候选，不具备 draft content / suggested path / apply 语义。
- 只支持 `accepted` / `rejected` / `kept`，不支持 `applied`。accepted 只确认候选状态，不写入正式 Guide / Sensor。
- 本轮只提供 guided action，不新增 standalone CLI 命令，降低命令面扩张；如未来需要自动化治理，再基于本轮 schema 增加专家命令。

## Assumptions / Risks

- Assumption：初始候选治理是 Maintainer 对首次 init 遗留审查债的接管动作，应该保守地只更新 candidate report 与 governance log。
- Risk：`accepted` 可能被误解为正式应用。通过 action summary、governance Markdown 和 README / init workflow 明确 `accepted` 不修改正式 Harness 资产。
- Risk：Markdown review files 由 report 重新生成，可能改变人工已有备注。本轮只重写 Builder 生成的 candidate review files，不触碰正式 Guides / Sensors；人工长期备注应通过 governance log 保留。
