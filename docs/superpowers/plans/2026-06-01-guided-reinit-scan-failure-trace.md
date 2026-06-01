# Guided Reinit 扫描失败 Trace 审计实施计划

## 目标

补齐 guided `init` 在 existing Harness `reinit` 后扫描失败的审计边界：CLI 继续显式失败且不写正式资产，trace summary 保留 reinit 来源、扫描未完成和未写入正式资产事实。

## 步骤

1. 测试先红
   - 在 `tests/integration/test_init_on_fixture_projects.py` 新增 `test_guided_init_existing_harness_reinit_scan_failure_keeps_action_and_assets`。
   - 先用非交互 init 生成 baseline Harness，并保存正式资产 snapshot。
   - patch guided TTY 和 `scan_repository()`，让 reinit 后扫描抛 `RuntimeError("synthetic reinit scan failure")`。
   - 断言 CLI 输出 reinit 边界、扫描失败和未写入正式资产；断言正式资产 snapshot 不变；断言 trace summary 目标字段。
   - 增强既有 `test_guided_init_scan_failure_prints_progress_and_no_formal_assets`，断言普通 guided scan failure summary 也有 `scan_completed=false` 和 `formal_assets_written=false`。

2. 实现
   - 修改 `src/harness_builder_agent/tools/interactive_init.py` 的 guided scan exception 分支。
   - 使用 `_short_error_message(exc)` 生成短错误摘要。
   - `trace.event("scan", "failed", ...)` 写短错误。
   - 构造 failed summary：`error_type`、`scan_error`、`scan_completed=false`、`formal_assets_written=false`。
   - 如果 `_is_existing_harness_reinit_requested(trace)` 为真，追加 `existing_harness_action=reinit`。
   - 保持 `_show_scan_progress_failed(exc)` 和 `raise typer.Exit(code=1)`。

3. 文档
   - 更新 `README.md` 的 reinit 段落，说明 reinit 扫描失败 trace summary 保留 action、scan_completed 和未写入边界。
   - 更新 `docs/engineering/init-workflow.md` 的 guided scan failure / reinit 规则。
   - 在 `docs/evolution-log.md` 顶部新增本轮记录，包含 gap analysis 摘要、用户故事、决策、验证和 Gate。

4. 验证
   - 先运行新增 targeted test，确认 RED。
   - 实现后运行新增 targeted test、普通 guided scan failure、reinit cancel / completion 相关 targeted tests。
   - 运行 `tests/integration/test_init_on_fixture_projects.py`。
   - 运行 `compileall` 覆盖修改模块。
   - 运行 `git diff --check`。
   - commit 前运行 `scripts/test-fast.sh`。
   - push 前按规则尝试 `scripts/test-full.sh`；若因外部 DeepSeek 网络 / 审批失败，则记录为未 push 前置。

## 边界

- 不改 LLM、scan reconcile、evidence expansion、schema、writer、benchmark 或 Runtime。
- 不新增 `.ai/task-runs`。
- 不把 scan failure fallback 成确定性成功。
- 不解决 full regression 外部网络与真实仓库 evidence 外发审批问题。
