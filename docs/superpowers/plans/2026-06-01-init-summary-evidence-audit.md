# Init Summary Evidence Audit 迁移计划

## Milestone

作为首次运行 `init` 后阅读 `.ai/init-summary.md` 的 Harness Maintainer，当本次扫描执行了 LLM-guided evidence expansion 或记录了 coverage selected paths 时，我可以在入口摘要中看到请求补读路径、实际读取路径、风险关注点、置信度、读取数量、rationale 和关键 coverage selected paths，并且 benchmark 会在这些摘要丢失时报告 `content:init-summary` missing detail，从而把首次交付摘要和深度扫描审计链路连接起来。

## TDD 步骤

1. 更新 `tests/unit/test_init_summary.py`：
   - 构造带 `scan_metadata.evidence_expansion` 和 `scan_metadata.coverage` 的 inventory。
   - 断言 `init-summary.md` 包含 `## 扫描证据审计`、requested/read paths、risk focus、confidence、read_file_count、rationale、`evidence_selected` 和 selected paths。
2. 更新 `tests/integration/test_benchmark_command.py`：
   - 新增完整 init-summary evidence audit 通过测试。
   - 新增缺少 audit section / detail 时 `content:init-summary` 失败并报告具体 missing 的测试。
3. 先运行 targeted tests，确认新测试失败。

## 实现步骤

1. 更新 `src/harness_builder_agent/tools/init_summary.py`：
   - 在 `build_init_summary_markdown()` 中加入 `## 扫描证据审计`。
   - 从 `inventory.stack_extensions["scan_metadata"]` 渲染 evidence expansion 和 coverage 摘要。
   - 无 metadata 时显式写出 not_run / not_available。
2. 更新 `src/harness_builder_agent/tools/benchmark.py`：
   - `_content_checks()` 调整为把 inventory 传给 `_init_summary_check()`。
   - `content:init-summary` 校验 `## 扫描证据审计`。
   - 当 inventory 有 evidence expansion / coverage selected paths 时，校验 requested/read/risk/confidence/read_file_count/rationale 和 selected paths。
3. 更新文档：
   - `README.md`、`docs/engineering/init-workflow.md`、`docs/engineering/llm-contracts.md`、`docs/engineering/testing-strategy.md`、`docs/engineering/sensor-and-gate-rules.md`。
   - `docs/todos/local-unique-capability-migration.md` 标记 init-summary evidence audit 已迁移。
   - `docs/evolution-log.md` 追加本轮记录。

## 验证步骤

1. `scripts/test-unit.sh tests/unit/test_init_summary.py -q`
2. `scripts/test-integration.sh tests/integration/test_benchmark_command.py -q`
3. `git diff --check`
4. `scripts/test-fast.sh`

## Commit

- 本地 commit message：`迁移初始化摘要证据审计`
- 本轮仍属于迁移工作包中的一个切片；todo 尚未整体结束，不 push。
