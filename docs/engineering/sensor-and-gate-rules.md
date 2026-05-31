# Sensor 与 Gate 规则

本文约束 Harness Builder 生成和验证 Sensor、hard gate、benchmark 检查的规则。修改 sensor、benchmark、验证报告或质量门禁前，先阅读本文。

## 基本概念

Sensor 是 Harness 中用于验证质量、风险和执行结果的机制。它不应该只是说明文档，而应该能对应到明确的验证活动或待补齐的验证能力。

Gate 是 Sensor 的执行强度。

当前建议分类：

- `hard`：必须通过。失败应导致 benchmark 失败或任务不能被视为通过。
- `advisory`：建议检查。失败或缺失会产生风险提示，但不一定阻断。
- `manual`：需要人工确认，不能自动判断。

Sensor 状态应明确：

- `passed`：验证已执行并通过。
- `failed`：验证已执行但失败。
- `skipped`：验证未执行，必须说明原因。
- `unresolved`：当前缺少足够信息判断。

`skipped` 和 `unresolved` 不能当作成功。

## 生成 Sensor 的规则

生成的 Sensor Markdown 至少应包含：

- 已发现的验证命令。
- 缺失验证能力。
- 推荐验证活动。
- 失败处理策略。
- hard/advisory/manual 的区分。

Sensor 内容应来自：

- `command-catalog.yaml` 中的命令候选。
- 内置武器库中的 stack-specific sensor。
- LLM scan proposal 中的风险和验证建议。
- 人工确认输入或组织级上下文。

Sensor 内容不应：

- 凭空假设项目有某个测试命令。
- 把无法执行的命令标记为 hard。
- 只写“请运行测试”这类泛泛建议。
- 对失败没有处理策略。

## Hard gate 规则

Hard gate 是质量底线。

规则：

- hard gate 必须有可执行命令或明确验证机制。
- Harness Builder benchmark 必须检查 hard gate command 是否有明确 source、confidence 和 gate 证据。
- 真实 hard gate 执行失败或 skipped 必须由未来宿主 AI Coding Runtime 在 `sensor-report.yaml` 中显式报告。
- future runtime 不能把 hard gate failed/skipped 当作 passed。
- 如果命令过重、缺少依赖或无法确认，应先标记为 advisory 或 manual，而不是 hard。

适合 hard gate 的例子：

- 明确存在且可运行的单元测试命令。
- 明确存在且可运行的编译命令。
- 明确存在且可运行的 lint/typecheck 命令。

不适合直接 hard gate 的例子：

- 需要外部数据库但没有本地配置的集成测试。
- 需要云服务账号的测试。
- LLM 猜测出来但 evidence 不支持的命令。

## Benchmark 规则

Benchmark 是 Harness Builder 的 POC 验收器，应检查生成 Harness 的最低质量。

Benchmark 应检查：

