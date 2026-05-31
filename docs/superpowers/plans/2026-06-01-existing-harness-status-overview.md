# Existing Harness 维护状态人话摘要实施计划

## 目标

在已有 Harness 维护入口中，在 raw `Benchmark / Workflow / Experience` signals 之前展示短中文维护状态摘要，让 Maintainer 先理解健康状态、积压事项和建议动作，再按需查看机器友好的 key/value signals。

## 实施步骤

1. RED 测试：
   - 新增 `tests/unit/test_existing_harness_status_overview.py`，覆盖 benchmark not_run、benchmark failed、Experience backlog、human-input pending、no pending signal。
   - 扩展 existing Harness guided exit integration，断言输出包含 `维护状态摘要（Maintenance overview）`、benchmark not run 中文摘要、routing 中文摘要和 top action 编号。
2. 新增 `src/harness_builder_agent/tools/existing_harness_status.py`：
   - 暴露 `render_existing_harness_status_overview_lines(ai, config, score, actions)`。
   - 使用 `BenchmarkReport`、`ExperienceIndex`、`Questionnaire` schema 读取结构化文件。
   - 使用 `existing_harness_action_number()` 查询 triage 第一动作编号。
3. 接入 `interactive_init.py`：
   - 在读取 `maintenance_actions` 后、raw signals 前输出 `维护状态摘要（Maintenance overview）`。
   - 保留 raw signals、triage lines、guidance、shortcuts 和菜单顺序。
4. 更新 `docs/evolution-log.md`，记录 Gap Analysis、完成内容、验证结果和 Gate。
5. 验证：
   - targeted unit / integration。
   - `git diff --check`。
   - `scripts/test-fast.sh`。
6. 本地提交；不 push，除非后续形成完整工作包并通过 full regression。

## 验证命令

```bash
.venv/bin/python -m pytest tests/unit/test_existing_harness_status_overview.py tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_can_exit_with_numbered_action -q
git diff --check
scripts/test-fast.sh
```

## 非目标

- 不删除 raw `Benchmark signals` / `Workflow routing signals` / `Experience / review signals`。
- 不改变 maintenance triage 排序或 action shortcut 文案。
- 不新增、删除或重排维护菜单动作。
- 不改变任何已有 Harness 动作的执行语义。
- 不修改 benchmark、LLM、schema 或 Runtime 契约。
- 不创建 `.ai/task-runs`，不覆盖正式 Harness 资产。
