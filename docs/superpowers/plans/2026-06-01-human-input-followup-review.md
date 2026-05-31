# Human Input Follow-up 人工复核实施计划

## 修改范围

- `src/harness_builder_agent/schemas/human_confirmation.py`
- `src/harness_builder_agent/schemas/human_input_governance.py`
- `src/harness_builder_agent/tools/human_input_governance.py`
- `src/harness_builder_agent/tools/human_confirmation.py`
- `src/harness_builder_agent/tools/interactive_init.py`
- `src/harness_builder_agent/cli.py`
- `tests/unit/test_schema_contracts.py`
- `tests/unit/test_human_confirmation.py`
- `tests/unit/test_interactive_init_preview.py`
- `tests/unit/test_human_input_governance.py`
- `tests/integration/test_assess_improve_commands.py` 或 `tests/integration/test_init_on_fixture_projects.py`
- `README.md`
- `docs/engineering/init-workflow.md`
- `docs/evolution-log.md`

## TDD 步骤

1. Schema 测试：
   - `Questionnaire` 接受 `reviewed_resolved_by_harness_maintainer`。
   - `HumanInputGovernanceLog` 校验 resolved / reopened 决策。
2. Unit 测试：
   - `review_human_input(..., decision="resolved")` 更新 `questionnaire.yaml`，写 governance YAML / Markdown，刷新 `human-input-needed.md`。
   - `reopened` 从 resolved 回到 partial 或 unaddressed。
   - 未知 id、非 scan follow-up、空 rationale 显式失败。
3. Markdown / maintenance preview 测试：
   - `human_input_markdown()` 对 resolved / partial / unaddressed follow-up 输出不同处理建议。
   - `_human_input_needed_status_lines()` 增加 resolved count。
4. CLI integration 测试：
   - 准备一个 fixture Harness，人工制造或使用已有 scan follow-up。
   - 调用 `review-human-input --decision resolved`。
   - 断言退出成功、产物 schema 有效、formal assets 未改变。
5. 实现：
   - 扩展 response status enum。
   - 新增 governance schema / tool。
   - 新增 CLI command 和 trace artifacts。
   - 更新 human-input Markdown 和 existing Harness status lines。
6. 文档与记录：
   - README 增加命令。
   - `docs/engineering/init-workflow.md` 固化 human-input review-only 治理边界。
   - `docs/evolution-log.md` 记录 Gap Analysis、完成内容和 Gate。
7. 验证：
   - 目标 unit / integration。
   - 完整 guided init integration。
   - `git diff --check`。
   - `scripts/test-fast.sh`。
8. 提交：
   - 中文 commit message。
   - 不 push，除非后续完整工作包进入统一 push 边界并通过 `scripts/test-full.sh`。

## 验收命令

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py::test_questionnaire_accepts_resolved_followup_response_status tests/unit/test_human_input_governance.py tests/unit/test_human_confirmation.py::<目标测试名> tests/unit/test_interactive_init_preview.py::test_human_input_needed_status_lines_summarize_questionnaire -q
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::<目标测试名> -q
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py -q
git diff --check
scripts/test-fast.sh
```