- 必需文件存在。
- JSON/YAML schema 正确。
- Markdown 必需章节存在。
- workflow skill 文件存在并被引用。
- generation trace 存在且包含阶段和 artifact。
- weapon library selection 与生成 guide/sensor 内容一致。
- scan report evidence visibility 可审计；`.ai/scan-report.md` 必须展示 Evidence、LLM Evidence Expansion、Evidence Coverage、Stack Evidence Validation、Scan Warnings、Risk Areas 和 Command Candidates。缺失章节、inventory evidence path、evidence reason、coverage selected path、evidence expansion detail、scan warning code、risk path 或 command confidence 时，`content:scan-report` 必须失败并保留具体 `missing_*` detail。
- init summary evidence audit 可审计；`.ai/init-summary.md` 必须在 `## 扫描证据审计` 中摘要展示 evidence expansion requested/read paths、risk focus、confidence、read file count、rationale 和 coverage selected paths。缺失时 `content:init-summary` 必须失败并保留具体 `missing_summary_expansion_*` 或 `missing_summary_coverage_selected_path:*` detail。
- project-context evidence context 可审计；`.ai/guides/project-context.md` 的 `## 来源证据` 必须保留 `ProjectInventory` 中的 evidence、documents、configs 和 CI 路径及其 reason，`## LLM 证据扩展` 必须保留 `ScanMetadata.evidence_expansion` 的 requested/read paths、risk focus、confidence、read file count 和 rationale。缺失时 `content:project-context-evidence-context` 必须失败并保留具体 `missing_evidence_path:<path>`、`missing_evidence_reason:<path>`、`missing_llm_evidence_expansion_section` 或 `missing_expansion_*`。
- Guide、Sensor、Workflow Skill 和 stack-specific Guide 的内容质量检查失败时，benchmark 必须保留具体 `missing` detail；例如缺失章节名、缺失 `.ai/skills/*/SKILL.md` 文件、缺失 skill marker、缺失 hard gate marker 或缺失 stack-specific weapon id。
- scan risk path 在 Guide、Sensor 和 standard routing 之间一致；`ProjectInventory` 中的风险路径必须出现在 `.ai/guides/project-context.md`、`.ai/sensors/verification.md`，并以 `risk_area:<path>` trigger 或 rationale 进入 `.ai/harness-config.yaml` 的 `standard-escalation`。缺失时 `content:risk-context-consistency` 必须失败并保留具体 `missing_*_risk:<path>`。
- hard gate command 有 source、confidence、type 和 gate 证据；source 必须指向目标仓库内真实存在的文件。source 为空、low confidence、source path 不存在或逃出仓库时，benchmark 必须让 `content:hard-gate-command-evidence` 失败，并在 `weak_commands` 中保留 command id、source、confidence 和 reason。
- 显式 LLM review 命令生成的可选 review artifacts 在存在时必须被校验。它们不是 baseline required files，但 schema 错误、YAML/Markdown 缺少配对、跨文件引用无效或丢失 review-only 状态时，benchmark 应失败。
- `.ai/review/maturity-review.yaml` 和 `.ai/review/maturity-review.md` 属于可选 LLM review artifacts；不存在时 benchmark 不应失败，存在时必须校验 schema、Markdown 配对章节、candidate id 引用、`.ai/` evidence 边界、evidence source allowlist 和 `pending_harness_maintainer_review` 状态。
- `.ai/review/asset-candidates.yaml` 和配套 `asset-candidate-*.md` 属于可选 review-only artifacts；不存在时 benchmark 不应失败，存在时必须校验 schema、Markdown 配套章节、source candidate 引用、`.ai/` evidence/suggested path 边界、evidence source allowlist 和 `pending_harness_maintainer_review` 状态。
- `.ai/review/candidate-governance.yaml` 和 `.ai/review/candidate-governance.md` 属于可选候选治理 artifacts；不存在时 benchmark 不应失败，存在时必须校验 schema、Markdown 配对章节、candidate id 引用、安全 `.ai/` evidence/suggested/applied path 边界，以及 applied path 是否存在。对已应用的 `workflow_policy` candidate，还必须校验源候选存在结构化 `workflow_policy_patch`，源候选 `source_review_decision` 必须是 `support` 或 `revise`，候选 `suggested_path` 必须精确等于 `.ai/harness-config.yaml`，且 `.ai/harness-config.yaml` 中对应 routing rule 与 patch 一致。
- `.ai/review/self-improve-package.yaml` 和 `.ai/review/self-improve-package.md` 属于可选 self-improve review package；不存在时 benchmark 不应失败，存在时必须校验 schema、Markdown 配套章节、generated artifact 路径边界和 `pending_harness_maintainer_review` 状态。
- `.ai/experience/experience-summary.yaml` 和 `.ai/experience/experience-summary.md` 属于可选 review-only Experience artifacts；不存在时 benchmark 不应失败，存在时必须校验 schema、Markdown 配对章节、`.ai/` evidence 边界、evidence source allowlist 和 `pending_harness_maintainer_review` 状态。
- `.ai/review/workflow-routing-recommendation.yaml`、`.ai/review/workflow-routing-recommendation.md` 和 `.ai/review/workflow-routing-recommendations/` 历史产物属于可选 workflow recommendation artifacts；不存在时 benchmark 不应失败，存在时必须校验 workflow/rule 引用、Markdown 配对章节、history index schema、每条 history YAML schema、review-only 状态、`.ai/` evidence 边界和 evidence source allowlist。
- `.ai/task-runs/<task-id>/` 属于宿主 Runtime 生成的可选任务级过程数据；不存在时 benchmark 不应失败，存在时必须校验 `harness-map.yaml`、`sensor-report.yaml`、`runtime-summary.yaml`、`decision-log.md` 和 `handoff-summary.md` 的 schema / 内容 / task id / selected workflow / sensor status 一致性。Harness Builder 只读消费这些文件，不创建、不执行、不修复 Runtime 产物。
- Benchmark 的 evidence source allowlist 必须从结构化上游产物构建，例如 `maturity-evidence.yaml`、`experience-index.yaml`、`improvement-candidates.yaml`、`maturity-review.yaml` 和 experience source inputs；不能用“任意存在的 `.ai/**` 文件”替代。

