# Benchmark Quality Scoring Design

## 背景

当前 `harness-builder-agent benchmark` 已经能做最低结构验收：文件存在、schema 正确、关键章节存在、trace 完整、workflow skill 引用正确、hard gate sensor passed。这个能力能证明 Harness 不是空壳，但还不能说明生成内容质量是否足够好。

需要补充的是一套确定性的质量评分：不引入额外 LLM，不做复杂语义评审，但让 benchmark report 能回答 guide 是否具体、sensor 是否可执行、命令是否可靠、evidence coverage 是否充分、workflow trace 是否完整。

## 目标

1. `benchmark-report.yaml` 增加结构化质量评分。
2. 每个评分项有明确规则、分数、扣分原因和建议下一步。
3. 保持现有 hard gate 行为：硬验收失败时 benchmark 仍失败。
4. 增加 `quality_status` 表达 `passed`、`degraded`、`failed` 三类质量结论。
5. 测试覆盖 passed、degraded、failed 三类报告。

## 非目标

第一版不做：

- 使用 LLM 再评审 benchmark report。
- 建立复杂评分模型。
- 用质量评分自动修复生成资产。
- 让 degraded 直接改变现有 CLI exit code 语义。

## 状态语义

保留现有字段：

```yaml
status: passed | failed
```

`status` 继续表示硬验收：

- `passed`：所有 hard benchmark checks 通过。
- `failed`：存在缺文件、schema 错误、hard gate failed/skipped 或其他硬验收失败。

新增字段：

```yaml
quality_status: passed | degraded | failed
```

`quality_status` 表示质量评分：

- `passed`：硬验收通过，所有评分项达到目标阈值。
- `degraded`：硬验收通过，但部分质量评分低于目标阈值。
- `failed`：硬验收失败，或者关键质量项为 0。

这样可以保留现有 CLI 对 `status != passed` 返回非 0 的行为，同时让报告表达“结构过了但质量有缺口”的场景。

## 报告结构

新增 schema：

```yaml
quality_scores:
  scan_quality:
    evidence_coverage:
      score: 0-5
      max_score: 5
      passed: true
      reasons: []
      recommendations: []
  guide_quality:
    evidence_reference: ...
  sensor_quality:
    executable_gate: ...
  workflow_quality:
    runtime_trace_completeness: ...
quality_summary:
  total_score: 0-100
  minimum_score: 0-5
  degraded_items: []
  failed_items: []
```

Pydantic schema：

- `QualityScoreItem`
- `QualityScoreCategory`
- `QualitySummary`
- `BenchmarkReport.quality_status`
- `BenchmarkReport.quality_scores`
- `BenchmarkReport.quality_summary`

## 评分项

第一版实现以下评分。

### scan_quality

`evidence_coverage`

- 5：`scan-metadata.yaml` 有 coverage，selected evidence > 0，且没有 coverage warnings。
- 4：有 coverage，selected evidence > 0，但有 warning。
- 3：没有 coverage，但 evidence_file_count > 0。
- 1：evidence_file_count 为 0。
- 0：`scan-metadata.yaml` 不可读。

`stack_confidence`

- 5：LLM proposal confidence 为 high，且 primary_stack 不是 unknown。
- 3：confidence 为 medium。
- 1：confidence 为 low 或 primary_stack 为 unknown。
- 0：LLM proposal 不可读。

`command_reliability`

- 5：所有 hard command 都有 source 且 confidence high。
- 4：hard command 有 source，但部分 confidence medium。
- 2：存在 hard command confidence low 或 source 为空。
- 1：没有 hard command。
- 0：command catalog 不可读。

### guide_quality

`specificity`

- 5：project-context guide 包含当前 stack、模块、武器库命中和团队上下文章节。
- 4：缺团队上下文但有 stack、模块、武器库命中。
- 2：只包含必需章节，但缺少 stack/module 具体内容。
- 0：guide 不可读。

`evidence_reference`

- 5：guide 包含 `## 来源证据`，且列出至少一个路径。
- 2：有来源证据章节但没有路径。
- 0：缺来源证据章节或 guide 不可读。

`stack_specificity`

- 5：当前 stack 对应 weapon id 出现在 guide。
- 3：只有 common weapon id。
- 1：primary_stack unknown。
- 0：guide 不可读。

### sensor_quality

`executable_gate`

- 5：至少一个 hard gate sensor passed。
- 3：有 hard gate，但 status skipped/failed。
- 1：没有 hard gate。
- 0：sensor report 不可读。

`failure_policy`

- 5：sensor Markdown 包含失败处理策略，且 hard gate failed/skipped 会进入 benchmark failed_or_skipped。
- 3：包含失败处理策略，但没有 hard gate 结果。
- 0：缺失败处理策略或 sensor Markdown 不可读。

`missing_capability_clarity`

- 5：sensor Markdown 包含缺失验证能力和推荐验证活动。
- 2：只包含其中一个。
- 0：两个都缺失。

### workflow_quality

`skill_reference_integrity`

- 5：harness map 引用的 workflow skill 路径存在。
- 0：引用缺失或文件不存在。

`runtime_trace_completeness`

- 5：runtime-summary、workflow-events、used-guides 都存在且内容一致。
- 3：存在 runtime-summary，但 events 或 used-guides 不完整。
- 0：runtime trace 不可读。

## 与现有 checks 的关系

`checks` 仍然存在，负责硬验收。

`quality_scores` 不替代 checks，而是补充解释力。部分 quality item 可以引用已有 check 的结果，但不要直接把 check 列表当评分模型。评分逻辑应集中在 benchmark 模块的独立 helper 中，便于单测覆盖。

## 错误处理

- benchmark 不因单个质量评分读取失败而崩溃，应把对应 quality item 记为 0 分并写明 reason。
- schema 损坏等硬验收仍通过 existing checks 使 `status=failed`。
- 当 `status=failed` 时，`quality_status` 必须为 `failed`。

## 测试策略

Unit：

- `BenchmarkReport` schema 接受 quality fields。
- quality scoring helper 能给完整 fixture 打高分。
- guide 缺 evidence reference 时对应评分下降。
- sensor 没有可执行 hard gate 时 `executable_gate` 降分。
- command source/confidence 不可靠时 `command_reliability` 降分。

Integration：

- benchmark passed report 包含 `quality_status=passed` 或 `degraded`，且有完整 quality_scores。
- hard gate skipped 时 `status=failed` 且 `quality_status=failed`。
- 人为破坏 guide evidence reference 时，硬 checks 可以通过但 `quality_status=degraded`。

Docs：

- README 说明 `status` 与 `quality_status` 的区别。
- `docs/engineering/sensor-and-gate-rules.md` 增加 benchmark 质量评分规则。
- `docs/todos/benchmark-quality-scoring.md` 标记 implemented。

## 设计决策

### 为什么不把 `status` 扩成 degraded

现有 CLI 会在 `status != passed` 时返回非 0。为了不破坏当前 CI/脚本语义，保留 `status` 做硬验收。`quality_status=degraded` 表示“可运行但质量有缺口”，更适合报告和后续改进使用。

### 为什么第一版不用 LLM

Benchmark 本身是质量门禁，应尽量确定性、可重复、可测试。LLM 评审可以作为未来增强，但不能作为第一版质量评分的基础。

