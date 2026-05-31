# Workflow 补充结构化影响契约实施计划

## 范围

本轮只把 Workflow 补充的影响范围和 review-only routing 边界写入 `InteractionDecisions` 机器契约。修改范围：

- `src/harness_builder_agent/schemas/interaction_decision.py`
- `src/harness_builder_agent/tools/interaction_decisions.py`
- `src/harness_builder_agent/tools/interactive_init.py`
- `tests/unit/test_interaction_decisions.py`
- `tests/integration/test_init_on_fixture_projects.py`
- `docs/engineering/init-workflow.md`
- `docs/evolution-log.md`

不修改 `harness-config.yaml` routing policy、不生成 workflow policy candidate、不修改 LLM prompt / benchmark / Runtime 契约。

## TDD 步骤

1. 更新 unit 测试：
   - `test_interaction_decisions_schema_accepts_interactive_confirmation` 断言 `WorkflowConfirmation` 可保存 `impact_scopes`、`review_status`、`routing_policy_effect`。
   - `test_default_non_interactive_decisions_record_missing_human_confirmation` 断言默认 workflow impact 为 not required / not applicable。
   - `test_interaction_decisions_markdown_summarizes_decisions` 断言 Markdown 输出 workflow impact / review status / routing effect。
2. 更新 guided init integration 测试：
   - 在有 workflow note 的路径中断言 `interaction-decisions.yaml` 含结构化字段。
   - 断言 `harness-config.yaml` routing rules 未被 workflow note 文本污染。
3. 先运行目标测试，确认当前代码失败。
4. 实现：
   - 在 `WorkflowConfirmation` schema 中新增 Literal 类型字段和默认值。
   - 新增 helper 构造 review-only workflow confirmation impact。
   - `_show_workflows()` 有 note 时返回结构化 impact；无 note 时保持默认 not required / not applicable。
   - `interaction_decisions_markdown()` 输出影响字段。
5. 更新 `docs/engineering/init-workflow.md`，固化 Workflow 补充必须在 interaction decisions 中保留机器可读 impact / review-only 边界。
6. 更新 `docs/evolution-log.md`，记录本轮 gap、取舍、验证和 Gate。

## 验证命令

```bash
.venv/bin/python -m pytest \
  tests/unit/test_interaction_decisions.py::test_interaction_decisions_schema_accepts_interactive_confirmation \
  tests/unit/test_interaction_decisions.py::test_default_non_interactive_decisions_record_missing_human_confirmation \
  tests/unit/test_interaction_decisions.py::test_interaction_decisions_markdown_summarizes_decisions \
  tests/integration/test_init_on_fixture_projects.py::test_guided_init_restates_user_supplements_before_write_and_persists_them -q
.venv/bin/python -m pytest \
  tests/integration/test_init_on_fixture_projects.py::test_guided_init_restates_user_supplements_before_write_and_persists_them \
  tests/integration/test_init_on_fixture_projects.py::test_guided_init_final_summary_can_go_back_to_workflow_note \
  tests/unit/test_interaction_decisions.py -q
scripts/test-fast.sh
```

## 提交策略

- commit 前必须完成 `scripts/test-fast.sh`。
- 本轮是独立 schema / guided init 信任切片，可以本地 commit。
- 不 push；当前不是完整远端同步批次，push 前 full regression 前置条件未重新满足。
