# Harness Builder 演进记录

## 2026-06-01 Content Quality Detail Preservation 迁移

- North Star 模块：Benchmark / Review Intelligence、CLI Experience、Maturity & Evolution。
- init North Star 旅程阶段：已有 Harness 维护；质量门禁解释；语义资产可审计。
- Gap Analysis 摘要：当前唯一 high priority 迁移 todo 仍是本地独有 / 更细能力合并与迁移。scan-report、init-summary、project-context、risk context 和 hard gate command 已逐步保留 missing/errors/weak detail，但 `content:workflow-skills`、`content:guides-quality`、`content:sensors-quality` 和 `content:stack-specific-guides` 仍只返回 `passed=false`，维护者无法从 benchmark report 直接知道缺哪个章节、marker 或 weapon id。
- 用户故事：作为 Harness Maintainer，当我运行 `benchmark` 发现 Guide、Sensor、Workflow Skill 或 stack-specific Guide 内容质量失败时，我可以在 `benchmark-report.yaml` 中看到具体缺失章节、缺失 workflow skill marker 或缺失 weapon id，从而知道应该修哪份语义资产，而不是只看到 `passed=false`。
- 当前代码 gap：四个内容质量 check 的 pass/fail 判断存在，但没有填充 `BenchmarkReport` schema 已支持的 `missing` 字段。
- 关键决策 / 取舍：不新增 schema，不改变 writer 输出，不改变 pass/fail 语义；复用 `missing` 字段承载缺失文件、缺失 marker、缺失章节和缺失 weapon id。
- Assumptions / risks：旧 benchmark report 不会 retroactively 获得 detail；新 report 与维护入口已能消费 `missing`。本轮只覆盖最常见的老内容质量 check，系统性全量审计仍保留为后续 gap。
- Sub agent 使用情况：尝试启动只读 explorer 审查本轮候选，但当前环境返回 `agent thread limit reached`；本轮由主线程完成分析、TDD、实现和验证。
- 价值切分说明：本轮是 failed check detail preservation 的一个纵向小切片，直接保护 benchmark 失败诊断工作流，不混入 scanner schema、writer 生成逻辑或 Runtime。
- 可执行验收标准及验证方式：integration 负向测试断言 Guide 缺章节、standard Workflow Skill 文件缺失、Sensor 缺章节 / hard marker 时，对应 content check 均返回可行动 `missing` detail；stack-specific Guide 缺 weapon id 时返回具体 weapon id。
- 完成内容：`_workflow_skills_check()`、`_guide_quality_check()`、`_sensor_quality_check()` 和 `_stack_specific_guide_check()` 保留 missing detail；README、sensor/gate rules、testing strategy、迁移 todo、spec 和 plan 同步。
- 验证结果：targeted integration 已通过；fast regression 见本轮提交前验证。
- Self-Harness Gate：Runtime 边界未变化，未执行任务、不创建 `.ai/task-runs`。下一轮候选 gap：failed check missing / errors / detail preservation 系统性全量审计，或 evidence reason preservation。

## 2026-06-01 Scan Evidence Failed Check Triage 迁移

- North Star 模块：CLI Experience、Benchmark / Review Intelligence、Maturity & Evolution。
- init North Star 旅程阶段：再次进入已有 Harness；质量门禁解释和维护建议。
- Gap Analysis 摘要：当前迁移 todo 仍 open，上一轮新增 `content:scan-report` 与 `content:init-summary` 后，benchmark report 已保留 missing detail，但已有 Harness 维护入口对这两个新 check id 仍缺少中文 label 和专门 triage reason。本轮候选包括 scan evidence failed check triage、failed check detail preservation 系统审计和 evidence helper 去重，优先选择 scan evidence triage，因为它直接补齐新门禁的用户可见解释。
- 用户故事：作为再次运行 guided `init` 进入已有 Harness 维护入口的 Harness Maintainer，当最近 benchmark 因 `content:scan-report` 或 `content:init-summary` 失败时，我可以在 Benchmark signals 和 Maintenance triage guidance 中看到中文解释、具体 missing detail 和下一步动作，从而知道要补齐 scan-report / init-summary 的扫描证据审计。
- 当前代码 gap：`_benchmark_failed_check_label()` 对 `content:scan-report` 和 `content:init-summary` 返回泛化“查看 benchmark-report.yaml”；`build_maintenance_triage()` 只专门处理 hard gate、risk context 和 project-context evidence，scan evidence 失败被归入泛化 schema/content failed checks。
- 关键决策 / 取舍：不改 BenchmarkReport schema，不改变 benchmark pass/fail；只把两个近期新增的 scan evidence check 专门化为 `reason=scan_evidence_audit_incomplete`，detail 取第一条 missing，完整列表仍在 benchmark report。
- Assumptions / risks：维护入口是已有 Harness 诊断的第一视图；多个 scan evidence check 同时失败时只展示第一条 missing detail，避免 triage 过长。
- Sub agent 使用情况：尝试启动只读 explorer 审查本轮候选，但当前环境返回 `agent thread limit reached`；本轮由主线程完成分析、TDD、实现和验证。
- 价值切分说明：本轮是 failed check detail preservation 的一个小而完整切片，不做全量 benchmark check 审计，也不重构 evidence helper。
- 可执行验收标准及验证方式：unit 覆盖 Benchmark signals 的中文 label / missing detail，以及 Maintenance triage 的 reason/source/detail/guidance。
- 完成内容：为 `content:scan-report`、`content:init-summary` 增加中文 failed check label；Maintenance triage 新增 `scan_evidence_audit_incomplete`；README、init workflow、迁移 todo、spec 和 plan 同步。
- 验证结果：targeted unit 通过；fast regression 见本轮提交前验证。
- Self-Harness Gate：Runtime 边界未变化；下一轮候选 gap：failed check missing / errors / detail preservation 系统性全量审计，或 evidence helper 去重。

## 2026-06-01 Init Summary Evidence Audit 迁移

- North Star 模块：Deep Scan Evidence、CLI Experience、Maturity & Evolution、Benchmark / Review Intelligence。
- init North Star 旅程阶段：写入后的交付摘要；扫描理解可解释；质量门禁解释。
- Gap Analysis 摘要：当前唯一 open todo 仍是本地独有 / 更细能力迁移。project-context 和 scan-report 已经展示并由 benchmark 守住 LLM evidence expansion，但首次交付入口 `.ai/init-summary.md` 还没有摘要化展示 requested/read paths、risk focus、confidence、read file count、rationale 或 coverage selected paths。本轮候选包括 init-summary evidence audit、failed check detail preservation、evidence helper 去重和 evidence reason preservation，优先选择 init-summary，因为它补齐迁移 todo 中 “LLM requested evidence 在 scan report、project-context 和 init summary 中的审计展示” 的最后一环。
- 用户故事：作为首次运行 `init` 后阅读 `.ai/init-summary.md` 的 Harness Maintainer，当本次扫描执行了 LLM-guided evidence expansion 或记录了 coverage selected paths 时，我可以在入口摘要中看到请求补读路径、实际读取路径、风险关注点、置信度、读取数量、rationale 和关键 coverage selected paths；如果这些摘要丢失，benchmark 会用 `content:init-summary` 给出具体 missing detail。
- 当前代码 gap：`build_init_summary_markdown()` 没有扫描证据审计章节；`benchmark.py` 的 `content:init-summary` 只检查成熟度、确认入口和 benchmark readiness；`assess_maturity()` 会重写 `init-summary.md` 且没有传入 inventory / commands，导致 benchmark 前刷新会丢失扫描上下文。
- 关键决策 / 取舍：不新增 schema，继续以 `scan-metadata.yaml` / `project-inventory.json` 为机器事实源；summary 只做摘要，完整审计仍在 scan-report 和 scan-metadata；benchmark 只在 inventory 存在 evidence expansion / coverage 时要求对应 detail。
- Assumptions / risks：`init-summary.md` 是首次 init 后最容易被团队转发的入口，因此应承接深扫摘要；旧 Harness 手工删掉该章节会被 benchmark 标记 failed，这是内容契约升级。
- Sub agent 使用情况：尝试启动只读 explorer 审查下一迁移切片，但当前环境返回 `agent thread limit reached`；本轮由主线程完成分析、TDD、实现和验证。
- 价值切分说明：本轮只连接 init-summary 与扫描证据审计，不做 scanner schema 深化或 failed check detail 全量审计；evidence helper 去重保留为后续技术债候选。
- 可执行验收标准及验证方式：unit 覆盖 init-summary 正向渲染；benchmark integration 覆盖完整 audit 通过和缺 audit section / detail 失败；fast regression 作为提交前验证。
- 完成内容：`init-summary.md` 新增 `## 扫描证据审计`；`assess_maturity()` 刷新 summary 时保留 inventory / commands；`content:init-summary` 校验 evidence expansion detail 和 coverage selected paths；README、init workflow、LLM contracts、testing strategy、sensor/gate rules、迁移 todo、spec 和 plan 同步。
- 验证结果：targeted unit / integration 已通过；fast regression 见本轮提交前验证。
- Self-Harness Gate：长期文档已同步；Runtime 边界未变化，未执行任务、不创建 `.ai/task-runs`。下一轮候选 gap：failed check missing / errors / detail preservation 系统审计，或 evidence helper 去重。

## 2026-06-01 Scan Report Evidence Visibility 迁移

- North Star 模块：Deep Scan Evidence、Benchmark / Review Intelligence、Maturity & Evolution。
- init North Star 旅程阶段：扫描理解可解释；写入后的扫描审计报告；质量门禁解释。
- Gap Analysis 摘要：当前唯一 open todo 仍是本地独有 / 更细能力迁移。上一轮已把 LLM evidence expansion 推到 project-context 并由 benchmark 守住，但 `.ai/scan-report.md` 仍只展示 repo、primary stack、少量 evidence 和 commands，无法承载 coverage、stack validation、warnings、risk areas 或 LLM requested evidence 的审计。本轮候选包括 scan-report evidence visibility、init-summary evidence audit、failed check detail preservation 和 evidence helper 去重，优先选择 scan-report，因为它是扫描链路最直接的审计产物。
- 工程信任故事：作为 Harness Maintainer，当我查看 `.ai/scan-report.md` 或运行 `benchmark` 验收 Harness 时，我可以看到 evidence coverage、selected paths、LLM evidence expansion、stack validation、scan warnings、risk areas 和命令候选置信度；如果这些审计信息丢失，benchmark 会用 `content:scan-report` 给出具体 missing detail。
- 当前代码 gap：`asset_writers/reports.py` 的 `_scan_report()` 只列 `inventory.evidence` 和 command；`benchmark.py` 没有 `content:scan-report`；旧分支实现更完整但依赖当前 schema 不存在的顶层 evidence 字段和旧 `evidence_expansion_plan` 字段。
- 关键决策 / 取舍：适配当前 `scan_metadata.coverage`、`scan_metadata.evidence_expansion`、`scan_validation`、`scan_warnings` 和 `risk_areas`；test/risk/API/document evidence visibility 先通过 coverage bucket selected paths 和现有 inventory documents/configs/CI 展示，不新增 ProjectInventory 顶层字段。
- Assumptions / risks：旧 Harness 缺少 scan-report 审计章节会被 benchmark failed，这是有意暴露质量退化；本轮不改 LLM prompt、planner 策略或 evidence collector 预算。
- Sub agent 使用情况：尝试启动只读审查 agent，但当前 agent thread limit reached；本轮由主线程完成旧分支对比、TDD 和实现。
- 价值切分说明：本轮只强化 scan-report 与 benchmark，不把 init-summary evidence audit 混入；summary 可在下一轮基于稳定 scan-report 摘要化。
- 可执行验收标准及验证方式：unit 覆盖 report writer 的稳定章节和关键字段；benchmark integration 覆盖 Java fixture check id、完整 scan-report context 通过、缺章节、缺 coverage selected path、缺 evidence expansion detail 失败。
- 完成内容：`scan-report.md` 新增 Evidence、LLM Evidence Expansion、Evidence Coverage、Stack Evidence Validation、Scan Warnings、Risk Areas、Command Candidates 审计内容；benchmark 新增 `content:scan-report`；README、init workflow、LLM contracts、testing strategy、sensor/gate rules、迁移 todo、spec 和 plan 同步。
- 验证结果：targeted unit / integration 已通过；fast regression 见本轮提交前验证。
- Self-Harness Gate：长期文档已同步；Runtime 边界未变化，未执行任务、不创建 `.ai/task-runs`。下一轮候选 gap：init-summary evidence audit，或 failed check missing/errors/detail preservation。

## 2026-06-01 Project Context Evidence Context Gate 迁移

- North Star 模块：Deep Scan Evidence、Sensor & Quality Gate、Maturity & Evolution。
- init North Star 旅程阶段：扫描理解可解释；写入后质量门禁；Maintainer 审查 project-context 证据链。
- Gap Analysis 摘要：当前唯一 open todo 仍是本地独有 / 更细能力迁移。本轮候选包括 project-context evidence context gate、scan-report evidence visibility、init-summary evidence audit 和 failed check detail preservation。当前 `ScanMetadata.evidence_expansion` 已记录 LLM 深扫计划和读取结果，但 `project-context.md` 只渲染 `inventory.evidence`，benchmark 没有守住 evidence expansion 审计章节，因此优先补齐 project-context 的用户可见证据闭环。
- 工程信任故事：作为 Harness Maintainer，当我运行 `init` 或 `benchmark` 审查一个刚生成的 Harness 时，我可以在 `.ai/guides/project-context.md` 看到扫描来源证据和 LLM evidence expansion 的 requested/read paths、risk focus、confidence 与 rationale，并且 benchmark 会防止这些证据上下文从 Guide 中丢失。
- 当前代码 gap：Guide writer 没有 `## LLM 证据扩展`，来源证据未合并 documents/configs/CI；`benchmark.py` 没有 `content:project-context-evidence-context`；旧分支实现读取旧字段和旧 inventory 顶层 evidence 字段，不能直接 cherry-pick。
- 关键决策 / 取舍：适配当前 `scan_metadata.evidence_expansion`；只校验 inventory evidence/doc/config/CI 和 expansion requested/read/risk/confidence/rationale；coverage bucket 的 selected paths、scan-report 和 init-summary evidence audit 留作后续。
- Assumptions / risks：旧 Harness 缺少 `## LLM 证据扩展` 会被 benchmark 显式标记 failed；这是质量门禁而非 fallback。真实 LLM prompt 和 schema 不变。
- Sub agent 使用情况：尝试启动 explorer 做只读调研，但当前 agent thread limit reached；本轮由主线程完成旧分支对比、TDD 和实现。
- 价值切分说明：本轮只迁移 project-context evidence context gate，不把 scan-report 和 init-summary 的 evidence visibility 混入，避免一次改变多个交付入口。
- 可执行验收标准及验证方式：unit 覆盖 writer 正向章节和字段；integration 覆盖 Java fixture check id、完整 context 通过、缺 evidence path、缺 LLM section、缺 requested/read/rationale detail 失败。
- 完成内容：`project-context.md` 新增 `## LLM 证据扩展`；来源证据合并 evidence/documents/configs/CI；benchmark 新增 `content:project-context-evidence-context`；README、init workflow、LLM contracts、testing strategy、sensor/gate rules、迁移 todo、spec 和 plan 同步。
- 验证结果：targeted unit / integration 已通过；fast regression 见本轮提交前验证。
- Self-Harness Gate：长期文档已同步；Runtime 边界未变化，未执行任务、不创建 `.ai/task-runs`。下一轮候选 gap：scan-report evidence visibility，或 init-summary evidence audit，继续从迁移 todo 的 Scan evidence 可审计细节中选择。

## 2026-06-01 Risk Context Consistency Benchmark 迁移

- North Star 模块：Sensor & Quality Gate、Workflow Toolkit、Maturity & Evolution。
- init North Star 旅程阶段：写入后质量门禁；风险区域解释、验证策略和 Workflow routing 的一致性。
- Gap Analysis 摘要：当前唯一 open todo 仍是本地独有 / 更细能力迁移。本轮候选包括 risk context consistency、project-context evidence context gate 和 scan evidence reason/report visibility。当前维护入口已能识别 `content:risk-context-consistency`，Guide / Sensor 已渲染风险路径，但 benchmark 主体没有该 check，生成的 `harness-config.yaml` 也不会把扫描风险路径写入 standard escalation，因此优先补齐风险上下文质量门禁闭环。
- 工程信任故事：作为 Harness Maintainer，当我运行 `benchmark` 验收包含扫描风险区域的 Harness 时，我可以确认每个 scan risk path 同时出现在 project-context Guide、verification Sensor 和 standard escalation routing 中；如果任一环缺失，benchmark 会给出精确 `missing_*_risk:<path>` 错误。
- 当前代码 gap：`content:risk-context-consistency` 不存在；维护入口虽然有 risk context triage 分支，但没有 benchmark check 产生该信号；默认 config 只含泛化 `high_risk_module`，不含仓库具体风险路径。
- 关键决策 / 取舍：新增独立 `content:risk-context-consistency`，不塞进 `content:workflow-routing-policy`；routing 认可 `risk_area:<path>` trigger 或 rationale path；只取前 5 个风险路径，避免报告过长；不判断风险是否已人工确认。
- Assumptions / risks：`ProjectInventory.stack_extensions.risk_areas` 或 `llm_scan_proposal.risk_areas` 是 scan risk path 来源；旧 Harness 如果手工删掉 Guide / Sensor / routing 中任一风险路径，会被 benchmark 显式标为 failed。
- Sub agent 使用情况：尝试启动 explorer 做只读方案审查，但当前 agent thread limit reached；本轮由主线程对比旧分支实现和当前代码。
- 价值切分说明：本轮只迁移风险上下文一致性，不混入 project-context evidence context gate 或 scan evidence writer 深化。
- 可执行验收标准及验证方式：integration 覆盖生成风险路径时 benchmark 通过并写出 `risk_area:<path>` trigger；三类负向缺失分别报告 Guide、Sensor、Routing 缺失；Java fixture check id 列表包含 `content:risk-context-consistency`。
- 完成内容：`benchmark.py` 新增 `_risk_context_consistency_check()`；`write_assets.py` 新增 `build_harness_config()`，把扫描风险路径写入 standard escalation trigger / rationale；README、init workflow、sensor/gate 规则、testing strategy、迁移 todo、spec 和 plan 同步。
- 验证结果：targeted benchmark integration 已通过；fast regression 见本轮提交前验证。
- Self-Harness Gate：Runtime 边界未变化，未执行任务、不创建 `.ai/task-runs`。下一轮候选 gap 来自迁移 todo：project-context evidence context gate 与 Scan evidence 可审计细节可合并评估。

## 2026-06-01 Hard Gate Source Path Benchmark 迁移

- North Star 模块：Sensor & Quality Gate、Maturity & Evolution、Runtime Boundary。
- init North Star 旅程阶段：质量门禁解释；写入后通过 benchmark 判断第一版 Harness 是否可信。
- Gap Analysis 摘要：当前唯一 open todo 仍是本地独有 / 更细能力迁移。对比当前 main 与 `backup/local-61-before-migration` 后，本轮候选包括 hard gate source path 校验、risk context consistency、project-context evidence context gate。当前 main 已能展示 hard gate weak command detail，但 `_hard_gate_command_evidence_check()` 只检查 source 是否为空和 low confidence，不能发现 source 指向不存在文件或逃出目标仓库，因此优先补齐最小的 hard gate 可信来源校验。
- 工程信任故事：作为 Harness Maintainer，当我运行 `benchmark` 验收已有 Harness 时，如果 hard gate command 的 `source` 指向不存在文件或逃出目标仓库，我可以在 `benchmark-report.yaml` 的 `content:hard-gate-command-evidence` 中看到失败和 `weak_commands.reason`，从而知道该 hard gate 缺少可信来源证据，不能被当作已验证质量门禁。
- 当前代码 gap：`content:hard-gate-command-evidence` 对 `docs/testing.md` 这类不存在 source 或 `../outside.md` 这类仓库外 source 仍可能通过。
- 关键决策 / 取舍：复用现有 check id，不新增新 benchmark check；只验证 source path 可追溯，不执行命令；`BenchmarkReport` schema 继续兼容旧报告，但新生成的 weak command 会写 reason。
- Assumptions / risks：`CommandDefinition.source` 应是目标仓库内 evidence path；旧 Harness 如果写 URL、说明文本或组合路径，会被标记为不可追溯，需要 Maintainer 修正为仓库内文件。
- Sub agent 使用情况：尝试启动 explorer 做只读方案审查，但当前 agent thread limit reached；本轮由主线程对比旧分支实现。
- 价值切分说明：本轮只迁移 hard gate source path 校验，不把 risk context consistency 或 project-context evidence context gate 混入同一轮。
- 可执行验收标准及验证方式：benchmark integration 覆盖 source missing、source outside repo 和 source 为空；正常 Java fixture benchmark 继续通过。
- 完成内容：`_hard_gate_command_evidence_check()` 新增 `_hard_gate_command_evidence_issue()`，保留 `missing_source`、`low_confidence`、`source_path_missing`、`source_path_outside_repo`；README、sensor/gate 规则、测试策略、迁移 todo、spec 和 plan 同步。
- 验证结果：targeted benchmark integration 已通过；fast regression 见本轮提交前验证。
- Self-Harness Gate：长期文档已同步；Runtime 边界未变化，未执行 hard gate command、未创建 `.ai/task-runs`。下一轮候选 gap 继续来自迁移 todo：risk context consistency 或 project-context evidence context gate。

