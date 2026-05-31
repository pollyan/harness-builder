# Project Context Evidence Context Gate 迁移设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/local-unique-capability-migration.md`、`docs/engineering/init-workflow.md`、`docs/engineering/llm-contracts.md`、`docs/engineering/testing-strategy.md`、`docs/engineering/sensor-and-gate-rules.md`。
- 已对比：当前 `asset_writers/guides.py`、`asset_writers/reports.py`、`benchmark.py`、`ProjectInventory` / `ScanMetadata` schema、`tests/unit/test_write_assets.py`、`tests/integration/test_benchmark_command.py`。
- 已查旧分支：`backup/local-61-before-migration` 中存在 `content:project-context-evidence-context`、`_inventory_evidence_paths()` 和 Guide 的 `## LLM 证据扩展` 旧实现，但旧实现依赖当前 schema 不存在的 `inventory.test_files` / `risk_files` / `api_entrypoints` / `llm_requested_files` 字段，并读取旧字段 `evidence_expansion_plan`。
- 按需未展开：architecture 未展开，因为本轮不调整模块边界或目录结构；acceptance 未运行，因为本轮不改真实 LLM prompt 或外部服务调用。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Project Context evidence context gate | todo / Gate / 旧分支 | `.ai/guides/project-context.md` 保留扫描来源证据、文档/配置/CI evidence，以及 LLM evidence expansion 的 requested/read paths、risk focus、confidence、rationale；benchmark 能发现漂移 | 当前 Guide 有 `## 来源证据`，但只渲染 `inventory.evidence`；`ScanMetadata.evidence_expansion` 已存在；benchmark 还没有该 check | LLM 深扫计划和补读结果已经落在机器 metadata 中，但没有稳定进入 Maintainer 首看的 project-context，也没有 quality gate 防止丢失 | 把 evidence 深度从内部 schema 推到用户可审计 Guide，并让维护入口已有 project-context evidence triage 真正有来源 | 中：新增 hard benchmark check，必须同步生成侧，避免新生成 Harness 自己失败 | unit writer 断言 Guide 内容；integration benchmark 正向和 missing section/path/rationale 负向 | 依赖当前 `scan_metadata.evidence_expansion` 字段；不依赖真实 LLM | 本轮 |
| B. Scan report evidence visibility | todo / evidence depth | `.ai/scan-report.md` 展示 coverage、stack validation、warnings、risk/test/API/document/LLM requested evidence，便于审计 scan 过程 | 当前 scan report 只列 repo、primary stack、`inventory.evidence` 和 commands | scan report 仍不足以承载完整 deep scan 审计 | 让 scan artifact 本身更接近 North Star 的“解释判断依据” | 中高：会改 report 结构和可能新增 benchmark check | unit/integration 检查 scan-report 稳定章节和字段 | 与 A 共用 evidence 数据，但交付面不同 | 下一轮候选 |
| C. Init summary evidence audit | todo / init North Star | 初始化交付摘要能用人话概括 LLM requested evidence 和未确认深扫风险 | 当前 summary 已有成熟度、待人工确认、benchmark readiness；evidence expansion 主要在 metadata/questionnaire/CLI guided 展示 | summary 未直接暴露 requested/read evidence 审计摘要 | 用户不打开 scan-metadata 也能理解深扫发生了什么 | 中：会影响 completion message/summary 断言 | integration/guided init transcript 和 init-summary benchmark | 应等 A/B 稳定后合并，避免 summary 承载过多细节 | 后续候选 |
| D. Failed check detail preservation | todo / benchmark quality | benchmark failed checks 的 missing/errors/detail 在维护入口和 report 中保持完整 | 近期已迁移 weak command、risk context 和 maintenance preview 的 detail | 仍需系统性审查是否所有 failed check 都有可行动 detail | 提升已有 Harness 维护入口诊断体验 | 中：涉及多个 check 的报告形态 | integration 逐项 failed check detail | 与 evidence depth 主线相关但不是同一数据流 | 后续候选 |

