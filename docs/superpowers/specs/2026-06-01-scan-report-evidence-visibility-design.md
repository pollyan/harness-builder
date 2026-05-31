# Scan Report Evidence Visibility 迁移设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/local-unique-capability-migration.md`、`docs/engineering/init-workflow.md`、`docs/engineering/llm-contracts.md`、`docs/engineering/testing-strategy.md`、`docs/engineering/sensor-and-gate-rules.md`。
- 已对比：当前 `asset_writers/reports.py`、`asset_writers/guides.py`、`benchmark.py`、`init_summary.py`、`ProjectInventory` / `ScanMetadata` schema、`tests/unit/test_asset_writer_reports.py`、`tests/integration/test_benchmark_command.py`、`tests/integration/test_init_on_fixture_projects.py`。
- 已查旧分支：`backup/local-61-before-migration` 中有更完整的 `_scan_report()` 和 `content:scan-report` check，可迁移章节结构包括 Evidence Coverage、Stack Evidence Validation、Scan Warnings、Risk Areas；旧实现读取当前 schema 不存在的 `inventory.test_files` / `risk_files` / `api_entrypoints` / `llm_requested_files` 和旧字段 `evidence_expansion_plan`，需要适配当前 `scan_metadata.evidence_expansion` 与 coverage bucket。
- 按需未展开：architecture 未展开，因为本轮不调整模块边界；acceptance 未运行，因为不改真实 LLM prompt、DeepSeek 调用或外部仓库验收。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Scan report evidence visibility | todo / 上轮 Gate / 旧分支 | `.ai/scan-report.md` 展示来源证据、coverage bucket、selected paths、stack validation、scan warnings、risk areas、LLM evidence expansion 和命令置信度；benchmark 防止 report 退化 | `scan-metadata.yaml` 已有 coverage / warnings / evidence_expansion，project-context 已展示 evidence expansion | scan report 仍只列 repo、primary stack、少量 evidence 和 command；benchmark 没有 `content:scan-report` | 让 scan artifact 本身成为可审计交付物，避免 Maintainer 必须读 JSON/YAML 才理解 scan 深度 | 中：新增 benchmark hard check，需要同步生成侧避免新 Harness 自己失败 | unit report writer 正向；integration benchmark check id 和缺章节 / 缺 path 负向 | 不依赖外部服务；依赖当前 `scan_metadata` 结构 | 本轮 |
| B. Init summary evidence audit | todo / 上轮 Gate | 交付摘要用简短中文说明 LLM requested evidence、read paths 和低置信度影响 | init-summary 已有成熟度、待确认、benchmark readiness；CLI guided 已展示 LLM 深度补充 | summary 尚未概括深扫审计细节 | 用户不打开 scan-report / metadata 也能理解深扫发生了什么 | 中：影响 completion message 与 summary，需避免摘要过长 | init-summary unit / guided integration | 最好基于更完整 scan-report 稳定后推进 | 下一轮候选 |
| C. Failed check detail preservation | todo / benchmark quality | 所有 failed check 的 missing/errors/detail 都能被 report 与维护入口消费 | 近期已迁移 weak command、risk context、project-context evidence detail | 仍缺系统性审查 | 提升已有 Harness 维护入口诊断能力 | 中：跨多个 check | integration 逐项 failed detail | 与 evidence visibility 不是同一数据流 | 后续候选 |
| D. Evidence helper 去重 | Self-Harness Gate | Guide、Report、Benchmark 共享 evidence expansion/path 提取逻辑 | 当前上一轮新增了 guides.py 与 benchmark.py 的相似 helper | 本轮 report 若再复制会增加维护成本 | 降低后续 scan evidence 迭代成本 | 中低：重构需保持现有测试绿 | unit/integration 回归 | 可作为 A 的轻量内部实现，但不单独成 milestone | 随 A 小范围处理或后续 |

排序结论：

1. 选择 A，因为它直接承接上轮 Gate 和迁移 todo 的 Scan evidence 可审计细节；project-context 已经展示 evidence expansion，但 scan-report 这个扫描审计产物仍薄，用户无法从 report 理解 coverage、warnings、risk 和 stack validation。
2. B 有用户价值，但应等 scan-report 先成为稳定审计来源后再摘要化，避免 summary 承载过多低层细节。
3. C 与 D 保留后续；D 如能小范围复用 helper 可作为实现取舍，但不扩大为本轮主目标。

## 本轮 milestone

作为 Harness Maintainer，当我查看 `init` 生成的 `.ai/scan-report.md` 或运行 `benchmark` 验收 Harness 时，我可以看到本次扫描的 evidence coverage、selected paths、LLM evidence expansion、stack validation、scan warnings、risk areas 和命令候选置信度；如果这些 scan 审计信息从 report 中丢失，benchmark 会用 `content:scan-report` 给出具体 missing detail，从而让我不用直接读多份 JSON/YAML 也能审计仓库理解深度。

## 验收标准

- `.ai/scan-report.md` 保留稳定章节：`## Evidence`、`## LLM Evidence Expansion`、`## Evidence Coverage`、`## Stack Evidence Validation`、`## Scan Warnings`、`## Risk Areas`、`## Command Candidates`。
- `## Evidence` 合并 inventory evidence、documents、configs、ci_files，并保留 path 与 reason/kind。
- `## LLM Evidence Expansion` 展示 `requested_paths`、`read_paths`、`risk_focus`、`confidence`、`read_file_count`、`rationale`；未执行时显示 `evidence_expansion=not_run`。
- `## Evidence Coverage` 展示 detected/selected 数、bucket selected/total/skipped，以及每个 bucket 的 selected_paths，覆盖 test/risk/API/document evidence 的可见性。
- `## Stack Evidence Validation` 展示 checked/supported/unsupported stack claim。
- `## Scan Warnings` 展示 warning code、severity、message 和 evidence。
- `## Risk Areas` 展示 scan risk path/reason。
- `## Command Candidates` 展示 command id、type、gate、source、confidence。
- `benchmark` 报告包含 `content:scan-report`；缺章节、缺 evidence path、缺 coverage selected path、缺 evidence expansion detail、缺 warning/risk/command confidence 时该 check 失败并保留 `missing`。
- README、engineering docs、迁移 todo 和 evolution log 同步说明该 scan-report 质量门禁。

## 决策 / 取舍

- 适配当前 schema，不恢复旧 `ProjectInventory.test_files` 等顶层字段；test/risk/API/document evidence visibility 先通过 `scan_metadata.coverage.bucket_coverage[].selected_paths` 展示。
- 本轮不新增新的 Pydantic schema；`scan-report.md` 是语义上下文产物，benchmark 负责稳定章节和关键细节校验。
- 本轮不改 LLM prompt、planner 策略、evidence collector 采样预算或真实 acceptance。
- 本轮不把 scan-report 内容塞进 init-summary；summary evidence audit 作为下一轮候选。

## Assumptions / Risks

- `scan_metadata.coverage` 是当前 coverage bucket 的事实源；如果旧 Harness 没有 coverage，report 显示 `evidence_coverage=not_available`，benchmark 不要求 bucket detail。
- 当前 `scan_metadata.evidence_expansion` 是 LLM evidence planner 的事实源；旧字段 `evidence_expansion_plan` 可兼容读取，但不是主路径。
- 新增 `content:scan-report` 会让手工删掉 scan-report 审计章节的旧 Harness benchmark failed，这是有意暴露质量退化。
- Sub agent 使用：按目标模式要求尝试启动只读审查，但当前返回 `agent thread limit reached`，本轮由主线程完成对比、TDD 和实现。
