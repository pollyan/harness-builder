# Existing Harness 智能维护动作抽取计划

目标：把已有 Harness 维护入口中的 `recommend-workflow` 与 `self-improve` LLM / review-only 动作从 `existing_harness_action_runner.py` 抽到独立 intelligent action 模块，保持 CLI、trace、artifact 和 Runtime 边界不变。

## 实施步骤

1. 写 RED 边界测试
   - 增强 `tests/unit/test_existing_harness_action_boundaries.py`。
   - 断言存在 `existing_harness_intelligent_actions` 模块及 `run_recommend_workflow_action()` / `run_self_improve_action()`。
   - 断言 runner 调用 delegate，且不再直接持有 `recommend_workflow()`、`run_self_improve()`、`WorkflowRecommendationReport`、`SelfImprovePackageManifest`。
   - 先运行 targeted unit，确认新模块缺失或边界未满足时失败。

2. 新增 intelligent action 模块
   - 新增 `src/harness_builder_agent/tools/existing_harness_intelligent_actions.py`。
   - 搬迁 `recommend-workflow` 的 task brief / task id prompt、`recommend_workflow()` 调用、`WorkflowRecommendationReport` 读取、trace artifacts、trace finish 和 summary 输出。
   - 搬迁 `self-improve` 的 `run_self_improve()` 调用、`SelfImprovePackageManifest` 读取、trace artifacts、trace finish 和 summary 输出。
   - 复用 `fail_existing_harness_action()` 与 `short_action_error_message()` 保持 action-specific 失败语义。

3. 收窄 runner
   - `existing_harness_action_runner.py` 导入并调用 `run_recommend_workflow_action()` / `run_self_improve_action()`。
   - 删除 runner 对 `yaml`、`WorkflowRecommendationReport`、`SelfImprovePackageManifest`、`recommend_workflow`、`run_self_improve`、`workflow_recommendation_summary`、`self_improve_summary`、`short_action_error_message` 的直接依赖。
   - 保留 `exit`、`assess`、`improve`、`benchmark`、review action delegate、`reinit` 和 unknown action 行为不变。

4. 更新测试 monkeypatch 路径
   - 将 existing Harness LLM failure integration 中的 monkeypatch 路径从 runner 改到 `existing_harness_intelligent_actions`。
   - 不放宽任何 CLI 输出、trace summary、正式资产 snapshot 或 `.ai/task-runs` 断言。

5. 文档与演进记录
   - 更新 `docs/evolution-log.md`，记录本轮 Gap Analysis 摘要、工程信任故事、关键取舍、验证结果和 Self-Harness Gate。
   - 本轮行为保持，不更新 README / engineering 长期契约；架构文档已有 runner / review action 边界，本轮如只增加子模块无需扩展产品规则。

6. 验证
   - RED targeted unit。
   - 实现后运行：
     - `.venv/bin/python -m pytest -q tests/unit/test_existing_harness_action_boundaries.py`
     - recommend-workflow / self-improve success 与 failure targeted integration。
     - `python -m compileall src/harness_builder_agent/tools/existing_harness_action_runner.py src/harness_builder_agent/tools/existing_harness_intelligent_actions.py`
     - `git diff --check`
     - `scripts/test-fast.sh`
   - 按 Self-Harness Gate 运行 `scripts/test-full.sh` 评估 push 前状态；若 acceptance 仍因外部 DeepSeek / 网络 / 审批失败，记录并不 push。

## 非目标

- 不新增或删除 existing Harness action。
- 不改变 action 菜单、action prompt、默认 `exit`、成功 / 失败文案、trace summary、artifact kind 或输出文件。
- 不修改 LLM prompt、Pydantic schema、benchmark 检查规则、writer、Sensor 或 Runtime 产物。
- 不执行 Runtime，不创建 `.ai/task-runs`。
- 不把 full regression / push 伪装成本轮代码能力完成条件。