## 2026-06-01 Init Summary 待确认处理入口迁移

- North Star 模块：Progressive Collaboration、CLI Experience、Maturity & Evolution、Sensor & Quality Gate。
- init North Star 旅程阶段：写入后的交付摘要；仍需人工确认的问题和下一步处理入口。
- Gap Analysis 摘要：当前唯一 open todo 是本地独有 / 更细能力迁移。对比当前 main 与 `backup/local-61-before-migration` 后，本轮候选包括 Init Summary 待确认处理入口、Benchmark / quality gate 深层迁移、Scan evidence 可审计细节。当前 `human-input-needed.md` 和已有 Harness 维护入口已经有 `.ai/human-input-needed.md#处理方式`，但首次 `init-summary.md` 仍缺少稳定 `## 待人工确认` 章节和 questionnaire ID 对齐，因此优先补齐交付摘要闭环。
- 用户故事：作为首次运行 `init` 后阅读 `.ai/init-summary.md` 的 Harness Maintainer，当我看到 `## 待人工确认` 时，我可以直接知道这些 `confirm:*` 问题应去 `.ai/human-input-needed.md#处理方式` 处理，并且 scan warning 会显示对应 action hint，从而把交付报告里的风险解释连接到可执行补充动作。
- 当前代码 gap：`build_init_summary_markdown()` 没有 `## 待人工确认`；CLI completion 的待确认区只列问题，不说明处理入口；benchmark `content:init-summary` 不校验 confirmation 处理入口或 questionnaire ID 对齐。
- 关键决策 / 取舍：不新增 schema，复用 `Questionnaire`；将 scan warning action hint 从 human confirmation 内部 helper 提取为公共 helper，避免 `human-input-needed.md`、`init-summary.md` 和 CLI completion 文案漂移；summary 只展示前几个问题，完整处理建议仍以 `.ai/human-input-needed.md#处理方式` 为准。
- Assumptions / risks：`init-summary.md` 是首次 init 后团队会共享的持久化入口，因此必须能独立指向人工确认处理方式；旧 Harness 如果没有该章节，benchmark 可暴露为内容契约失败；action hint 只是处理建议，不代表 Builder 自动修正扫描结论。
- Sub agent 使用情况：尝试启动 explorer 做只读旧分支对比，但当前 agent thread limit reached；本轮由主线程用当前文件和 `git show` 完成对比。
- 价值切分说明：本轮聚焦首次 init 交付摘要和待确认处理入口，不把 Benchmark 深层 quality gate 或 Scan evidence writer 迁入同一轮。
- 可执行验收标准及验证方式：unit 覆盖 summary / CLI completion 的 `## 待人工确认`、处理入口、`confirm:*` ID 和 scan warning action hint；integration 覆盖 Java / .NET fixture init 产物；benchmark integration 覆盖 `content:init-summary` 缺处理入口时失败。
- 完成内容：`init-summary.md` 新增 `## 待人工确认`；`render_init_completion_message()` 复用同一待确认摘要；`benchmark` 增强 `content:init-summary` 检查；README、init workflow、迁移 todo、spec 和 plan 同步。
- 验证结果：targeted unit / integration 已通过；`git diff --check` 通过；`scripts/test-fast.sh` 通过，结果为 `347 passed in 17.77s`。
- Self-Harness Gate：长期文档已同步；Runtime 边界未变化，未创建 `.ai/task-runs`。下一轮候选 gap 继续来自迁移 todo：优先审视 Benchmark / quality gate 细化，或进入 Scan evidence 可审计细节。

## 2026-06-01 Existing Harness Benchmark / Routing Signals 迁移

- North Star 模块：CLI Experience、Maturity & Evolution、Sensor & Quality Gate、Runtime Boundary。
- init North Star 旅程阶段：再次进入已有 Harness；健康状态、维护建议和下一步动作。
- Gap Analysis 摘要：当前唯一 open todo 仍是本地独有 / 更细能力迁移。对比当前 main 与 `backup/local-61-before-migration` 后，本轮候选包括 Benchmark / Workflow routing 只读信号、Benchmark 深层 quality gate 迁移、Scan evidence 可审计细节。README 与 init workflow 已把 Benchmark signals / Workflow routing signals 描述为维护入口契约，但当前代码只在 Experience signals 中混合展示 `schema_content_failed_checks`，没有独立小节和 failed detail；因此本轮优先修正代码、schema 和测试的事实源漂移。
- 用户故事：作为 Harness Maintainer，当我再次运行 guided `init` 进入已有 Harness 维护入口时，我可以直接看到最近 benchmark 失败项的数量、ID、中文解释、可行动错误详情，以及当前 workflow routing 的 default / standard escalation / risk trigger 状态，从而不用先打开多个 YAML 文件也能判断应该先修质量门禁还是调整 routing 策略。
- 当前代码 gap：`BenchmarkReport` schema 没有保留 `errors`、`missing`、`weak_commands`；existing-Harness 入口没有输出 `Benchmark signals` / `Workflow routing signals`；Maintenance triage 不能把 hard gate weak command 或 project-context evidence missing 升级为专属 reason/detail。
- 关键决策 / 取舍：新增宽松的 `BenchmarkWeakCommand` schema，兼容当前 benchmark 只写 `id/source/confidence` 和旧分支带 `reason` 的报告；保留 `schema_content_failed_checks` Experience 行以兼容现有输出；Workflow routing signals 只读解释 `.ai/harness-config.yaml`，不执行 Runtime、不修改 routing policy。
- Assumptions / risks：`standard-escalation` 是当前 routing 健康度的关键观察点；schema 变宽只保留已有 report detail，不改变 benchmark pass/fail 计算；CLI 仍保留 `key=value` 稳定契约，后续可继续人类化展示。
- Sub agent 使用情况：尝试启动 explorer 做旧分支对比，但当前 agent thread limit reached；本轮由主线程用 `git show` / `git grep` 完成只读对比。
- 价值切分说明：本轮把 Benchmark failed preview 与 Workflow routing signals 合并，因为它们共享已有 Harness 维护入口的只读状态视图和同一 CLI 验收；不把更深 benchmark 检查或 scan evidence writer 混入。
- 可执行验收标准及验证方式：unit 覆盖 BenchmarkReport detail schema、benchmark signal helper、workflow routing signal helper、maintenance triage 专属 reason/detail；integration 覆盖已有 Harness `init -> exit` 输出两个独立小节且不扫描、不覆盖正式资产。
- 完成内容：`BenchmarkReport` 保留 check detail；`interactive_init.py` 输出 `Benchmark signals` 和 `Workflow routing signals`；`maintenance_triage.py` 增加 hard gate weak command、risk context、project-context evidence 专属排序与 guidance；README、init workflow、迁移 todo、spec 和 plan 同步。
- 验证结果：targeted unit / integration 已通过；fast regression 见本轮提交前验证。
- Self-Harness Gate：长期文档已同步；下一轮候选 gap 转向迁移 todo 中剩余的人机闭环细节，例如 `init-summary.md` 与 questionnaire `confirm:*` ID 对齐，或进入 Benchmark / quality gate 深层校验迁移。

## 2026-06-01 Human Input 待确认回访入口迁移

- North Star 模块：Progressive Collaboration、CLI Experience、Maturity & Evolution。
- init North Star 旅程阶段：再次进入已有 Harness；深度追问和人工确认回访。
- Gap Analysis 摘要：当前迁移 todo 仍有 Existing Harness human-input-needed signals、benchmark failed preview 和 routing signals。Benchmark preview 依赖更细 BenchmarkCheck 字段，routing signals 主要解释正式 routing policy；human input 回访直接补齐“用户跳过的问题必须能回访处理”的渐进式协作闭环，因此本轮优先。
- 用户故事：作为 Harness Maintainer，当我首次 init 后仍有待确认问题，并在之后再次运行 guided `init` 进入已有 Harness 维护入口时，我可以看到待确认项数量、scan 类确认数量、优先处理的 interaction id 和 `.ai/human-input-needed.md#处理方式` 入口，从而知道哪些人工上下文仍需补齐，以及应该用哪个命令或治理动作处理它们。
- 当前代码 gap：`human-input-needed.md` 只有待确认问题和下一步建议，没有稳定 `## 处理方式`；已有 Harness 入口只显示 `human_input_needed=present/missing`，不能展示 questionnaire backlog。
- 关键决策 / 取舍：复用现有 `Questionnaire` schema，不新增机器契约；scan 类确认项限定为当前 schema 类型；本轮不自动处理确认项，不修改正式 Guides / Sensors / routing policy，不执行 Runtime。
- Assumptions / risks：当前 Questionnaire 还没有 processed 状态，因此本轮展示的是待确认问题总数和前几个 id；后续可结合 candidate governance / Experience evidence 做更细状态。
- Sub agent 使用情况：未使用 sub agent；此前线程 agent 数量达到上限，本轮范围小且主线程可直接完成。
- 价值切分说明：本轮同时更新 `human-input-needed.md` 和已有 Harness 入口，因为它们共享“待确认项回访”这一用户故事，不把 benchmark failed preview 或 routing signals 混入同一轮。
- 可执行验收标准及验证方式：unit 覆盖 Markdown 章节与处理建议、helper 对 questionnaire 的 schema 校验和 missing 边界；integration 覆盖已有 Harness `init -> 1` 输出 backlog status 且 formal assets 不变。
- 完成内容：`human_input_markdown()` 增加 `## 扫描待确认摘要` 和 `## 处理方式`；`interactive_init.py` 增加 `_human_input_needed_status_lines()` 并在 Experience / review signals 中展开 human input backlog；README、init workflow、迁移 todo、spec 和 plan 同步。
- 验证结果：targeted unit / integration 已通过；fast regression 见本轮提交前验证。
- Self-Harness Gate：长期文档已同步；无新增 schema。下一轮候选 gap：benchmark failed preview 与 BenchmarkCheck detail 字段、Workflow routing signals、init-summary 与 questionnaire `confirm:*` ID 对齐。

## 2026-06-01 Existing Harness 编号菜单与维护指引迁移

- North Star 模块：CLI Experience、Maturity & Evolution、Experience & Self-Improve。
- init North Star 旅程阶段：再次进入已有 Harness。
- Gap Analysis 摘要：当前唯一 open todo 是本地独有 / 更细能力迁移。对比当前主线和 `backup/local-61-before-migration` 后，本轮候选包括 Existing Harness 编号菜单与 guidance、benchmark failed preview、human-input-needed backlog、Workflow routing signals。编号菜单与 guidance 最小且直接提升维护入口可用性，因此先迁移。
- 用户故事：作为 Harness Maintainer，当我再次运行 guided `init` 进入已有 Harness 维护入口时，我可以看到带编号的维护动作菜单，并按编号选择只读退出或后续维护动作，同时从 Maintenance triage guidance 中理解 top actions 应该如何处理，从而不用记英文命令或自行解读 reason code。
- 当前代码 gap：已有入口只输出英文命令列表和 `top_action_* reason/source/next`，没有编号选择，也没有中文处理建议。
- 关键决策 / 取舍：本轮只迁移编号菜单、action normalization 和 triage guidance；benchmark 失败细节、human-input backlog、routing signals 保留为迁移 todo 的后续候选。
- Assumptions / risks：编号菜单不改变任何正式资产写入边界；未知输入仍默认只读退出。sub agent 已尝试启用但线程 agent 数量达到上限，本轮改为主线程本地对比。
- 边界情况 / 失败模式：`1` 到 `8`、英文命令和常见中文别名都规范化到稳定 action；未知输入保持原有保守退出路径；`exit` 不触发 scan、不覆盖正式 Harness 资产。
- 价值切分说明：该切片围绕“已有 Harness 维护入口能被低成本操作”这一用户故事，不把更细 benchmark/human-input/routing 信号混入同一轮。
- 可执行验收标准及验证方式：unit 覆盖 action normalization 和 guidance 渲染；integration 覆盖输入 `1` 只读退出、编号菜单输出、guidance 输出、formal assets 不变；文档和迁移 todo 同步。
- 完成内容：新增 `render_maintenance_triage_guidance_lines()`；existing-Harness guided entry 输出 `Maintenance triage guidance` 和编号菜单；新增 `_normalize_existing_harness_action()`；同步 README、init workflow、迁移 todo、spec 和 plan。
- 验证结果：targeted unit / integration 已通过；fast regression 见本轮提交前验证。
- Self-Harness Gate：长期文档已同步；无新增 schema 或 benchmark 契约。下一轮候选 gap：benchmark failed preview 与更细 failure detail、human-input-needed backlog 状态、Workflow routing signals，仍需下一轮 Current State Gap Analysis 重新排序。

## 2026-06-01 本地独有能力迁移 Todo 收敛

- 关联 todo：`docs/todos/local-unique-capability-migration.md`。
- North Star 模块：目标模式执行系统、Init Experience、Maturity & Evolution、工程可持续性。
- init North Star 旅程阶段：本轮不改用户旅程，先收敛后续迁移基线，避免并行实现继续污染 `init` 主线。
- Gap Analysis 摘要：最新远端 `origin/main` 已包含 guided init 进度、maturity preview、LLM evidence plan、scan follow-up 和 self-check 等 30 个提交；本地旧 `main` 另有 61 个未 push 提交，且两边在 `interactive_init.py`、`init_summary.py`、`scan_repo.py`、`human_confirmation.py` 等核心文件高度重叠。用户明确要求先处理合并问题、剩余重复 commit 可以丢掉，因此本轮选择基线收敛，而不是继续功能迁移。
- 工程信任故事：作为 Harness Builder 维护者，当本地 61 个提交和远端 30 个提交已经并行演进且决定放弃整包 merge 时，我可以在最新 `origin/main` 基线上保留旧实现备份、把当前 open todo 收敛为“本地独有 / 更细能力迁移”，从而让后续目标模式只按小步迁移独有增量，而不是继续尝试合并两套实现。
- 当前代码 gap：`main` 已 reset 到最新 `origin/main` 后，远端仍有两个 open todo，会让目标模式继续按旧大主题推进；迁移策略 todo 曾在旧工作树里写好，但需要恢复到新基线，并记录备份分支 / stash 事实。
- 关键决策 / 取舍：以最新 `origin/main` 为主线；旧 61 个提交保留在 `backup/local-61-before-migration`；reset 前未提交工作树保留在 `stash@{0}: local-worktree-before-origin-main-reset`；`guided-init-ai4se-real-repo-findings.md` 与 `maturity-driven-init-wizard.md` 暂停为背景参考；本轮不迁移功能代码。
- Assumptions / risks：备份分支是本地引用，后续如需共享旧实现需要单独推送或导出；stash 序号可能变化，因此 todo 记录 stash message；暂停旧 todo 不是否定其价值，而是避免绕开迁移决策。
- Sub agent 使用情况：未使用 sub agent。本轮是 git / 文档基线收敛，范围小且不涉及并行代码调研。
- 价值切分说明：本轮完成后，后续目标模式有一个干净远端基线和唯一迁移入口，能把冲突风险从“整包合并 61 个提交”降为“逐个迁移独有能力”。
- 验收标准及验证方式：`main` 与 `origin/main` 对齐；备份分支存在；`docs/todos` 只有迁移 todo 为 open；`git diff --check` 和 `scripts/test-fast.sh` 通过。
- 完成内容：恢复并更新 `local-unique-capability-migration.md`；更新 todo README；暂停两个旧 open todo；新增本轮 spec / plan。
- 验证结果：open todo 检查只返回迁移 todo；备份分支存在；`git diff --check` 通过；`scripts/test-fast.sh` 通过，334 passed。
- Self-Harness Gate：下一轮应从迁移 todo 的推荐顺序中选择第一个小步迁移切片，优先 Existing Harness 维护入口独有能力；不要直接 merge 或 cherry-pick 整组旧提交。

## 2026-06-01 Guided Init 扫描失败退出边界硬化

- 关联 todo：`docs/todos/maturity-driven-init-wizard.md`、`docs/todos/testing-coverage-and-acceptance-strategy.md`。
- North Star 模块：CLI Experience、Progressive Collaboration、可解释失败边界、可观测 Harness 生成。
- init North Star 旅程阶段：阶段化扫描与进度反馈、错误信息、可审计 trace、正式资产写入边界。
- Gap Analysis 摘要：本轮重新读取事实源后发现工作区已有 guided scan failure 的退出边界改动。候选对比中，用户自然语言补充影响成熟度/推荐和路径型 claim validation 更接近下一阶段深度体验，但当前 dirty diff 已形成独立工程信任故事：扫描失败应由 CLI 友好失败和 scan trace 表达，而不是泄露 traceback 或被外层 `init failed` 混淆。
- 工程信任故事：作为 Harness Maintainer，当首次 guided `init` 的扫描阶段因为 LLM、网络或 schema 问题失败时，我可以看到清晰的中文失败说明和“未写入正式 Harness 资产”的边界，并且后续维护者可以从 trace 中确认失败只发生在 scan 阶段，从而更快定位问题而不误以为系统生成了不可信 Harness。
- 当前代码 gap：已有测试只断言终端失败提示和正式资产未写入，没有验证 `trace.yaml`、`events.jsonl` 和外层 `init failed` 污染；上一轮 scan progress spec/plan 也没有记录 `typer.Exit` 退出语义。
- 关键决策 / 取舍：guided scan failure 在 `interactive_init.py` 中记录 `scan failed` details、输出中文失败说明、finish failed trace 后抛出 `typer.Exit(1)`；`cli.py` 透传 `typer.Exit` / `typer.Abort`，避免通用异常处理重复写入外层失败事件。失败仍显式暴露，不 fallback，不写正式 Harness 资产。
- Assumptions / risks：失败 trace 目录属于过程审计产物，不代表正式 Harness 已生成；隐藏 traceback 不能隐藏错误摘要，因此错误类型和短消息同时进入 CLI、trace summary 和 events。
- Sub agent 使用情况：使用两个只读 explorer 子代理并行审查 dirty diff 和下一轮 init gap。一个建议本轮收口扫描失败边界并补 trace 断言；另一个建议下一轮优先做自然语言补充影响成熟度/推荐。
- 价值切分说明：本轮只硬化 guided scan failure 的退出与 trace 契约，不混入自然语言补充消费、targeted rescan、claim validation 或 benchmark 交互。
- 验收标准及验证方式：integration 覆盖扫描失败输出无 traceback、`CliRunner` 不再暴露原始 `RuntimeError`、`trace.yaml status=failed`、summary 包含 `error_type` / `scan_error`、`events.jsonl` 只有 scan failed 事件、正式 Harness 资产未写入；工程文档和 spec/plan 同步。
- 完成内容：补强 guided scan failure 测试；`interactive_init.py` 在 scan failure 后 finish trace 并 Typer exit；`cli.py` 透传 Typer 控制流异常；新增本轮 spec / plan，更新 init workflow 和演进记录。
- 验证结果：targeted test `1 passed in 0.20s`；commit 前快速回归见本轮提交前验证。
- Self-Harness Gate：长期失败边界已沉淀到 `docs/engineering/init-workflow.md`；本轮没有新增 `.ai` 资产契约。下一轮候选 gap：自然语言补充与 self-check resolution 如何影响成熟度预览、推荐解释和最终资产；路径型 claim validation；已有 Harness schema / contract 损坏时的维护入口修复引导。

## 2026-06-01 Push Gate：Scan Self-check Evidence Source 契约修复

- 触发来源：用户要求当前任务完成后统一 push；push 前 `scripts/test-full.sh` 在真实 eShopOnWeb acceptance 中失败。
- 失败现象：真实 DeepSeek scan self-check 返回 `source_sampling_truncated` 作为 `resolutions[].evidence_sources`，parser 报 `unknown evidence source`，导致非交互 `init` 失败。
- 根因：`source_sampling_truncated` 是 `ScanMetadata.warnings[].code` 中的稳定扫描审计来源；prompt 文案允许引用 scan warning / scan metadata 中已有 evidence 字符串，但 parser allowlist 只接受 warning 的 `evidence` 值，没有接受 warning code，契约两侧不一致。
- 决策：将 scan warning code 明确纳入 self-check evidence source allowlist，并同步 prompt / LLM contract；继续拒绝任意未知路径或字符串，不引入 fallback。
- 验收方式：新增 unit 测试复现 `source_sampling_truncated` 作为 evidence source 的真实 LLM 行为；保留未知 evidence source 失败测试；重新运行 targeted / fast / full regression 后再 push。

