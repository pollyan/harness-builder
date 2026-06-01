# Scan Self-Check 结构化建议动作实施计划

## 目标

把 LLM scan self-check 的 `suggested_next_action` 从纯自由文本补强为 schema 可校验的 `suggested_action_type`，并让 CLI / questionnaire 展示可执行动作提示。

## 步骤

1. RED 测试
   - 在 `tests/unit/test_llm_scan_self_checker.py` 中新增：fresh LLM response 缺 `suggested_action_type` 时 `parse_scan_self_check_response()` 显式失败。
   - 扩展合法 parse 测试，断言 action type 被保留。
   - 扩展 prompt 测试，断言 prompt 枚举 `suggested_action_type`。
   - 扩展 guided scan presentation 或 human confirmation 测试，断言 CLI / questionnaire reason 展示 action type 和对应格式提示。

2. Schema / parser
   - 在 `src/harness_builder_agent/schemas/scan.py` 增加 `ScanSelfCheckActionType` 枚举和 `suggested_action_type` 字段。
   - 字段默认 `maintainer_review` 用于旧 metadata 兼容。
   - 在 `parse_scan_self_check_response()` 中对 raw payload 进行 fresh response 显式字段检查，缺字段时报错。

3. Prompt
   - 更新 `src/harness_builder_agent/prompts/llm_scan_self_check_v1.md`：JSON 示例包含 `suggested_action_type`；字段要求列出允许枚举；说明不能只返回自由文本建议。

4. 展示 / questionnaire
   - 新增轻量 helper，把 action type 翻译为中文动作提示和结构化补充格式。
   - `show_scan_self_check()` 输出 `动作=<type>` 和提示。
   - `build_questionnaire()` 的 self-check reason 追加 action type，保证 `.ai/human-input-needed.md` 可以审计。

5. 文档与记录
   - 更新 README、`docs/engineering/llm-contracts.md`、`docs/engineering/init-workflow.md`。
   - 更新 `docs/evolution-log.md`。

6. 验证
   - 运行新增 targeted 测试，确认 RED -> GREEN。
   - 运行 `tests/unit/test_llm_scan_self_checker.py`、相关 human confirmation / guided presentation tests。
   - 运行 `python -m compileall src tests`、`git diff --check`。
   - commit 前运行 `scripts/test-fast.sh`。
   - 本轮不 push。
