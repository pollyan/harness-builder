# Human Input 深度追问处理建议实施计划

**Goal:** `.ai/human-input-needed.md#处理方式` 对 scan follow-up 保留和 CLI 一致的 trigger-specific 回答建议，让会后处理也能看到 `stack` / `module` / `command` / `risk` 示例和人工复核边界。

**Architecture:** 把上一轮 CLI guidance 的确定性映射抽到轻量 `scan_followup_guidance.py` helper。`guided_scan_presentation.py` 和 `human_confirmation.py` 共用它；不改 schema、不改 LLM、不改 benchmark、不改 Runtime。

## Steps

1. **RED：human-input markdown unit**
   - 修改 `tests/unit/test_human_confirmation.py`。
   - 新增或扩展测试，构造 coverage / stack / test `scan_followup_confirmation`。
   - 断言 Markdown `## 处理方式` 包含：
     - `confirm:scan-followup:coverage-source-java`
     - `module=src/main/java|backend|核心模块`
     - `risk=src/main/java/payments|支付或权限高风险`
     - `stack=java-spring`
     - `command=unit_test|mvn test|test|hard|pom.xml|high`
     - `不会自动关闭追问`

2. **RED：guided integration artifact**
   - 扩展 `tests/integration/test_init_on_fixture_projects.py::test_guided_init_shows_scan_followup_questions`。
   - 断言 `.ai/human-input-needed.md` 包含同一套具体处理建议。

3. **实现共享 helper**
   - 新增 `src/harness_builder_agent/tools/scan_followup_guidance.py`。
   - 搬迁 / 复用 `scan_followup_answer_guidance_line()` 和 list helper。
   - `guided_scan_presentation.py` 改为调用 helper，保持现有 CLI transcript。
   - `human_confirmation.py` 的 `_scan_followup_action_guidance()` 追加 helper 产出的建议文本。

4. **文档同步**
   - 更新 `README.md` 的 human-input-needed 描述。
   - 更新 `docs/engineering/init-workflow.md` 的 `.ai/human-input-needed.md` 规则，说明 scan follow-up action guidance 会保留 trigger-specific 示例。

5. **演进记录**
   - 在 `docs/evolution-log.md` 顶部新增本轮记录。

6. **验证与提交**
   - 运行 targeted tests：
     - `.venv/bin/python -m pytest tests/unit/test_human_confirmation.py tests/unit/test_guided_scan_presentation.py tests/integration/test_init_on_fixture_projects.py::test_guided_init_shows_scan_followup_questions -q`
   - 运行相关 human input governance regression：
     - `.venv/bin/python -m pytest tests/unit/test_human_input_governance.py tests/integration/test_init_on_fixture_projects.py::test_review_human_input_command_marks_scan_followup_resolved_without_overwriting_formal_assets -q`
   - 运行 compile / diff：
     - `.venv/bin/python -m compileall src/harness_builder_agent tests`
     - `git diff --check`
   - commit 前运行 `scripts/test-fast.sh`。
   - 本轮不 push。

## Self-Harness Gate 检查点

- 是否需要新增 todo：预计不需要；本轮直接完成上一轮 Gate 候选。
- 是否需要 benchmark：本轮不新增 benchmark check；如果后续发现 human-input action guidance 漂移，再作为独立 benchmark hardening 候选。
- 是否影响 Runtime：不影响，必须保留不执行 Runtime / 不创建 `.ai/task-runs` 边界。
