# Guided 初始 LLM 候选治理实施计划

## 目标

在已有 Harness guided `init` 维护入口中新增 `review-initial-candidate` 动作，让 Maintainer 可以对 `.ai/experience/weapon-library-candidates.yaml` 中的初始 LLM Guide / Sensor 候选记录 accepted / rejected / kept 决策，并留下独立治理日志。该动作不修改正式 Harness 资产。

## 步骤

1. TDD：schema 和 tool unit
   - 新增 `tests/unit/test_schema_contracts.py` 覆盖 `WeaponCandidateGovernanceLog` schema。
   - 新增 `tests/unit/test_weapon_candidate_governance.py`：
     - accepted 更新 candidate report 为 confirmed / no human confirmation。
     - rejected 更新为 rejected / no human confirmation。
     - kept 保持 candidate / human confirmation required。
     - 写 governance YAML / Markdown。
     - 重写 LLM enhancement Markdown，使 status 同步。
     - 缺 rationale、未知 id、非法 decision、缺 report 显式失败。
2. TDD：existing Harness menu / triage / runner
   - 更新 `tests/unit/test_existing_harness_actions.py`，断言 `review-initial-candidate` 有稳定编号和别名。
   - 更新 `tests/unit/test_maintenance_triage.py`，断言 `weapon_library_candidates_pending` shortcut 映射到新编号。
   - 更新 `tests/unit/test_existing_harness_action_runner.py` 或 integration，覆盖 runner action 不扫描、不修改正式资产。
3. TDD：guided integration transcript
   - 在 `tests/integration/test_init_on_fixture_projects.py` 新增 existing Harness guided action 测试：
     - 初始化 fixture。
     - 记录正式资产 snapshot。
     - 选择 `review-initial-candidate`，输入候选 id、accepted、rationale、reviewer。
     - 断言 governance schema、candidate report 状态、trace artifacts、正式资产不变、无 `.ai/task-runs`。
4. 实现 schema / tool
   - 新增 `src/harness_builder_agent/schemas/weapon_candidate_governance.py`。
   - 新增 `src/harness_builder_agent/tools/weapon_candidate_governance.py`。
   - 复用 `llm_enhancement_candidates` 的 Markdown renderer 重写 review files。
5. 接入 guided action
   - `existing_harness_actions.py` 新增 `10. review-initial-candidate`。
   - `maintenance_triage.py` 把 `weapon_library_candidates_pending` 的 `next_action` 改为 `review-initial-candidate`。
   - `existing_harness_action_runner.py` 新增 prompt、调用 tool、trace artifact 和 summary。
   - `existing_harness_action_summaries.py` 增加治理摘要 helper。
6. 文档与演进记录
   - 更新 README 和 `docs/engineering/init-workflow.md` 的 existing Harness 动作列表与边界说明。
   - 更新 `docs/evolution-log.md`。
7. 验证
   - `.venv/bin/python -m pytest tests/unit/test_schema_contracts.py::test_weapon_candidate_governance_log_schema tests/unit/test_weapon_candidate_governance.py tests/unit/test_existing_harness_actions.py tests/unit/test_maintenance_triage.py tests/unit/test_existing_harness_status_overview.py::test_existing_harness_status_overview_mentions_initial_llm_candidates -q`
   - `.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_can_review_initial_candidate_without_overwriting_formal_assets -q`
   - `.venv/bin/python -m compileall src/harness_builder_agent/schemas/weapon_candidate_governance.py src/harness_builder_agent/tools/weapon_candidate_governance.py src/harness_builder_agent/tools/existing_harness_action_runner.py src/harness_builder_agent/tools/existing_harness_actions.py src/harness_builder_agent/tools/maintenance_triage.py`
   - `git diff --check`
   - `scripts/test-fast.sh`
8. 本地 commit
   - commit message：`支持初始候选 guided 治理`
   - 本轮不 push；push 仍等待完整工作包和 `scripts/test-full.sh`。

## 非目标

- 不新增 standalone `review-initial-candidate` CLI 命令。
- 不支持 `applied`，不写正式 Guide / Sensor。
- 不复用 asset candidate governance。
- 不运行 LLM / benchmark / self-improve。
- 不创建 `.ai/task-runs`。
