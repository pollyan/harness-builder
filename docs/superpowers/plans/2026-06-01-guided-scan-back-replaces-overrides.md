# Guided Init Scan 返回修改替换补充实施计划

## 范围

本轮只修正首次 guided `init` 中 `back -> scan` 的内存态替换语义。修改范围：

- `tests/integration/test_init_on_fixture_projects.py`
- `src/harness_builder_agent/tools/interactive_init.py`
- `docs/engineering/init-workflow.md`
- `docs/evolution-log.md`

不修改 schema、LLM、benchmark、asset writer、workflow routing policy 或 Runtime 契约。

## TDD 步骤

1. 新增 integration 测试 `test_guided_init_final_summary_back_to_scan_replaces_previous_corrections`：
   - 第一次 scan 补充输入 legacy module / command / risk。
   - 最终确认输入 `back` -> `scan`。
   - 第二次 scan 补充输入 final module / command / risk。
   - confirm 后断言 inventory、command catalog、project-context、verification、init-summary 只包含 final，不包含 legacy。
2. 运行目标测试，确认当前代码失败。
3. 修改 `interactive_init.py`：
   - scan 完成后保存 `base_inventory = inventory.model_copy(deep=True)` 和 `base_commands = commands.model_copy(deep=True)`。
   - 新增 helper，从 baseline 深拷贝并应用最新 `GuidedScanOverrides`。
   - 初次 scan supplement 和 `back -> scan` 都通过 helper 生成当前内存态。
   - `back -> scan` 展示 clean baseline 的 scan findings / maturity snapshot，再收集最新补充。
4. 更新 `docs/engineering/init-workflow.md`，说明返回 scan 后最新补充替换旧补充。
5. 更新 `docs/evolution-log.md`，记录 gap、取舍、验证和 Gate。

## 验证命令

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_final_summary_back_to_scan_replaces_previous_corrections -q
.venv/bin/python -m pytest \
  tests/integration/test_init_on_fixture_projects.py::test_guided_init_final_summary_back_to_scan_replaces_previous_corrections \
  tests/integration/test_init_on_fixture_projects.py::test_guided_init_structured_scan_corrections_update_modules_commands_and_risks \
  tests/integration/test_init_on_fixture_projects.py::test_guided_init_stack_correction_updates_inventory_and_decisions \
  tests/integration/test_init_on_fixture_projects.py::test_guided_init_final_summary_can_go_back_to_team_rules \
  tests/integration/test_init_on_fixture_projects.py::test_guided_init_final_summary_can_go_back_to_workflow_note -q
scripts/test-fast.sh
```

## 提交策略

- commit 前必须完成 `scripts/test-fast.sh`。
- 本轮是独立 guided init 正确性切片，可以本地 commit。
- 不 push；当前还不是完整远端同步批次，push 前 full regression 条件未重新满足。
