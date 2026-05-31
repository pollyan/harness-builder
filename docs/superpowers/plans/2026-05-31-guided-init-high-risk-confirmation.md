# Guided Init 高风险发现确认链路 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 guided `init` 把疑似密钥、凭证、安全、支付、权限或数据迁移风险作为待确认高影响风险贯穿 CLI、人工确认和 Guide/Sensor 资产。

**Architecture:** 新增一个轻量 `risk_signals` helper 统一分类风险线索；CLI、questionnaire、Guide writer 和 Sensor writer 只消费 helper 输出，不迁移 `risk_areas` schema，不自动应用 workflow policy。

**Tech Stack:** Python、Typer CLI、Pydantic schema、pytest unit / integration。

---

### Task 1: 高风险分类 helper

**Files:**
- Create: `src/harness_builder_agent/tools/risk_signals.py`
- Test: `tests/unit/test_risk_signals.py`

- [ ] **Step 1: Write failing helper tests**

覆盖英文 API key、中文权限 / 支付 / 数据迁移、普通配置风险三类输入。期望高风险返回 `is_high_impact=True` 和中文 confirmation reason，普通风险为 false。

- [ ] **Step 2: Run RED**

Run: `.venv/bin/python -m pytest tests/unit/test_risk_signals.py -q`

Expected: FAIL because module does not exist.

- [ ] **Step 3: Implement helper**

实现 `RiskSignal` dataclass、`classify_risk_area()`、`high_impact_risk_areas()` 和稳定 slug helper。

- [ ] **Step 4: Run GREEN**

Run: `.venv/bin/python -m pytest tests/unit/test_risk_signals.py -q`

Expected: PASS。

### Task 2: Guided CLI 高风险突出与建议补充

**Files:**
- Modify: `src/harness_builder_agent/tools/interactive_init.py`
- Modify: `tests/integration/test_init_on_fixture_projects.py`

- [ ] **Step 1: Write failing CLI assertions**

扩展 `test_guided_init_groups_scan_risks_uncertainties_and_validation_gaps`，加入 `docs/a.json` / `明文 API key` 风险，断言输出包含 `高风险，需人工确认`、`docs/a.json`、`Workflow 升级` 或 `standard`，并且出现在团队规则输入前。

- [ ] **Step 2: Run RED**

Run: `.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_groups_scan_risks_uncertainties_and_validation_gaps -q`

Expected: FAIL because CLI only prints normal risk.

- [ ] **Step 3: Implement CLI formatting**

在 `_risk_attention_lines()` 和 `_human_followup_lines()` 中使用 `classify_risk_area()` / `high_impact_risk_areas()`。

- [ ] **Step 4: Run GREEN**

Run: `.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_groups_scan_risks_uncertainties_and_validation_gaps -q`

Expected: PASS。

### Task 3: 人工确认资产包含高风险确认问题

**Files:**
- Modify: `src/harness_builder_agent/schemas/human_confirmation.py`
- Modify: `src/harness_builder_agent/tools/human_confirmation.py`
- Modify: `src/harness_builder_agent/tools/write_assets.py`
- Modify: `tests/unit/test_human_confirmation.py`
- Modify: `tests/unit/test_write_assets.py`

- [ ] **Step 1: Write failing questionnaire tests**

扩展 `test_build_questionnaire_includes_context_guides_sensors_and_warnings`，传入高风险 risk areas，断言 `risk_area_confirmation` 问题存在、schema 校验通过、问题包含路径和“高风险”。

- [ ] **Step 2: Run RED**

Run: `.venv/bin/python -m pytest tests/unit/test_human_confirmation.py -q`

Expected: FAIL because build_questionnaire has no risk_areas parameter / schema enum lacks risk_area_confirmation.

- [ ] **Step 3: Implement questionnaire flow**

