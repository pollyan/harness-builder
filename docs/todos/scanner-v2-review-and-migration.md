# 旧 scanner v2 实现审查与迁移评估

## 状态

- 状态：implemented
- 优先级：high
- 发现日期：2026-05-31
- 相关命令：`harness-builder-agent init`
- 相关工程规则：`docs/engineering/init-workflow.md`、`docs/engineering/llm-contracts.md`、`docs/engineering/testing-strategy.md`

## 背景

当前 `harness_builder_agent` 的扫描链路已经是 LLM-first，并且大仓库 evidence 深度增强已经完成第一版实现。当前代码已经支持分桶采样、priority evidence、coverage metadata、coverage warnings，以及将 coverage 写入 `scan-metadata.yaml` 并提供给 LLM prompt。原来的“大仓库 Evidence 扫描深度增强”事项已经归档到 `docs/todos/archive.md`。

Git 历史里曾经存在一套更深的 scanner v2 实现，位于旧包名 `harness_builder/scanner/` 下。该实现后来在 `50413fc chore: remove legacy scanner package` 中被整包删除，但相关研究和 smoke test 文档仍保留在 `docs/research/scanner-v2-smoke-test.md`。

历史 scanner v2 里曾包含：

- `file_tree_collector.py`：全量轻量文件树 manifest。
- `llm_scanner.py`：两轮 LLM scan 和 self-check。
- `evidence_extractor.py`：根据 LLM 分析选择性运行 Java、Node、.NET 等 detector。
- `core.py` 五阶段流水线：file tree -> LLM analysis -> evidence extraction -> validation -> output。
- LLM claim 与确定性 evidence 的 validation。
- `fileTree + analysis + evidence + validation` 输出结构。

## 问题

当前需要在“现有 evidence depth v1 已经增强”的基础上，重新判断旧 scanner v2 还有没有值得吸收的能力，而不是直接恢复旧包或重复已经完成的 evidence depth 工作。

需要回答：

- 旧 scanner v2 的 file tree、两轮 LLM、自检、detector、validation 设计是否仍适合当前 Harness Builder。
- 旧实现相对当前 enhanced `evidence_collector.py` 还有哪些增量价值。
- 旧实现有哪些问题，例如 fallback 语义、schema 不统一、命令目录形状、测试设计、与 no silent fallback 规则的冲突。
- 哪些逻辑可以迁移，哪些只能作为参考。
- 迁移后应该如何融入当前 `harness_builder_agent` 的 Pydantic schema、LLM-first 契约、weapon library 和 benchmark。

当前已经完成的能力包括：

- `EvidenceBundle` 支持 priority、bucket、coverage、priority files、test files、API entrypoints 和 risk files。
- `evidence_collector.py` 已从简单源码样本截取升级为分桶采样和重点 evidence 优先。
- `scan-metadata.yaml` 已记录 coverage、truncation、skipped bucket 和 scan warnings。
- LLM prompt 已引入 coverage、priority evidence、test/API/risk evidence 的阅读规则。

当前仍值得对比旧 scanner v2 的潜在增量包括：

- 两轮 LLM scan 与 self-check 是否能提升大仓库扫描可靠性。
- targeted detector / evidence extraction 是否比当前 bucket-based evidence 更适合验证 LLM claim。
- LLM claim 与 deterministic evidence validation 是否应成为当前 `scan_reconciler` 的显式产物。
- 旧 `fileTree + analysis + evidence + validation` 输出模型中，哪些字段可以映射到当前 schema。

## 理想状态

先做一次审查，再决定迁移范围。

建议拆成两个阶段：

1. 审查阶段：恢复阅读旧 scanner v2 的关键实现和测试，判断哪些能力值得迁移。
2. 迁移阶段：只迁移已被证明有价值的能力，并按当前 `harness_builder_agent` 的 schema、no fallback 规则和 benchmark 体系重新落地。

如果旧 scanner v2 合理，应将其优秀部分迁移到当前扫描链路：

```text
当前 scan_repository
  -> enhanced EvidenceBundle / coverage
  -> LLM-first structured proposal
  -> optional scanner-v2-inspired self-check or targeted validation
  -> reconcile / validate LLM claims against evidence
  -> ProjectInventory + CommandCatalog + ScanMetadata
```

迁移后的扫描链路不要求完美，但应在现有 evidence depth v1 之上提供明确增量：

- 能更清楚地区分旧 scanner v2 中的可迁移能力和已由当前 enhanced evidence 实现覆盖的能力。
- 能把 LLM 推断和确定性证据的冲突更明确地记录为 warnings、validation 或 human confirmation。
- 如引入 targeted evidence extraction，应证明它比当前 bucket/priority/coverage 机制提供了额外价值。
- 仍然遵守 no silent fallback：LLM 不可用时不能伪装成成功扫描。

## 初步验收标准

实现该 todo 前，应先产出审查结论，至少包括：

- 旧 scanner v2 关键文件和提交清单。
- 可迁移能力清单。
- 不应迁移或需要重写的能力清单。
- 当前扫描链路的目标架构草案。

如果进入迁移实施，至少应满足：

- 不破坏当前 evidence depth v1 的 coverage、priority、bucket 和 scan metadata 行为。
- 单测覆盖新增的 self-check、targeted extraction 或 validation 行为。
- integration 或 e2e 证明 Java Spring 和 .NET fixture 的扫描结果不退化。
- benchmark 或测试能检查新增 validation / warning 输出。
- 默认测试通过。

## 待澄清点

- 旧 scanner v2 中哪些 fallback 行为与当前 no silent fallback 规则冲突。
- 旧 command catalog 形状是否需要完全丢弃，只保留 evidence / validation 思路。
- 第一轮迁移是否只覆盖 Java Spring、.NET ASP.NET 和 Node 线索，还是同步保留旧 detector 的全部范围。

## 非目标

第一阶段不要求：

- 直接恢复旧 `harness_builder/scanner/` 包。
- 复制旧实现的所有代码和字段名。
- 支持所有语言和框架。
- 做完整语义索引或向量数据库。

重点是先审查旧实现的合理性，再把真正有价值的扫描能力迁移到当前代码架构中。

## 完成说明

已完成审查并迁移第一轮能力：旧 scanner v2 的 LLM claim validation 思路已落入当前 `scan_reconciler`，以 `ScanMetadata.warnings` 和 `ProjectInventory.stack_extensions["scan_validation"]` 记录 LLM stack claims 与 deterministic evidence 的支持/冲突关系。

相关落点：

- 审查设计：`docs/superpowers/specs/2026-05-31-scanner-v2-review-validation-design.md`
- 实施计划：`docs/superpowers/plans/2026-05-31-scanner-v2-validation-migration.md`
- 代码：`src/harness_builder_agent/tools/scan_reconciler.py`
- 测试：`tests/unit/test_scan_reconciler.py`