## 2026-06-01 Scan Follow-up Self-check

- 关联 todo：`docs/todos/guided-init-ai4se-real-repo-findings.md`。
- North Star 模块：Scanner & Analyzer、CLI Experience、Progressive Collaboration、Maturity & Evolution、智能化闭环。
- init North Star 旅程阶段：扫描结果友好呈现、深度追问、渐进式深入、人工确认资产。
- Gap Analysis 摘要：上一轮已把扫描不确定性转成 `followup_questions` 并进入 CLI / questionnaire / human input，但追问仍只是待办项，没有被 LLM 再审查；本轮比较了 follow-up self-check、自然语言补充消费、维护入口浏览和 claim-level validation，选择先做 review-only self-check，因为它能最小纵向消费现有追问契约，同时不自动改正式扫描结论。
- 用户故事：作为 Harness Maintainer，当大型或多栈仓库首次 guided `init` 生成深度追问时，我可以看到 Builder 基于当前 evidence 对这些追问执行 LLM 二次自检，并把每个追问的 review-only 结论、风险和下一步写入 scan metadata、CLI 和人工确认链路，从而知道哪些问题仍需人工补充或后续 targeted scan。
- 当前代码 gap：`scan_repo.py` 只在 reconcile 后返回 metadata；`followup_questions` 只被 CLI 和 questionnaire 展示；没有 `ScanSelfCheckReport`、self-check prompt、parser、progress event 或 questionnaire resolution 合并。
- 关键决策 / 取舍：新增 `ScanSelfCheckReport` / `ScanSelfCheckResolution` 和 `ScanMetadata.self_check`；新增集中 prompt `llm_scan_self_check_v1.md`；真实 LLM 路径或显式 mock caller 才运行 self-check；self-check 只做 review-only 审计，不自动修改 inventory、commands、Guides、Sensors 或 Workflow routing。
- Assumptions / risks：真实有 follow-up 的 init 会增加一次 LLM 调用；mock scan 测试如果没有显式传 self-check caller 不会被额外调用；后续仍需要 claim-level support/conflict/unknown validation。
- Sub agent 使用情况：使用两个只读 explorer 子代理并行调研 follow-up 消费链路、实现风险和候选排序；两者均建议本轮优先做审计型 self-check，把自动修正和 claim-level validation 留作后续。
- 价值切分说明：本轮完成“follow-up questions -> LLM self-check -> scan metadata -> CLI -> questionnaire”的纵向闭环，不把 targeted rescan、自动修正或完整 claim map 混入同一 milestone。
- 验收标准及验证方式：schema unit 覆盖 `ScanMetadata.self_check`；LLM parser unit 覆盖合法 JSON、非法 JSON、未知 interaction id 和未知 evidence source；scan repo unit 覆盖有 follow-up 时调用 self-check、无 follow-up 时不调用；guided integration 覆盖“LLM 二次自检”和 questionnaire reason；prompt registry 测试覆盖集中 prompt 管理。
- 完成内容：新增 self-check schema、prompt、parser 和 scan repo 阶段；guided CLI 展示 review-only 二次自检；questionnaire 合并对应 resolution；同步 engineering docs、todo、spec 和 plan。
- 验证结果：targeted suite `25 passed in 0.15s`；commit 前快速回归 `scripts/test-fast.sh` 为 `333 passed in 16.24s`；`git diff --check` 通过。
- Self-Harness Gate：剩余 LLM-planned deep scan 仍 open。下一轮候选 gap 优先考虑 claim-level support/conflict/unknown validation 的第一切片，其次是用户自然语言补充与 self-check resolution 如何共同影响成熟度预览和 Harness 推荐。

## 2026-06-01 Scan Follow-up Questions

- 关联 todo：`docs/todos/guided-init-ai4se-real-repo-findings.md`。
- North Star 模块：Scanner & Analyzer、CLI Experience、Progressive Collaboration、Maturity & Evolution、智能化闭环。
- init North Star 旅程阶段：扫描结果友好呈现、成熟度初评前的深度追问、可审计 evidence、human-input-needed。
- Gap Analysis 摘要：当前 coverage gap、unsupported stack claim、primary stack unknown、模块边界缺失和测试 evidence 缺失已经会产生 warning 或 CLI 文案，但它们没有统一的机器契约，不能稳定进入 targeted 追问、questionnaire 和 human input。子代理建议最小切片是在现有 warning / metadata / questionnaire 链路上增加 scan self-check trigger，而不是直接引入第二次 LLM 调用。
- 用户故事：作为 Harness Maintainer，当大型或多栈仓库首次 guided `init` 存在源码覆盖不足、LLM 栈判断缺少证据、主要技术栈未知或模块边界不清时，我可以在 CLI、`.ai/scan-metadata.yaml`、`.ai/questionnaire.yaml` 和 `.ai/human-input-needed.md` 中看到明确的补救追问，从而知道应该补充哪些关键路径、技术栈、模块边界或验证线索。
- 当前代码 gap：`ScanMetadata` 只有 warnings、coverage 和 evidence_expansion；`human_confirmation.py` 只把 raw warnings 转成 “接受降级 / 人工修正” 问题；guided CLI 的“不确定性 / 建议补充”缺少稳定、可测试的 follow-up question 契约。
- 关键决策 / 取舍：新增 `ScanFollowupQuestion` 和 `ScanMetadata.followup_questions`；新增 `scan_followup_confirmation` questionnaire 类型；guided CLI 展示 `深度追问`。本轮不新增二次 LLM self-check、不扩大读取预算、不自动修正 proposal、不调整 benchmark scoring。
- Assumptions / risks：follow-up 与原始 scan warning confirmation 会有一定重叠；当前保留原始 warning 作为审计问题，follow-up 用于面向用户的补救追问，后续可以做去重或优先级排序。
- Sub agent 使用情况：使用 explorer 子代理只读调研 coverage warning、planner low confidence、stack conflict / unknown 的产生和消费路径；采纳其“最小切片先加 scan self-check trigger / targeted follow-up”的建议。
- 价值切分说明：本轮完成“warning / validation -> metadata follow-up -> CLI 深度追问 -> questionnaire / human-input”的纵向闭环，不把二次 LLM self-check 和 claim-level validation 扩展混入同一 milestone。
- 验收标准及验证方式：schema unit 覆盖 `followup_questions`；reconciler unit 覆盖 coverage gap、unsupported stack、unknown stack、module boundary 和 test evidence follow-up；human confirmation unit 覆盖 `scan_followup_confirmation`；guided integration 覆盖 CLI `深度追问`、questionnaire 和 human-input。
- 完成内容：新增 `ScanFollowupQuestion` schema；`reconcile_scan()` 根据 warnings / stack validation / proposal 状态生成 follow-up；`interactive_init.py` 展示深度追问；`build_questionnaire()` 写入 scan follow-up confirmation；同步 spec、plan、工程文档和 todo。
- Self-Harness Gate：剩余 LLM-planned deep scan 仍 open。下一轮候选 gap 优先考虑二次 LLM self-check 或 targeted scan 对 `followup_questions` 的消费，其次是 module / risk / config / CI 的 claim-level support / conflict / unknown validation。

## 2026-06-01 Guided Init LLM Evidence Plan 可见化

- 关联 todo：`docs/todos/guided-init-ai4se-real-repo-findings.md`。
- North Star 模块：Scanner & Analyzer、CLI Experience、Progressive Collaboration、Maturity & Evolution、智能化闭环。
- init North Star 旅程阶段：阶段化扫描与进度反馈、扫描结果友好呈现、深度追问、可审计 evidence。
- Gap Analysis 摘要：上一轮已把 `evidence_expansion` 写入 `.ai/scan-metadata.yaml`，但首次 guided `init` 主界面仍不解释 LLM 为什么补读哪些文件、实际读到哪些文件、planner 低置信度为什么需要人工确认；子代理建议下一步优先处理 coverage gap / conflict / unknown 后的补救和 targeted 追问，本轮选取其中低风险且可独立验收的 planner low-confidence targeted confirmation 切片。
- 用户故事：作为 Harness Maintainer，当大型或多栈仓库首次 guided `init` 触发 LLM-guided evidence expansion 时，我可以在扫描发现阶段看到 LLM 补读了哪些文件、为什么补读、实际读到了哪些文件，以及低置信度补读计划为何需要人工确认，从而在补充上下文前校准扫描理解和风险边界。
- 当前代码 gap：`interactive_init.py` 只展示通用风险、不确定性和验证缺口；`human_confirmation.py` 会把 scan warning 转成确认项，但没有专门的 evidence expansion 交互类型，导致 planner 低置信度缺少可读的问题表达。
- 关键决策 / 取舍：新增 CLI “LLM 深度补充”分组；新增 `evidence_expansion_confirmation` questionnaire 类型和稳定 `confirm:evidence-expansion` id；本轮不做二次 LLM self-check、不扩大读取预算、不调整 planner prompt 或 benchmark scoring。
- Assumptions / risks：planner rationale 可能来自真实 LLM，后续如出现英文或过长表达，再通过 prompt 或渲染层继续收紧；旧 scan metadata 没有 `evidence_expansion` 时不输出空分组。
- Sub agent 使用情况：使用 explorer 子代理只读调研下一轮 gap；采纳其 P0 中“targeted 追问触发”的方向，但把更大的二次 self-check / claim-level validation 留作下一轮候选。
- 价值切分说明：本轮完成“planner metadata -> CLI 可见解释 -> low confidence 待确认资产”的用户可见闭环，不把 claim validation、二次 self-check 和 schema hardening 混入同一 milestone。
- 验收标准及验证方式：integration 覆盖 guided CLI 输出 `LLM 深度补充`、路径、关注原因、rationale 和 low confidence；unit 覆盖 low-confidence evidence expansion 生成 questionnaire；schema unit 覆盖新 interaction type；文档和 todo 同步契约。
- 完成内容：`QuestionnaireQuestion` 支持 `evidence_expansion_confirmation`；`build_questionnaire()` 将 low-confidence planner 转成 `confirm:evidence-expansion`；guided CLI 展示 planner requested/read paths、risk focus、rationale 和 confidence；同步 spec、plan、工程文档和 todo。
- Self-Harness Gate：剩余 LLM-planned deep scan 仍 open。下一轮候选 gap 优先考虑子代理提出的 coverage gap / conflict / unknown 二次 self-check 或 targeted scan，再考虑 claim-level support/conflict/unknown validation 和 `LLMScanProposal` 结构化 hardening。

## 2026-06-01 LLM Evidence Plan 可审计

- 关联 todo：`docs/todos/guided-init-ai4se-real-repo-findings.md`。
- North Star 模块：Scanner & Analyzer、CLI Experience、Maturity & Evolution、智能化闭环。
- init North Star 旅程阶段：阶段化扫描与进度反馈、扫描结果友好呈现、可审计 evidence、成熟度初评输入。
- Gap Analysis 摘要：上一轮已让全量轻量 manifest 带 bucket / priority / reason，但 `LLMEvidencePlan` 的 requested paths、risk focus、rationale 和 confidence 只在内存中用于读取补充文件，最终 `.ai/scan-metadata.yaml` 仍无法回答“LLM 为什么补读这些文件、实际读到了哪些文件、planner 是否低置信度”。
- 用户故事：作为 Harness Maintainer，当大型多栈仓库的首次 `init` 触发 LLM-guided evidence expansion 时，我可以在 `.ai/scan-metadata.yaml` 中审计 planner 计划、实际读取结果和低置信度风险，从而调试扫描结论并判断哪些判断需要人工确认。
- 当前代码 gap：`scan_repository()` 调用 planner 后没有把 plan 传入 `reconcile_scan()`；`ScanMetadata` 只有 coverage、warnings 和 final scan reasoning summary；planner 低置信度不会改变 `needs_human_confirmation`。
- 关键决策 / 取舍：新增 `LLMEvidenceExpansionMetadata` 作为 `ScanMetadata.evidence_expansion` 可选字段；不把 planner metadata 写入 `llm-scan-proposal.json`；不扩大读取预算、不新增第二轮 LLM scan；planner 低置信度追加 warning 并置位 human confirmation signal。
- Assumptions / risks：旧 scan metadata 可以没有 `evidence_expansion`；真实 LLM planner 的 rationale 会进入机器审计产物，应保持短文本并由现有 planner prompt 约束。
- Sub agent 使用情况：使用一个 explorer 子代理只读调研 scan metadata 数据流、writer、benchmark 和测试落点；采纳其“schema + scan_repo + scan_reconciler 最小切点，writer 大概率透传”的建议。
- 价值切分说明：本轮完成“LLM 规划 -> Python 安全读取 -> 最终 scan -> metadata 审计 -> low confidence 人工确认信号”的纵向闭环，不把 `modules/risk_areas` schema hardening 或 claim-level validation 混入同一 milestone。
- 验收标准及验证方式：schema unit 覆盖 `ScanMetadata.evidence_expansion`；reconciler unit 覆盖 planner audit 和 low confidence warning / human confirmation；scan repo unit 覆盖 planner metadata 透传；init fixture integration 覆盖 `.ai/scan-metadata.yaml` schema 和空 requested paths 的 audit 落盘。
- 完成内容：新增 `LLMEvidenceExpansionMetadata`；`scan_repository()` 向 `reconcile_scan()` 传递 `LLMEvidencePlan`；`reconcile_scan()` 生成 `evidence_expansion` 并处理 low confidence；同步 init workflow、LLM contracts、todo、spec 和 plan。
- Self-Harness Gate：剩余 LLM-planned deep scan 仍 open。下一轮候选 gap 优先考虑严格化 `LLMScanProposal` 中 modules / risk_areas / configs / ci_files schema，其次是 claim-level support/conflict/unknown 调和和 ai4se-like integration / acceptance。

## 2026-06-01 LLM 规划式深度扫描 Manifest 语义增强

- 关联 todo：`docs/todos/guided-init-ai4se-real-repo-findings.md`。
- North Star 模块：Scanner & Analyzer、CLI Experience、Maturity & Evolution、智能化闭环。
- init North Star 旅程阶段：基础扫描、阶段化扫描与进度反馈、扫描结果友好呈现、成熟度初评输入。
- Gap Analysis 摘要：当前已有 `collect evidence -> LLM evidence plan -> 读取补充文件 -> LLM scan -> reconcile` 链路，但全量轻量 `EvidenceBundle.files` 只有路径和大小，未携带 bucket / priority / reason；这会让 LLM planner 虽然能看到全量路径，却难以区分未采样文件中的风险、API 入口、测试和核心源码优先级。
- 用户故事：作为 Harness Maintainer，当我在大型多栈仓库运行首次 guided `init` 且初始 source sampling 跳过大量文件时，我可以相信 LLM evidence planner 在最终扫描前基于全量轻量 manifest 主动选择未采样但高价值的文件补读，而不是只被确定性采样结果牵引。
- 当前代码 gap：`collect_evidence()` 对 `files[]` 使用 `_evidence_file(..., max_summary_chars=0)`，没有传入 `_bucket_for()`、`_priority_for()` 和 `_reason_for()`；`llm_evidence_plan_v1.md` 没有明确要求 LLM 消费 full manifest 语义和 coverage gap。
- 关键决策 / 取舍：复用 `EvidenceFile` 现有字段，不新增 schema；全量 manifest 仍不读取正文摘要；LLM 只能从 allowlist 中逐字复制路径，Python 继续负责路径校验、预算读取和 no silent fallback。
- Assumptions / risks：bucket / priority / reason 是 evidence classification，不是最终业务判断；真实 LLM 的 requested paths 可能变化，但仍被 schema、max 8、allowlist 和 retry 约束。
- Sub agent 使用情况：使用一个 explorer 子代理只读调研当前 deep scan 链路；其结论确认 full manifest 偏薄，并建议后续补 planner rationale / requested paths 进入 scan metadata、claim-level validation 和 ai4se-like integration。
- 价值切分说明：本轮完成“全量轻量 manifest -> planner prompt -> LLM requested file -> final scan evidence”的最小纵向闭环，不把 metadata 审计、二次 self-check 和完整 claim validation 混进同一 milestone。
- 验收标准及验证方式：unit 覆盖全量 `files[]` 未采样文件带 bucket / priority / reason 且不读 summary；planner prompt 覆盖 full manifest 语义、coverage warnings 和未进入初始摘要的高价值文件；scan repo 测试覆盖 planner 从增强 manifest 请求未采样文件并进入 final scan prompt。
- 完成内容：`collect_evidence()` 为全量轻量文件索引填充 bucket / priority / reason；`llm_evidence_plan_v1.md` 增加 full manifest、coverage warnings、未采样高价值文件的规划规则；同步 spec、plan 和 todo。
- Self-Harness Gate：剩余 LLM-planned deep scan 仍 open。下一轮候选 gap 优先考虑将 `LLMEvidencePlan` 的 rationale、risk_focus、requested_paths、实际读取文件和 planner confidence 写入 scan metadata，并让 coverage gap / low confidence 显式影响 human confirmation；其次是严格化 `LLMScanProposal` 中 modules / risk_areas / configs / ci_files schema 和 claim-level support/conflict/unknown。

## 2026-05-31 成熟度叙事中文化

- 关联 todo：`docs/todos/guided-init-ai4se-real-repo-findings.md`。
- North Star 模块：Maturity & Evolution、CLI Experience、可解释性、Harness 推荐质量。
- init North Star 旅程阶段：成熟度初评与差距解释、设计预览、写入摘要、已有 Harness 维护入口。
- Gap Analysis 摘要：真实 `ai4se` guided `init` 暴露“主要差距”中出现 `Guides are structured...` 等英文内部句；代码确认 `maturity_model.py` 的 blocker、evidence summary、next level requirement 和 blocking cap 会被 CLI、`maturity-score.yaml`、`maturity-report.md`、`init-summary.md` 直接消费。
- 用户故事：作为 Harness Maintainer，当我查看首次 `init` 的成熟度初评、写入前 preview、`maturity-report.md` 或 assess 刷新的成熟度报告时，我可以看到中文、面向 L0-L4 工程影响的阻断项和下一步建议，而不是英文内部叙事。
- 当前代码 gap：`maturity_model.py` 源头 user-facing strings 多数是英文；`asset_writers/reports.py` 和 `assess_maturity.py` 还在维度详情中输出 `evidence:` / `blockers:` 英文标签。
- 关键决策 / 取舍：在源头中文化 maturity free-text，保留 dimension key、blocker id、source path 和 schema 字段；新增 `maturity_rendering.py` 只做中文展示 label，不翻译机器 key；保留 `Guides`、`Sensors`、`Workflow`、`Runtime`、`hard gate` 等产品术语。
- Assumptions / risks：LLM reviewer 后续会消费中文 maturity score；这符合仓库“过程文档和用户叙事中文化”的方向，但若需要 LLM 输出也中文化，应单独调整 maturity review prompt。
- Sub agent 使用情况：使用一个只读子代理审查 maturity 出口、测试和 LLM 风险；采纳其“源头翻译为主，渲染层补标签映射”的建议。
- 价值切分说明：本轮修的是同一成熟度叙事出口链路，不改变评分算法和 schema，直接保护用户理解 L0-L4 成熟度、阻断项和下一步建议的体验。
- 验收标准及验证方式：unit 覆盖 `build_maturity_report()` 不含已知英文 blocker / next step；report writer 覆盖 `maturity-score.yaml` 和 `maturity-report.md` 中文文案；assess integration 覆盖刷新报告不含 `evidence:` / `blockers:`；guided init happy path 覆盖 CLI 不再出现已知英文 maturity blocker。
- 完成内容：中文化 maturity evidence / blocker / next requirement / blocking cap；新增中文 maturity report rendering helper；asset writer 和 assess 共用该 helper；同步 todo、spec 和 plan。
- Self-Harness Gate：同一 high priority todo 只剩 LLM-planned deep scan 主线；它风险更高，下一轮应重新做 gap analysis，优先判断是否先做 planner prompt / coverage confidence 的较窄纵向切片。

## 2026-05-31 Guided Init 多栈仓库组合建模

