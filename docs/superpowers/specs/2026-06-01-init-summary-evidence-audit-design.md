# Init Summary Evidence Audit 迁移设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/local-unique-capability-migration.md`。
- 已读取相关工程文档：`docs/engineering/init-workflow.md`、`docs/engineering/llm-contracts.md`、`docs/engineering/testing-strategy.md`、`docs/engineering/sensor-and-gate-rules.md`。
- 已对比当前代码与测试：`init_summary.py`、`benchmark.py`、`asset_writers/guides.py`、`asset_writers/reports.py`、`interactive_init.py`、`tests/unit/test_init_summary.py`、`tests/integration/test_benchmark_command.py`、上一轮 scan-report / project-context evidence specs 和 plans。
- 按需未展开：`architecture.md` 未展开，因为本轮不调整模块边界；acceptance 未运行，因为不改 LLM prompt、DeepSeek 调用、真实仓库扫描或 Runtime 契约。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Init Summary evidence audit | todo / 上轮 Gate | 首次 init 交付入口用中文摘要展示 LLM evidence expansion 和 coverage selected paths，并指向 scan-report / metadata 深查 | CLI guided 已展示 LLM 深度补充；project-context 和 scan-report 已渲染 evidence expansion 且 benchmark 守住 | `init-summary.md` 仍只列仓库事实、成熟度、待确认和 benchmark readiness，没有“本次深扫看了哪些补充证据”的交付摘要 | Maintainer 不打开多份 YAML/Markdown 也能在入口摘要理解扫描深度、补读路径和证据覆盖边界 | 中低：只改 Markdown 语义产物和 benchmark 内容检查，不改 schema / LLM | unit 覆盖 summary 正向；benchmark integration 覆盖缺 summary audit detail 失败 | 依赖当前 `scan_metadata.evidence_expansion` 和 coverage；不依赖外部服务 | 本轮 |
| B. Failed check detail preservation system audit | todo / Gate | benchmark 每个 failed check 的 missing/errors/weak detail 都能进入 report 和维护入口 | BenchmarkReport schema 已保留 errors/missing/weak_commands；维护入口已展示 failed detail | 还缺跨所有 check 的系统性审查，不确定是否有遗漏 | 提升已有 Harness 维护入口诊断可信度 | 中：跨多个 check 和 CLI 输出，范围更大 | unit / integration 逐 check 构造失败报告 | 不依赖外部服务，但需要更广 checklist | 后续候选 |
| C. Evidence helper 去重 | Gate 技术债 | report、guide、summary、benchmark 共享 evidence expansion / coverage 提取逻辑 | 当前 reports.py、guides.py、benchmark.py 已有相似 helper | 继续在 summary 加 helper 会增加重复 | 降低后续维护成本 | 中：重构跨 writer / benchmark，容易扩大变更面 | 现有 writer / benchmark 回归 | 可在后续专门重构 | 后续候选 |
| D. Evidence reason preservation 深化 | todo | 顶层记录 test/risk/API/document evidence reason，而不只展示 path | scan-report 已通过 coverage selected paths、risk areas、documents/configs/CI 展示 | 没有新增顶层 inventory 字段承载更细 reason | 后续更深扫描审计 | 中高：可能涉及 schema / scanner / reconciler | schema、unit、integration、acceptance | 需要先明确字段契约 | 暂缓 |

排序结论：

1. 选择 A，因为它直接承接迁移 todo 中“LLM requested evidence 在 scan report、project-context 和 init summary 中的审计展示”的最后一环；前两轮已经稳定了 scan-report 和 project-context，当前适合把同一事实源摘要化到交付入口。
2. B 有价值，但当前已有多处 detail preservation 能力，下一步应先做系统审计，避免在本轮顺手扩散。
3. C 是真实技术债，但单独做 helper 重构没有直接用户价值；若本轮局部 helper 重复过多，只记录到 Gate。
4. D 可能需要 schema 设计，超出当前迁移小切片。

## 本轮 milestone

作为首次运行 `init` 后阅读 `.ai/init-summary.md` 的 Harness Maintainer，当本次扫描执行了 LLM-guided evidence expansion 或记录了 coverage selected paths 时，我可以在入口摘要中看到请求补读路径、实际读取路径、风险关注点、置信度、读取数量、rationale 和关键 coverage selected paths，并且 benchmark 会在这些摘要丢失时报告 `content:init-summary` missing detail，从而把首次交付摘要和深度扫描审计链路连接起来。

## 验收标准

- `.ai/init-summary.md` 保留稳定 `## 扫描证据审计` 章节。
- 当 `ProjectInventory.stack_extensions.scan_metadata.evidence_expansion` 存在时，summary 展示 requested paths、read paths、risk focus、confidence、read file count 和 rationale。
- 当 `scan_metadata.coverage` 存在时，summary 展示 `evidence_selected=<selected>/<detected>`，并列出前几个 bucket selected paths。
- 未执行 evidence expansion 或 coverage 不可用时，summary 显式显示 `evidence_expansion=not_run` / `evidence_coverage=not_available`，不伪装成深扫成功。
- `benchmark` 的 `content:init-summary` 在 inventory 包含 evidence expansion 或 coverage selected paths 时校验该章节和关键 detail；缺失时保留 `missing_*` detail。
- README、init workflow、LLM contracts、testing strategy、sensor/gate rules、迁移 todo 和 evolution log 同步稳定契约。

## 决策 / 取舍

- 本轮不新增机器 schema；`init-summary.md` 是语义入口，机器事实仍来自 `scan-metadata.yaml` / `project-inventory.json`。
- Summary 只做摘要，完整审计仍在 `.ai/scan-report.md` 和 `.ai/scan-metadata.yaml`；coverage selected paths 最多展示少量条目，避免入口报告过长。
- Benchmark 只在 inventory 中确实存在 evidence expansion / coverage 时要求对应 detail；旧 Harness 没有这些 metadata 时不要求伪造细节。
- 本轮不改 LLM planner、scanner、reconciler、prompt 或真实 acceptance。

## Assumptions / Risks

- Assumption：`init-summary.md` 是首次 init 后最先被团队阅读和转发的入口，因此应能摘要说明“本次深扫补读了什么”。
- Risk：新增章节会让手工删改过 summary 的旧 Harness benchmark failed；这是内容契约升级，用于暴露交付摘要漂移。
- Risk：当前 evidence helper 在 reports / guides / benchmark / summary 之间会继续有重复；本轮控制范围，Gate 中保留去重候选。
- Sub agent 使用：尝试启动只读 explorer 审查下一迁移切片，但当前环境返回 `agent thread limit reached`，本轮由主线程完成分析、TDD、实现和验证。
