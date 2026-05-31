# Guided Init Scan 返回修改替换 / 清空提示实施计划

## 范围

本轮只补齐首次 guided `init` 中 `back -> scan` 的用户可见替换 / 清空语义。修改范围：

- `tests/integration/test_init_on_fixture_projects.py`
- `src/harness_builder_agent/tools/interactive_init.py`
- `docs/engineering/init-workflow.md`
- `docs/evolution-log.md`

不修改 schema、LLM、benchmark、asset writer、workflow routing policy 或 Runtime 契约。

## TDD 步骤

1. 新增 integration 测试 `test_guided_init_final_summary_back_to_scan_can_clear_previous_corrections`：
   - 第一次 scan 补充输入 `legacy` module / command / risk。
   - 最终确认输入 `back` -> `scan`。
   - 第二次 scan 补充直接回车。
   - 断言 CLI 包含返回修改替换 / 清空提示和清空确认。
   - 断言最终 `.ai` 资产不包含旧 `legacy` module / command / risk。
2. 先运行目标测试，确认当前代码因缺少 CLI 提示失败。
3. 修改 `interactive_init.py`：
   - 新增 `_has_scan_overrides()`。
   - 新增 `_show_scan_back_revision_notice(previous_scan_overrides)`。
   - 新增 `_show_scan_supplement_cleared_summary()`。
   - 在 `action == "scan"` 分支中保存上一版补充、展示返回修改提示、重新收集补充；若新补充为空且上一版非空，展示清空确认。
4. 更新 `docs/engineering/init-workflow.md`，固化返回 scan 时必须说明替换 / 清空语义。
5. 更新 `docs/evolution-log.md`，记录本轮 gap、取舍、验证和 Gate。

## 验证命令

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_final_summary_back_to_scan_can_clear_previous_corrections -q
.venv/bin/python -m pytest \
  tests/integration/test_init_on_fixture_projects.py::test_guided_init_final_summary_back_to_scan_can_clear_previous_corrections \
  tests/integration/test_init_on_fixture_projects.py::test_guided_init_final_summary_back_to_scan_replaces_previous_corrections \
  tests/integration/test_init_on_fixture_projects.py::test_guided_init_structured_scan_corrections_update_modules_commands_and_risks \
  tests/integration/test_init_on_fixture_projects.py::test_guided_init_final_summary_can_go_back_to_team_rules \
  tests/integration/test_init_on_fixture_projects.py::test_guided_init_final_summary_can_go_back_to_workflow_note -q
scripts/test-fast.sh
```

## 提交策略

- commit 前必须完成 `scripts/test-fast.sh`。
- 本轮是独立 guided init CLI 信任感切片，可以本地 commit。
- 不 push；当前还不是完整远端同步批次，push 前 full regression 条件未重新满足。