- 关联 todo：`docs/todos/guided-init-ai4se-real-repo-findings.md`。
- North Star 模块：LLM-first Repository Understanding、CLI Experience、Guides / Sensors、Maturity & Evolution。
- init North Star 旅程阶段：基础扫描、扫描结果友好呈现、与用户对齐扫描理解、写入前 Harness 设计预览。
- Gap Analysis 摘要：真实 `ai4se` 试跑中扫描看到了 Python、Flask、React、TypeScript、Vite、Docker、Nginx 等线索，但 `primary_stack` 只能在 Java / .NET / Node / unknown 中选择，用户补充提示也只能修正为单栈，导致多栈仓库容易被降级为 `unknown`。
- 用户故事：作为 Harness Maintainer，当我在 Python Flask + React / TypeScript 混合仓库上运行 guided `init` 时，我可以看到系统用中文说明组合技术栈、模块角色和验证能力，并让后续 Guide / Sensor 推荐围绕真实后端与前端模块，而不是误导成单一技术栈或 unknown。
- 当前代码 gap：`LLMScanProposal.primary_stack` 缺少 `python-flask`；`scan_reconciler` 没有 Python Flask evidence validation 和组合栈 profile；`interactive_init` 只显示 `_stack_label(primary_stack)`；`weapon_library` 只按 primary stack 选择一组栈特定 weapons。
- 关键决策 / 取舍：新增 `python-flask` 作为第一批 Python 主栈；React / TypeScript / Vite 暂由既有 `node` canonical 栈承载；新增 `stack_profile` 作为 `stack_extensions` 中的派生用户叙事，不替代 `primary_stack`、`stacks`、`modules` 机器契约；本轮不做完整 LLM-planned deep scan。
- Assumptions / risks：`python-flask` 不能代表所有 Python Web 项目，FastAPI / Django 后续应单独建模；多栈 profile 依赖 LLM proposal 和 evidence validation，扫描覆盖不足仍需通过已有 uncertainty 机制提醒用户。
- Sub agent 使用情况：使用两个只读子代理并行做 gap 排序与测试覆盖审查；两个结论均建议多栈建模优先，成熟度中文叙事与 LLM-planned deep scan 保留为后续切片。
- 价值切分说明：本轮完成“扫描理解 -> schema/reconciler 验证 -> CLI 组合表达 -> weapon selection -> 正式资产保留”的纵向闭环，避免只改字段或只改文案。
- 验收标准及验证方式：unit 覆盖 `python-flask` scan schema、Python Flask + React evidence validation、`stack_profile`、多栈 weapon selection；integration 覆盖 guided CLI 输出 `Python Flask 后端 + React / TypeScript 前端`、补充入口包含 `stack=python-flask` 和自然语言多栈说明，并验证 project inventory / weapon selection 产物。
- 完成内容：扩展 scan schema 与 LLM prompt；reconciler 增加 Python Flask / Node 多栈验证和 `stack_profile`；weapon library 增加 Python Flask 与 Node / 前端 Guide / Sensor；guided CLI 使用组合栈标签并允许 `stack=python-flask`。
- Self-Harness Gate：下一轮候选 gap 优先继续消化同一 todo 中的成熟度英文叙事中文化；更大范围的 LLM-planned deep scan 仍需单独 spec，避免和当前多栈 schema 扩展混在一起。

## 2026-05-31 Guided Init 高风险发现确认链路

- 关联 todo：`docs/todos/guided-init-ai4se-real-repo-findings.md`。
- North Star 模块：CLI Experience、Progressive Collaboration、Guides / Sensors、Workflow Routing、Maturity & Evolution。
- init North Star 旅程阶段：扫描结果友好呈现、深度追问、人工确认资产、正式 Guide / Sensor 生成。
- Gap Analysis 摘要：真实 `ai4se` guided `init` 发现 `docs/a.json` 可能包含明文 API key，但 CLI、questionnaire、Guide 和 Sensor 都只把它当作普通风险区域展示，缺少“疑似高影响风险、需要人工确认、命中后升级 workflow / 验证”的连续链路。
- 用户故事：作为 Harness Maintainer，当首次 guided `init` 发现疑似密钥、凭证、安全、支付、权限或数据迁移风险时，我可以在终端、`.ai/questionnaire.yaml`、`.ai/human-input-needed.md`、`.ai/guides/project-context.md` 和 `.ai/sensors/verification.md` 中看到它被标记为待确认高风险，并理解它对人工确认、Sensor 验证和 standard workflow / 人工升级的影响。
- 当前代码 gap：`risk_areas` 已进入 inventory 和正式资产，但 `_risk_attention_lines()`、`build_questionnaire()`、Guide writer 和 Sensor writer 都没有区分普通风险和高影响风险；`write_initial_assets()` 也没有把 risk areas 传给 questionnaire。
- 关键决策 / 取舍：新增轻量 `risk_signals` helper 统一分类风险线索，不迁移 `risk_areas` schema，不自动清理密钥，不执行 Runtime，不把疑似风险写成已确认事实，也不自动修改正式 workflow routing policy。
- Assumptions / risks：关键词分类可能误报，因此所有高风险表达都使用“疑似 / 待确认 / 需人工确认”；更强准确性留给后续 LLM-planned deep scan 和 detector validation。
- Sub agent 使用情况：使用两个只读子代理并行确认 milestone 边界、代码路径和非目标；结论建议把 CLI 高风险展示、human-input 确认、Guide/Sensor 表达合并为一个完整用户故事。
- 价值切分说明：本轮消化同一 high priority todo 中的高风险信任问题，覆盖用户从扫描发现到正式资产审查的完整确认链路；多栈建模、成熟度中文叙事和 LLM-planned deep scan 保持后续独立工作包。
- 验收标准及验证方式：unit 覆盖高风险分类、questionnaire schema、Guide / Sensor 文案；integration 覆盖 guided CLI 在进入团队规则前输出 `高风险，需人工确认`、具体路径和 standard workflow 升级提示；write assets 测试覆盖 `human-input-needed.md` 包含高风险确认问题且 `harness-config.yaml` 不出现具体风险路径 routing rule。
- 完成内容：新增 `risk_signals.py`；CLI 风险摘要和建议补充区标记高风险；questionnaire schema 增加 `risk_area_confirmation`；`write_initial_assets()` 传递 risk areas；Guide / Sensor 对待确认高风险使用专门表达。
- Self-Harness Gate：下一轮候选 gap 继续优先消化 `docs/todos/`，首选同一 todo 中“多栈表达与自然语言用户补充入口”，其次是“成熟度 blocker 中文化”，再其次是“LLM-planned deep scan 架构切片”。

## 2026-05-31 Guided Init 采样覆盖不足中文化

- 关联 todo：`docs/todos/guided-init-ai4se-real-repo-findings.md`。
- North Star 模块：CLI Experience、深度扫描、可解释 evidence、Maturity & Evolution。
- init North Star 旅程阶段：基础扫描、扫描结果友好呈现、与用户对齐扫描理解。
- Gap Analysis 摘要：真实多栈仓库中源码 bucket 被抽样时，机器 warning `source:.py skipped 73 files` 会直接出现在 guided CLI “不确定性”区块；`scan-metadata.yaml` 已有 coverage / bucket / skipped 统计，但 CLI 没把这些审计字段翻译成用户可理解的覆盖不足说明。
- 用户故事：作为 Harness Maintainer，当首次 guided `init` 扫描一个源码文件较多的仓库时，我可以在“不确定性”中看到中文说明：某类源码已抽样多少、仍有多少未进入初始摘要、这会影响哪些判断、我应该补充什么，从而理解扫描覆盖边界并校准关键模块或风险路径。
- 当前代码 gap：`evidence_collector._coverage()` 的 warning 只有 code / bucket / 英文 message；`interactive_init._uncertainty_attention_lines()` 原样输出 `scan_warnings[].message`，导致内部 bucket warning 泄露到用户界面。
- 关键决策 / 取舍：本轮只做 source sampling warning 的中文化和 metadata detail；不改变采样上限、不把 coverage gap 变成失败、不实现完整多栈建模、高风险候选治理或 LLM-planned deep scan。未知 warning 仍保留原 message 作为调试线索。
- Assumptions / risks：旧 inventory 如果缺少 coverage 详情，会使用中文通用覆盖不足说明；机器 metadata 继续保留 warning code / bucket / message 和 coverage 详情，避免损失审计能力。
- Sub agent 使用情况：使用两个只读 explorer 子代理并行确认选题优先级、代码路径和测试层级；结论一致建议本轮优先做 skipped / sampled 中文化，把高风险突出和多栈建模留作后续切片。
- 价值切分说明：本轮继续优先消化 high priority todo，但只处理“用户能不能理解扫描覆盖边界”这一条独立信任问题；它直接改善 CLI-first `init` 体验，并为后续 targeted scan / deep scan 留出明确用户补充入口。
- 验收标准及验证方式：unit 覆盖 coverage warning 保留 total / selected / skipped 计数；guided integration 覆盖“不确定性”输出中文抽样说明、包含 `.py` / `20/93` / `73`，且不再出现 raw `source:.py skipped 73 files` 或英文测试证据 warning。
- 完成内容：`EvidenceCoverage.warnings` 补充抽样统计 detail；`interactive_init.py` 新增 warning 中文格式化 helper；guided scan attention summary 测试从英文 warning 断言更新为中文用户语义断言。
- Self-Harness Gate：下一轮候选 gap 首选同一 todo 中的“高风险风险项突出展示并进入人工确认 / 候选链路”，其次是“多栈表达与用户补充入口”，再其次是“成熟度 blocker 中文化”和“LLM-planned deep scan 架构切片”。

## 2026-05-31 Init 工具工作区 Evidence 降噪

- 关联 todo：`docs/todos/guided-init-ai4se-real-repo-findings.md`。
- North Star 模块：CLI Experience、深度扫描、可解释 evidence、LLM-first evidence hygiene。
- init North Star 旅程阶段：基础扫描、扫描结果友好呈现、与用户对齐扫描理解。
- Gap Analysis 摘要：真实 `ai4se` guided `init` 试跑显示 `.claude/worktrees`、`.opencode`、`deploy-package/.opencode` 等工具工作区中的 `package.json` 会进入 key evidence，并可能优先出现在 CLI “判断依据”中；同时 Python 项目根文件如 `pyproject.toml`、`requirements.txt` 还没有被视为关键 evidence。
- 用户故事：作为 Harness Maintainer，当我在包含 AI 工具工作区和真实项目 manifest 的仓库上运行 guided `init` 时，我可以看到根项目和真实应用文件作为优先判断依据，而不是工具工作区里的临时 `package.json`，从而相信 Builder 正在理解项目本身。
- 当前代码 gap：`evidence_collector._walk_files()` 未忽略 `.claude` / `.opencode`；`_is_key_file()` 未覆盖 Python 项目 manifest；`scan_reconciler` 和 guided CLI 会沿用 `evidence.key_files` 作为判断依据。
- 关键决策 / 取舍：本轮只在 evidence collection 层做 hygiene，忽略 `.claude` / `.opencode` 任意层级目录，并把 `pyproject.toml`、`requirements*.txt`、`Pipfile`、`poetry.lock` 纳入 key evidence；不扩展 primary stack 枚举，不实现完整多栈模型，也不忽略整个 `deploy-package`。
- Assumptions / risks：`.claude` / `.opencode` 语义上属于工具状态目录，忽略后如果客户把真实业务代码放在其中，需要用户显式补充或后续高级扫描策略处理；Python 关键文件进入 evidence 只提升输入可信度，不代表当前 schema 已支持 Python primary stack。
- Sub agent 使用情况：使用两个只读 explorer 子代理并行审查 ai4se todo；一个定位 evidence 噪声、skipped 和高风险展示落点，另一个确认多栈表达和英文成熟度 blocker 是后续更大切片。
- 价值切分说明：本轮优先消化 `docs/todos/` 中 high priority 工作项，但只处理第一个可独立验收的信任问题；skipped 中文化、高风险突出、多栈建模和中文成熟度 blocker 继续保留为后续切片。
- 验收标准及验证方式：unit 覆盖 `collect_evidence()` 忽略 `.claude` / `.opencode` / `deploy-package/.opencode` 文件，并确认根 `package.json`、`pyproject.toml`、`requirements.txt` 进入 key / priority evidence。
- 完成内容：扩展 `IGNORED_DIRS` 和 `KEY_FILE_NAMES`；新增 evidence collector 单元测试固定工具工作区降噪行为；同步本 todo 的已完成切片记录。
- Self-Harness Gate：下一轮候选 gap 首选同一 todo 中的 skipped / sampled 文件信息中文化和覆盖不足说明，其次是高风险风险项突出展示，再其次是多栈表达与成熟度英文 blocker 中文化。

## 2026-05-31 Guided Init 启动边界说明

- North Star 模块：CLI Experience、Progressive Collaboration、Maturity & Evolution。
- init North Star 旅程阶段：启动与目标说明、CLI 视觉焦点。
- Gap Analysis 摘要：首次 guided `init` 在扫描前只有泛化的 `.ai` 资产说明和 `继续生成 Harness?`，用户还不知道扫描范围、后续确认范围、预计生成资产，以及 Runtime、`.ai/task-runs`、benchmark 和正式写入边界。
- 用户故事：作为首次使用 Harness Builder 的 Harness Maintainer，我希望在等待扫描前先理解本次流程会做什么、不会做什么、何时才写入正式资产，从而能判断是否继续进入耗时扫描。
- 关键决策 / 取舍：新增稳定的 `== 启动说明 ==` CLI 区块，放在已有 Harness 维护入口之后、`继续生成 Harness?` 之前；本轮只增强首次生成向导，不改变非交互输出、扫描、LLM、成熟度评分或资产 schema；generation trace 从会话开始记录，但文案明确它不同于最终确认后写入的正式 Harness 资产。
- Assumptions / risks：启动说明保持短列表，避免把首次 CLI 变成说明书；目标输出目录和已有 `.ai` 状态的更细展示留给后续阶段标题和状态 contract 切片。
- Sub agent 使用情况：使用两个只读 explorer 子代理并行审查启动说明缺口和用户补充分流缺口；本轮采纳启动说明切片，将“自然语言补充不应伪装成扫描事实”记录为后续更大契约切片。
- 验收标准及验证方式：integration 覆盖 `== 启动说明 ==` 在 `继续生成 Harness?` 和 `扫描仓库` 之前出现，包含扫描范围、确认范围、生成资产、Runtime / `.ai/task-runs` / benchmark 和最终 `confirm` 写入边界；同时断言 `--non-interactive` 不输出该 guided 启动说明。
- Self-Harness Gate：下一轮候选 gap 首选“用户扫描补充后的结构化吸收与自然语言说明分流”，避免自由文本被表达成已验证扫描事实；其次是 CLI 阶段标题统一。

## 2026-05-31 Init CLI 交付摘要增强

- North Star 模块：CLI Experience、Maturity & Evolution、Guides / Sensors、Progressive Collaboration。
- init North Star 旅程阶段：写入后的交付摘要、CLI 视觉焦点、下一步入口。
- Gap Analysis 摘要：`init` 已经在 CLI 中展示扫描、成熟度初评、用户补充影响和写入前 preview，但写入完成后的 completion message 仍只显示英文资产路径、成熟度、benchmark readiness 和少量入口；它没有完整承担 North Star 要求的 CLI-first 交付摘要职责。
- 用户故事：作为 Harness Maintainer，当我完成首次 `init` 写入后，我可以直接在 CLI 中看到本次生成结果、当前 L0-L4 成熟度、主要证据 / 缺口、Benchmark 状态、优先查看入口、仍需人工确认的问题和下一步命令，从而不用先打开 Markdown 文件也能理解初始化交付。
- 当前代码 gap：`render_init_completion_message()` 只读取 `maturity-score.yaml` 和 benchmark report，缺少生成结果清单、待确认问题摘要、优先入口原因和 CLI / Markdown 边界说明；integration 测试只覆盖“当前成熟度”和 benchmark 字段。
- 关键决策 / 取舍：本轮只增强 completion message，不改扫描、LLM、成熟度评分、资产 schema 或已有 Harness 维护入口；`questionnaire.yaml` 通过 `Questionnaire` schema 只读校验后提取待确认问题，缺失时显式提示查看 `human-input-needed.md`。
- Assumptions / risks：completion message 是交付说明，不是新的交互菜单；首次 `init` 仍不默认运行 benchmark，也不执行 Runtime task-run。
- Sub agent 使用情况：使用两个只读 explorer 子代理并行审查 guided init transcript 和 completion summary gap；两者均建议优先补齐 CLI completion summary，并把更完整 Transcript Contract V1 留作后续切片。
- 价值切分说明：本轮直接回应“CLI 工具第一优先级”，把写入后的理解和下一步从 Markdown 前移到终端，同时保留 Markdown 作为持久化材料。
- 验收标准及验证方式：unit 覆盖 completion message 的 `== 初始化完成 ==`、生成结果、成熟度、Benchmark、优先查看、仍需人工确认和 CLI-first 说明；integration 覆盖非交互与 guided init 输出均包含这些交付摘要要素，并覆盖已有 Harness `exit` / `assess` 不追加首次初始化交付摘要。
- 完成内容：`render_init_completion_message()` 改为中文 CLI-first 交付摘要；新增生成资产摘要、优先入口和待确认问题 helper；`cli.py` 通过 trace summary 区分首次生成与已有 Harness 维护动作；init workflow、todo 和演进记录同步。
- Self-Harness Gate：下一轮候选 gap 首选“首次 guided init 启动说明和阶段标题统一”，其次是“用户补充后区分结构化吸收与 notes 保存”，继续围绕 CLI-first 用户旅程推进。

## 2026-05-31 Init 资产仓库特异性增强

- North Star 模块：CLI Experience、Guides / Sensors、Maturity & Evolution、Progressive Collaboration。
- init North Star 旅程阶段：用户补充影响链路、正式资产生成、初始化交付摘要。
- Gap Analysis 摘要：guided `init` 已经能展示扫描关注点、成熟度初评和用户补充影响，但正式写入后的 `project-context.md`、`verification.md` 和 `init-summary.md` 仍偏模板化；结构化 `module/command/risk` 主要进入 inventory/catalog，团队规则和 workflow 补充进入 interaction decisions，三者缺少在正式语义资产中的完整闭环。
- 用户故事：作为 Harness Maintainer，当我在 `init` 中补充或确认模块、风险区域、验证命令和团队规则后，我希望在正式生成的 Guide、Sensor 和 init summary 中看到这些信息如何进入 Harness 资产并关联成熟度缺口，从而确认生成结果是面向当前仓库定制，而不是模板拼装。
- 当前代码 gap：`write_guide_assets()` 不消费 `CommandCatalog`；`write_sensor_assets()` 不消费 `ProjectInventory` 风险区域；`write_init_summary()` 只消费 `MaturityReport`，没有展示本仓库关键事实、用户补充和资产补缺关系。
- 关键决策 / 取舍：本轮只增强首次 `init` 的语义 Markdown，不新增机器消费 schema、不改 maturity scoring、不改 workflow policy、不把 workflow 自然语言补充直接应用为 routing 规则；扫描事实从 inventory/catalog 渲染，自然语言补充从 interaction decisions 渲染。
- Sub agent 使用情况：使用两个只读 explorer 子代理并行调研资产数据流和 benchmark 质量约束；结论支持本轮先做 Guides / Sensors / Summary 的仓库特异性注入，benchmark 语义质量评分暂缓。
- 价值切分说明：本轮面向用户完成 `init` 后最先审查的正式产物，让用户确认“扫描与补充确实改变了 Harness”，而不是只在 CLI 里看到一次性预览。
- 验收标准及验证方式：unit 覆盖 Guide/Sensor/Summary 渲染模块、风险、命令、用户补充和成熟度缺口关联；integration 覆盖 guided structured scan 补充进入 `project-context.md`、`verification.md` 和 `init-summary.md`。
- 完成内容：Guide writer 增加风险区域、验证入口和成熟度缺口关联；Sensor writer 增加风险与验证映射和成熟度缺口关联；init summary 增加本仓库关键事实、本次吸收的用户补充、资产如何补齐缺口；write assets 编排传递 inventory / commands / interaction decisions。
- Self-Harness Gate：后续继续围绕 `init` 提升交互扫描深度和产出质量；候选 gap 包括 architecture signals 进入 Guide、team rules 对 Sensor/Workflow 的更明确影响、benchmark repository-specific quality score 从 soft score 逐步增强。

## 2026-05-31 Guided Init 扫描后成熟度初评前置

