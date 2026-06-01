# 已有 Harness 初始候选成熟度信号实施计划

## 目标

把 `.ai/experience/weapon-library-candidates.yaml` 中的初始 LLM Guide / Sensor 候选成熟度影响接入已有 Harness 维护入口，让 Maintainer 再次运行 guided `init` 时能看到 pending 初始候选、成熟度维度、top candidate 和 review-only 边界。

## 步骤

1. TDD：补 unit 测试
   - `tests/unit/test_existing_harness_signals.py`：新增 candidate report fixture，断言 Experience / review signals 输出总数、pending 数、maturity dimensions 和 top candidate。
   - `tests/unit/test_existing_harness_status_overview.py`：断言 overview 包含初始 LLM candidate 待确认数量。
   - `tests/unit/test_maintenance_triage.py`：断言没有更高优先级失败时，pending 初始 candidate 进入 triage，且 menu hint 不伪造编号。
2. TDD：补 integration transcript 测试
   - 更新 `test_guided_init_existing_harness_can_exit_without_overwriting_assets` 或新增窄测试，构造 non-interactive 初始 Harness 后再次 guided exit，断言输出包含 weapon candidate signals、overview 和 guidance。
3. 实现只读 helper
   - 新增或内聚在 `existing_harness_signals.py` 中读取 `WeaponLibraryCandidateReport`。
   - 输出稳定 signal lines，并兼容 report 缺失。
4. 接入 overview 与 triage
   - `existing_harness_status.py` 把 pending 初始 candidate count 纳入 Experience / review 摘要。
   - `maintenance_triage.py` 在 asset candidates / human input 之后、pending improvements 之前加入 `weapon_library_candidates_pending` action，`next_action="manual-review"`。
   - guidance 说明查看 `.ai/review/llm-enhancement-candidates.md` 与 `.ai/experience/weapon-library-candidates.yaml`，保持 review-only。
5. 更新文档记录
   - `docs/evolution-log.md` 记录本轮 Gap Analysis、决策、验证和 Gate。
   - 若 CLI 维护入口契约稳定变化，同步 `README.md` 与 `docs/engineering/init-workflow.md` 的已有 Harness signals 描述。
6. 验证
   - `.venv/bin/python -m pytest tests/unit/test_existing_harness_signals.py tests/unit/test_existing_harness_status_overview.py tests/unit/test_maintenance_triage.py -q`
   - `.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_can_exit_without_overwriting_assets -q`
   - `.venv/bin/python -m compileall src/harness_builder_agent/tools/existing_harness_signals.py src/harness_builder_agent/tools/existing_harness_status.py src/harness_builder_agent/tools/maintenance_triage.py`
   - `git diff --check`
   - `scripts/test-fast.sh`
7. 本地 commit
   - commit message：`展示初始候选成熟度维护信号`
   - 本轮不 push；push 仍等待完整工作包和 `scripts/test-full.sh`。

## 非目标

- 不新增初始 weapon-library candidate 的治理命令。
- 不复用 `.ai/review/asset-candidates.yaml` 的 `review-candidate` 语义。
- 不修改 `WeaponLibraryCandidate` schema。
- 不修改正式 Guides、Sensors、Workflow routing 或 `harness-config.yaml`。
- 不执行 Runtime，不创建 `.ai/task-runs`。
