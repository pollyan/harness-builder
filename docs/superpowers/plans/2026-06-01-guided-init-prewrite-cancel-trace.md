# Guided Init 写入前取消 Trace 审计实施计划

用户故事：

作为 Harness Maintainer，当我在 guided `init` 已完成扫描和写入前设计预览后选择取消时，我可以在 CLI 中确认未写入正式 Harness 资产，并在 trace summary 中看到取消发生在写入前、扫描已经完成、识别出的 stack / command 摘要以及 reinit 来源，从而能安全复盘一次未完成的初始化或重新生成会话。

## 步骤

1. 写失败测试
   - 在 `tests/integration/test_init_on_fixture_projects.py` 新增首次 init final cancel 测试：
     - 输入 happy path 直到最终确认，选择 `cancel`。
     - 断言输出中文取消摘要、无 `== 初始化完成 ==`、没有正式 `.ai/project-inventory.json`。
     - 断言 latest trace failed summary 含 `cancelled=true`、`cancel_stage=prewrite_confirmation`、`scan_completed=true`、`primary_stack=java-spring`、`command_count=1`。
   - 新增 reinit final cancel 测试：
     - 先 non-interactive baseline。
     - 再 guided 选择 `9. reinit`，走到最终确认选择 `cancel`。
     - 断言正式资产 snapshot 不变，trace summary 含 prewrite cancel 字段和 `existing_harness_action=reinit`。
   - 更新 reinit before-scan cancel 断言 `cancel_stage=startup_confirmation`、`scan_completed=false`。
   - 先运行 targeted tests，确认 RED。

2. 实现
   - 修改 `_cancel_guided_init()` 签名，增加 `cancel_stage`、`inventory=None`、`commands=None`。
   - startup cancel 调用传 `cancel_stage="startup_confirmation"`。
   - final cancel 调用传 `cancel_stage="prewrite_confirmation"`、`inventory`、`commands`。
   - summary 追加 `scan_completed`，在存在 inventory/commands 时追加 `primary_stack`、`command_count`。
   - 保持现有 CLI 文案和 `typer.Exit(1)`。

3. 文档
   - README 补充取消 trace 审计字段。
   - `docs/engineering/init-workflow.md` 补充 startup / prewrite cancel trace 规则。
   - `docs/evolution-log.md` 顶部新增本轮记录。

4. 验证
   - targeted RED / GREEN：
     ```bash
     .venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_final_cancel_after_scan_keeps_trace_audit_without_assets tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_reinit_final_cancel_keeps_trace_audit_and_assets -q
     ```
   - 回归：
     ```bash
     .venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_reinit_cancel_before_scan_keeps_assets tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_reinit_completion_keeps_audit_and_summary -q
     .venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py -q
     .venv/bin/python -m compileall src/harness_builder_agent/tools/interactive_init.py
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
