# Existing Harness LLM 维护动作失败 Trace 实施计划

## 目标

让已有 Harness 维护入口中的 `recommend-workflow` 和 `self-improve` 在 LLM / schema / review-only 生成失败时保留 action-specific trace，而不是退化成顶层 `init failed`。

## 步骤

1. 测试先红
   - 在 `tests/integration/test_init_on_fixture_projects.py` 新增 `test_guided_init_existing_harness_recommend_workflow_llm_failure_preserves_action_trace`。
   - 在同文件新增 `test_guided_init_existing_harness_self_improve_failure_preserves_action_trace`。
   - 两个测试都先生成 baseline Harness，保存正式资产 snapshot，patch TTY 和 scan 防止误重扫。
   - 分别 monkeypatch `existing_harness_action_runner.recommend_workflow` / `run_self_improve` 抛多行 `RuntimeError`。
   - 断言目标 action-specific trace、CLI、正式资产不变、无 `.ai/task-runs`、无顶层 `init failed`。

2. 实现
   - 在 `existing_harness_action_failures.py` 增加 `short_action_error_message()`。
   - 在 `existing_harness_action_runner.py` 中导入 helper。
   - 包裹 `recommend_workflow()` 和 recommendation report 读取 / schema 校验；失败时调用 `fail_existing_harness_action(..., error=\"workflow_recommendation_failed\", details={...})`。
   - 包裹 `run_self_improve()` 和 manifest 读取 / schema 校验；失败时调用 `fail_existing_harness_action(..., error=\"self_improve_failed\", details={...})`。

3. 文档
   - 更新 README 的已有 Harness 维护入口说明，指出 LLM / schema 失败会保留 action-specific failed trace。
   - 更新 `docs/engineering/init-workflow.md` 的维护动作失败规则。
   - 更新 `docs/evolution-log.md` 记录本轮 gap、用户故事、验证和 Gate。

4. 验证
   - 运行新增 targeted tests，确认先红后绿。
   - 运行 recommend-workflow success / empty task failure / self-improve success 回归。
   - 运行 `tests/integration/test_init_on_fixture_projects.py`。
   - 运行 `compileall`、`git diff --check`、`scripts/test-fast.sh`。
   - 评估 `scripts/test-full.sh`；若仍因外部 DeepSeek 网络 / 审批失败，不 push 并记录。

## 边界

- 不改变成功路径产物。
- 不修改 LLM prompt、schema、writer、benchmark、Sensor 或 Runtime。
- 不做正式资产 rollback；以测试保证失败时正式资产 snapshot 不变。
