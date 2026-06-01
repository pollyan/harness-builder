# Existing Harness 确定性维护动作抽取计划

目标：把已有 Harness 维护入口中的 `assess`、`improve` 和 `benchmark` 确定性动作从 `existing_harness_action_runner.py` 抽到独立 deterministic action 模块，保持 CLI、trace、artifact 和 Runtime 边界不变。

## 实施步骤

1. 写 RED 边界测试
   - 增强 `tests/unit/test_existing_harness_action_boundaries.py`。
   - 断言存在 `existing_harness_deterministic_actions` 模块及 `run_assess_action()`、`run_improve_action()`、`run_benchmark_action()`。
   - 断言 runner 调用 delegate，且不再直接持有 `assess_maturity()`、`generate_improvements()`、`run_benchmark()`、`BenchmarkReport`。
   - 先运行 targeted unit，确认新模块缺失或边界未满足时失败。

2. 新增 deterministic action 模块
   - 新增 `src/harness_builder_agent/tools/existing_harness_deterministic_actions.py`。
   - 搬迁 `assess` 的 maturity refresh 调用、trace artifacts、trace finish 和 CLI summary。
   - 搬迁 `improve` 的 experience index refresh、maturity refresh、improvement generation、trace artifacts、trace finish 和 CLI summary。
   - 搬迁 `benchmark` 的 `run_benchmark()` 调用、`BenchmarkReport` 校验、failed check 统计、trace artifacts、trace finish 和 CLI summary。

3. 收窄 runner
   - `existing_harness_action_runner.py` 导入并调用 `run_assess_action()` / `run_improve_action()` / `run_benchmark_action()`。
   - 删除 runner 对 `BenchmarkReport`、`assess_maturity`、`generate_improvements`、`run_benchmark`、`write_experience_index`、`benchmark_summary`、`top_improvement_candidate` 的直接依赖。
   - 保留 `exit`、review action delegate、intelligent action delegate、`reinit` 和 unknown action 行为不变。

4. 文档与演进记录
   - 更新 `docs/engineering/architecture.md`，记录 deterministic action 模块职责。
   - 更新 `docs/evolution-log.md`，记录本轮 Gap Analysis 摘要、工程信任故事、关键取舍、验证结果和 Self-Harness Gate。
   - 本轮行为保持，不更新 README / init workflow 用户契约。

5. 验证
   - RED targeted unit。
   - 实现后运行：
     - `.venv/bin/python -m pytest -q tests/unit/test_existing_harness_action_boundaries.py`
     - assess / improve / benchmark targeted integration。
     - `tests/integration/test_init_on_fixture_projects.py`
     - `python -m compileall` 针对 runner 与新模块。
     - `git diff --check`
     - `scripts/test-fast.sh`
   - 按 Self-Harness Gate 运行 `scripts/test-full.sh` 评估 push 前状态；若 acceptance 仍因外部 DeepSeek / 网络 / 审批失败，记录并不 push。

## 非目标

- 不新增或删除 existing Harness action。
- 不改变 action 菜单、action prompt、默认 `exit`、成功 / 失败文案、trace summary、artifact kind 或输出文件。
- 不修改 LLM prompt、Pydantic schema、benchmark 检查规则、writer、Sensor 或 Runtime 产物。
- 不执行 Runtime，不创建 `.ai/task-runs`。
- 不把 full regression / push 伪装成本轮代码能力完成条件。
