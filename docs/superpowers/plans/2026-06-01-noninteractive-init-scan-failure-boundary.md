# 非交互 init 扫描失败边界实施计划

## 用户故事

作为 CI / acceptance 维护者，当我运行 `harness-builder-agent init --non-interactive` 且 LLM 扫描、网络或 schema 阶段失败时，我可以看到简短、中文、阶段明确的 scan 失败说明，并在 generation trace 中看到 `scan failed` 和错误类型，同时确认没有写入正式 Harness 资产，从而能快速定位外部服务或扫描契约问题。

## 步骤

1. TDD 红灯
   - 在 `tests/integration/test_init_on_fixture_projects.py` 新增 `test_non_interactive_init_scan_failure_prints_short_message_and_trace`。
   - monkeypatch `harness_builder_agent.tools.interactive_init.scan_repository` 抛 `RuntimeError("synthetic noninteractive scan failure")`。
   - 断言 CLI 输出、exit code、trace、无正式资产、无 traceback、无外层 `init failed`。
   - 运行 targeted pytest，确认失败。

2. 实现
   - 在 `src/harness_builder_agent/tools/interactive_init.py` 的 `run_non_interactive_init()` 中包裹 `scan_repository(repo)`。
   - scan 异常时记录 `trace.event("scan", "failed", ...)`、输出短错误说明、`trace.finish("failed", ...)`，然后 `raise typer.Exit(code=1) from None`。
   - 复用 `_short_error_message()`，必要时调整 helper 位置但不改变现有调用语义。

3. 文档
   - 更新 `docs/engineering/init-workflow.md`，把非交互 scan failure 的稳定边界与“无 guided 进度契约”区分清楚。
   - 更新 `README.md` 的非交互模式说明，提示自动化失败时会短错误、scan trace、无正式资产。
   - 更新 `docs/evolution-log.md`，记录 gap analysis 摘要、决策、验证、Self-Harness Gate。

4. 验证
   - 运行新增 targeted test。
   - 运行 guided scan failure 相关 targeted test，防止复用 helper 影响 guided 路径。
   - 运行 `tests/integration/test_init_on_fixture_projects.py`。
   - 运行 `python -m compileall src tests`。
   - 运行 `git diff --check`。
   - commit 前运行 `scripts/test-fast.sh`。
   - commit 后按 push gate 评估 `scripts/test-full.sh`；若仍因 DeepSeek DNS / 外部网络失败，则记录不 push。

## 验收命令

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_non_interactive_init_scan_failure_prints_short_message_and_trace -q
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_scan_failure_prints_progress_and_no_formal_assets tests/integration/test_init_on_fixture_projects.py::test_non_interactive_init_scan_failure_prints_short_message_and_trace -q
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py -q
.venv/bin/python -m compileall src tests
git diff --check
scripts/test-fast.sh
scripts/test-full.sh
```
