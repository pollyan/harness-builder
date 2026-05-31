# Evidence Reason Preservation 迁移计划

## Milestone

作为 Harness Maintainer，当我查看 `.ai/scan-report.md`、`.ai/guides/project-context.md` 或 benchmark report 审计扫描 evidence 时，我可以看到每个关键 evidence path 为什么被选中，并且 benchmark 会在 reason 从报告中丢失时指出具体 path，从而判断扫描结论不是只有路径列表，而是有可解释依据。

## TDD 步骤

1. 更新 `tests/unit/test_scan_reconciler.py`：
   - 构造 key/document/config/CI `EvidenceFile.reason`。
   - proposal 提供 configs / ci_files 但不提供 reason。
   - 断言 `ProjectInventory` 对应 entries 保留 reason。
2. 更新 `tests/unit/test_asset_writer_reports.py` 和 `tests/unit/test_asset_writer_guides.py`：
   - 断言 scan-report / project-context 输出 reason 文案。
3. 更新 `tests/integration/test_benchmark_command.py`：
   - scan-report evidence section 缺 reason 时，`content:scan-report.missing` 包含 `missing_evidence_reason:<path>`。
   - project-context 来源证据缺 reason 时，`content:project-context-evidence-context.missing` 包含同类 detail。
4. 先运行 targeted tests，确认新断言失败。

## 实现步骤

1. 更新 `src/harness_builder_agent/tools/scan_reconciler.py`：
   - 增加 `_evidence_entry()`，保留 path、kind、reason。
   - 增加 proposal entries 的 reason 补齐逻辑。
   - 在 `ProjectInventory.evidence/documents/configs/ci_files` 中使用该逻辑。
2. 更新 `src/harness_builder_agent/tools/benchmark.py`：
   - 增加 inventory evidence detail helper。
   - `content:scan-report` 和 `content:project-context-evidence-context` 校验 reason。
3. 更新文档记录：
   - `README.md`、`docs/engineering/llm-contracts.md`、`docs/engineering/testing-strategy.md`、`docs/todos/local-unique-capability-migration.md`、`docs/evolution-log.md`。

## 验证步骤

1. targeted unit / integration：
   - `scripts/test-unit.sh tests/unit/test_scan_reconciler.py tests/unit/test_asset_writer_reports.py tests/unit/test_asset_writer_guides.py -q`
   - `scripts/test-integration.sh tests/integration/test_benchmark_command.py::test_benchmark_fails_when_scan_report_omits_evidence_reason tests/integration/test_benchmark_command.py::test_benchmark_fails_when_project_context_omits_evidence_reason -q`
2. `scripts/test-integration.sh tests/integration/test_benchmark_command.py -q`
3. `git diff --check`
4. `scripts/test-fast.sh`

## Commit

- 本地 commit message：`迁移扫描证据原因保留`
- 本轮仍属于迁移工作包中的一个切片；todo 尚未整体结束，不 push。
