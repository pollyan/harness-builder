# Existing Harness Benchmark / Routing Signals 迁移实施计划

## Goal

迁移本地旧分支中已有 Harness 维护入口的只读 Benchmark signals、Workflow routing signals，以及 benchmark failed detail 驱动的 triage 细化。

## Files

- 修改 `src/harness_builder_agent/schemas/benchmark_report.py`
- 修改 `src/harness_builder_agent/tools/interactive_init.py`
- 修改 `src/harness_builder_agent/tools/maintenance_triage.py`
- 修改 `tests/unit/test_interactive_init_preview.py`
- 修改 `tests/unit/test_maintenance_triage.py`
- 修改 `tests/integration/test_init_on_fixture_projects.py`
- 修改文档：
  - `README.md`
  - `docs/engineering/init-workflow.md`
  - `docs/todos/local-unique-capability-migration.md`
  - `docs/evolution-log.md`

## Tasks

### Task 1: RED Tests

- [x] 增加 unit 测试，要求 `BenchmarkReport` 保留 `errors`、`missing` 和 `weak_commands`。
- [x] 增加 unit 测试，要求 `_benchmark_signal_lines()` 输出 failed count、id、中文 detail 和 weak command detail。
- [x] 增加 unit 测试，要求 `_workflow_routing_status_lines()` 输出 standard escalation / risk trigger 状态。
- [x] 增加 unit 测试，要求 maintenance triage 对 hard gate weak command 和 project-context missing 生成专属 reason/detail。
- [x] 增加 integration 断言，已有 Harness `init -> exit` 输出 `Benchmark signals` 和 `Workflow routing signals`。
- [x] 运行 targeted tests，确认新增测试在实现前失败。

### Task 2: Green Implementation

- [x] 扩展 `BenchmarkReport` schema 的 check detail 字段。
- [x] 在 existing Harness 入口接入 Benchmark / Workflow routing signals。
- [x] 实现 `_benchmark_signal_lines()`、`_benchmark_failed_check_label()`、`_benchmark_check_detail()` 和 `_workflow_routing_status_lines()`。
- [x] 增强 `maintenance_triage.py` 的 benchmark failed detail 排序和中文 guidance。
- [x] 运行 targeted tests 至通过。

### Task 3: Docs, Gate, Commit

- [x] README 和 `docs/engineering/init-workflow.md` 同步本轮稳定契约。
- [x] 迁移 todo 标记本轮已完成的子能力。
- [x] 更新 `docs/evolution-log.md`。
- [x] 运行 `git diff --check`。
- [x] 运行 `scripts/test-fast.sh`。
- [x] 创建中文本地 commit。

## Verification Commands

```bash
scripts/test-unit.sh tests/unit/test_interactive_init_preview.py tests/unit/test_maintenance_triage.py tests/unit/test_schema_contracts.py -q
scripts/test-integration.sh tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_can_exit_without_overwriting_assets -q
git diff --check
scripts/test-fast.sh
```
