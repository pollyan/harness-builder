# Guided Init Workflow 补充返回修改实施计划

## 范围

本轮只修改首次 guided `init` 的最终确认返回控制流，让用户可以返回 Workflow 补充阶段重新输入 note。修改范围：

- `tests/integration/test_init_on_fixture_projects.py`
- `src/harness_builder_agent/tools/interactive_init.py`
- `docs/engineering/init-workflow.md`
- `docs/evolution-log.md`

不修改 schema、LLM、benchmark、asset writer、workflow routing policy 或 Runtime 契约。

## TDD 步骤

1. 新增 integration 测试 `test_guided_init_final_summary_can_go_back_to_workflow_note`：
   - 初次输入 workflow note。
   - 最终确认输入 `back`，返回目标输入 `workflow`。
   - 重新输入新的 workflow note，再 `confirm`。
   - 断言返回菜单包含 `workflow=Workflow补充`。
   - 断言 `Workflow 补充理解` 至少出现两次，最终 preview 使用新 note。
   - 断言 `interaction-decisions.yaml`、project-context、human-input-needed 只持久化新 note，不包含旧 note。
2. 运行目标测试，确认当前代码失败。
3. 修改 `interactive_init.py`：
   - `_confirm_summary()` 的 back prompt 加入 workflow。
   - 接受 `workflow` 返回值。
   - `run_guided_init()` loop 增加 `workflow` 分支，重新调用 `_show_workflows()` 和 `_show_workflow_note_immediate_summary()`。
4. 更新 `docs/engineering/init-workflow.md`，说明最终确认可返回 Workflow 补充并重新预览。
5. 更新 `docs/evolution-log.md`，记录本轮 gap、取舍、验证和 Gate。

## 验证命令

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_final_summary_can_go_back_to_workflow_note -q
.venv/bin/python -m pytest \
  tests/integration/test_init_on_fixture_projects.py::test_guided_init_final_summary_can_go_back_to_team_rules \
  tests/integration/test_init_on_fixture_projects.py::test_guided_init_final_summary_can_go_back_to_workflow_note \
  tests/integration/test_init_on_fixture_projects.py::test_guided_init_restates_user_supplements_before_write_and_persists_them \
  tests/integration/test_init_on_fixture_projects.py::test_init_default_guided_mode_accepts_happy_path -q
scripts/test-fast.sh
```

## 提交策略

- commit 前必须完成 `scripts/test-fast.sh`。
- 本轮是独立 guided init 体验切片，可以本地 commit。
- 不 push；当前还不是完整远端同步批次，push 前 full regression 条件未重新满足。