- North Star 模块：CLI Experience、Maturity & Evolution、Progressive Collaboration、深度扫描。
- init North Star 旅程阶段：扫描结果友好呈现、成熟度初评与差距解释、与用户对齐扫描理解。
- Gap Analysis 摘要：guided `init` 已经有扫描发现、风险 / 不确定性 / 验证缺口分组和写入前成熟度设计预览，但成熟度解释发生在团队规则、候选审查和 Workflow 展示之后；用户在扫描补充前还不知道当前扫描会如何影响 L0-L4 等级、下一等级差距和后续 Harness 推荐。
- 用户故事：作为 Harness Maintainer，当我首次 guided `init` 扫描一个遗留仓库并准备补充或修正扫描理解时，我可以先看到基于当前扫描结果的 L0-L4 成熟度初评、下一等级差距和会影响判断的补充方向，从而知道应该优先确认哪些模块、命令、风险或团队规则。
- 当前代码 gap：`_show_prewrite_maturity_preview()` 只服务最终写入前确认；`_collect_scan_supplement()` 之前缺少成熟度语境，用户补充仍偏字段修正。
- 关键决策 / 取舍：本轮只新增 guided CLI 前置初评，复用 `build_maturity_report()`、`HarnessConfig.default()` 和 `select_weapon_library()`；不改 maturity schema、不改评分规则、不改变非交互输出和正式资产契约。
- Assumptions / risks：前置初评是基于当前扫描的写入前预测，不代表正式 Harness 已写入或 benchmark 已通过；用户后续修正后，最终写入前 preview 仍会重新计算。
- Sub agent 使用情况：使用两个只读 explorer 子代理并行审查 guided init 用户旅程和资产质量缺口。一个推荐后续做用户补充影响链路可见化；另一个推荐后续做仓库特异性资产注入与成熟度缺口叙事。
- 价值切分说明：本轮保护的是“扫描发现 -> 用户补充”之间的决策质量，让用户知道为什么要补充 hard gate、模块边界、风险区域和团队规则，而不是盲目回答字段。
- 验收标准及验证方式：integration 覆盖 `扫描后的成熟度初评` 出现在 `扫描发现` 后、`需要你补充或修正的地方` 前，并包含 L0 起步、预计基线、下一目标、主要差距和建议优先补充；非交互输出不出现该 guided 文案。
- 完成内容：`interactive_init.py` 新增扫描后成熟度初评 helper；init workflow、spec/plan 和演进记录同步。
- 全量回归修正：真实 RuoYi-Vue acceptance 暴露 DeepSeek evidence planner 偶发请求未在 `files[].path` 中的近似路径；已补一次契约修正重试，重试仍失败时继续显式失败，不放宽 allowlist、不做 Python 近似匹配、不引入确定性 fallback，并同步 LLM contract 和 prompt 精确路径要求。
- Self-Harness Gate：下一轮候选 gap 首选“用户补充影响链路可见化”或“仓库特异性资产注入”，重点让结构化补充和团队规则更明确进入 preview、summary、Guides / Sensors 和质量断言。

## 2026-05-31 Guided Init 扫描内部阶段进度

- North Star 模块：CLI Experience、Progressive Collaboration、深度扫描、可解释失败边界。
- init North Star 旅程阶段：阶段化扫描与进度反馈、扫描结果友好呈现。
- Gap Analysis 摘要：guided `init` 已有“扫描仓库”和“扫描完成”的粗粒度提示，但 `scan_repository()` 内部的 evidence 收集、LLM evidence plan、补充 evidence 读取、最终 LLM scan 和 reconcile 仍是一个阻塞调用；真实仓库和真实 LLM 场景下，用户无法判断耗时来自哪个内部阶段。
- 用户故事：作为 Harness Maintainer，当我首次 guided `init` 一个真实遗留仓库且扫描和 LLM 调用需要等待时，我可以看到正在收集 evidence、请求 LLM 规划补充 evidence、读取补充 evidence、请求最终 LLM scan 和调和扫描结果的阶段状态，从而判断程序仍在工作，并能在失败时定位失败发生在哪个阶段。
- 当前代码 gap：`scan_repository()` 没有可观察的进度事件；guided init 只能在调用前后输出粗粒度文案；非交互路径不应承担这种 UI transcript 契约。
- 关键决策 / 取舍：给 `scan_repository()` 增加 optional keyword-only progress callback 和 `ScanProgressEvent`，默认 `None`；guided init 通过签名检测兼容旧单参数 fake scan；本轮不改 LLM prompt、schema、reconciler 或正式产物契约。
- Assumptions / risks：progress event 是过程可观察性接口，不是新的落盘机器产物；事件 id 由 unit test 固定，中文文案由 guided renderer 翻译。
- Sub agent 使用情况：使用只读子代理审查 scan pipeline、monkeypatch 兼容点和测试策略；结论建议 unit 精确锁定 callback 事件序列，guided integration 只断言关键中文阶段和顺序。
- 价值切分说明：本轮面向首次 `init` 中最容易长时间等待的用户旅程，不是孤立日志；它让后续更深的交互扫描和智能 evidence expansion 有稳定的阶段可观察性基础。
- 验收标准及验证方式：unit 覆盖 collect / plan / expand / llm-scan / reconcile 的 started/completed 顺序和 details；guided integration 覆盖阶段文案出现在“扫描仓库”和“扫描完成”之间；非交互测试断言不出现 guided 阶段文案。
- 完成内容：`scan_repo.py` 新增 `ScanProgressEvent` 与 progress callback；`interactive_init.py` 接入 guided renderer；init workflow、spec/plan 和演进记录同步。
- Self-Harness Gate：后续循环按用户最新要求优先继续完善 `init` 流程深度、用户交互扫描和产出内容质量。

## 2026-05-31 Guided Init 推荐项成熟度关联

- North Star 模块：Maturity & Evolution、CLI Experience、Guides / Sensors、Progressive Collaboration。
- init North Star 旅程阶段：成熟度驱动的 Harness 设计预览、最终确认前审查。
- Gap Analysis 摘要：写入前 preview 已展示 L0 起步、写入后预计基线、整体阻断项、推荐动作、Guides / Sensors / Workflow routing，但每个 Guide / Sensor 推荐项只显示 action，未说明它关联哪个成熟度维度、解决哪个阻断项、对下一阶段能力有什么贡献。
- 用户故事：作为 Harness Maintainer，当我在首次 guided `init` 写入 `.ai/` 前审查 Harness 设计预览时，我可以看到每个即将生成的 Guide / Sensor 推荐对应的成熟度维度、正在缓解的阻断项和下一阶段贡献，从而判断这套 Harness 是围绕当前仓库的成熟度缺口生成，而不是固定模板拼装。
- 当前代码 gap：`build_maturity_report()` 已有 dimensions、blockers 和 next level requirements；weapon library 已有 kind、tags、gate 和 recommended action；但 `_show_prewrite_maturity_preview()` 没把两者关联后呈现给用户。
- 关键决策 / 取舍：本轮只改 guided CLI preview 渲染层，不改 `WeaponLibraryEntry`、`MaturityReport`、`weapon-library-selection.yaml` 或正式资产 schema；成熟度关联使用内置 weapon tags 和 planned maturity 维度做保守推导。
- Assumptions / risks：这是写入前预计基线叙事，不表示当前仓库已经达到相关成熟度；对无 blocker 的维度展示保持基线和后续 benchmark / Runtime 验证的说明。
- Sub agent 使用情况：使用两个只读 explorer 子代理并行审查 preview gap 和测试策略；结论支持本轮做 CLI 逐项 maturity linkage，并建议补一个小 unit 固定映射规则。
- 价值切分说明：本轮保护的是用户在最终确认前的审查动作，让用户能判断每个 Guide / Sensor 与 L0-L4 缺口的关系，而不是只看到资产清单。
- 验收标准及验证方式：integration 覆盖 preview 区的 Guides 和 Sensors 都出现 `关联成熟度`、`解决阻断`、`下一阶段贡献`；unit 覆盖 Guide 映射到 guides / risk_control 阻断，Sensor 映射到 sensors / verification_sophistication 阻断。
- 完成内容：`interactive_init.py` 新增 weapon preview maturity linkage helper；init workflow、spec/plan 和演进记录同步。
- 验证结果：targeted integration / unit 已通过；fast/full/push 结果见本轮提交记录。
- Self-Harness Gate：下一轮候选 gap 首选“真正的 scan 内部阶段 callback”，其次是“生成资产 Markdown 中保留推荐项成熟度来源”。

## 2026-05-31 Guided Init 扫描关注点分组

- North Star 模块：CLI Experience、Progressive Collaboration、深度扫描、成熟度叙事输入。
- init North Star 旅程阶段：扫描结果友好呈现、与用户对齐扫描理解和成熟度判断。
- Gap Analysis 摘要：guided `init` 已有扫描前/后进度提示和写入前成熟度预览，但 `_show_scan_findings()` 仍主要展示技术栈、证据、模块和命令；风险区域、scan warning、低置信度命令、无 hard gate、缺失验证类型等关注点没有在用户补充前形成清晰分组，用户不容易判断应该纠正哪里。
- 用户故事：作为 Harness Maintainer，当首次 guided `init` 扫描完成并准备补充或修正扫描理解时，我可以在 CLI 中看到按“风险区域”“不确定性”“验证缺口”“建议补充”分组的关注点摘要，从而知道哪些判断需要优先确认、哪些验证能力会影响后续 Guides / Sensors / 成熟度预览。
- 当前代码 gap：`ProjectInventory.stack_extensions` 已包含 `risk_areas`、`scan_warnings`、`needs_human_confirmation` 和 LLM proposal confidence；`CommandCatalog` 已包含 gate、source、confidence 和 type；但这些数据没有被翻译成面向用户的扫描关注点。
- 关键决策 / 取舍：本轮只改 guided CLI 渲染层，不改 schema、不改 LLM prompt、不改 scan reconciler、不改变非交互输出；缺口表达统一使用“当前扫描未确认 / 建议补充”，避免把 evidence 缺失断言为项目能力不存在。
- Assumptions / risks：旧 inventory 可能没有完整 `stack_extensions`，渲染层必须容错；风险摘要不是成熟度评分，后续成熟度仍由 preview 和 maturity report 负责解释。
- Sub agent 使用情况：使用两个只读 explorer 子代理并行审查 scan findings gap 和测试策略；结论一致建议本轮做“风险 / 不确定性 / 验证缺口分组展示”，且只用 guided integration 覆盖即可。
- 价值切分说明：本轮保护的是用户在“扫描完成 -> 输入补充”之间的判断动作，不是孤立文案；它让用户在正式生成 Guides / Sensors 前知道哪些扫描判断需要修正。
- 验收标准及验证方式：integration 覆盖 happy path 中四个关注点分组出现在“扫描发现”后、“团队规则”前；专门 fake scan 场景覆盖风险路径、scan warning、低置信度 soft command、无 hard gate 和建议补充真实 hard gate。
- 完成内容：`interactive_init.py` 新增扫描关注点摘要与 helper；README、init workflow、spec/plan 和演进记录同步。
- 验证结果：targeted guided scan attention tests 已通过；fast/full/push 结果见本轮提交记录。
- Self-Harness Gate：下一轮候选 gap 首选“Guide / Sensor 推荐与成熟度维度、阻断项的逐项关联”，其次是“真正的 scan 内部阶段 callback”。

## 2026-05-31 Guided Init 扫描进度反馈

- North Star 模块：CLI Experience、Progressive Collaboration、深度扫描、可解释失败边界。
- init North Star 旅程阶段：启动与目标说明、阶段化扫描与进度反馈、扫描结果友好呈现。
- Gap Analysis 摘要：首次 guided `init` 在用户确认继续后会直接进入 `scan_repository()`，真实仓库和真实 LLM 场景下可能长时间无输出；扫描失败时虽然 CLI 会显式失败并记录 trace，但用户无法从屏幕上判断失败发生在扫描阶段，也不知道正式 `.ai` Harness 资产尚未写入。
- 用户故事：作为 Harness Maintainer，当我首次运行 guided `init` 并确认继续后，我可以在耗时扫描开始前看到系统正在收集仓库证据、请求 LLM 结构化扫描和调和 evidence；如果扫描失败，我能看到失败阶段、原因摘要和“未写入正式 Harness 资产”的边界。
- 当前代码 gap：`run_guided_init()` 只有 trace event，没有用户可见的扫描进度；`run_non_interactive_init()` 作为自动化路径不应被改变。
- 关键决策 / 取舍：本轮只在 guided 分支的 `scan_repository()` 调用周边增加阶段提示和失败边界，不改变 `scan_repository()` 签名，不加入 callback，不拆分内部扫描 pipeline，避免破坏现有 monkeypatch 测试和非交互输出语义。更细粒度的 evidence / LLM / reconcile 分阶段 callback 保留为后续独立切片。
- 边界情况 / 失败模式及回应：扫描失败继续重新抛出原异常，不吞异常、不 fallback、不写入正式 inventory、config、Guides、Sensors 或 Workflow Skills；异常类型和消息只作为原因摘要展示。
- Sub agent 使用情况：使用两个只读 explorer 子代理并行审查实现切入点和测试策略；一个指出如给 `scan_repository()` 增加 progress 参数会破坏现有 monkeypatch，另一个建议用 `typer.echo` 调用顺序证明进度提示发生在扫描调用前。
- 价值切分说明：本轮解决的是用户在 `init` 第一段耗时等待中的可解释性和失败边界，不是内部扫描智能增强；它为后续更深的交互扫描和阶段 callback 打基础。
- 验收标准及验证方式：integration 覆盖 happy path 中 `扫描仓库` / `扫描完成` 出现在 `扫描发现` 前；失败路径 monkeypatch `scan_repository()` 抛错，断言扫描前已输出进度、失败提示包含原因和未写入正式资产，并断言正式 Harness 资产未生成。
- 完成内容：`interactive_init.py` 新增 guided 扫描开始、完成、失败渲染；init workflow 规则和 spec/plan 同步。
- 验证结果：targeted guided scan progress tests 已通过；fast/full/push 结果见本轮提交记录。
- Self-Harness Gate：下一轮候选 gap 首选“扫描结果按风险 / 不确定性 / 验证缺口分组展示”，其次是“Guide / Sensor 推荐与成熟度维度、阻断项的更精确关联”。

## 2026-05-31 Guided Init 用户补充复述与影响说明

- North Star 模块：CLI Experience、Progressive Collaboration、Maturity & Evolution、Guides / Sensors。
- init North Star 旅程阶段：扫描理解对齐、成熟度初评、深度追问、设计预览、最终确认。
- Gap Analysis 摘要：guided `init` 已能收集自然语言和结构化补充，并把它们写入部分资产；但最终确认只展示数量，用户无法在写入前看到系统如何理解这些补充，也不知道它们会影响 Guide、Sensor、成熟度预览或 Workflow 说明。CLI 阶段进度、扫描结果分组、推荐项成熟度关联和写入后 summary 一致性仍是后续 gap。
- 用户故事：作为 Harness Maintainer，当我在首次 guided `init` 中补充模块边界、真实验证命令、风险区域、团队规则或工作流说明时，我可以在写入前看到系统如何理解这些补充，以及它们会影响哪些 Guides、Sensors、成熟度预览或 Workflow 说明，从而确认 Harness Builder 不是只记录文本，而是在用我的输入调整 Harness 设计。
- 当前代码 gap：`_collect_scan_supplement()` 和 `_apply_scan_overrides()` 已能记录和应用补充，但 `_confirm_summary()` 只输出团队规则数量、hard gate 命令和 workflow 名称，缺少补充内容与影响面复述。
- 关键决策 / 取舍：不新增 LLM 语义理解；结构化补充继续更新 inventory / commands / risk，非结构化自然语言保持人工补充说明；Workflow note 只进入说明和确认记录，不直接修改 routing policy。
- Assumptions / risks：自然语言补充不能自动变成正式规则；长补充在 CLI 中只展示摘要，完整内容仍进入 interaction decisions 和 Markdown 产物。
- Sub agent 使用情况：使用两个只读 explorer 子代理分别审查 init North Star 旅程 gap 和测试覆盖缺口；两者都把“用户补充复述与影响说明”列为高价值下一步。
- 价值切分说明：本轮保护的是“渐进式协作”用户价值，不是孤立字段或文案；用户在最终确认前能看到自己的输入被系统吸收，并理解其对后续 Harness 设计的影响。
- 验收标准及验证方式：新增 integration 测试断言 `最终确认` 之后包含具体 scan note、团队规则、workflow note 和“补充影响”；断言 `interaction-decisions.yaml`、`project-context.md`、`human-input-needed.md` 保留补充；相关 guided init 测试保持通过。
- 完成内容：`interactive_init.py` 在最终确认前输出“已吸收的用户补充”和“补充影响”；init workflow 规则和 spec/plan 同步。
- 验证结果：targeted guided init tests 已通过；fast/full/push 结果见本轮提交记录。
- Self-Harness Gate：本轮强化了用户输入消费链路。下一轮候选 gap：CLI 扫描阶段进度反馈、扫描结果按风险/不确定性分组、preview 与落盘资产 / init-summary 的一致性验收。

## 2026-05-31 Guided Init 写入前成熟度预览

- North Star 模块：CLI Experience、Maturity & Evolution、Workflow Routing、Guides / Sensors。
- Gap Analysis 摘要：首次 guided `init` 已能扫描、收集补充、展示候选并写入资产，但成熟度叙事主要发生在写入完成后的 `init-summary.md` 和 CLI completion message。用户在输入 `confirm` 前无法判断当前是否从 L0 起步、写入后预计建立什么基线、下一等级缺什么，以及 `standard` workflow 如何参与高风险任务治理。
- 用户故事：作为 Harness Maintainer，当我第一次对遗留仓库运行 guided `init` 并准备确认写入 `.ai/` 前，我可以先看到当前 Harness 成熟度初评、写入后预计基线、下一目标、阻断项、推荐补齐动作，以及 Guides / Sensors / Workflow routing 设计预览，从而在写入前判断这套 Harness 是否值得接管和如何继续完善。
- 关键决策 / 取舍：不新增 LLM 调用，不提前写入 `.ai/`；复用现有 `build_maturity_report(ai=None, ...)` 计算 planned baseline，并在 CLI 中明确区分当前 L0 起点和确认写入后的预计基线。本轮不实现扫描阶段进度 callback、不重构 scan pipeline、不增强自然语言语义归因。真实 acceptance 暴露 RuoYi-Vue self-improve 的 LLM 输出过长和 evidence source 契约矛盾后，本轮只收紧 review-only LLM 输出长度约束，并把 Runtime repair loop 证据源调整为 `.ai/task-runs/` 契约路径，不引入 silent fallback。
- 边界情况 / 失败模式及回应：启动 trace 可能已创建 `.ai/runs`，但这不代表项目已有 Harness；只有已存在正式 inventory / config 时才按 partial Harness 处理。用户从最终确认返回修改 scan 后，会重新选择武器库并刷新候选报告，让下一次预览基于更新后的 inventory / commands。maturity review / asset candidate 真实 LLM 输出必须保持短 JSON；下游 review evidence source 仍只接受 Builder 提供的 `.ai/` allowlist。
- Sub agent 使用情况：使用两个只读 explorer 子代理分别审查 North Star / 代码旅程 gap 和 guided init 测试覆盖；结论共同推荐“扫描后成熟度初评 + 写入前 Harness 设计预览”作为下一轮最高价值 `init` 切片。
- 价值切分说明：本轮面向首次 `init` 用户旅程，不是内部字段补丁；它把 `init` 从“文件生成器写完后解释”推进到“写入前用成熟度框架解释设计方案”。
- 可执行验收标准及验证方式：guided init integration 覆盖成熟度预览出现在最终确认前、当前从 L0 起步、显示写入后预计基线 / 下一目标 / 阻断项 / 推荐动作、展示 Guides / Sensors / Workflow routing，并包含 `standard-escalation` 高风险升级语义；同时断言 CLI 不暴露内部 schema 字段名。
- 完成内容：`interactive_init.py` 新增写入前成熟度预览；最终确认前渲染 preview；返回 scan 后刷新 weapon selection 和候选报告；maturity review / asset candidate prompt 增加真实 LLM 输出长度约束；repair loop 无 Runtime 证据源改为 `.ai/task-runs/`；README、init workflow、LLM contracts、North Star、spec/plan 和演进记录同步。
- 验证结果：targeted guided init happy path、guided init integration、LLM prompt unit、maturity model unit 和 RuoYi-Vue real self-improve acceptance 已通过；fast/full/push 结果见本轮提交记录。
- Self-Harness Gate：本轮固定了首次 `init` 的成熟度叙事契约。下一轮候选 gap：扫描阶段进度反馈、用户自然语言补充后的复述和影响说明、Guide / Sensor 推荐与具体成熟度维度的更精确关联。

## 2026-05-31 Workflow 推荐到 Routing Policy 生命周期

