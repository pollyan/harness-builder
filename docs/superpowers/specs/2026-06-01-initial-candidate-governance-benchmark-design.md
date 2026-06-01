# 初始候选治理 Benchmark 契约设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划前段、`docs/todos/README.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/engineering/sensor-and-gate-rules.md`、`docs/engineering/architecture.md`、`docs/evolution-log.md`。
- 已检查代码：`src/harness_builder_agent/tools/benchmark.py`、`src/harness_builder_agent/schemas/weapon_candidate_governance.py`、`src/harness_builder_agent/schemas/weapon_library_candidate.py`、相关 integration / unit tests。
- 按需未展开：LLM prompt 资产和 acceptance 真实仓库测试；本轮不修改 LLM prompt、扫描行为或真实 DeepSeek acceptance。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. 初始候选治理后的 benchmark 契约 | 上一轮 Gate / 新发现 | Maintainer 对初始 LLM Guide / Sensor 候选执行 accepted / rejected / kept 后，benchmark 能校验候选报告、治理日志和 Markdown 一致，不因候选不再全部 pending 而误报 | 已有 `review-initial-candidate` 写出 `.ai/review/weapon-candidate-governance.*` 并刷新 candidate report / Markdown；benchmark 只校验 candidate report schema 和 summary 中包含 `candidate` | `_llm_enhancement_checks()` 仍要求所有候选 `status=candidate` 且 `human_confirmation_required=True`；benchmark 不校验 `weapon-candidate-governance.*` 配对、candidate id、状态转移、review-only 边界或 Markdown 同步 | 保护已有 Harness 维护入口的候选接管闭环，避免治理动作完成后质量门禁失真 | 中等；触碰 benchmark hard gate，但不改正式资产 writer、LLM、Runtime 或 scan schema | integration tests 可直接构造 accepted / rejected / kept 后的候选报告与治理日志；run_benchmark 可证明完整报告通过 | 无外部凭证；依赖上一轮 governance schema | `content:llm-enhancement-candidates` 接受合法 governed status；新增 `content:weapon-candidate-governance` 对可选治理产物做 schema / 配对 / cross-reference 检查 | 本轮 |
| B. Existing Harness raw signals 瘦身 | 上一轮 Gate | 再次进入已有 Harness 时先看到精炼中文维护摘要，raw signals 只作为审计定位，不压过用户动作 | README / init workflow 已说明维护状态摘要和分项 signals；CLI 仍输出较多 raw 字段 | 输出密度高，用户可能难以聚焦第一动作 | 提升 CLI 可读性，但不修复契约正确性 | 中等；主要是 transcript 文案调整，容易造成测试漂移 | guided init integration transcript 可验证 | 无外部依赖 | 维护入口输出顺序和分组更清晰，测试覆盖关键摘要和 shortcut | 下一轮候选 |
| C. Full regression / push 工作包 | Gate / git 状态 | 完整迁移与目标模式本地提交形成可同步批次后，运行 full regression 并 push | 当前 main ahead origin 58，最新提交未 push；commit 前均有 fast regression | push 需要 `scripts/test-full.sh`，可能依赖真实 DeepSeek / `.benchmarks` / 网络 | 同步远端，但不直接增强 init North Star 能力 | 高；外部凭证和真实仓库可能阻塞 | full regression、git push、可选 CI 查询 | 需要外部服务可用 | full regression 通过后 push | 等形成更完整工作包后处理 |

排序结论：

1. 选择 A，因为它直接保护上一轮已经交付给 Maintainer 的 `review-initial-candidate` 工作流。如果 benchmark 仍把所有候选固定理解为未治理状态，用户完成治理后会得到错误质量信号，破坏 init North Star 中“可审计、可持续演进”的闭环。
2. B 是用户体验优化，但当前已有摘要和 triage 可用；相比 A，它不阻塞治理链路的正确性。
3. C 是同步节奏问题，不是本轮产品 / 工程价值切片；按 AGENTS 和 playbook，push 前需要 full regression，本轮先继续本地小步 commit。

本轮 milestone：

作为 Harness Maintainer，当我在已有 Harness 入口对初始 LLM Guide / Sensor 候选执行 accepted / rejected / kept 后再运行 benchmark，我可以得到一个校验 candidate report、governance log 和 Markdown 审查材料一致性的质量门禁结果，从而信任候选治理债已经被正确接管，而且 Builder 没有越界修改正式 Harness 资产或 Runtime 产物。

## 验收标准

1. `content:llm-enhancement-candidates` 不再要求所有候选永远保持 pending；它必须接受合法的 `candidate` / `confirmed` / `rejected` 状态，并校验 `human_confirmation_required` 与状态一致。
2. `content:llm-enhancement-candidates` 必须检查 summary / guide / sensor Markdown 包含候选 id、当前 status 和 `review_only_no_formal_asset_change` 边界；缺失时报告具体 `missing` detail。
3. benchmark 新增可选 `content:weapon-candidate-governance` 检查；不存在时不失败，存在时必须校验 YAML / Markdown 成对、`WeaponCandidateGovernanceLog` schema、source report、candidate id / type、previous / new status、decision 与 report 当前状态的一致性、review-only 边界和 Markdown 章节。
4. `accepted` 必须对应 report 中 `status=confirmed`、`human_confirmation_required=false`；`rejected` 必须对应 `status=rejected`、`human_confirmation_required=false`；`kept` 必须对应 `status=candidate`、`human_confirmation_required=true`。
5. 完整 `run_benchmark()` 在候选治理后仍可通过，且不创建 `.ai/task-runs`、不要求正式 Guide / Sensor 被自动修改。
6. 更新 README / engineering docs 中 benchmark 可选 artifact 规则，并在 `docs/evolution-log.md` 记录本轮稳定决策、验证结果和 Gate 结论。

## 决策

- 初始 LLM candidates 的 governance artifact 独立于 `.ai/review/asset-candidates.yaml`，benchmark 也使用独立 check id，避免把“确认初始候选方向”和“应用正式资产候选”混为一谈。
- benchmark 不把缺失 `weapon-candidate-governance.*` 当失败，因为未审查初始候选仍是合法初始状态；但只要出现 YAML 或 Markdown 任一文件，就必须按可选 review artifact 的规则严格校验。
- 本轮不新增 standalone CLI 命令、不修改 `review-initial-candidate` 行为、不把 accepted candidate 自动写入正式 Guide / Sensor。

## Assumptions / Risks

- `accepted` 表示 Maintainer 确认候选方向有价值，不表示正式资产已经应用；因此 benchmark 只校验 review-only 治理一致性，不要求正式 Guide / Sensor 出现新内容。
- `previous_status` 只能通过 governance log 自身证明历史状态；当前 report 只保存最终状态，所以 benchmark 校验 decision -> new_status -> 当前 report 的一致性。
- sub agent 使用按 playbook 尝试，但当前环境返回 `agent thread limit reached`；本轮由主线程完成调研和实现。
