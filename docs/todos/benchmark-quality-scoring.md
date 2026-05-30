# Benchmark 质量评分细化

## 状态

- 状态：implemented
- 优先级：medium-high
- 发现日期：2026-05-30
- 相关命令：`harness-builder-agent benchmark`
- 相关工程规则：`docs/engineering/testing-strategy.md`、`docs/engineering/sensor-and-gate-rules.md`

## 背景

当前 benchmark 已经能检查 Harness 产物是否存在、schema 是否正确、关键章节是否存在、trace 是否完整、workflow skill 是否被引用，以及 hard gate sensor 是否通过。

这对 POC 很重要，但它仍然更偏结构验收。它还不能充分评价生成内容的实际质量，例如 guide 是否具体、sensor 是否可执行、命令是否可靠、推荐是否有 evidence 支撑。

## 当前现状

当前 benchmark 会检查：

- 必需文件存在。
- `project-inventory.json`、`command-catalog.yaml`、`harness-config.yaml` 等 schema。
- `scan-metadata.yaml`、`llm-scan-proposal.json`、`weapon-library-selection.yaml` schema。
- generation trace 和 runtime trace。
- human confirmation 文件。
- LLM enhancement candidate 文件。
- guide/sensor 是否包含必需章节。
- stack-specific guide 是否出现。
- weapon library selection 是否和 guide/sensor 内容一致。
- hard gate sensor 是否 passed。

当前测试覆盖：

- Java fixture benchmark passed。
- .NET fixture benchmark passed。
- hard gate sensor skipped 时 benchmark failed。

## 问题

当前 benchmark 的问题：

- 对 Markdown 内容的检查主要是章节级和关键词级。
- 无法判断 guide 是否空泛、是否真正引用 evidence。
- 无法判断 sensor 是否真的可执行或只是说明文字。
- 对 command reliability 没有评分。
- 对 evidence coverage 没有评分。
- 对 LLM candidate 的价值和可采纳性没有评分。
- 对 maturity score 的解释力和一致性缺少检查。

因此当前 benchmark 更像“最低结构门禁”，还不是“质量评估器”。

## 理想状态

未来 benchmark 应输出更细的质量评分，例如：

```yaml
quality_scores:
  scan_quality:
    evidence_coverage: 0-5
    stack_confidence: 0-5
    command_reliability: 0-5
  guide_quality:
    specificity: 0-5
    evidence_reference: 0-5
    stack_specificity: 0-5
  sensor_quality:
    executable_gate: 0-5
    failure_policy: 0-5
    missing_capability_clarity: 0-5
  workflow_quality:
    skill_reference_integrity: 0-5
    runtime_trace_completeness: 0-5
```

评分不应只给数字，还应给出扣分原因和建议下一步。

## 初步验收标准

未来实现该 todo 时，至少应满足：

- `benchmark-report.yaml` 能表达分项质量评分。
- 评分项有明确规则，不是随意文本。
- 缺少 evidence 引用的 guide 会扣分或失败。
- 没有可执行 hard gate 的 sensor 会扣分或标记风险。
- command source 不可靠时会影响 command reliability。
- 测试覆盖 passed、failed、degraded 三类报告。
- README 和测试策略文档同步说明 benchmark 的质量评分含义。

## 非目标

第一版不要求：

- 完全语义级自动评审。
- 引入额外 LLM 对 benchmark 报告再评分。
- 建立复杂评分模型。

第一版重点是把当前结构检查升级为有解释力的分项质量评估。

## 实现结果

- `benchmark-report.yaml` 已包含 `quality_status`、`quality_scores` 和 `quality_summary`。
- 评分覆盖 `scan_quality`、`guide_quality`、`sensor_quality`、`workflow_quality` 四类。
- `status` 保持硬验收 pass/fail 语义，缺文件、schema 错误或 hard gate failed/skipped 仍会让 benchmark failed。
- `quality_status` 表达质量评分结论：`passed`、`degraded` 或 `failed`。
- 每个质量评分项包含 `score`、`max_score`、`passed`、`reasons` 和 `recommendations`。
- 已补充 passed、degraded、failed 报告测试，包括 guide evidence reference 缺失、command reliability 降分、hard gate skipped 失败等场景。