- North Star 模块：Workflow Runtime Specification、Experience & Self-Improve、Maturity & Evolution、Governance & Auditability、Benchmark / Review Intelligence。
- Gap Analysis 摘要：`recommend-workflow`、`improve`、`review-maturity`、`generate-asset-candidates`、`review-candidate` 和 `benchmark` 已具备分段能力，但缺少一条可验收的纵向闭环证明智能 workflow recommendation 能进入 review-only policy candidate、经治理应用为正式 routing policy，并被 maturity evidence 与 benchmark 识别。
- 用户故事：作为 Harness Maintainer，当我先为真实任务生成 review-only workflow recommendation，再运行自改进相关命令时，我可以得到结构化 `workflow_policy_patch` 候选，并通过显式 `review-candidate --decision applied` 应用到 `.ai/harness-config.yaml`，随后 benchmark 验证候选、治理记录和正式 routing policy 一致，从而确信智能推荐不会绕过人工治理，也不会停留在孤立报告。
- 当前代码 gap：asset candidates 写出后只刷新 Experience index，没有立即刷新 maturity evidence；CLI trace 没记录派生证据；asset candidate parser 只检查 `.ai/` 前缀；workflow policy applied 未要求 source review 为 support/revise；routing rule upsert 会把替换 rule 移到末尾；benchmark 对手工或旧版本落盘的非法 workflow policy target、路径穿越和未支持 review 的 applied governance 兜底不足。
- 关键决策 / 取舍：不新增命令；复用专家链路 `recommend-workflow -> improve -> review-maturity -> generate-asset-candidates -> review-candidate applied -> benchmark`。recommendation、maturity review 和 asset candidates 仍保持 review-only；只有 candidate governance 的 `applied` 决策能修改正式 `.ai/harness-config.yaml`。
- Assumptions / risks：真实 LLM 可能生成不同 routing patch，因此 parser、schema、candidate governance 和 benchmark 必须共同兜底；maturity evidence 刷新只表示候选进入证据面，不表示候选已应用。
- 边界情况 / 失败模式及回应：`defer` / `missing` 的 workflow policy 候选不能 applied；`.ai/../...` 路径穿越被 parser 与 benchmark 拒绝；workflow policy target 只能是 `.ai/harness-config.yaml`；替换已有 routing rule 原位替换，新增 rule 才追加；benchmark 会拒绝 applied 但 source review 未 support/revise 的手工治理状态。
- Sub agent 使用情况：使用 explorer 子代理只读审查当前 milestone 的 spec、plan、测试和 benchmark 兜底；它指出 benchmark 缺少 support/revise 与安全路径兜底，主线程补充了对应负向测试和实现。
- 价值切分说明：本轮不是单纯增加 parser 校验或测试，而是打通“智能推荐 -> 改进候选 -> LLM review -> 资产候选 -> 人工治理应用 -> benchmark 证明”的完整治理生命周期。
- 可执行验收标准及验证方式：integration 覆盖完整 CLI 链路、不创建 `.ai/task-runs`、asset candidate 后 maturity evidence 计数刷新、应用后 config 顺序保持、benchmark 三个相关 check 通过；unit 覆盖 parser 路径和 workflow target、defer/missing 不能 applied、rule 原位替换；benchmark integration 覆盖旧产物/手工产物的非法 path、target 和 review decision。
- 完成内容：`generate-asset-candidates` 刷新 maturity 派生证据并记录 trace；asset candidate parser 增加安全 `.ai/` 路径和 workflow target 校验；candidate governance 增加 support/revise applied 门禁和原位 upsert；benchmark 增加 workflow policy governance 兜底；README、LLM contracts、init workflow、sensor/gate rules、spec/plan 同步。
- 验证结果：targeted lifecycle / governance / benchmark tests 已通过；fast/full/push 结果见本轮提交记录。
- Self-Harness Gate：本轮新增稳定治理边界已沉淀到长期工程文档；未恢复 `run`，未引入 Runtime 执行。下一轮候选 gap：self-improve package consumption、existing Harness 主入口对 workflow policy lifecycle 的引导、更细的 acceptance efficiency matrix。

## 2026-05-31 Runtime 运行证据成熟度门禁

- North Star 模块：Maturity & Evolution、Experience & Self-Improve、Workflow Runtime Specification、Governance & Auditability。
- Gap Analysis 摘要：Runtime task-run 已能被 Builder 只读校验并进入 Experience / Maturity evidence，但 `maturity_model.py` 仍主要按命令和 workflow 文件判断 overall，`workflow` 维度在没有 resolved Runtime 证据时也可到 L3，`repair_loop` 固定 L0，导致成熟度语义和真实任务结果脱节。
- 用户故事：作为 Harness Maintainer，当宿主 Runtime 已写出合法 `.ai/task-runs/<task-id>/` 时，我可以运行 `assess` 看到成熟度基于真实 Sensor Report、Decision Log、Handoff Summary 和 repair attempts 更新，从而判断 Harness 是否真的进入 Workflow-bound L3。
- 当前代码 gap：`overall_level` 只看命令和 workflow 文件；`workflow` 维度不区分 runtime sensor passed / failed；`observability` 和 `governance_auditability` 只看 Builder generation trace；`repair_loop` 不消费 Runtime repair attempts。
- 关键决策 / 取舍：继续不恢复 `run`，不生成 Runtime 产物；只复用 `summarize_runtime_task_runs()` 的 schema-valid summary。全部 Runtime sensor resolved 才允许 workflow / overall 到 L3；failed / skipped / unresolved sensor 是成熟度 blocker，不是 Builder 结构校验失败。
- Assumptions / risks：单个 resolved task-run 只能证明已有一次 Workflow-bound 运行证据，不能证明 L4 自适应能力；L4 仍依赖多任务趋势、Experience 治理和策略优化。
- 边界情况 / 失败模式及回应：无 task-runs 不让 `assess` 失败，但保持 L2 ceiling；存在 bad task-run 时 Runtime loader 显式失败；存在 failed/skipped/unresolved sensor 时成熟度保守停在 L2 并列出 blocker。
- Sub agent 使用情况：使用三个 explorer 子代理并行做 North Star gap、代码/测试现状和验收效率调研；结论共同指出 L3/L4 语义、workflow policy lifecycle 和 acceptance efficiency 是高优先候选。本轮选取 Runtime maturity gate。
- 价值切分说明：本轮只做“运行证据影响成熟度”的纵向切片，不实现参考 Runtime、不做 L4 趋势分析、不改变 benchmark 结构校验。
- 可执行验收标准及验证方式：unit 覆盖 passed Runtime task-run 使 workflow / observability / governance / repair_loop 和 overall 提升；failed Runtime sensor 阻止 L3 并生成 blocker；maturity evidence 既有 Runtime 汇总测试保持通过。
- 完成内容：`maturity_model.py` 消费 Runtime summary；新增 runtime resolved 判定；更新 workflow、repair_loop、observability、governance、overall 和 blocking caps；README、init workflow、spec/plan 和演进记录同步。
- 验证结果：targeted maturity tests 已通过；fast/full/push 结果见本轮提交记录。
- Self-Harness Gate：长期 Runtime 分工和成熟度门禁规则已同步。下一轮候选 gap：workflow recommendation 到 policy lifecycle 端到端验收、self-improve package consumption、acceptance efficiency matrix、过程文档中文 gate。

## 2026-05-31 Runtime Task-Run 只读摄取

- North Star 模块：Experience & Self-Improve、Maturity & Evolution、Sensors、Governance & Auditability。
- Gap Analysis 摘要：North Star 要求真实任务记录、Sensor Report、Decision Log 和 Handoff Summary 进入 Experience / Maturity；当前 Builder 已删除 `run` 并保留 Runtime artifact contract，但只统计 `.ai/task-runs` 目录数量，benchmark 不校验存在的 Runtime 产物，experience summary 也只向 LLM 注入文件名列表。
- 用户故事：作为 Harness Maintainer，当外部 Runtime 已经在 `.ai/task-runs/<task-id>/` 写出过程产物时，我可以让 Builder 只读校验并汇总这些任务结果，从而让后续 self-improve 基于可审计的运行证据，而不是只基于候选文件计数。
- 当前代码 gap：`experience_index.py` 裸统计 task-run 目录；`maturity_evidence.py` 只记录 has_runtime_task_runs；`benchmark.py` 没有 optional runtime check；`summarize_experience.py` 只注入 task-run 文件名。
- 关键决策 / 取舍：不恢复 `run`，不生成 `.ai/task-runs`，不执行 Sensors；新增 Runtime schema / loader 只读校验外部产物。缺失 task-runs 仍为 optional passed；存在但 schema、task id、workflow 或 sensor status 不一致时 benchmark 失败。
- Assumptions / risks：第一版要求 `harness-map.yaml`、`sensor-report.yaml`、`runtime-summary.yaml`、`decision-log.md` 和 `handoff-summary.md`；未来宿主 Runtime 格式变化时通过 schema 版本演进处理。
- 边界情况 / 失败模式及回应：空缺 task-runs 不阻断；坏 YAML、缺 `runtime-summary.yaml`、failed/skipped sensor 没有 summary、runtime summary 与 sensor report 不一致都会显式失败；合法 failed sensor 被视为真实任务结果，不等同于 Runtime 产物校验失败。
- Sub agent 使用情况：使用 Hume 做 North Star gap 调研，建议 Runtime Task-Run Ingestion；使用 Epicurus 做测试覆盖审查，提出 E2E 和 self-improve 纵向验收后续 gap；两者均已关闭。
- 价值切分说明：本轮只补“外部 Runtime 数据进入 Harness Builder 证据面”的纵向能力，为后续成熟度真实晋级和 self-improve 经验闭环打基础，不直接改成熟度 overall 评分。
- 可执行验收标准及验证方式：unit 覆盖合法 / 缺失 / 不一致 Runtime task-run loader、Experience index、maturity evidence、experience summary source；integration 覆盖 benchmark absent / valid / invalid Runtime task-run。
- 完成内容：新增 `RuntimeSummary` / `RuntimeTaskRunSummary` schema 与 `runtime_task_runs.py`；Experience index 改为统计 schema-valid task-runs；maturity evidence 增加 Runtime sensor / repair 汇总；benchmark 新增 `content:runtime-task-run-artifacts`；experience summary 注入 sensor / handoff / decision 详情；README 和 engineering docs 同步。
- 全量回归修正：真实 DeepSeek 验收发现 maturity review 会引用 Builder 固定生成的 `.ai/guides/project-context.md` 和 Runtime 契约目录 `.ai/task-runs/`；已补精确 evidence allowlist，仍拒绝任意未知 `.ai/guides/**` 或 `.ai/task-runs/<task-id>/**` 路径。
- 验证结果：targeted regression `66 passed`；fast/full/push 结果见本轮提交记录。
- Self-Harness Gate：长期 Runtime 分工和 benchmark 规则已同步。下一轮候选 gap：E2E 产物契约深度、过程文档中文 gate、self-improve 包被 benchmark 全量消费、成熟度 L3/L4 真实晋级语义。

## 2026-05-31 Existing Harness Maintenance Triage

- North Star 模块：CLI Experience、Maturity & Evolution、Experience & Self-Improve、Benchmark / Review Intelligence。
- Gap Analysis 摘要：已有 Harness 维护入口已经展示成熟度、benchmark 和 Experience / review signals，但仍偏计数面板。Maintainer 需要自己理解 `pending_improvements`、`asset_candidates`、`workflow_recommendations`、`schema_content_failed_checks` 的优先级和命令顺序，才能决定下一步。
- 用户故事：作为 Harness Maintainer，当我再次运行 guided `init` 进入已有 Harness 维护入口时，我可以直接看到当前最该处理的 3 个维护动作、每个动作的原因、来源文件和对应菜单动作，从而不用从一组计数里自行推断下一步。
- 当前代码 gap：`interactive_init.py` 的 `_experience_status_lines()` 已分项展示信号，但没有形成 top action、reason、source 和 next action；状态摘要与菜单之间缺少动作路由层。
- 决策：新增只读 `maintenance_triage.py` helper，基于 `MaturityReport`、`BenchmarkReport` 和 `ExperienceIndex` 生成最多 3 个 `MaintenanceAction`；不新增持久化 `.ai` 产物和 schema。
- 决策：优先级为 maturity 缺失、benchmark 未运行、schema/content benchmark 失败、候选未治理、workflow recommendation 待转化、pending improvements 需要 self-improve package；没有待处理信号时建议 `recommend-workflow`。
- Assumptions / risks：`asset_candidate_count > candidate_governance_decision_count` 只是第一版 pending 近似；后续可按 candidate id 计算 unresolved。workflow recommendation 只代表待 review routing signal，不能解释为已应用 policy。
- 边界与失败模式：triage 不执行动作、不刷新 Experience index、不覆盖正式资产、不重新计算成熟度；schema 错误继续显式失败，不降级成 missing。
- Sub agent 使用：使用 explorer 子代理只读审计 existing-Harness 状态信号来源、Top 3 action 优先级、测试位置和是否需要新 schema；结论支持第一版只读 console triage，不新增 schema。
- 价值切分：本轮服务“回到已有 Harness 后知道下一步做什么”的用户价值，不是单纯增加字段或菜单项。
- 可执行验收标准及验证方式：unit 覆盖 benchmark/schema-content 优先于候选治理和 workflow recommendation、benchmark missing、no pending fallback；integration 覆盖 existing-Harness `init -> exit` 输出 Maintenance triage 且不覆盖正式资产。
- 完成内容：新增 `MaintenanceAction` triage helper；guided existing-Harness entry 在 Experience signals 后输出 Maintenance triage；README、init workflow、todo、spec/plan 和演进记录同步。
- 验证结果：RED targeted failed with missing `maintenance_triage` module；GREEN targeted unit + integration passed；fast regression 见提交前验证。
- Self-Harness Gate：本轮未新增机器产物契约；长期 init 工作流规则已同步。下一轮候选 gap：workflow recommendation 到 routing policy 的 guided 治理闭环、self-improve candidate lifecycle/maturity delta、或真实 acceptance 验证 LLM-guided evidence expansion。

## 2026-05-31 LLM-Guided Evidence Expansion

- North Star 模块：Scanner & Analyzer、Prompt Contract、Maturity & Evolution、智能化职责边界。
- Gap Analysis 摘要：当前扫描已经是 LLM-first，但 evidence 选择仍主要由确定性 bucket、排序和 source sample 上限决定。复杂遗留仓库中关键业务风险文件可能不在固定采样前几项，导致最终 scan proposal 仍受脚本采样偏差限制。
- 用户故事：作为遗留仓库的 Harness Maintainer，当仓库文件结构不规范、关键风险代码没有落在固定采样前几项时，我希望 Harness Builder 先让 LLM 基于初始 evidence 规划需要深入读取的补充文件，再生成最终 scan proposal，从而让模块、风险区和验证建议更贴近真实代码。
- 当前代码 gap：`scan_repository()` 直接执行 `collect_evidence -> analyze_evidence_with_llm -> reconcile_scan`；`EvidenceBundle.files` 虽有完整轻量文件索引，但模型不能先选择补充读取文件。
- 决策：新增 `llm-evidence-plan-v1` 机器 prompt、`LLMEvidencePlan` schema 和 `llm_evidence_planner.py`；planner 只输出路径计划，不生成最终扫描结论。
- 决策：Python 按 allowlist 校验 requested paths，只允许来自 `EvidenceBundle.files` 的仓库内文件；非法、未知、`.ai/` 或仓库外路径显式失败，不能 fallback 成固定采样成功。
- 决策：真实无 caller 扫描路径默认执行 planner；现有 mock `llm_caller` 测试保持只注入最终 scan，显式 `evidence_planner_caller` 才测试两阶段链路。
- Assumptions / risks：多一次真实 LLM 调用会增加 acceptance 成本，但这是提升扫描智能化的核心投入；本轮最多请求 8 个文件，避免 prompt 体积失控。
- 边界与失败模式：不改变最终 `LLMScanProposal` schema，不让 LLM 直接读写文件，不恢复旧 scanner 包，不跳过 reconcile stack conflict 校验。
- Sub agent 使用：使用两个只读 explorer 子代理并行做整体 gap 和 Prompt/LLM 智能化调研；其中 Prompt/LLM 调研明确推荐 LLM-guided evidence expansion 作为最直接回应“确定性脚本太多”的下一 milestone。
- 价值切分：本轮不是单纯新增 prompt 或字段，而是让扫描从“固定采样后 LLM 判断”推进到“LLM 参与选择补充证据”的纵向智能化能力。
- 可执行验收标准及验证方式：unit 覆盖 planner JSON/schema/path allowlist 失败、被固定 source sampling 跳过的文件可进入 `llm_requested_files`、scan_repository 两阶段调用、prompt registry 自动发现资产清单。
- 完成内容：新增 evidence planner prompt / schema / tool；`EvidenceBundle` 增加 `llm_requested_files`；collector 支持 allowlisted expansion；scan_repository 接入两阶段规划；prompt asset 测试移除第二份静态清单；LLM contracts、architecture、scanner todo、spec/plan 同步。
- 验证结果：RED targeted unit failed with missing expansion implementation；GREEN targeted unit 13 passed；fast regression 见提交前验证。
- Self-Harness Gate：长期 LLM / 架构规则已同步；未新增正式 `.ai` 产物契约。本轮未跑真实 DeepSeek acceptance，后续候选 gap 包括真实仓库 acceptance 验证两阶段扫描效果、maintenance triage queue、workflow recommendation 到 routing policy 的治理闭环。

## 2026-05-31 First Init Benchmark Readiness

- North Star 模块：CLI Experience、Benchmark / Review Intelligence、Maturity & Evolution。
- Gap Analysis 摘要：首次 `init` 已生成成熟度摘要和下一步入口，但没有解释 benchmark 是否已运行、质量门禁状态是否已证明通过，以及下一步如何触发验收。已有 Harness 维护入口能显示 benchmark 状态，首次 0->1 用户仍可能把“资产生成成功”误解为“benchmark passed”。
- 用户故事：作为第一次为仓库建立 Harness 的 Harness Maintainer，当 `init` 完成第一版 `.ai` 资产生成后，我可以直接看到 benchmark 健康度目前是未运行、为什么不默认运行、应该用哪个入口完成首次质量验收，以及验收会检查哪些方面，从而知道第一版 Harness 还没有被质量门禁证明通过。
- 当前代码 gap：`init-summary.md` 只有成熟度、阻断项、下一步和 Runtime 边界；CLI completion message 只列成熟度、阻断项、下一步和入口文件；两者都不读取或解释 `.ai/benchmark-report.yaml`。
- 决策：首次 `init` 不默认运行 benchmark，只展示 benchmark readiness 和 next command，保持首次初始化反馈快速且不引入额外质量门禁写入；已有 benchmark report 时通过 `BenchmarkReport` schema 展示 status、quality status 和 failed check count。
- 决策：把 `## Benchmark 健康度` 纳入 `init-summary.md` 稳定章节，并让 benchmark 自身检查该章节和 `benchmark_status=` / `quality_status=`，防止后续摘要退化。
- Assumptions / risks：当前 POC 更适合显式 benchmark；未来可增加“初始化后立即运行 benchmark”的可选动作。本轮只解释 readiness，不改变真实验收边界。
- 边界与失败模式：不调用 `run_benchmark()`，不生成 `.ai/benchmark-report.yaml`，不改变 standalone / existing-Harness guided `benchmark` 行为；已有 benchmark report schema 错误时显式失败。
- Sub agent 使用：使用 explorer 子代理只读审查首次 init benchmark readiness 的边界、是否默认运行 benchmark、验收测试和长期文档影响；结论支持先做 readiness，不默认执行 benchmark。
- 价值切分：本轮服务首次用户“知道 Harness 尚未验收”的独立价值，不是内部字段或测试补丁。
- 可执行验收标准及验证方式：integration 覆盖首次 init Markdown 和 CLI 输出包含 benchmark readiness / next command，并确认不创建 `.ai/benchmark-report.yaml`；unit 覆盖已有 benchmark report 时 readiness 通过 schema 展示 failed checks；benchmark 内容检查覆盖 `## Benchmark 健康度`。
- 完成内容：`init_summary.py` 新增 benchmark readiness helper；`init-summary.md` 和 completion message 输出 readiness；benchmark 检查、README、init workflow、testing strategy、sensor/gate rules、strategy、todo、spec/plan 和演进记录同步。
- 验证结果：RED targeted integration failed；GREEN targeted integration + unit passed；fast regression 见提交前验证。
- Self-Harness Gate：长期规则已同步到 strategy / engineering / todo；无新增机器契约。下一轮候选 gap：更完整的候选列表浏览 / 编号选择；可选立即运行 benchmark 的 guided 交互；或拆分 `interactive_init.py` 维护入口降低后续迭代成本。

## 2026-05-31 Guided Candidate Apply Preview

