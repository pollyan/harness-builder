# 扫描补充结构化决策契约实施计划

## 目标

让 guided `init` 的结构化扫描补充不仅进入 inventory / command catalog，也进入 `interaction-decisions.yaml` 的机器契约，并明确这些补充是用户提供、待维护者审查的扫描修正，不是已验证扫描事实。

## 步骤

- [x] **Step 1: 写失败测试**
  - 修改 `tests/unit/test_interaction_decisions.py`：
    - `ScanConfirmation` schema 接受 `modules`、`commands`、`risk_areas`、`impact_scopes`、`review_status`、`fact_effect`。
    - `accepted_interactive_decisions()` 有 structured scan supplements 时写入字段和 impact contract。
    - 无 scan supplement 时 impact contract 为空 / not required。
    - `interaction_decisions_markdown()` 展示 scan impact 和结构化补充。
  - 修改 `tests/integration/test_init_on_fixture_projects.py`：
    - 对现有 structured scan supplement 测试增加 `interaction-decisions.yaml` 结构化字段断言。

- [x] **Step 2: 扩展 schema**
  - 修改 `src/harness_builder_agent/schemas/interaction_decision.py`：
    - 引入 `CommandDefinition`。
    - 新增 `ScanImpactScope`、`ScanReviewStatus`、`ScanFactEffect`。
    - 给 `ScanConfirmation` 增加 modules / commands / risk_areas / impact_scopes / review_status / fact_effect。

- [x] **Step 3: 写入决策契约**
  - 修改 `src/harness_builder_agent/tools/interaction_decisions.py`：
    - `accepted_interactive_decisions()` 新增 `scan_modules`、`scan_commands`、`scan_risk_areas` 参数。
    - 根据补充类型计算 impact scopes、review status 和 fact effect。
    - `interaction_decisions_markdown()` 展示新增字段。
  - 修改 `src/harness_builder_agent/tools/interactive_init.py`：
    - 传入 `scan_overrides.modules`、`scan_overrides.commands`、`scan_overrides.risk_areas`。

- [x] **Step 4: 同步长期文档和演进记录**
  - 修改 `docs/engineering/init-workflow.md`：
    - 在用户补充复述与影响说明处固化 scan_confirmation 的结构化字段和 review-required 边界。
  - 修改 `docs/evolution-log.md`：
    - 记录本轮 Gap Analysis、用户故事、取舍、验证和 Gate。

- [x] **Step 5: 验证**
  - 运行目标 unit：
    - `.venv/bin/python -m pytest tests/unit/test_interaction_decisions.py -q`
  - 运行目标 integration：
    - `.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_accepts_structured_scan_corrections -q`
  - 运行完整 guided init integration：
    - `.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py -q`
  - 运行 `git diff --check`。
  - commit 前运行 `scripts/test-fast.sh`。

- [x] **Step 6: 本地提交**
  - 暂存本轮文件。
  - 提交中文 commit：`结构化记录扫描补充决策`
  - 本轮不 push。

## 边界

- 不修改 LLM prompt、scan self-check、benchmark 或 Sensor gate 规则。
- 不自动关闭 questionnaire 的 follow-up questions。
- 不从自然语言 notes 推断 module / command / risk。
- 不修改正式 workflow routing policy。
