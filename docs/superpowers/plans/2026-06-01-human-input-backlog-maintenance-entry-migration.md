# Human Input 待确认回访入口迁移实施计划

## Goal

迁移本地旧分支中 human-input 待确认项的可行动回访体验：`human-input-needed.md#处理方式` 和已有 Harness 维护入口的 questionnaire backlog 状态。

## Files

- 修改 `src/harness_builder_agent/tools/human_confirmation.py`
- 修改 `src/harness_builder_agent/tools/interactive_init.py`
- 修改 `tests/unit/test_asset_writer_human_confirmation.py`
- 修改 `tests/unit/test_interactive_init_preview.py`
- 修改 `tests/integration/test_init_on_fixture_projects.py`
- 修改文档：
  - `README.md`
  - `docs/engineering/init-workflow.md`
  - `docs/todos/local-unique-capability-migration.md`
  - `docs/evolution-log.md`

## Tasks

### Task 1: RED Tests

- [x] 增加 unit 测试，要求 `human_input_markdown()` 输出扫描待确认摘要和处理方式。
- [x] 增加 unit 测试，要求 existing-Harness human input status helper 读取 questionnaire 并输出待确认数量、scan 确认数量、first ids 和 action entry。
- [x] 增加 integration 断言，已有 Harness `init -> 1` 输出 human input backlog status。
- [x] 运行 targeted tests，确认新增测试在实现前失败。

### Task 2: Green Implementation

- [x] 在 `human_confirmation.py` 增加 scan confirmation summary 与 per-question action guidance。
- [x] 为 scan warning confirmation 生成具体修正建议。
- [x] 在 `interactive_init.py` 增加 `_human_input_needed_status_lines()`，用 `Questionnaire` schema 校验 `.ai/questionnaire.yaml`。
- [x] 将 `_experience_status_lines()` 从单行 human input status 改为展开多行 backlog status。
- [x] 运行 targeted tests 至通过。

### Task 3: Docs, Gate, Commit

- [x] README 和 `docs/engineering/init-workflow.md` 同步 human input backlog / action entry 契约。
- [x] 迁移 todo 标记本轮已完成的子能力，并保留 benchmark failed preview / routing signals 等下一轮候选。
- [x] 更新 `docs/evolution-log.md`。
- [x] 运行 `git diff --check`。
- [x] 运行 `scripts/test-fast.sh`。
- [x] 创建中文本地 commit。

## Verification Commands

```bash
scripts/test-unit.sh tests/unit/test_asset_writer_human_confirmation.py tests/unit/test_interactive_init_preview.py::test_human_input_needed_status_lines_summarize_questionnaire tests/unit/test_interactive_init_preview.py::test_human_input_needed_status_lines_report_missing_files -q
scripts/test-integration.sh tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_can_exit_with_numbered_action -q
git diff --check
scripts/test-fast.sh
```
