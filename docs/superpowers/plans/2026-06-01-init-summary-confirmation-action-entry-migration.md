# Init Summary 待确认处理入口迁移实施计划

## Goal

迁移本地旧分支中 `init-summary.md` 待人工确认处理入口：让首次 init 的交付摘要把 `confirm:*` 问题、`.ai/human-input-needed.md#处理方式` 和 scan warning action hint 串起来。

## Files

- 修改 `src/harness_builder_agent/tools/human_confirmation.py`
- 修改 `src/harness_builder_agent/tools/init_summary.py`
- 修改 `src/harness_builder_agent/tools/benchmark.py`
- 修改 `tests/unit/test_init_summary.py`
- 修改 `tests/integration/test_init_on_fixture_projects.py`
- 修改 `tests/integration/test_benchmark_command.py`
- 修改文档：
  - `README.md`
  - `docs/engineering/init-workflow.md`
  - `docs/todos/local-unique-capability-migration.md`
  - `docs/evolution-log.md`

## Tasks

### Task 1: RED Tests

- [x] 增加 unit 测试，要求 `build_init_summary_markdown()` 输出 `## 待人工确认`、处理入口、`confirm:*` ID 和 scan warning action hint。
- [x] 增加 unit 测试，要求 `render_init_completion_message()` 的“仍需人工确认”输出处理入口。
- [x] 增加 integration 断言，fixture init 生成的 `init-summary.md` 包含处理入口和 questionnaire 中的 `confirm:*` ID。
- [x] 增加 benchmark integration 断言，`content:init-summary` 会在 summary 缺少确认入口时失败。
- [x] 运行 targeted tests，确认新增测试在实现前失败。

### Task 2: Green Implementation

- [x] 提取 scan warning action hint 公共 helper，供 human input 和 init summary 复用。
- [x] 在 `build_init_summary_markdown()` 中新增 `## 待人工确认`。
- [x] 增强 `_pending_confirmation_lines()`，输出处理入口、前几个 ID、omitted 数和 scan warning action。
- [x] 增强 benchmark `content:init-summary` 检查，校验处理入口与 questionnaire ID 对齐。
- [x] 运行 targeted tests 至通过。

### Task 3: Docs, Gate, Commit

- [x] README 和 `docs/engineering/init-workflow.md` 同步本轮稳定契约。
- [x] 迁移 todo 标记本轮已完成子能力。
- [x] 更新 `docs/evolution-log.md`。
- [x] 运行 `git diff --check`。
- [x] 运行 `scripts/test-fast.sh`。
- [ ] 创建中文本地 commit。

## Verification Commands

```bash
scripts/test-unit.sh tests/unit/test_init_summary.py -q
scripts/test-integration.sh tests/integration/test_init_on_fixture_projects.py::test_init_generates_expected_assets_for_fixture tests/integration/test_benchmark_command.py::test_benchmark_fails_when_init_summary_missing_confirmation_entry -q
git diff --check
scripts/test-fast.sh
```
