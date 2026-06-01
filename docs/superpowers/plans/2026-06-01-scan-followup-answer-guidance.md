# 深度追问回答建议实施计划

**Goal:** 首次 guided `init` 在展示深度追问和 LLM 二次自检后、收集 scan supplement 前，展示可行动的“深度追问回答建议”，把每个 follow-up trigger 映射到自然语言或 `stack` / `module` / `command` / `risk` 示例。

**Architecture:** 只改 guided scan presentation renderer。`interactive_init.py` 继续通过 `_show_scan_findings()` 编排扫描发现；`guided_scan_presentation.py` 在 `show_scan_attention_summary()` 内新增 answer guidance renderer。不新增 schema，不修改 writer / benchmark / LLM / Runtime。

## Steps

1. **RED：新增 unit renderer 测试**
   - 修改 `tests/unit/test_guided_scan_presentation.py`。
   - 新增测试构造含 5 类 follow-up 的 `ProjectInventory`，调用新 renderer 或 `show_scan_attention_summary()`。
   - 断言输出包含：
     - `深度追问回答建议`
     - `confirm:scan-followup:test-evidence`
     - `command=unit_test|mvn test|test|hard|pom.xml|high`
     - `module=src/main/java|backend|核心模块`
     - `stack=java-spring`
     - `不会自动关闭追问`

2. **RED：扩展 guided integration transcript**
   - 修改 `tests/integration/test_init_on_fixture_projects.py::test_guided_init_shows_scan_followup_questions`。
   - 断言 transcript 包含 answer guidance、针对 coverage / stack / test follow-up 的示例和 review-only 边界。
   - 先运行 targeted tests，确认失败来自缺少新输出。

3. **实现 renderer**
   - 修改 `src/harness_builder_agent/tools/guided_scan_presentation.py`：
     - 新增 `show_scan_followup_answer_guidance(inventory)`。
     - 新增 `scan_followup_answer_guidance_lines(inventory)` 和 trigger -> suggestion helper。
     - 在 `show_scan_attention_summary()` 中 `show_scan_self_check()` 后调用。
   - 用确定性 trigger 映射，不解析 LLM 自然语言。
   - 超过 5 条 follow-up 时只展示前 5 条并保留数量提示，避免终端过长。

4. **文档同步**
   - 更新 `README.md` 的 `init` 说明，补一句深度追问会给出回答建议。
   - 更新 `docs/engineering/init-workflow.md` 中 ScanMetadata follow-up 规则，说明 CLI 会展示回答建议且不会自动关闭追问。

5. **演进记录**
   - 在 `docs/evolution-log.md` 顶部新增本轮记录，包含 Gap Analysis 摘要、用户故事、决策、sub agent 使用、验证结果和下一轮候选。

6. **验证与提交**
   - 运行 targeted tests：
     - `.venv/bin/python -m pytest tests/unit/test_guided_scan_presentation.py tests/integration/test_init_on_fixture_projects.py::test_guided_init_shows_scan_followup_questions -q`
   - 运行相关 scan follow-up regression：
     - `.venv/bin/python -m pytest tests/unit/test_human_confirmation.py tests/integration/test_init_on_fixture_projects.py::test_guided_init_marks_scan_followup_partially_addressed_by_current_supplement -q`
   - 运行 compile / diff：
     - `.venv/bin/python -m compileall src/harness_builder_agent tests`
     - `git diff --check`
   - commit 前运行 `scripts/test-fast.sh`。
   - 本轮不 push，除非后续组成完整工作包并通过 `scripts/test-full.sh`。

## Self-Harness Gate 检查点

- 是否需要新增 todo：预计不需要；这是直接进入 spec / plan 的小型 `init` UX milestone。
- 是否影响 schema / benchmark：不影响。
- 是否影响 Runtime 分工：不影响；文案要明确不会创建 `.ai/task-runs`，不会自动关闭人工复核。
- 是否需要 acceptance：不需要，本轮不改 LLM prompt / parser /真实扫描逻辑。
