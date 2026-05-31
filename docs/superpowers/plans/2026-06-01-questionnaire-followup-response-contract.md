# Questionnaire Follow-up 回应状态契约实施计划

## 目标

把 scan follow-up 的“本轮 scan 补充可能已部分回应”从自然语言 reason 升级为 `Questionnaire` schema 字段，并让已有 Harness 维护入口能显示 partial / unaddressed follow-up 计数。

## 文件

- 修改：`src/harness_builder_agent/schemas/human_confirmation.py`
- 修改：`src/harness_builder_agent/tools/human_confirmation.py`
- 修改：`src/harness_builder_agent/tools/interactive_init.py`
- 修改：`tests/unit/test_schema_contracts.py`
- 修改：`tests/unit/test_human_confirmation.py`
- 修改：`tests/unit/test_interactive_init_preview.py`
- 修改：`tests/integration/test_init_on_fixture_projects.py`
- 修改：`docs/engineering/init-workflow.md`
- 修改：`docs/evolution-log.md`

## TDD 步骤

1. Schema 测试：
   - 旧 questionnaire payload validate 后默认 `response_status=unaddressed`、`response_sources=[]`。
   - 新 payload 支持 `response_status=partially_addressed_by_current_scan_supplement`。
   - 预期先失败，因为 schema 还没有字段。

2. Human confirmation unit：
   - matching scan supplement 的 follow-up 断言 `response_status` 和 `response_sources`。
   - unrelated supplement 断言保持 `unaddressed`。
   - 预期先失败，因为 builder 只写 reason。

3. Existing Harness maintenance unit：
   - `_human_input_needed_status_lines()` 对 scan follow-up partial / unaddressed 分别计数。
   - 预期先失败，因为当前只统计 scan confirmations 总数。

4. Guided integration：
   - 扩展上一轮 scan follow-up supplement 测试，断言 `.ai/questionnaire.yaml` 结构化字段。
   - 预期先失败。

5. 实现：
   - 在 `QuestionnaireQuestion` 增加 `response_status` 和 `response_sources` 默认字段。
   - 复用 `_matching_scan_supplement_snippets()`，让 `build_questionnaire()` 写入字段。
   - `_human_input_needed_status_lines()` 统计 scan follow-up partial / unaddressed。

6. 文档：
   - `docs/engineering/init-workflow.md` 固化 questionnaire response contract。
   - `docs/evolution-log.md` 记录本轮 Gap Analysis、完成内容和验证结果。

7. 验证：
   - Targeted schema / human confirmation / preview / guided integration。
   - 完整 `tests/integration/test_init_on_fixture_projects.py`。
   - `git diff --check`。
   - `scripts/test-fast.sh`。

## 非目标

- 不新增 `resolved` 状态。
- 不关闭或删除 follow-up question。
- 不改变正式扫描事实或 workflow routing policy。
- 不新增 workflow policy candidate。