- North Star 模块：CLI Experience、Experience & Self-Improve、Maturity & Evolution、Governance & Auditability。
- Gap Analysis 摘要：已有 Harness 维护入口已支持 `review-candidate` 并允许单个 Guide / Sensor 候选 `applied`，但 Maintainer 在输入决策前只能看到候选字段，看不到正式资产写入影响、重复 marker 状态或即将追加的内容 diff。open todo 仍要求补 guided apply 前 diff / summary。
- 用户故事：作为 Harness Maintainer，当我在已有 Harness 的 guided `init -> review-candidate` 中审查一个 Guide / Sensor 候选并可能选择 `applied` 时，我可以在输入决策前看到它会写入哪个正式资产、采用什么应用方式、是否已有重复 marker，以及将追加的内容 diff 摘要，从而避免盲目把 review-only 候选固化进正式 Harness。
- 当前代码 gap：`_asset_candidate_detail()` 展示 id、kind、target、risk、evidence 和 acceptance checks；`review_candidate()` 底层已有 marker 防重和路径边界，但这些信息没有在用户决策前暴露。
- 决策：新增 CLI-only `_asset_candidate_apply_preview()`，只读目标文件状态并生成 unified append diff 片段；实际写入、重复应用阻断和 governance 仍由 `review_candidate()` 负责。
- 决策：不新增二次确认；当前 guided 流程已经要求用户显式输入 `applied`，本轮只把 summary / diff 放到 decision prompt 前。workflow policy 继续显示 expert-command preview 并拒绝 guided apply。
- Assumptions / risks：diff 片段覆盖 marker、heading、rationale 和 candidate draft 关键新增行，足以支持第一步审查；完整候选浏览器和结构化 workflow policy diff 仍留给后续。
- 边界与失败模式：不新增 LLM / prompt / schema，不批量 apply，不应用 workflow policy，不创建 `.ai/task-runs`。重复 marker 预览为 `present`，实际 `applied` 仍显式失败并不写 governance。
- Sub agent 使用：使用 explorer 子代理只读审计 review-candidate apply 支持、风险边界和验收建议；主线程采纳 summary + diff 方向，但暂缓二次确认和完整候选浏览器以保持切片小而可验收。
- 价值切分：本轮保护“正式应用候选前的用户审查决策”，不是单纯增加字段，也不是做泛化 UI。
- 可执行验收标准及验证方式：integration 覆盖 Guide candidate apply 前输出 target/mode/target_exists/duplicate_marker/block heading/source report/unified append diff；integration 覆盖 duplicate marker preview 后 applied 显式失败且不写 governance；integration 覆盖 workflow policy preview 显示 expert command required 且仍拒绝 guided apply。
- 完成内容：新增 apply preview helper；guided `review-candidate` 在 decision prompt 前输出 preview；底层治理失败在 guided CLI 中显式记录 trace 并作为 `BadParameter` 暴露；README、init workflow、todo、spec/plan 和演进记录同步。
- 验证结果：RED targeted integration 3 failed；GREEN targeted integration 3 passed；fast regression 见提交前验证。
- Self-Harness Gate：本轮无新增机器契约；长期 init workflow 边界已更新。下一轮候选 gap：更完整的候选列表浏览 / 编号选择；首次 `init` 后 benchmark 健康度解释与下一步治理节奏；或拆分 `interactive_init.py` 维护入口降低后续迭代成本。

## 2026-05-31 Existing Harness Workflow History Status

- North Star 模块：CLI Experience、Workflow Runtime Specification、Experience & Self-Improve、Maturity & Evolution。
- Gap Analysis 摘要：open todo 只剩“成熟度驱动的 init 主向导与命令信息架构重构”；当前 `recommend-workflow` 已保留历史并让 Experience / Maturity 统计多次 recommendation，但已有 Harness 维护入口仍只展示 `workflow_recommendations=<count>`，Maintainer 无法直接看到最近一个待审核 routing signal。Prompt 集中管理经代码、测试和工程文档检查已基本落地，本轮不再重复处理。
- 用户故事：作为 Harness Maintainer，当我再次运行 guided `init` 查看已有 Harness 状态时，我可以直接看到 workflow recommendation 历史中的最新任务、推荐 workflow、风险和待审核状态，从而判断是否需要进入 `improve` 或 `review-candidate` 处理 routing policy gap。
- 当前代码 gap：`interactive_init.py` 的 Experience / review signals 只显示 workflow recommendation count；guided `recommend-workflow` 已写 history artifacts，但输出和 trace artifacts 仍只列 latest recommendation 文件。
- 决策：新增 `_workflow_recommendation_status_lines()`，优先消费 `.ai/review/workflow-routing-recommendations/index.yaml` 的 `WorkflowRecommendationHistory`，没有 history 时兼容 `.ai/review/workflow-routing-recommendation.yaml` 的 `WorkflowRecommendationReport`；schema 无效时显式失败，不伪装成 missing。
- 决策：guided `recommend-workflow` 输出和 trace 同步记录 latest compatibility files、history index、history summary、Experience index 和 maturity evidence，让主向导状态与 standalone 命令产物保持一致。
- Assumptions / risks：一行 latest signal 足以支撑第一步维护入口判断；完整历史浏览、候选 diff / summary 和 workflow policy guided apply 留给后续小切片。旧 latest 与新 history 同时存在时优先信任 history index。
- 边界与失败模式：不执行 Runtime，不创建 `.ai/task-runs`，不修改正式 routing policy，不改变 LLM router prompt/parser，不改变 Experience / Maturity 计数模型；history schema 或 latest schema 错误直接失败。
- Sub agent 使用：使用 explorer 子代理只读审计 open todos、North Star 候选 gap 和 Prompt 集中管理现状；结论支持先收口当前 workflow history status WIP，并确认它属于 maturity-driven init 主向导价值链。
- 价值切分：本轮不是单纯增加字段或测试，而是把已存在的机器历史计数转成 Maintainer 在主入口可审查、可接管的最新 routing signal。
- 可执行验收标准及验证方式：integration 覆盖 history index 有两条 recommendation 时 `init -> exit` 展示 count/latest id/task/workflow/risk/status/source；integration 覆盖 legacy latest 无 history 时仍展示 task/workflow/risk/status/source；integration 覆盖 guided `recommend-workflow` 输出和 trace artifacts 包含 history index / summary，且不创建 `.ai/task-runs`、不覆盖正式资产。
- 完成内容：新增 existing-Harness latest workflow recommendation 状态 helper；guided `recommend-workflow` trace/output 补 history artifacts；README、init workflow、spec/plan 和演进记录同步。
- 验证结果：RED targeted integration 3 failed；GREEN targeted integration 3 passed；fast regression 见提交前验证。
- Self-Harness Gate：本轮更新了长期 init workflow 边界和 README；无需新增 schema 或 benchmark，因为 history schema / benchmark 已在上一轮完成。下一轮候选 gap：guided candidate governance 的候选浏览与 apply 前摘要/diff；首次 `init` 后 benchmark 健康度解释与下一步治理节奏；或 `interactive_init.py` 维护入口拆分以降低后续迭代成本。

## 2026-05-31 Test Loop Slices

- North Star 模块：Benchmark / Review Intelligence、Maturity-driven Evolution、工程验证体系。
- Gap Analysis 摘要：目标模式连续小步演进依赖快速且可信的验证反馈；当前只有 `scripts/test-fast.sh` / `test-full.sh` / `test-acceptance.sh` 三层入口，开发中常要手写 pytest target，commit hook 还可能重复运行刚刚通过的 fast regression。当前工作树已有脚本切片草稿，但缺少测试、文档和 stamp 安全边界。
- 工程信任故事：作为 Harness Builder 维护者或目标模式 Codex，当我在一轮小功能中只修改某类能力时，我可以运行命名清晰的测试切片，并让 pre-commit 复用刚刚通过的 fast regression，从而缩短反馈循环，同时不削弱 push 前 full / acceptance 验收边界。
- 当前代码 gap：`scripts/test-fast.sh` 无 stamp 缓存；没有 unit / integration / guided-init / LLM-contract / acceptance 常用切片入口；脚本行为缺少测试；原草稿把 stamp 写入 `.git`，在 Codex sandbox 中会导致测试已通过但脚本失败。
- 决策：新增共享 `scripts/lib-test-env.sh` 和常用切片脚本；fast stamp 只在完整 fast 通过后写入 `.pytest_cache/harness-builder-test-fast.stamp`，pre-commit 只在指纹匹配时跳过重复 fast。
- 决策：切片脚本只服务开发反馈，不替代 `scripts/test-fast.sh`、`scripts/test-full.sh` 或真实 acceptance；Codex 创建 commit 前仍必须主动运行 fast。
- Assumptions / risks：`.pytest_cache/` 已被 ignore，适合放本地验证缓存；指纹覆盖 HEAD、tracked/staged/untracked 非 ignored 文件，但不覆盖虚拟环境、外部服务或 ignored 文件，因此只表示当前工作树 fast regression 通过。
- 边界与失败模式：pytest 失败不写 stamp；targeted fast 不写 whole-tree stamp；stamp 损坏或指纹缺失时不跳过；acceptance 缺 key / 缺真实仓库仍显式失败。
- Sub agent 使用：使用 explorer 子代理只读审计未提交脚本改动、规则一致性、测试缺口和风险，结论要求补脚本测试、文档和 `.git` stamp 风险修正。
- 价值切分：本轮只优化测试循环入口与 pre-commit 去重，不改变测试覆盖范围、不改变 acceptance 是否进入 CI，也不调整产品功能。
- 可执行验收标准及验证方式：unit 覆盖脚本 bash 语法、README 切片文档、`.pytest_cache` stamp、stamp 匹配/失配和切片脚本选项；shell targeted checks 覆盖 unit/integration/guided-init/LLM-contract 脚本；fast regression 覆盖全量默认快速测试。
- 完成内容：新增测试切片脚本和共享 helper；`test-fast.sh` 支持 target passthrough 和 safe stamp；pre-commit 支持 stamp 命中跳过；README、testing strategy、todo、spec/plan 和演进记录同步。
- 验证结果：targeted regression 见本轮验证；fast regression 见提交前验证。
- Self-Harness Gate：测试脚本行为已纳入 unit 测试，长期规则已沉淀到 README 和 testing strategy。下一轮候选 gap：existing-Harness 状态展示 latest recommendation id、guided apply 前 diff/summary，或 benchmark/interactive init 大文件拆分。

## 2026-05-31 Workflow Recommendation History

- North Star 模块：Workflow Runtime Specification、Experience & Self-Improve、Maturity & Evolution、Benchmark / Review Intelligence。
- Gap Analysis 摘要：`recommend-workflow` 已能生成 review-only 最新推荐并刷新 Experience / Maturity，但每次都会覆盖 `.ai/review/workflow-routing-recommendation.*`；Maintainer 无法审计多次任务路由判断，Experience 也只能把推荐计数为 1，难以识别重复 routing gap。
- 用户故事：作为 Harness Maintainer，当我在已有 Harness 上为多个真实任务运行 `recommend-workflow` 时，我可以保留每一次 review-only workflow recommendation 的独立记录和索引，从而审计任务路由判断的演进，并让 Experience / Maturity 能识别重复 routing gap。
- 当前代码 gap：`recommend_workflow()` 只写 latest 文件；`experience_index` 只读取单个 latest YAML；benchmark 只校验单份 workflow recommendation pair。
- 决策：保留 latest 文件作为兼容出口，同时新增 `.ai/review/workflow-routing-recommendations/<recommendation_id>.*`、`index.yaml` 和摘要 Markdown。Experience index 优先读取 history index，没有 history 时再兼容 legacy latest。
- 决策：history 是确定性审计层；LLM 仍只输出单次 `WorkflowRecommendationReport`，Python 负责 history id、schema、索引、Markdown 摘要和 benchmark 校验。
- Assumptions / risks：保留 latest 是最低风险兼容策略；history 目录增加 review 复杂度，因此用机器 index 和稳定 summary 控制可读性。history 缺失条目或 Markdown 章节时 benchmark 必须失败。
- 边界与失败模式：不实现 Runtime execution history，不创建 `.ai/task-runs`，不应用 routing policy，不改变 LLM router prompt/parser；history index schema 无效或条目 YAML/Markdown 不配对时显式失败。
- Sub agent 使用：使用 explorer 子代理只读调研 integration / benchmark 既有测试模式和 helper 位置；主线程并行完成 RED 测试、实现、文档和验证。
- 价值切分：本轮完整覆盖“多任务 workflow recommendation 可审计历史”这一用户故事；不拆成单纯 schema、字段或文件改动，也暂缓 UI 历史浏览、diff 和 Runtime 任务轨迹。
- 可执行验收标准及验证方式：unit 覆盖 `WorkflowRecommendationHistory` schema 和 Experience history 计数；integration 覆盖两次 CLI recommendation 后 history 有两条、latest 指向第二条、Experience/Maturity 计数为 2、trace 记录 history artifact 且不生成 `.ai/task-runs`；benchmark integration 覆盖 history 缺 Markdown 时失败；README 和 engineering docs 同步。
- 完成内容：新增 workflow recommendation history schema；`recommend-workflow` 写入历史条目、index 和 summary；Experience / Maturity 消费 history count；benchmark 校验可选 history artifacts；README、architecture、init workflow、sensor/gate rules、spec/plan 同步。
- 验证结果：targeted regression 见本轮验证；fast regression 见提交前验证。
- Self-Harness Gate：本轮新增稳定 `.ai/review/workflow-routing-recommendations/` 机器契约，已纳入 schema、integration、benchmark 和长期工程文档。下一轮候选 gap：guided apply 前 diff/summary、测试脚本分层与 fast/full 耗时优化、或 existing-Harness 状态中展示 latest recommendation id。

## 2026-05-31 Guided Candidate Apply

- North Star 模块：CLI Experience、Experience & Self-Improve、Maturity & Evolution、Governance & Auditability。
- Gap Analysis 摘要：已有 Harness 维护入口已支持 `improve`、`self-improve`、`recommend-workflow` 和候选治理；standalone `review-candidate` 已能安全应用 Guide / Sensor Markdown 和结构化 workflow policy patch。但 guided `init` 只能记录 `accepted` / `deferred` / `rejected`，Maintainer 仍需离开主入口使用专家命令才能正式接管低风险 Guide / Sensor 候选。
- 用户故事：作为 Harness Maintainer，当我在已有 Harness 上再次运行 guided `init` 并查看 self-improve 生成的 Guide / Sensor 候选时，我可以审查单个候选的目标路径、证据、风险和验收检查，并明确选择 `applied` 将它写入正式 Markdown，从而完成一条可审计的自改进接管闭环。
- 当前代码 gap：`interactive_init.py` 对所有 `applied` 决策一律失败；候选详情只展示列表摘要，没有在决策前展示 evidence sources、acceptance checks 和 apply boundary。
- 决策：guided 入口复用现有 `review_candidate()`，只放开 Guide / Sensor 单候选 `applied`；workflow policy 在 guided 入口继续失败并提示专家命令，因为它涉及 `.ai/harness-config.yaml` 结构化 patch 审核。
- Assumptions / risks：Guide / Sensor Markdown 追加式应用是当前最低风险的正式接管动作；错误经验固化仍有风险，因此本轮保持单候选、显式 id、rationale 必填、候选详情展示和底层路径校验。
- 边界与失败模式：不批量应用，不开放 guided workflow policy apply，不从自由文本推断配置变更，不执行 Runtime，不创建 `.ai/task-runs`。未知 candidate id、空 rationale、非 `.ai/` suggested path 和重复 applied 继续显式失败。
- Sub agent 使用：使用 explorer 子代理审计 existing-Harness 候选治理闭环，结论建议优先补 guided 单候选安全采纳；另两个 explorer 并行审计 workflow recommendation history 和测试效率脚本，作为后续候选 gap。
- 价值切分：本轮只补 Guide / Sensor 候选的 guided apply 接管闭环；暂缓 workflow recommendation history、guided apply diff/summary、workflow policy guided apply 和测试脚本分层。
- 可执行验收标准及验证方式：integration 覆盖 guided `init -> review-candidate -> applied` 成功追加 Guide candidate marker、记录 governance `applied_paths`、刷新 Experience index、trace artifacts、不重新扫描、不创建 `.ai/task-runs`、不覆盖其他正式资产；integration 覆盖 guided workflow policy `applied` 显式失败且不写 governance。
- 完成内容：guided `review-candidate` 展示候选详情并允许 Guide / Sensor `applied`；candidate governance summary 输出真实 applied path count；README、init workflow 规则、maturity-driven init todo 和演进记录同步更新。
- 验证结果：targeted regression 9 passed；fast regression 见本轮提交前验证。
- Self-Harness Gate：本轮只改变 `init` 维护入口和候选治理文档；不需要新增 schema。下一轮候选 gap：workflow recommendation history、guided apply 前 diff/summary、测试脚本分层与 acceptance 分组。

## 2026-05-31 LLM Evidence Source Whitelist Hardening

- North Star 模块：Benchmark / Review Intelligence、Experience & Self-Improve、Prompt Contract、Maturity & Evolution。
- Gap Analysis 摘要：North Star 要求自改进产物可审计、可追溯；当前 workflow recommendation、maturity review、asset candidates 和 benchmark 已拒绝 `.ai/` 外路径，但仍允许未知 `.ai/` 路径伪装成 evidence source。experience summary parser 已有类似白名单校验，说明该约束应提升为跨 LLM review-only 产物的统一契约。
- 工程信任故事：作为 Harness Maintainer，当我审阅 LLM 生成的 recommendation / review / candidate / experience summary 时，我可以相信每个 `evidence_sources` 都来自 Builder 提供或上游结构化产物中的证据，从而避免无法追溯的智能建议进入自改进闭环。
- 当前代码 gap：`llm_workflow_router.py` 只校验 `.ai/` 前缀；`llm_maturity_reviewer.py` 和 `llm_asset_candidate_generator.py` 未校验 evidence source；benchmark 对可选 review artifact 也只检查前缀，没有验证来源是否在 allowlist 中。
- 决策：新增共享 `tools/evidence_sources.py`，由 LLM 编排函数基于 `MaturityEvidencePack`、`ImprovementCandidateReport`、`MaturityReviewReport` 和 `ExperienceSummaryReport` 构建 allowlist；parser 必须显式接收 allowlist。Benchmark 从落盘 schema artifact 构建 allowlist，不使用任意 `.ai/**` glob。
- Assumptions / risks：核心成熟度输入、experience index source 和上游候选 evidence source 是可引用证据；空 `evidence_sources` 暂不 hard fail，本轮只拒绝明确伪造或未知的路径。真实 LLM 可能因引用未提供路径而更早失败，这是期望的 no silent fallback 行为。
- 边界与失败模式：非 `.ai/` evidence source 继续以 `evidence_source_outside_ai` 失败；未知 `.ai/` evidence source 以 `unknown_evidence_source` 失败；allowlist 依赖的上游 schema 无效时 benchmark 记录 `invalid_evidence_allowlist_source:*`，不静默放行。
- Sub agent 使用：使用两个只读 explorer 子代理并行审计 LLM parser 和 benchmark 的 evidence source 缺口；主线程整合后选择本轮 hardening milestone，并负责测试、实现、文档和验证。
- 价值切分：本轮只做 evidence source 可追溯性 hardening；暂缓 recommendation history、guided apply diff/summary、candidate UX 和 acceptance 测试耗时优化。
- 可执行验收标准及验证方式：unit 覆盖 workflow recommendation、maturity review、asset candidate parser 拒绝未知 `.ai/` evidence source；benchmark integration 覆盖四类落盘 review-only artifact 引用未知 source 时失败；工程文档和 todo/archive 同步。
- 完成内容：新增 evidence source allowlist helper；接入三个 LLM parser 和 benchmark 四类可选 review artifact；归档 todo，更新 LLM contract、sensor/gate rules、spec/plan 和演进记录。
- 验证结果：targeted regression `75 passed`；fast regression 见本轮提交前验证。
- Self-Harness Gate：长期规则已沉淀到 `docs/engineering/llm-contracts.md` 和 `docs/engineering/sensor-and-gate-rules.md`；todo 已归档；未新增正式 `.ai` 产物契约。下一轮候选 gap：existing-Harness guided apply 前 diff/summary、workflow recommendation history、或把 full/acceptance 测试拆成更细的目标模式验证脚本。

## 2026-05-31 Goal Mode Retrospective Hardening

