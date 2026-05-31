# Guided Init Workflow 补充影响与预览实施计划

## 范围

本轮只补齐首次 guided `init` 中 workflow note 的即时反馈和写入前预览。修改范围：

- `tests/integration/test_init_on_fixture_projects.py`
- `src/harness_builder_agent/tools/interactive_init.py`
- `docs/engineering/init-workflow.md`
- `docs/evolution-log.md`

不修改 schema、LLM prompt、正式 workflow routing policy、benchmark 或 Runtime 契约。

## TDD 步骤

1. 更新 `test_guided_init_restates_user_supplements_before_write_and_persists_them`：
   - 断言 `Workflow 补充理解` / `Workflow 补充影响` 出现在 workflow prompt 之后、成熟度预览之前。
   - 断言即时区块包含 workflow note、`interaction-decisions.yaml`、`project-context.md`、`human-input-needed.md`、`review-only` / 人工确认和不直接修改正式 routing policy 的边界。
   - 断言写入前 preview 包含 `Workflow 补充约束`、workflow note 和 routing policy 边界。
2. 运行目标测试，确认当前实现失败。
3. 在 `interactive_init.py` 中实现：
   - 新增 `_show_workflow_note_immediate_summary(workflow_confirmation)`。
   - 在 `_show_workflows()` 后调用即时 summary。
   - 扩展 `_show_prewrite_maturity_preview(..., workflow_confirmation)`，在 design preview 中展示 `Workflow 补充约束`。
   - 保持无 note 时即时 summary 静默；preview 说明按内置 routing 预览。
4. 更新 `docs/engineering/init-workflow.md` 的用户补充规则，固化 workflow note 的即时复述和 preview 边界。
5. 更新 `docs/evolution-log.md`，记录本轮 gap、用户故事、决策、验证和 Gate。

## 验证命令

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_restates_user_supplements_before_write_and_persists_them -q
.venv/bin/python -m pytest \
  tests/integration/test_init_on_fixture_projects.py::test_init_default_guided_mode_accepts_happy_path \
  tests/integration/test_init_on_fixture_projects.py::test_guided_init_records_scan_notes_and_team_rules_in_assets \
  tests/integration/test_init_on_fixture_projects.py::test_guided_init_restates_user_supplements_before_write_and_persists_them \
  tests/integration/test_init_on_fixture_projects.py::test_guided_init_final_summary_can_go_back_to_team_rules -q
scripts/test-fast.sh
```

## 提交策略

- commit 前必须完成 `scripts/test-fast.sh`。
- 本轮是独立 init 体验切片，可以创建本地 commit。
- 不 push；当前本地批次尚未重新满足 push 前 full regression 条件。
