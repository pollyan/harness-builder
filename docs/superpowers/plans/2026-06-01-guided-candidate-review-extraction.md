# Guided 候选审查边界抽取实施计划

## 目标

把首次 guided `init` 中 Guide / Sensor 基线呈现、LLM 候选逐项审查和 `CandidateDecision` 构造从 `interactive_init.py` 抽到独立模块，保持用户可见 transcript 与生成产物不变。

## 步骤

1. TDD：新增 `tests/unit/test_guided_candidate_review.py`
   - 先导入不存在的 `guided_candidate_review`，确认 RED。
   - 覆盖 no-candidate 分支。
   - 覆盖候选选择 `a`、`r`、`e`、默认回车四种决策。
   - 覆盖 baseline Guide / Sensor / command 呈现。
2. 实现 `src/harness_builder_agent/tools/guided_candidate_review.py`
   - 新增 `review_candidates(report, weapon_selection, commands, prompt=typer.prompt)`。
   - 复用 `CandidateDecision`、`WeaponLibrarySelection`、`CommandCatalog`。
   - 不依赖 `interactive_init.py`。
3. 更新 `interactive_init.py`
   - 导入 `review_candidates as _review_candidates`。
   - 删除内联 `_review_candidates()` 实现。
   - 保持其余状态机调用不变。
4. 验证
   - `.venv/bin/python -m pytest tests/unit/test_guided_candidate_review.py -q`
   - `.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_reviews_candidates_one_by_one -q`
   - `.venv/bin/python -m compileall src/harness_builder_agent/tools/interactive_init.py src/harness_builder_agent/tools/guided_candidate_review.py`
   - `git diff --check`
   - `scripts/test-fast.sh`
5. 更新 `docs/evolution-log.md`
   - 记录 Gap Analysis 摘要、工程信任故事、取舍、验证结果和 Self-Harness Gate。
6. 本地 commit
   - commit message：`抽取 guided 候选审查模块`
   - 本轮不 push；push 仍以 full regression 通过和完整工作包为边界。

## 非目标

- 不改变候选审查选项或用户文案。
- 不修改 LLM candidate generation。
- 不修改 `InteractionDecisions` schema 或 candidate report schema。
- 不应用正式 Guide / Sensor / workflow policy。
- 不执行 Runtime，不创建 `.ai/task-runs`。
