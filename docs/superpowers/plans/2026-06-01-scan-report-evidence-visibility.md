# Scan Report Evidence Visibility 迁移计划

## Milestone

作为 Harness Maintainer，当我查看 `init` 生成的 `.ai/scan-report.md` 或运行 `benchmark` 验收 Harness 时，我可以看到本次扫描的 evidence coverage、selected paths、LLM evidence expansion、stack validation、scan warnings、risk areas 和命令候选置信度；如果这些 scan 审计信息从 report 中丢失，benchmark 会用 `content:scan-report` 给出具体 missing detail，从而让我不用直接读多份 JSON/YAML 也能审计仓库理解深度。

## TDD 步骤

1. 更新 `tests/unit/test_asset_writer_reports.py`：
   - 构造包含 documents/configs/ci、scan_metadata.coverage、scan_metadata.evidence_expansion、scan_validation、scan_warnings、risk_areas 的 inventory。
   - 断言 `scan-report.md` 包含稳定章节、coverage selected paths、evidence expansion detail、stack validation、warning、risk、command confidence。
2. 更新 `tests/integration/test_benchmark_command.py`：
   - Java fixture benchmark check id 包含 `content:scan-report`。
   - 新增完整 scan-report context 通过测试。
   - 新增缺少 scan-report 章节、缺 coverage selected path 或缺 evidence expansion detail 的负向测试。
3. 运行 targeted tests，确认新测试先失败。

## 实现步骤

1. 更新 `src/harness_builder_agent/tools/asset_writers/reports.py`：
   - 增强 `_scan_report()`，输出 Evidence、LLM Evidence Expansion、Evidence Coverage、Stack Evidence Validation、Scan Warnings、Risk Areas、Command Candidates。
   - 从 `inventory.stack_extensions["scan_metadata"]` 读取 coverage / evidence_expansion。
   - 从 `inventory.stack_extensions["scan_validation"]`、`scan_warnings` 和 `risk_areas` 读取审计上下文。
2. 更新 `src/harness_builder_agent/tools/benchmark.py`：
   - `_content_checks()` 加入 `_scan_report_check(ai, inventory)`。
   - 校验稳定章节、inventory evidence/doc/config/CI paths、coverage selected_paths、evidence expansion detail、warnings、risk paths 和 command confidence。
3. 更新文档：
   - `README.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/engineering/sensor-and-gate-rules.md`。
   - `docs/todos/local-unique-capability-migration.md` 标记 scan-report visibility 已迁移，保留 init-summary evidence audit 为后续。
   - `docs/evolution-log.md` 追加本轮记录。

## 验证步骤

1. `scripts/test-unit.sh tests/unit/test_asset_writer_reports.py -q`
2. `scripts/test-integration.sh tests/integration/test_benchmark_command.py -q`
3. `git diff --check`
4. `scripts/test-fast.sh`

## Commit

- 本地 commit message：`迁移扫描报告证据可见性`
- 本轮仍属于迁移工作包中的一个切片；todo 尚未整体结束，不 push。
