# 团队规则结构化影响契约实施计划

## 目标

让团队规则 / context 输入在 `interaction-decisions.yaml` 中具备和 Workflow 补充一致的机器可读影响边界：影响范围、review-only 状态，以及不直接修改正式 policy 的契约。

## 步骤

- [x] **Step 1: 写失败测试**
  - 修改 `tests/unit/test_interaction_decisions.py`：
    - schema 正向断言新增 context impact 字段。
    - 默认 non-interactive 不写 pending review。
    - `accepted_interactive_decisions()` 有 inline/context path 时写入 impact 字段。
    - Markdown 摘要包含 context impact 字段。
  - 修改 `tests/integration/test_init_on_fixture_projects.py`：
    - guided init 团队规则测试断言 `interaction-decisions.yaml` 中 context impact/review/policy 字段。
    - 断言 `harness-config.yaml` routing 不包含团队规则自由文本。

- [x] **Step 2: 扩展 schema 与 writer**
  - 修改 `src/harness_builder_agent/schemas/interaction_decision.py`：
    - 新增 `ContextImpactScope`、`ContextReviewStatus`、`ContextPolicyEffect`。
    - 扩展 `ContextConfirmation` 默认字段。
  - 修改 `src/harness_builder_agent/tools/interaction_decisions.py`：
    - `accepted_interactive_decisions()` 在已确认 context 时填充结构化字段。
    - `interaction_decisions_markdown()` 输出 context impact/review/policy。
    - `default_non_interactive_decisions()` 保持默认值。

- [x] **Step 3: 同步稳定文档**
  - 修改 `docs/engineering/init-workflow.md`：
    - 在团队规则规则段落补充 `context_confirmation` 的机器契约。
  - 修改 `docs/evolution-log.md`：
    - 追加本轮记录，包含 Gap Analysis 摘要、用户故事、决策、验证和 Gate。

- [x] **Step 4: 验证**
  - 运行目标测试：
    - `.venv/bin/python -m pytest tests/unit/test_interaction_decisions.py -q`
    - `.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_records_scan_notes_and_team_rules_in_assets tests/integration/test_init_on_fixture_projects.py::test_guided_init_restates_user_supplements_before_write_and_persists_them -q`
  - 运行相关 guided init 片段：
    - `.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py -q`
  - commit 前运行：
    - `scripts/test-fast.sh`

- [x] **Step 5: 本地提交**
  - 检查 `git status --short`。
  - 提交中文 commit：`结构化记录团队规则影响`。
  - 本轮不 push；当前仍是持续演进工作包的一部分。

## 边界

- 不修改 LLM prompt。
- 不修改 benchmark。
- 不生成 team context asset candidate。
- 不修改正式 `harness-config.yaml` routing policy。
- 不执行 Runtime、不创建 `.ai/task-runs`。