- North Star 模块：CLI Experience、Prompt Contract、Benchmark / Review Intelligence、Experience & Self-Improve。
- Gap Analysis 摘要：用户指出前几轮目标提示词不完整后，本轮用主线程和只读子代理回顾最近 13 个本地提交。结论是功能方向没有明显偏离北极星，但存在审计轨迹与契约硬度缺口：existing-Harness 状态摘要过粗、workflow recommendation LLM 缺字段可被 schema 默认值掩盖、maturity review 缺 review-only 状态与 Markdown 边界、formal asset snapshot 覆盖不完整，以及 todo / README 的少量陈旧描述。
- 当前代码 gap：`interactive_init.py` 只输出 Experience 总数；`llm_workflow_router.py` 和 `llm_maturity_reviewer.py` 未要求模型显式返回所有顶层契约字段；`MaturityReviewReport` 没有 `review_status`；benchmark 未要求 maturity review Markdown 的 `## Review Boundary`；guided 维护测试未 snapshot architecture guide 与 task templates。
- 决策：本轮做 hardening 小切片，不改变正式资产应用语义，不实现 guided apply，不恢复 Runtime / `run`。把 evidence source 白名单作为独立 high-priority todo，避免混入过大的跨 LLM 工具改造。
- Assumptions / risks：显式字段校验可能让真实 LLM 更早失败，这是期望行为；prompt 已同步给出完整模板。状态摘要只读，不刷新 index、不跑 benchmark、不写文件，保持 `exit` 路径不覆盖资产。
- 边界与失败模式：缺失 `experience-index.yaml`、`benchmark-report.yaml`、`self-improve-package.yaml` 等状态文件时显示 missing / not_available；schema 无效继续显式失败，不静默降级。
- Sub agent 使用：启动两个只读 explorer 子代理分别审计文档/spec/plan/evolution 记录和 guided init/self-improve 代码契约；另一个既有 explorer 审计 existing-Harness 状态摘要字段。主线程综合结果后选择本轮修复切片。
- 价值切分：修复 parser / prompt / benchmark / CLI 状态摘要 / 测试盲区 / 文档一致性；暂缓 evidence source whitelist、guided apply diff 和 recommendation history。
- 验收方式：unit 覆盖 LLM 显式 `review_status` 缺失失败；integration 覆盖 maturity review review-only 边界、benchmark 缺边界失败、existing-Harness 分项状态摘要，以及 guided actions formal asset snapshot。
- 验证结果：targeted regression 62 passed；fast regression 见本轮提交前验证。
- Self-Harness Gate：README、init workflow、LLM contracts、guided init todo、follow-up todo、spec、plan 和演进记录已同步；下一轮候选 gap 首选 evidence source whitelist hardening，其次是 existing-Harness guided apply 前 diff / summary 或 recommendation history。

## 2026-05-31 Existing Harness Self-Improve Action

- North Star 模块：CLI Experience、Experience & Self-Improve、Maturity & Evolution。
- Gap Analysis 摘要：已有 Harness 维护入口已支持复评、改进候选、benchmark、workflow recommendation 和候选治理记录，但智能自改进包仍只能通过 standalone `self-improve` 触发。guided apply 和 recommendation history 也有价值，但会引入正式资产变更或新存储模型。
- 当前代码 gap：`interactive_init.py` 没有 self-improve 动作，Maintainer 需要记住专家命令才能触发 LLM maturity review 和 asset candidates。
- 决策：新增 guided `self-improve` 动作，复用 `run_self_improve()`，生成 maturity review、asset candidates 和 self-improve package，并在 init trace 中记录 candidate counts。
- 决策：该动作必须是显式用户选择；首次 `init` 仍不默认执行 self-improve。
- Assumptions / risks：真实 DeepSeek 可能耗时或失败；失败必须显式暴露，不 fallback。用户可能误解为自动应用 Harness，因此输出和文档强调 review-only、applied_paths=0、无 Runtime。
- 边界与失败模式：不重新扫描；不覆盖正式 Guides、Sensors、Workflow Skills、配置、inventory 或扫描产物；不执行 Runtime；不创建 `.ai/task-runs`；不应用 asset candidates。
- Sub agent 使用：启动 explorer 子代理审计 guided self-improve 的适配性、边界、测试和风险；主线程并行完成 RED 测试与实现。
- 价值切分：本轮只把既有 self-improve 能力接入主向导，不修改 prompt、schema、acceptance 或 candidate apply。
- 验收方式：integration mock LLM 覆盖 guided action，断言 SelfImprovePackageManifest schema、Benchmark self-improve package check、trace artifacts、不扫描和正式资产未变。
- 验证结果：targeted integration 已通过；fast regression 见本轮提交前验证。
- Self-Harness Gate：README、init workflow、todo 和演进记录已同步；下一轮候选 gap 包括 guided apply diff/summary、candidate list UX 增强、recommendation history 或拆分过大的 `interactive_init.py`。

## 2026-05-31 Existing Harness Candidate Governance Action

- North Star 模块：CLI Experience、Experience & Self-Improve、Maturity & Evolution。
- Gap Analysis 摘要：已有 Harness 维护入口已经支持复评、改进候选、benchmark 和 workflow recommendation，但“处理待确认候选”仍只能通过 standalone `review-candidate`。guided self-improve 和 recommendation history 也有价值，但候选治理更直接补齐接管闭环。
- 当前代码 gap：`interactive_init.py` 没有候选治理入口；Maintainer 必须记住 candidate id、decision、rationale 等专家命令参数。
- 决策：新增 guided `review-candidate` 动作，第一版只支持 `accepted`、`deferred`、`rejected`，复用 `review_candidate()` 写 `.ai/review/candidate-governance.*` 并刷新 Experience index。
- 决策：guided 模式显式拒绝 `applied`；正式资产应用仍留给 standalone 专家命令，因为 apply 会修改 Guides、Sensors 或 `.ai/harness-config.yaml`，需要更完整的 diff / summary UX。
- Assumptions / risks：非 applied 决策足以形成第一步可审计治理闭环；用户可能误以为 accepted 会自动应用，因此菜单、文档和输出都强调 applied_paths=0。
- 边界与失败模式：不重新扫描；不调用 LLM；不执行 Runtime；不创建 `.ai/task-runs`；不覆盖正式 Harness 资产；缺少 asset-candidates、未知 candidate id、空 rationale 或非法 decision 必须显式失败。
- Sub agent 使用：启动 explorer 子代理审计 guided candidate governance 的可行性、是否应排除 applied、风险和验收标准；主线程并行完成 RED 测试和实现。
- 价值切分：本轮只记录治理决策，不实现候选列表浏览、编号选择或 guided apply。
- 验收方式：integration 准备 review-only asset candidate，走 guided `init` 记录 accepted 决策，断言 CandidateGovernanceLog schema、Experience index、trace artifacts、不扫描和正式资产未变。
- 验证结果：targeted integration 已通过；fast regression 见本轮提交前验证。
- Self-Harness Gate：README、init workflow、todo 和演进记录已同步；下一轮候选 gap 包括 guided self-improve 入口、候选列表浏览 UX、guided apply 的 diff/summary 设计或 recommendation history，仍以下轮 Current State Gap Analysis 为准。

## 2026-05-31 Existing Harness Recommend Workflow Action

- North Star 模块：CLI Experience、Workflow Runtime Specification、Experience & Self-Improve。
- Gap Analysis 摘要：standalone `recommend-workflow` 已具备 LLM 结构化推荐、schema 校验、review-only artifact、Experience/Maturity 刷新和 benchmark 检查，但普通用户仍需记住专家命令及参数。candidate governance 菜单价值也高，但会涉及正式资产 apply 边界，复杂度更高。
- 当前代码 gap：已有 Harness 维护入口支持 `exit` / `assess` / `improve` / `benchmark` / `reinit`，没有从主向导输入 task brief 生成 workflow recommendation 的入口。
- 决策：新增 guided `recommend-workflow` 动作，收集任务说明和 task id，复用 `recommend_workflow()` 生成 `.ai/review/workflow-routing-recommendation.*`，再刷新 Experience / Maturity 派生证据。
- 决策：推荐产物是单份“最新推荐”review-only 文件；本轮不扩展历史存储模型，不生成多任务 recommendation registry。
- Assumptions / risks：任务说明不能为空；真实 LLM 缺 key、非法 JSON、schema 错误或引用未知 workflow/rule 时显式失败，不 fallback。推荐结果不能被解释为已执行或已应用 routing policy。
- 边界与失败模式：不重新扫描；不覆盖正式 Guides、Sensors、Workflow Skills、配置、inventory 或扫描产物；不创建 `.ai/task-runs`；不执行 Sensors；不修改业务代码。
- Sub agent 使用：使用 explorer 子代理只读审计 guided `recommend-workflow` 的适配性、交互输入、review-only 边界、测试与风险；结论支持作为下一小 milestone，并提醒单份推荐会刷新最新产物。
- 价值切分：本轮只补主向导入口；候选治理菜单、recommendation 历史记录和 guided self-improve 保留后续。
- 验收方式：integration mock LLM 覆盖 guided action，断言 schema、Markdown review boundary、Experience/Maturity 计数、benchmark 可验收、不扫描、不覆盖正式资产和 trace summary。
- 验证结果：targeted integration 已通过；fast regression 见本轮提交前验证。
- Self-Harness Gate：README、init workflow、todo 和演进记录已同步；下一轮候选 gap 首选 existing-Harness candidate governance 菜单或 guided self-improve 入口，具体仍以下轮 Current State Gap Analysis 为准。

## 2026-05-31 Existing Harness Benchmark Action

- North Star 模块：CLI Experience、Benchmark / Review Intelligence、Maturity & Evolution。
- Gap Analysis 摘要：再次执行 `init` 已能展示最近 benchmark 状态，并支持 `exit` / `assess` / `improve`，但用户仍需记住 standalone `benchmark` 命令才能刷新质量门禁；这与 North Star 中“向导组织底层能力”的目标不一致。
- 当前代码 gap：`interactive_init.py` 的已有 Harness 维护入口没有 `benchmark` / `bench` 动作，未知输入会默认退出；README 和 init workflow 文档也未说明 guided benchmark 的写边界。
- 决策：在已有 Harness 维护入口加入 `benchmark` 动作，复用 `run_benchmark(repo, profile=inventory.primary_stack, trace=trace)`，输出 hard status、quality status、check 计数和失败项，并将最终 init trace summary 覆盖为 `existing_harness_action: benchmark`。
- 决策：guided `benchmark` 维护动作失败时不返回非零退出码；它是人工维护入口的状态刷新动作，失败必须显式写入输出、trace 和 `.ai/benchmark-report.yaml`。CI / 自动化仍使用 standalone `benchmark`，保持失败时非零退出。
- Assumptions / risks：benchmark 不是只读动作，会刷新 maturity、improvement、experience index 等派生产物；本轮只承诺不覆盖正式 Guides、Sensors、Workflow Skills、配置、inventory 和扫描产物。
- 边界与失败模式：不重新扫描；不调用 LLM；不应用候选；不生成 `.ai/task-runs`；benchmark failed 不能被改写为 passed 或隐藏失败项。
- Sub agent 使用：使用 explorer 子代理审查候选 gap 和实现陷阱，确认该 milestone 优先级最高，并指出要避免把该动作描述为只读。
- 价值切分：一轮只补 existing-Harness guided `benchmark`，暂缓 guided `recommend-workflow` 和 candidate governance 菜单。
- 验收方式：integration 覆盖通过路径与失败项摘要路径，断言 `BenchmarkReport` schema、trace summary、artifact 记录、不扫描和正式资产未变。
- 验证结果：targeted integration 已通过；fast regression 见本轮提交前验证。
- Self-Harness Gate：README、init workflow、todo 和演进记录需要同步，已纳入本轮；下一轮候选 gap 首选 guided `recommend-workflow` 查看/生成 review-only workflow recommendation，其次是 candidate governance 菜单。

## 2026-05-31 Goal Mode Retrospective And Recommendation Contract Repair

- North Star 模块：Benchmark / Review Intelligence、Workflow Toolkit Evolution、Experience & Self-Improve。
- Gap Analysis 摘要：用户指出前几轮目标模式提示词不完整后，本轮回顾最近 8 个本地目标模式提交。主要遗漏是 evolution log 未显式记录 Self-Harness Gate、sub agent 使用和下一轮候选 gap；实质代码缺口是 `recommend-workflow` 真实生成的 Markdown 章节与 benchmark `content:workflow-recommendation-review` 契约不一致。
- 当前代码 gap：`recommend_workflow.py` 生成 `## Task Brief`、`## Required Guides`、`## Required Sensors`、`## Boundary`，而 benchmark 要求 `## Task`、`## Recommended Workflow`、`## Required Harness Assets`、`## Review Boundary`。这会导致工具自己生成的 review-only workflow recommendation 可能被 benchmark 拒绝。
- 决策：不放宽 benchmark；修 producer，使真实 `recommend-workflow` 产物满足现有质量门禁。暂缓 existing-Harness guided `benchmark` 菜单和候选治理菜单，先修 review artifact 契约可信度。
- Assumptions / risks：旧标题对人工阅读不是稳定机器契约；改为 benchmark 标准章节不改变 review-only 语义。更完整的逐提交审计可后续继续，但本轮先修最高确定性的契约问题。
- 边界与失败模式：recommendation 仍保持 `pending_harness_maintainer_review`，不执行 Runtime，不创建 `.ai/task-runs`，不应用 routing policy。
- Sub agent 使用：使用 explorer 子代理审查下一步 gap，结论同主线程一致：优先修 `recommend-workflow` 生成产物与 benchmark 契约不一致。
- 验收方式：integration 从 CLI 真实生成 `.ai/review/workflow-routing-recommendation.*`，再运行 benchmark 并断言 `content:workflow-recommendation-review` 通过；保留 benchmark 缺章节失败测试。
- Self-Harness Gate：本轮补齐了近期记录缺少 Gate 结论的问题；下一轮候选 gap 首选 existing-Harness guided `benchmark` action，其次是 candidate governance 菜单。

## 2026-05-31 Existing Harness Improve Action

- North Star 模块：CLI Experience、Maturity-driven Improve、Experience & Self-Improve、Maturity & Evolution。
- 当前 gap：已有 Harness 再次执行 guided `init` 时已能复评成熟度，但用户仍需记住底层 `improve` 命令才能把成熟度缺口转成下一步 review-only 改进候选。
- 决策：在已有 Harness 维护入口加入 `improve` 动作；先刷新 Experience index 和 maturity evidence，再生成 `improvement-candidates.yaml`、`evolution-plan.md`、`pending-improvements.md` 和 `experience-index.yaml`。
- 决策：`improve` 不重新扫描、不调用 LLM、不执行 `self-improve`、不应用候选、不覆盖正式 Guides、Sensors、Workflow Skills、`harness-config.yaml` 或 `project-inventory.json`。
- 验收方式：integration 覆盖 existing Harness 下 `improve` 不调用扫描、不覆盖正式资产、输出 top candidate、刷新 stale workflow recommendation evidence，并记录 trace artifacts 与 `existing_harness_action: improve`。

## 2026-05-31 Existing Harness Assess Action

- North Star 模块：CLI Experience、Maturity & Evolution、可观测 Harness 生成。
- 当前 gap：已有 Harness 再次执行 guided `init` 时只能退出或重建，普通用户仍需知道底层 `assess` 命令才能刷新成熟度。
- 决策：在已有 Harness 维护入口加入 `assess` 动作，复用成熟度评估能力刷新 `maturity-score.yaml`、`maturity-report.md`、`maturity-evidence.yaml` 和 `init-summary.md`。
- 决策：`assess` 不重新扫描、不调用 LLM、不覆盖 `project-inventory.json`、`harness-config.yaml`、Guides、Sensors 或 Workflow Skills。
- 验收方式：integration 覆盖 existing Harness 下 `assess` 可修复缺失 maturity 文件、不调用扫描、不覆盖正式资产，并记录 trace artifacts 和 `existing_harness_action: assess`。

## 2026-05-31 Existing Harness Init Entry

- North Star 模块：CLI Experience、Maturity & Evolution、资产生成与审核接管。
- 当前 gap：再次执行默认 guided `init` 时，系统还会直接进入生成流程，容易覆盖已有 `.ai` Harness，未体现“已有 Harness 的状态感知维护入口”定位。
- 决策：guided `init` 检测到 `.ai/project-inventory.json` 和 `.ai/harness-config.yaml` 后先展示现有 Harness 状态；第一版动作支持 `exit` 只读退出和 `reinit` 显式继续生成。
- 决策：`--non-interactive` 保持自动化重新生成语义，不在本轮引入 `--force` 或完整维护菜单。
- 验收方式：integration 覆盖已有 Harness 下 `exit` 不调用扫描、不改写正式资产，并记录 trace summary。

## 2026-05-31 Maturity Driven Init Summary

- North Star 模块：Maturity & Evolution、CLI Experience、Benchmark / Review Intelligence。
- 当前 gap：`init` 已生成成熟度评估，但完成输出仍偏“文件已生成”，没有把当前等级、阻断项和下一步入口作为主向导体验呈现。
- 决策：新增 `.ai/init-summary.md` 作为首次初始化后的成熟度驱动入口摘要，并让 CLI 完成输出打印当前成熟度、阻断项、建议下一步和推荐入口文件。
- 决策：本轮不默认运行 benchmark / self-improve / Runtime task-run，也不实现已有 Harness 的再次 init 状态菜单；这些保留在主向导 todo 的后续切片。
- 验收方式：integration / e2e / benchmark 覆盖 init summary 文件、稳定章节、CLI 输出和 no-runtime 边界。

## 2026-05-31 Workflow Policy Candidate Apply And Prompt Registry

- North Star 模块：Workflow Policy、Candidate Governance、Prompt Contract。
- 当前 gap：`workflow_policy` asset candidate 已能被 LLM 提出，但此前只能记录治理决策，不能以机器契约应用到正式 routing policy；同时 prompt 文件虽已集中，prompt 版本、文件名和输入标题仍散落在 `tools/llm_*.py`。
- 决策：新增 `WorkflowPolicyPatch` schema，要求 `workflow_policy` candidate 必须携带结构化 patch；`review-candidate --decision applied` 只允许通过该 patch upsert routing rule，并校验 guide/sensor 引用和核心 routing invariants。
- 决策：新增 `prompts.registry` 作为机器消费型 LLM prompt 的单一注册表，集中管理 prompt 文件、版本、输入标题和消息构造；LLM 工具层不再直接维护 prompt 文件名或调用 loader。
- 验收方式：schema / unit / CLI / benchmark 测试覆盖 workflow policy patch 应用、非法 patch 拒绝、成熟度证据刷新、benchmark 保留已应用 config，以及 prompt registry 防回退。

## 2026-05-31 Candidate Governance MVP

- North Star 模块：Experience & Self-Improve、Maturity & Evolution、资产生成与审核接管。
- 当前 gap：`self-improve` 已能生成 review-only asset candidates，但缺少 Maintainer 将候选记录为 accepted / deferred / rejected / applied 的机器契约，智能建议无法进入可审计接管闭环。
- 决策：新增显式 `review-candidate` 命令和 `.ai/review/candidate-governance.*`；保持原始 LLM candidate report 为 review-only。`applied` MVP 只支持 Guide / Sensor Markdown 追加，workflow policy 自动 patch 暂缓到结构化 patch schema 后实现。
- 验收方式：schema / tool / CLI / benchmark 测试覆盖 governance log、正式 Markdown 应用、Experience index 计数、未知 candidate、`.ai/` 路径边界和 trace artifact。

## 2026-05-31 Self-Improve 真实验收覆盖

- North Star 模块：Maturity-driven Improve、LLM Maturity Reviewer、Intelligent Asset Candidate Generation、Benchmark / Review Intelligence。
- 当前 gap：`self-improve` 已有 mock integration 覆盖，但真实 DeepSeek acceptance 没有跑到该智能闭环，无法证明真实模型输出仍符合 review-only schema 与 benchmark 契约。
- 本轮切分：只在 `RuoYi-Vue` 一个真实仓库上增加 `self-improve` acceptance，保持独立用户价值，同时控制全量回归成本。
- 关键发现：真实 DeepSeek 曾返回合法 JSON 但漏掉 `AssetCandidateDraft` 必填字段 `id/title/rationale`，说明 prompt schema 约束不够完整。
- 关键发现：真实 DeepSeek 还暴露过 maturity review 阶段的无效 JSON 和空 `content` 响应。诊断显示正常响应会同时包含 `content` 与 `reasoning_content`，因此不能解析 reasoning 文本作为替代。
- 决策：保持 Pydantic schema 严格失败，不引入 fallback；通过单元测试固定完整 prompt 字段契约，收紧 maturity-review / asset-candidate prompt 的字段模板和输出规模；DeepSeek client 仅对空 `content` 做一次有限重试，仍失败则显式报错。
- 决策：将所有机器消费型 LLM prompt 集中迁入 `src/harness_builder_agent/prompts/`，并通过共享 loader 读取 `## System Message` / `## User Message`。`tools/llm_*.py` 只保留 payload 拼装、调用、解析和 schema 校验。
- 验收方式：unit 覆盖 prompt 契约，acceptance 覆盖真实 `self-improve` 产物 schema、review-only 状态、benchmark `content:self-improve-package` 检查和 `.ai/task-runs` 边界。
- 风险：真实 acceptance 仍有耗时和网络不稳定成本；开发中优先使用可透传 pytest 目标的 targeted acceptance，push 或发布前再运行 full acceptance。
