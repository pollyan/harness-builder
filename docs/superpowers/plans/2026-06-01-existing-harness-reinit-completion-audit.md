# Existing Harness Reinit 完成审计实施计划

用户故事：

作为 Harness Maintainer，当我在已有 Harness 维护入口选择 `reinit` 并最终确认重新生成时，我可以在 trace summary 中看到这次完成来自 `existing_harness_action=reinit`，同时仍看到 `== 初始化完成 ==` 交付摘要，从而既能审计覆盖来源，也不会丢失重新生成后的交付说明。

## 步骤

1. 写失败测试
   - 在 `tests/integration/test_init_on_fixture_projects.py` 新增 `test_guided_init_existing_harness_reinit_completion_keeps_audit_and_summary`。
   - 先用 `--non-interactive` 生成 baseline Harness。
   - 默认 guided 再次进入，输入 `9` 选择 reinit，并沿 happy path 回车，最终输入 `confirm`。
   - 断言输出包含 reinit 边界、`== 初始化完成 ==`、`本次已生成`。
   - 断言 latest trace `status=completed`，summary 含 `existing_harness_action=reinit`、`primary_stack=java-spring`、`command_count=1`。
   - 先运行 targeted test，确认红在 trace summary 缺少 reinit action。

2. 实现 trace 和 completion 条件
   - 修改 `src/harness_builder_agent/tools/interactive_init.py`：成功 finish 前构造 summary，reinit 时追加 `existing_harness_action=reinit`。
   - 修改 `src/harness_builder_agent/cli.py`：`_should_render_initial_init_completion()` 允许 `existing_harness_action == "reinit"` 时渲染 completion，其他已有 Harness action 继续 suppress。

3. 同步事实源文档
   - 更新 `README.md` existing Harness reinit 段落，说明 reinit 成功完成后保留 trace action 且仍显示初始化完成摘要。
   - 更新 `docs/engineering/init-workflow.md` 对应 reinit 规则。
   - 在 `docs/evolution-log.md` 顶部新增本轮中文记录。

4. 验证
   - targeted RED：
     ```bash
     .venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_reinit_completion_keeps_audit_and_summary -q
     ```
   - targeted green：
     ```bash
     .venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_reinit_completion_keeps_audit_and_summary tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_reinit_cancel_before_scan_keeps_assets tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_can_exit_with_numbered_action -q
     ```
   - init integration 回归：
     ```bash
     .venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py -q
     ```
   - 语法与 diff：
     ```bash
     .venv/bin/python -m compileall src/harness_builder_agent/cli.py src/harness_builder_agent/tools/interactive_init.py
     git diff --check
     ```
   - commit 前：
     ```bash
     scripts/test-fast.sh
     ```
   - push gate：
     ```bash
     scripts/test-full.sh
     ```

5. 提交 / push 判断
   - fast 通过后创建中文 commit。
   - full 通过才 push；若 full 仍因 DeepSeek DNS / 外发审批失败，不 push，并在回复和 evolution log 记录。
