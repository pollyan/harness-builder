# Existing Harness Reinit 边界实施计划

## 用户故事

作为 Harness Maintainer，当我在已有 Harness 维护入口显式选择 `reinit` 准备重新生成时，我可以在继续扫描前看到重新生成现有 Harness 的边界说明，并且如果我取消，CLI 与 trace 都明确记录这是 reinit 取消且未扫描、未覆盖正式资产。

## 步骤

1. TDD 红灯
   - 在 `tests/integration/test_init_on_fixture_projects.py` 新增 `test_guided_init_existing_harness_reinit_cancel_before_scan_keeps_assets`。
   - 先用非交互 init 生成完整 `.ai`，保存正式资产 snapshot。
   - 再运行 guided init，输入 `9\nn\n`，并 monkeypatch scan 抛错以证明取消前不会扫描。
   - 断言输出 reinit 边界、中文取消摘要、无初始化完成、正式资产未变、trace failed 且 summary 含 `existing_harness_action=reinit`。
   - 运行 targeted test，确认失败。

2. 实现
   - 在 `interactive_init.py` 新增 `_is_reinit_requested(trace)`，从 trace events 识别 existing Harness reinit action。
   - `_show_guided_init_startup_boundary()` 增加 `reinit_requested` 参数，命中时输出 reinit 专属边界。
   - 新增 `_cancel_guided_init(trace, *, reinit_requested)`，统一 trace finish、中文取消输出和 `typer.Exit(1)`。
   - 替换当前两个 guided cancel 分支的 `trace.finish(...); raise typer.Abort()`。

3. 文档
   - 更新 `docs/engineering/init-workflow.md`，沉淀 `reinit` 后不会在最终确认前覆盖正式资产、取消应保留 reinit trace。
   - 更新 README existing Harness 维护入口说明，增加 reinit 边界。
   - 更新 `docs/evolution-log.md` 记录本轮 gap、决策、验证和 Gate。

4. 验证
   - 运行新增 targeted test。
   - 运行 partial Harness cancel targeted，确保普通取消仍不扫描。
   - 运行 existing Harness 相关 targeted tests。
   - 运行 `tests/integration/test_init_on_fixture_projects.py`。
   - 运行 `python -m compileall src tests`。
   - 运行 `git diff --check`。
   - commit 前运行 `scripts/test-fast.sh`。
   - commit 后评估 `scripts/test-full.sh`；若仍因 DeepSeek DNS / 外发审批失败，则不 push。

## 验收命令

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_reinit_cancel_before_scan_keeps_assets -q
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_partial_harness_core_is_explained_before_continue tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_reinit_cancel_before_scan_keeps_assets -q
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py -q
.venv/bin/python -m compileall src tests
git diff --check
scripts/test-fast.sh
scripts/test-full.sh
```
