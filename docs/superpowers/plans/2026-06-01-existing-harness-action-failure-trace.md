# Existing Harness 维护动作失败 Trace 保真实施计划

## 目标

统一已有 Harness guided maintenance action 的失败出口，避免 action-specific `trace.finish("failed", ...)` 被顶层 `init_command` 的泛化异常处理覆盖。

## 步骤

1. 写 RED integration tests。
   - 在 `tests/integration/test_init_on_fixture_projects.py` 增加：
     - `recommend-workflow` 空 task brief 失败保留 `existing_harness_action=recommend-workflow`。
     - `review-human-input` unknown interaction id 失败保留 `existing_harness_action=review-human-input`、interaction id、decision 和 error。
     - `review-initial-candidate` 缺 `.ai/experience/weapon-library-candidates.yaml` 失败保留 `existing_harness_action=review-initial-candidate`。
   - 补强既有 workflow policy guided apply 禁止测试，断言失败 trace summary。

2. 实现统一失败 helper。
   - 在 `existing_harness_action_runner.py` 增加 `_fail_existing_harness_action(...)`。
   - helper 负责写 failed event、finish summary、echo 简短失败说明，然后 `raise typer.Exit(code=1)`。
   - summary 保留 action、error、candidate id、interaction id、decision 等上下文。

3. 替换已知 BadParameter 失败出口。
   - `recommend-workflow` empty task brief。
   - `review-candidate` workflow policy guided apply。
   - `review-candidate` unsupported decision。
   - `review-candidate` governance exception。
   - `review-human-input` governance exception。
   - `review-initial-candidate` missing report。
   - `review-initial-candidate` governance exception。
   - 可顺手把上一轮 `review-candidate` precheck 迁到 helper，保持一致。

4. 验证。
   - 先运行新增 targeted tests，确认 RED。
   - 实现后运行 targeted failure tests。
   - 运行 `tests/integration/test_init_on_fixture_projects.py`。
   - 运行 `python -m compileall src tests` 或 `.venv/bin/python -m compileall src tests`。
   - 运行 `git diff --check`。
   - 更新 `docs/evolution-log.md` 后运行 `scripts/test-fast.sh`。

## 验收边界

- 本轮只处理 guided existing Harness maintenance action 失败 trace。
- 不修改 standalone CLI 命令。
- 不修改 LLM、benchmark check、schema 或 Runtime artifact contract。
- 本轮提交后不 push；push 仍等待 `scripts/test-full.sh` 在具备 DeepSeek key 和 `.benchmarks` 后通过。
