# Standard Workflow Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a fixed-template Standard Workflow Skill and harness config entry for complex/high-risk AI Coding tasks.

**Architecture:** Extend the deterministic Workflow Toolkit templates with `standard/SKILL.md`, make the skill writer copy it, add a `standard` workflow to `HarnessConfig.default()`, and update benchmark/content tests to require the generated skill and config reference. No runtime execution or dynamic LLM workflow generation is introduced.

**Tech Stack:** Python, Pydantic v2, Markdown templates, pytest.

---

## Files

- Create: `src/harness_builder_agent/templates/skills/standard/SKILL.md`
- Modify: `src/harness_builder_agent/tools/asset_writers/skills.py`
- Modify: `src/harness_builder_agent/schemas/harness_config.py`
- Modify: `src/harness_builder_agent/schemas/harness_map.py`
- Modify: `src/harness_builder_agent/tools/benchmark.py`
- Modify: `tests/unit/test_asset_writer_skills.py`
- Modify: `tests/unit/test_schema_contracts.py`
- Modify: `tests/integration/test_init_on_fixture_projects.py`
- Modify: `tests/integration/test_benchmark_command.py`
- Modify: `tests/e2e/test_fixture_end_to_end.py`
- Modify: `tests/acceptance/test_real_repositories_e2e.py`
- Modify: `docs/engineering/init-workflow.md`
- Modify: `docs/engineering/architecture.md`
- Modify: `docs/superpowers/plans/2026-05-31-standard-workflow-skill.md`

## Task 1: Skill Writer Template

- [x] **Step 1: Write failing skill writer assertions**

In `tests/unit/test_asset_writer_skills.py`, update `test_write_skill_assets_copies_workflow_templates_and_records_artifacts`:

```python
standard = ai / "skills" / "standard" / "SKILL.md"
assert standard.exists()
standard_text = standard.read_text(encoding="utf-8")
assert "标准开发工作流" in standard_text
assert "Requirement Alignment" in standard_text
assert "Solution Design" in standard_text
assert "Implementation Plan" in standard_text
assert "宿主 AI Coding Runtime" in standard_text
assert "runtime artifact contract" in standard_text
assert ".ai/task-runs/<task-id>/harness-map.yaml" in standard_text
assert "Harness Builder 不负责生成这些任务运行产物" in standard_text
assert {"path": ".ai/skills/standard/SKILL.md", "kind": "skill"} in artifacts["artifacts"]
```

- [x] **Step 2: Run skill writer test and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_asset_writer_skills.py -q
```

Expected: fail because the Standard Skill template is not written.

- [x] **Step 3: Add Standard Skill template and writer loop**

Create `src/harness_builder_agent/templates/skills/standard/SKILL.md`:

```markdown
---
name: standard
description: 用于复杂功能、高风险变更、跨模块改造、安全/数据/架构影响任务的项目级 AI Coding 工作流。
---

# 标准开发工作流

## 使用条件

当任务影响范围不清楚、涉及高风险模块、跨模块设计、安全/权限/金额/数据迁移/核心业务状态，或 lightweight workflow 覆盖不足时使用本 Skill。

## 必读资产

- `.ai/guides/project-context.md`
- `.ai/guides/architecture.md`
- `.ai/guides/coding-rules.md`
- `.ai/sensors/verification.md`
- `.ai/sensors/test-strategy.md`
- `.ai/experience/experience-summary.md`

## 执行步骤

1. Requirement Alignment：澄清需求、边界、不做范围和验收标准。
2. Harness Mapping：由宿主 AI Coding Runtime 创建或更新 `.ai/task-runs/<task-id>/harness-map.yaml`，映射影响模块、Guides、Sensors、风险区域和 restricted paths。
3. Solution Design：形成方案、取舍、风险和需要人工确认的问题。
4. Implementation Plan：拆成可验证小步骤，并明确每步对应的 Sensors。
5. Test-first Build & Verify Loop：优先补测试或验证证据，再实施变更，运行 hard gate Sensors。
6. Repair Loop / Human Escalation：Sensor 失败时修复并重跑；多次失败或高风险决策升级人工。
7. Review / Decision Log / Handoff：输出验证结果、残余风险、经验候选和交付摘要。

## Runtime Artifact Contract

