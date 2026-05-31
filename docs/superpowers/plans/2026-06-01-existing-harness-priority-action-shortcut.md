# Existing Harness 推荐动作编号提示实施计划

## 目标

让已有 Harness 维护入口在展示 Maintenance triage 后，直接告诉 Maintainer 推荐动作对应的菜单编号，降低从 triage 结论到实际选择动作的摩擦。

## 设计

- 在 `maintenance_triage.py` 新增渲染 helper，消费 `MaintenanceAction` 列表并输出 1-3 条“建议优先选择”提示。
- 编号映射覆盖 existing Harness 菜单当前支持的动作：`exit`、`assess`、`improve`、`benchmark`、`recommend-workflow`、`review-candidate`、`review-human-input`、`self-improve`、`reinit`。
- unknown action 显示“当前菜单无直接编号”，避免 silent fallback 或错误编号。
- `interactive_init.py` 在 `Maintenance triage guidance` 后、菜单前展示新提示。

## TDD 步骤

1. 先在 `tests/unit/test_maintenance_triage.py` 写失败测试：
   - `benchmark` 映射到 `4. benchmark`。
   - `review-human-input` 映射到 `7. review-human-input`。
   - `recommend-workflow` 映射到 `5. recommend-workflow`。
   - unknown action 不伪造编号。
2. 在 `tests/integration/test_init_on_fixture_projects.py` 的 existing Harness exit 场景补充 transcript 断言：
   - 输出包含 `建议优先选择`。
   - benchmark not run 时提示 `4. benchmark`。
   - 仍不出现首次 init completion summary，正式资产快照不变。
3. 实现 `render_maintenance_triage_menu_hint_lines()`。
4. 将 helper 接入 `interactive_init.py`。
5. 运行 targeted unit / integration。
6. 更新 `README.md` 与 `docs/engineering/init-workflow.md` 的长期说明：维护入口会把 triage top action 映射为菜单编号。
7. 更新 `docs/evolution-log.md`。
8. 运行 `git diff --check` 和 `scripts/test-fast.sh` 后提交。

## 验证命令

```bash
.venv/bin/python -m pytest tests/unit/test_maintenance_triage.py -q
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_can_exit_with_numbered_action -q
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_can_exit_without_overwriting_assets -q
git diff --check
scripts/test-fast.sh
```

## 非目标

- 不改变 triage 排序。
- 不改变菜单默认值，仍默认 `1` exit。
- 不自动执行推荐动作。
- 不修改正式 `.ai` 资产、不创建 `.ai/task-runs`。
- 不拆分整个 existing Harness 维护入口模块。
