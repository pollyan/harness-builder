# Existing Harness 编号菜单与维护指引迁移实施计划

## Goal

在最新 `origin/main` 基线上迁移旧分支中已有 Harness 维护入口的低负担操作体验：编号菜单、action normalization 和 Maintenance triage guidance。

## Files

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

- [x] 在 unit 测试中加入 existing Harness action normalization 断言。
- [x] 在 unit 测试中加入 maintenance triage guidance 渲染断言。
- [x] 在 integration 测试中加入输入 `1` 只读退出、不扫描、不覆盖正式资产、CLI 输出编号菜单和 guidance 的断言。
- [x] 运行 targeted tests，确认新增测试在实现前失败。

### Task 2: Green Implementation

- [x] 在 `maintenance_triage.py` 增加 `render_maintenance_triage_guidance_lines()` 和 reason 到中文处理建议的 helper。
- [x] 在 `interactive_init.py` 引入 guidance helper，复用一次 `build_maintenance_triage()` 结果，输出 `Maintenance triage guidance`。
- [x] 增加 `_existing_harness_action_menu_lines()`，用编号菜单替代散落的动作输出。
- [x] 增加 `_normalize_existing_harness_action()`，支持编号、英文命令和中文别名。
- [x] 将 guided existing-Harness prompt 默认值改为 `1`，并通过 normalization 分派原有动作分支。
- [x] 运行 targeted tests 至通过。

### Task 3: Docs, Gate, Commit

- [x] README 和 `docs/engineering/init-workflow.md` 同步编号菜单与 guidance 契约。
- [x] 迁移 todo 标记本轮已完成的子能力，并保留下一轮候选。
- [x] 更新 `docs/evolution-log.md`，记录 Gap Analysis 摘要、用户故事、验收结果和 Self-Harness Gate。
- [x] 运行 `git diff --check`。
- [x] 运行 `scripts/test-fast.sh`。
- [x] 创建中文本地 commit。

## Verification Commands

```bash
scripts/test-unit.sh tests/unit/test_interactive_init_preview.py::test_existing_harness_action_normalization_accepts_numbers_and_aliases tests/unit/test_maintenance_triage.py::test_maintenance_triage_guidance_explains_next_actions -q
scripts/test-integration.sh tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_can_exit_with_numbered_action -q
git diff --check
scripts/test-fast.sh
```