当宿主 AI Coding Runtime 执行本 Workflow Skill 时，必须维护任务级可观测产物。Harness Builder 不负责生成这些任务运行产物；它只生成本 Skill 和静态 Harness 资产。This section is the runtime artifact contract for host runtimes.

建议产物路径：

- `.ai/task-runs/<task-id>/harness-map.yaml`
- `.ai/task-runs/<task-id>/sensor-report.yaml`
- `.ai/task-runs/<task-id>/runtime-summary.yaml`
- `.ai/task-runs/<task-id>/workflow-events.jsonl`
- `.ai/task-runs/<task-id>/used-guides.yaml`
- `.ai/task-runs/<task-id>/decision-log.md`
- `.ai/task-runs/<task-id>/handoff-summary.md`
- `.ai/task-runs/<task-id>/experience-candidates.md`

## 交付要求

- 方案和实现必须引用项目事实、Guides、Sensors 或 Experience Summary。
- 不把单次经验直接写入正式 Guides / Sensors / Workflow。
- 高风险、低置信度或违反 restricted paths 的情况必须进入人工确认。
- 所有经验候选先进入待确认区，不自动升级为正式规则。
```

In `src/harness_builder_agent/tools/asset_writers/skills.py`, change:

```python
for name in ("lightweight", "bugfix"):
```

to:

```python
for name in ("lightweight", "bugfix", "standard"):
```

- [x] **Step 4: Run skill writer test and confirm pass**

Run the same pytest command. Expected: pass.

## Task 2: Harness Config and Harness Map Contracts

- [x] **Step 1: Write failing schema assertions**

In `tests/unit/test_schema_contracts.py`, update `test_harness_config_has_lightweight_and_bugfix_workflows`:

```python
assert {"lightweight", "bugfix", "standard"}.issubset(workflow_names)
assert config.workflows["standard"].skill_path == ".ai/skills/standard/SKILL.md"
assert "solution_design" in config.workflows["standard"].stages
assert "test_first_build_verify" in config.workflows["standard"].stages
```

Add a Harness Map assertion:

```python
def test_harness_map_accepts_standard_workflow_contract():
    harness_map = HarnessMap.model_validate(
        {
            "task_id": "demo-task-002",
            "task_type": "standard",
            "selected_workflow": "standard",
            "risk_level": "high",
            "guide_policy": {"required": [".ai/guides/architecture.md"]},
            "workflow_skill": {"path": ".ai/skills/standard/SKILL.md"},
            "sensor_policy": {"hard_gates": ["unit_test"]},
        }
    )

    assert harness_map.selected_workflow == "standard"
```

- [x] **Step 2: Run schema tests and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py::test_harness_config_has_lightweight_and_bugfix_workflows tests/unit/test_schema_contracts.py::test_harness_map_accepts_standard_workflow_contract -q
```

Expected: fail because config and HarnessMap do not include `standard`.

- [x] **Step 3: Extend schema defaults and runtime contract enum**

In `src/harness_builder_agent/schemas/harness_config.py`, add:

```python
"standard": WorkflowDefinition(
    skill_path=".ai/skills/standard/SKILL.md",
    stages=[
        "requirement_alignment",
        "harness_mapping",
        "solution_design",
        "implementation_plan",
        "test_first_build_verify",
        "review_handoff",
    ],
),
```

Keep `RuntimeConfig.default_workflow = "lightweight"`.

In `src/harness_builder_agent/schemas/harness_map.py`, change workflow literals to include `standard`:

```python
task_type: Literal["bugfix", "lightweight", "standard"]
selected_workflow: Literal["bugfix", "lightweight", "standard"]
```

- [x] **Step 4: Run schema tests and confirm pass**

Run the same pytest command. Expected: pass.

## Task 3: Init, Benchmark, and Fixture Coverage

- [x] **Step 1: Write failing init and benchmark assertions**

In `tests/integration/test_init_on_fixture_projects.py`:

```python
assert (ai / "skills" / "standard" / "SKILL.md").exists()
assert config.workflows["standard"].skill_path == ".ai/skills/standard/SKILL.md"
standard_skill = (ai / "skills" / "standard" / "SKILL.md").read_text(encoding="utf-8")
assert "标准开发工作流" in standard_skill
assert "Requirement Alignment" in standard_skill
assert ".ai/skills/standard/SKILL.md" in artifact_paths
```

