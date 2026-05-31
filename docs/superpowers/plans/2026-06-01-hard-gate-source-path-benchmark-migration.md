# Hard Gate Source Path Benchmark 迁移实施计划

## Goal

迁移本地旧分支中 hard gate command source path 的 benchmark 校验：让 `content:hard-gate-command-evidence` 能发现 source 缺失、low confidence、source path 不存在和 source path 逃出仓库，并在 `weak_commands.reason` 中保留可行动原因。

## Files

- 修改 `src/harness_builder_agent/tools/benchmark.py`
- 修改 `tests/integration/test_benchmark_command.py`
- 修改文档：
  - `README.md`
  - `docs/engineering/sensor-and-gate-rules.md`
  - `docs/engineering/testing-strategy.md`
  - `docs/todos/local-unique-capability-migration.md`
  - `docs/evolution-log.md`

## Tasks

### Task 1: RED Tests

- [x] 增加 benchmark integration 测试：hard gate source 指向仓库内不存在文件时 benchmark failed，`weak_commands[0].reason=source_path_missing`。
- [x] 增加 benchmark integration 测试：hard gate source 逃出仓库时 benchmark failed，`weak_commands[0].reason=source_path_outside_repo`。
- [x] 运行 targeted tests，确认新增测试在实现前失败。

### Task 2: Green Implementation

- [x] 在 `_hard_gate_command_evidence_check()` 中复用 helper 检查 source 空、low confidence、source path outside repo、source path missing。
- [x] 确保新生成的 `weak_commands` 保留 id/source/confidence/reason。
- [x] 运行 targeted benchmark tests 至通过。

### Task 3: Docs, Gate, Commit

- [x] README 和工程规则同步 hard gate source path benchmark 契约。
- [x] 迁移 todo 标记 hard gate source path 子能力已迁移。
- [x] 更新 `docs/evolution-log.md`。
- [x] 运行 `git diff --check`。
- [x] 运行 `scripts/test-fast.sh`。
- [ ] 创建中文本地 commit。

## Verification Commands

```bash
scripts/test-integration.sh tests/integration/test_benchmark_command.py::test_benchmark_fails_when_hard_gate_command_source_path_is_missing tests/integration/test_benchmark_command.py::test_benchmark_fails_when_hard_gate_command_source_path_escapes_repo tests/integration/test_benchmark_command.py::test_benchmark_generates_report_for_java_fixture -q
git diff --check
scripts/test-fast.sh
```
