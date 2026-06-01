# Init 扫描失败短错误与未写入审计实施计划

## 目标

让 guided 与 `--non-interactive` 的 init scan failure 共享清晰、短小、可审计的失败边界：CLI 使用短错误摘要，trace summary 显式记录扫描未完成和正式资产未写入。

## 步骤

1. 测试先红
   - 增强 `test_guided_init_scan_failure_prints_progress_and_no_formal_assets`：mock scan 抛多行 `RuntimeError`，断言 CLI 原因行使用折叠后的短错误，且不包含原始多行文本。
   - 增强 `test_non_interactive_init_scan_failure_prints_short_message_and_trace`：断言 trace summary 包含 `scan_completed=false` 和 `formal_assets_written=false`。

2. 实现
   - 修改 `guided_scan_presentation.show_scan_progress_failed()`，增加可选 `error_message` 参数。
   - 修改 `interactive_init.run_guided_init()` scan exception 分支，把已计算的 `error_message` 传给 `_show_scan_progress_failed()`。
   - 修改 `run_non_interactive_init()` scan exception 分支的 `trace.finish()` summary，增加 `scan_completed=false` 和 `formal_assets_written=false`。

3. 文档
   - 更新 README 的 guided / non-interactive scan failure 说明，沉淀短错误和 summary 未写入字段。
   - 更新 `docs/engineering/init-workflow.md` 的 guided 与 non-interactive scan failure 规则。
   - 更新 `docs/evolution-log.md`，记录本轮 gap、用户故事、验证和 Gate。

4. 验证
   - 运行新增 targeted tests，确认先红后绿。
   - 运行 scan failure / reinit scan failure targeted tests。
   - 运行 `tests/integration/test_init_on_fixture_projects.py`。
   - 运行 `compileall`、`git diff --check`、`scripts/test-fast.sh`。
   - 评估 `scripts/test-full.sh`；若仍因外部 DeepSeek 网络 / 审批失败，不 push 并记录原因。

## 边界

- 不改 LLM、DeepSeek、schema、scanner、writer、benchmark 或 Runtime。
- 不添加 fallback，不吞异常。
- 不改变正式资产生成成功路径。