In `tests/e2e/test_fixture_end_to_end.py` and `tests/acceptance/test_real_repositories_e2e.py`, add:

```python
assert (repo / ".ai" / "skills" / "standard" / "SKILL.md").exists()
```

In `tests/integration/test_benchmark_command.py`, update the missing skill test to unlink standard as well:

```python
(ai / "skills" / "standard" / "SKILL.md").unlink()
```

and assert `workflow_skill["passed"] is False`.

- [x] **Step 2: Run focused integration tests and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py tests/integration/test_benchmark_command.py::test_benchmark_content_checks_fail_when_workflow_skill_file_is_missing -q
```

Expected: fail until init and benchmark require/write Standard Skill.

- [x] **Step 3: Update benchmark required files and content check**

In `src/harness_builder_agent/tools/benchmark.py`:

1. Add `"skills/standard/SKILL.md"` to `REQUIRED_FILES`.
2. Update `_workflow_skills_check`:

```python
standard = ai / "skills" / "standard" / "SKILL.md"
passed = (
    lightweight.exists()
    and bugfix.exists()
    and standard.exists()
    and "轻量级开发工作流" in lightweight.read_text(encoding="utf-8")
    and "缺陷修复工作流" in bugfix.read_text(encoding="utf-8")
    and "标准开发工作流" in standard.read_text(encoding="utf-8")
    and "Requirement Alignment" in standard.read_text(encoding="utf-8")
)
```

- [x] **Step 4: Run focused integration tests and confirm pass**

Run the same pytest command. Expected: pass.

## Task 4: Engineering Docs, Verification, Commit

- [x] **Step 1: Update engineering docs**

In `docs/engineering/init-workflow.md`, add `.ai/skills/standard/SKILL.md` under required workflow skills and mention Standard is generated as a fixed template for high-risk/complex work.

In `docs/engineering/architecture.md`, update the Workflow Skill line to say fixed templates now include lightweight, bugfix, and standard, and still are not dynamically generated by LLM.

- [x] **Step 2: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_asset_writer_skills.py tests/unit/test_schema_contracts.py tests/integration/test_init_on_fixture_projects.py tests/integration/test_benchmark_command.py tests/e2e/test_fixture_end_to_end.py -q
```

Expected: pass.

- [x] **Step 3: Run fast regression**

Run:

```bash
scripts/test-fast.sh
```

Expected: pass.

- [x] **Step 4: Self-Harness Improvement Gate**

Record the gate result in this plan. Expected:

- Schema, writer, init, benchmark, e2e, and docs cover the new Standard workflow.
- Benchmark now catches missing Standard Skill.
- Runtime boundary remains intact: no `.ai/task-runs` generation.
- Next candidate gap: workflow selection intelligence or prototype-first workflow candidate.

Result:

- Focused regression: `42 passed`.
- Fast regression: `123 passed`.
- Standard Skill is covered by writer, config, HarnessMap, init, benchmark, e2e, acceptance assertions, and engineering docs.
- Benchmark now fails when only `.ai/skills/standard/SKILL.md` is missing.
- Runtime boundary remains covered by e2e/benchmark assertions that `.ai/task-runs` is not generated.
- Next candidate gap: workflow selection intelligence that can recommend `standard` without changing the default workflow.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/harness_builder_agent/templates/skills/standard/SKILL.md src/harness_builder_agent/tools/asset_writers/skills.py src/harness_builder_agent/schemas/harness_config.py src/harness_builder_agent/schemas/harness_map.py src/harness_builder_agent/tools/benchmark.py tests/unit/test_asset_writer_skills.py tests/unit/test_schema_contracts.py tests/integration/test_init_on_fixture_projects.py tests/integration/test_benchmark_command.py tests/e2e/test_fixture_end_to_end.py tests/acceptance/test_real_repositories_e2e.py docs/engineering/init-workflow.md docs/engineering/architecture.md docs/superpowers/specs/2026-05-31-standard-workflow-skill-design.md docs/superpowers/plans/2026-05-31-standard-workflow-skill.md
git commit -m "feat: add standard workflow skill"
```

Expected: commit succeeds after pre-commit fast regression.
