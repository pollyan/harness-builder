# Workflow Note 资产候选闭环实施计划

## 修改范围

- `src/harness_builder_agent/prompts/llm_maturity_review_v2.md`
- `src/harness_builder_agent/prompts/llm_asset_candidate_v2.md`
- `tests/unit/test_llm_maturity_reviewer.py`
- `tests/unit/test_llm_asset_candidate_generator.py`
- `tests/integration/test_init_on_fixture_projects.py`
- `README.md`
- `docs/engineering/init-workflow.md`
- `docs/evolution-log.md`

## TDD 步骤

1. Prompt unit 红测：
   - maturity review prompt 必须包含 `interaction-workflow-note-review`、`.ai/interaction-decisions.yaml`、`.ai/human-input-needed.md`、`workflow_routing_rules`、review-only 和不得声称已应用。
   - asset candidate prompt 必须包含 `interaction-workflow-note-review`、`workflow_policy`、`.ai/harness-config.yaml`、`workflow_policy_patch`、`pending_harness_maintainer_review` 和 review-only Workflow note evidence。
2. Integration 红测：
   - guided `init` 输入 Workflow note。
   - 再次进入 existing Harness 选择 `self-improve`。
   - mock maturity review 支持 `interaction-workflow-note-review`。
   - mock asset generator 返回 workflow_policy candidate，断言正式资产不变、不创建 `.ai/task-runs`、candidate source id / patch / evidence 正确。
3. 实现：
   - 更新 maturity review prompt。
   - 更新 asset candidate prompt。
   - 必要时补充 README / init workflow 文档，不改正式资产写入逻辑。
4. 验证：
   - 目标 unit。
   - 目标 integration。
   - 相关 guided init integration。
   - `git diff --check`。
   - `scripts/test-fast.sh`。
5. 提交：
   - 中文 commit message。
   - 不 push；除非后续进入完整工作包同步并通过 `scripts/test-full.sh`。

## 验收命令

```bash
.venv/bin/python -m pytest tests/unit/test_llm_maturity_reviewer.py::<目标测试名> tests/unit/test_llm_asset_candidate_generator.py::<目标测试名> -q
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::<目标测试名> -q
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py -q
git diff --check
scripts/test-fast.sh
```
