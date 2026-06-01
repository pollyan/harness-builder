# Guided 候选审查成熟度影响提示实施计划

## 目标

在首次 guided `init` 的 LLM candidate 逐项审查中，为每个候选展示成熟度影响和 review-only 边界，让 Maintainer 审查候选时理解它补齐的是 Guide 上下文、风险控制、Sensor 验证还是审计边界。

## 步骤

1. TDD：更新 `tests/unit/test_guided_candidate_review.py`
   - 断言 guide candidate 输出 `成熟度影响`、`Guides 上下文`。
   - 断言 risk guide 输出 `Risk Control 风险控制`。
   - 断言 sensor candidate 输出 `Sensors 验证`、`Verification 验证成熟度`。
   - 断言 no-enhancement candidate 输出审计边界而不是成熟度提升。
   - 断言 review-only 边界文案存在。
2. TDD：更新 guided init integration
   - 在 `test_guided_init_reviews_candidates_one_by_one` 中断言 transcript 包含成熟度影响和 review-only 边界。
3. 实现 `guided_candidate_review.py`
   - 新增 `candidate_maturity_impact_lines(item)` helper。
   - 在 candidate 渲染中输出 helper lines。
   - 不修改 decision prompt、notes 或 schema。
4. 验证
   - `.venv/bin/python -m pytest tests/unit/test_guided_candidate_review.py -q`
   - `.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_reviews_candidates_one_by_one -q`
   - `.venv/bin/python -m compileall src/harness_builder_agent/tools/guided_candidate_review.py`
   - `git diff --check`
   - `scripts/test-fast.sh`
5. 更新 `docs/evolution-log.md`
   - 记录 Gap Analysis 摘要、用户故事、取舍、验证结果和 Self-Harness Gate。
6. 本地 commit
   - commit message：`增强 guided 候选成熟度提示`
   - 本轮不 push；push 仍以 full regression 通过和完整工作包为边界。

## 非目标

- 不修改 `WeaponLibraryCandidate` schema。
- 不修改 LLM candidate 生成逻辑。
- 不应用正式 Guide / Sensor。
- 不修改 benchmark、writer 或 Runtime 分工。
