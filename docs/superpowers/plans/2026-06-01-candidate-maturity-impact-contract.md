# LLM 候选成熟度影响机器契约实施计划

## 目标

把上一轮只存在于 guided candidate review CLI transcript 中的 maturity impact 提升为 `.ai/experience/weapon-library-candidates.yaml` 的结构化字段，并让 Markdown review files 和 CLI 复用同一 helper。

## 步骤

1. TDD：更新 schema tests
   - 新增/更新 `tests/unit/test_schema_contracts.py`，证明新 maturity fields 可解析。
   - 证明旧 payload 缺字段时有默认值，保持兼容。
2. TDD：更新 candidate generation tests
   - `tests/unit/test_llm_enhancement_candidates.py` 断言 architecture / risk / sensor candidates 的 `maturity_dimensions`、summary、contribution、boundary。
   - 覆盖 no-enhancement fallback。
3. TDD：更新 writer / integration tests
   - `tests/unit/test_asset_writer_candidates.py` 断言 YAML 和 Markdown review files 输出 maturity impact。
   - `tests/integration/test_init_on_fixture_projects.py` 断言真实 guided init 生成的 candidate report 包含 maturity fields。
4. 实现结构化 helper
   - 新增 `src/harness_builder_agent/tools/candidate_maturity_impact.py`。
   - 提供 `candidate_maturity_impact_fields(candidate)` 和 `candidate_maturity_impact_lines(candidate)`。
5. 更新 schema / generation / presentation
   - `schemas/weapon_library_candidate.py` 增加字段。
   - `llm_enhancement_candidates.py` 在 append 前补齐 maturity fields，并在 Markdown 中展示。
   - `guided_candidate_review.py` 改用共享 helper。
6. 验证
   - `.venv/bin/python -m pytest tests/unit/test_schema_contracts.py::test_weapon_library_candidate_report_records_maturity_impact_contract tests/unit/test_llm_enhancement_candidates.py tests/unit/test_asset_writer_candidates.py tests/unit/test_guided_candidate_review.py -q`
   - `.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_reviews_candidates_one_by_one -q`
   - `.venv/bin/python -m compileall src/harness_builder_agent/tools/candidate_maturity_impact.py src/harness_builder_agent/tools/llm_enhancement_candidates.py src/harness_builder_agent/tools/guided_candidate_review.py src/harness_builder_agent/schemas/weapon_library_candidate.py`
   - `git diff --check`
   - `scripts/test-fast.sh`
7. 更新 `docs/evolution-log.md`
   - 记录 Gap Analysis、用户故事/工程信任故事、取舍、验证结果和 Self-Harness Gate。
8. 本地 commit
   - commit message：`记录候选成熟度影响契约`
   - 本轮不 push；push 仍以 full regression 通过和完整工作包为边界。

## 非目标

- 不修改 LLM scan prompt / response schema。
- 不修改正式 Guide / Sensor / routing policy。
- 不让 benchmark 因旧候选缺 maturity impact 失败。
- 不执行 Runtime，不创建 `.ai/task-runs`。