Benchmark 不应：

- 只做文件存在检查。
- 自动修复缺失文件。
- 把失败吞掉后返回成功。
- 因为真实命令失败就隐藏错误。

Benchmark 质量评分应覆盖：

- `scan_quality`：evidence coverage、stack confidence、command reliability。
- `guide_quality`：规则具体性、来源证据、stack-specific 内容。
- `sensor_quality`：可执行 hard gate、失败处理策略、缺失验证能力说明。
- `workflow_quality`：workflow skill 引用完整性。

质量评分不能替代 hard gate。`status` 仍表示硬验收 pass/fail；`quality_status` 表示质量评分结论，可以是 `passed`、`degraded` 或 `failed`。hard gate command 证据不足时，benchmark hard status 必须是 `failed`。

首次 `init` 只在 `.ai/init-summary.md` 和 CLI 完成输出中解释 benchmark readiness，不默认运行 benchmark，也不生成 `.ai/benchmark-report.yaml`。正式质量验收仍以显式 `benchmark` 命令生成的 `BenchmarkReport` 为准。

## Runtime Sensor Report 规则

Sensor report 是未来宿主 AI Coding Runtime 执行 Workflow Skill 时应写出的任务级 runtime artifact，不是 Harness Builder 当前生成的正式产物。它应能被程序读取。

规则：

- 必须符合 schema。
- 每个 sensor result 必须有 id、status、summary。
- failed/skipped/unresolved 必须有解释。
- hard gate 失败必须能被 benchmark 汇总。
- report 应保留执行命令和输出摘要，但不要无限制写入完整日志。

## 与生成资产的关系

Sensor 不是孤立文件。它应该和以下产物一致：

- `command-catalog.yaml`
- `harness-config.yaml`
- `weapon-library-selection.yaml`
- `benchmark-report.yaml`

跨文件引用必须可测试。例如：

- `weapon-library-selection.yaml` 中的 sensor weapon id 应出现在生成的 sensor Markdown 中。
- `harness-config.yaml` 中配置的 workflow skill 路径必须存在。
- 未来 runtime 生成的 `sensor-report.yaml` 中 hard gate 状态应影响宿主 runtime 的任务结果。

## 测试要求

修改 Sensor 或 benchmark 时，至少覆盖：

- Sensor Markdown 包含必需章节。
- Stack-specific sensor weapon id 出现在输出中。
- hard gate passed 时 benchmark 可以通过。
- scan report 缺少 evidence coverage、selected path、LLM evidence expansion、scan warning、risk area 或 command confidence 时 benchmark 失败并列出具体 missing detail。
- init-summary 缺少 scan evidence audit 章节、LLM evidence expansion detail 或 coverage selected path 时 benchmark 失败并列出具体 missing detail。
- project-context 缺少来源证据路径、reason 或 LLM evidence expansion 审计细节时 benchmark 失败并列出具体 missing detail。
- Guide、Sensor、Workflow Skill 或 stack-specific Guide 内容质量失败时 benchmark 失败并列出具体 missing detail。
- scan risk path 缺少 Guide、Sensor 或 routing 任一环时 benchmark 失败并列出具体路径。
- hard gate command source 缺失、source path 不存在、source path 逃出仓库或 low confidence 时 benchmark 失败并列出失败摘要。
- future runtime 中 skipped 不被当作 passed。
- command catalog 与 sensor 内容有关联。

## 后续演进

未来可以增强：

- 更细的 gate policy。
- 针对不同技术栈的 sensor weapon library。
- 对命令执行环境的可用性检测。
- 对 flaky gate 的单独标记。
- 人工确认后把 candidate sensor 晋升为正式 sensor。

但这些增强不能改变一个底线：Sensor 必须帮助暴露真实质量问题，而不是制造看起来通过的幻觉。