给 `QuestionnaireQuestion.interaction_type` 增加 `risk_area_confirmation`；`build_questionnaire()` 接收 `risk_areas`，对 high impact risks 生成确认问题；`write_initial_assets()` 传入 inventory risk areas。

- [ ] **Step 4: Run GREEN**

Run: `.venv/bin/python -m pytest tests/unit/test_human_confirmation.py tests/unit/test_write_assets.py -q`

Expected: PASS。

### Task 4: Guide / Sensor 使用待确认高风险表达

**Files:**
- Modify: `src/harness_builder_agent/tools/asset_writers/guides.py`
- Modify: `src/harness_builder_agent/tools/asset_writers/sensors.py`
- Modify: `tests/unit/test_asset_writer_guides.py`
- Modify: `tests/unit/test_asset_writer_sensors.py`

- [ ] **Step 1: Write failing writer tests**

在已有 risk fixture 中加入 `docs/a.json` / `明文 API key`，断言 Guide 包含“待确认高风险”，Sensor 包含 `standard workflow` 或 `人工升级`。

- [ ] **Step 2: Run RED**

Run: `.venv/bin/python -m pytest tests/unit/test_asset_writer_guides.py tests/unit/test_asset_writer_sensors.py -q`

Expected: FAIL because docs currently treat risk as normal.

- [ ] **Step 3: Implement writer formatting**

Guide / Sensor risk lines 使用 `classify_risk_area()`，高风险项标记待确认，不声称事实已验证。

- [ ] **Step 4: Run GREEN**

Run: `.venv/bin/python -m pytest tests/unit/test_asset_writer_guides.py tests/unit/test_asset_writer_sensors.py -q`

Expected: PASS。

### Task 5: 文档记录与验证

**Files:**
- Modify: `docs/todos/guided-init-ai4se-real-repo-findings.md`
- Modify: `docs/evolution-log.md`

- [ ] **Step 1: Focused verification**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_risk_signals.py tests/unit/test_human_confirmation.py tests/unit/test_asset_writer_guides.py tests/unit/test_asset_writer_sensors.py tests/unit/test_write_assets.py tests/integration/test_init_on_fixture_projects.py::test_guided_init_groups_scan_risks_uncertainties_and_validation_gaps -q
```

Expected: PASS。

- [ ] **Step 2: Update docs**

记录高风险确认链路已完成，剩余多栈建模、成熟度英文叙事和 LLM-planned deep scan 继续 open。

- [ ] **Step 3: Commit pre-check**

Run: `scripts/test-fast.sh`

Expected: PASS。

- [ ] **Step 4: Commit locally**

Run:

```bash
git add src/harness_builder_agent/tools/risk_signals.py src/harness_builder_agent/tools/interactive_init.py src/harness_builder_agent/tools/human_confirmation.py src/harness_builder_agent/tools/write_assets.py src/harness_builder_agent/tools/asset_writers/guides.py src/harness_builder_agent/tools/asset_writers/sensors.py src/harness_builder_agent/schemas/human_confirmation.py tests/unit/test_risk_signals.py tests/unit/test_human_confirmation.py tests/unit/test_asset_writer_guides.py tests/unit/test_asset_writer_sensors.py tests/unit/test_write_assets.py tests/integration/test_init_on_fixture_projects.py docs/todos/guided-init-ai4se-real-repo-findings.md docs/evolution-log.md docs/superpowers/specs/2026-05-31-guided-init-high-risk-confirmation-design.md docs/superpowers/plans/2026-05-31-guided-init-high-risk-confirmation.md
git commit -m "增强init高风险确认链路"
```

Expected: 本地 commit 创建成功，不 push。

## Self-Review

- Spec coverage：CLI、human-input、Guide、Sensor、非目标和测试层级均有任务覆盖。
- Placeholder scan：无 TBD / TODO / implement later。
- Type consistency：`risk_area_confirmation` 只扩展 questionnaire interaction enum；`risk_areas` 本身保持自由 dict，不做 schema 迁移。