排序结论：

1. 选择 A，因为它直接消化当前迁移 todo 中尚未完成的 `project-context evidence context gate`，也是 `init-north-star.md` “深度优先 / 可解释 / 可审计”的最短闭环：scan metadata 已经有深扫信息，Guide 和 benchmark 正好缺最后一跳。
2. B 和 C 同样重要，但分别改变 scan report 和交付摘要。它们可以复用 A 沉淀的 evidence 读取 helper，适合下一轮继续推进，避免本轮同时改变多个用户入口。
3. D 属于维护入口诊断质量，不应挤占 evidence 深度主线；保留在迁移 todo 后续。

## 本轮 milestone

作为 Harness Maintainer，当我运行 `init` 或 `benchmark` 审查一个刚生成的 Harness 时，我可以在 `.ai/guides/project-context.md` 看到扫描来源证据和 LLM evidence expansion 的 requested/read paths、risk focus、confidence 与 rationale，并且 `benchmark-report.yaml` 会用 `content:project-context-evidence-context` 防止这些证据上下文从 Guide 中丢失，从而让我能审计系统为什么深入读取了这些文件、哪些路径支撑了项目理解。

## 验收标准

- `project-context.md` 的 `## 来源证据` 不只包含 `inventory.evidence`，还包含 `inventory.documents`、`inventory.configs` 和 `inventory.ci_files` 中的路径，并保留 `reason` 或 `kind`。
- `project-context.md` 保留稳定章节 `## LLM 证据扩展`。
- 当 `scan_metadata.evidence_expansion` 缺失时，Guide 显示 `evidence_expansion=not_run`，benchmark 通过该边界。
- 当 `scan_metadata.evidence_expansion` 存在时，Guide 显示 `requested_paths`、`read_paths`、`risk_focus`、`confidence`、`read_file_count` 和 `rationale`。
- `benchmark` 报告包含 `content:project-context-evidence-context`。
- 缺失 `## 来源证据`、任一应出现的 evidence path、`## LLM 证据扩展`、requested/read path、risk focus、confidence 或 rationale 时，该 check 失败并在 `missing` 中保留精确原因。
- 新增测试必须覆盖 writer 正向、benchmark 正向和关键负向，不只断言文件存在。
- 相关 README、engineering docs、todo 和 evolution log 同步说明该 gate。

## 决策 / 取舍

- 适配当前 schema：读取 `inventory.evidence`、`documents`、`configs`、`ci_files` 和 `stack_extensions["scan_metadata"]["evidence_expansion"]`，不恢复旧分支中已经不存在的 `ProjectInventory.test_files` / `risk_files` / `api_entrypoints` / `llm_requested_files` 字段。
- LLM requested/read paths 通过 `scan_metadata.evidence_expansion` 校验，不把它们强塞进 `ProjectInventory` 顶层字段，避免为了 benchmark 改动机器契约。
- 本轮只让 project-context 承载 evidence expansion 审计；scan-report 和 init-summary 的完整 evidence 可视化作为下一轮候选。
- 新 check 属于 hard benchmark check，因为它验证的是生成资产和上游 scan metadata 的可审计一致性。

## Assumptions / Risks

- 当前 `scan_metadata.evidence_expansion` 是 evidence planner 的事实源；旧字段 `evidence_expansion_plan` 不再作为主路径，但 helper 可兼容读取以降低旧 Harness 迁移摩擦。
- 老 Harness 若没有 `## LLM 证据扩展` 会被 benchmark 标记 failed；这是有意暴露旧资产缺少审计章节，而不是 silent fallback。
- 如果真实仓库 evidence 列表很长，本轮只校验当前 inventory 明确保留的 evidence/doc/config/CI 路径和 evidence expansion 路径，coverage bucket 的 `selected_paths` 暂不进入硬校验，避免一次性扩大失败面。
- Sub agent 使用：按目标模式要求尝试启动 explorer 做只读调研，但当前返回 `agent thread limit reached`，本轮由主线程完成对比、迁移和验证。
