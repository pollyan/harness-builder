# Existing Harness 动作契约同源实施计划

## 目标

把已有 Harness 维护入口的菜单行、动作编号、别名 normalization 和 Maintenance triage shortcut 编号集中到一份动作契约，防止后续菜单调整时出现推荐编号与实际菜单漂移。

## 实施步骤

1. 新增失败测试：
   - `tests/unit/test_existing_harness_actions.py` 覆盖共享菜单行、编号查询和 alias normalization。
   - 调整 `tests/unit/test_maintenance_triage.py`，断言 shortcut 使用共享编号查询。
2. 新增 `src/harness_builder_agent/tools/existing_harness_actions.py`：
   - 定义不可变动作 dataclass。
   - 维护 1-9 action id、menu label、description 和 aliases。
   - 暴露 `existing_harness_action_menu_lines()`、`normalize_existing_harness_action()`、`existing_harness_action_number()`。
3. 更新 `interactive_init.py`：
   - 导入共享 helper。
   - 保留 `_existing_harness_action_menu_lines()` / `_normalize_existing_harness_action()` facade。
   - 不改 `_handle_existing_harness_entry()` 的动作分支和 trace 语义。
4. 更新 `maintenance_triage.py`：
   - 移除独立 `EXISTING_HARNESS_ACTION_NUMBERS`。
   - 通过 `existing_harness_action_number()` 渲染快捷编号。
5. 更新文档记录：
   - `docs/evolution-log.md` 添加本轮记录。
   - 如长期工程文档已有维护入口编号规则，无需重复扩写；若发现措辞冲突再同步。
6. 验证并提交：
   - 运行 targeted unit / integration。
   - 运行 `git diff --check`。
   - 创建 commit 前运行 `scripts/test-fast.sh`。

## 验证命令

```bash
.venv/bin/python -m pytest tests/unit/test_existing_harness_actions.py tests/unit/test_maintenance_triage.py::test_maintenance_triage_menu_hints_map_actions_to_existing_harness_numbers tests/unit/test_interactive_init_preview.py::test_existing_harness_action_normalization_accepts_numbers_and_aliases -q
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_can_exit_with_numbered_action -q
git diff --check
scripts/test-fast.sh
```

## 非目标

- 不改变 existing Harness 菜单顺序。
- 不新增、删除或重命名维护动作。
- 不改变默认 `1` exit。
- 不改变 triage 排序、guidance 文案或 benchmark 逻辑。
- 不拆分整个 `_handle_existing_harness_entry()`。
- 不执行 Runtime，不创建 `.ai/task-runs`，不覆盖正式 Harness 资产。
