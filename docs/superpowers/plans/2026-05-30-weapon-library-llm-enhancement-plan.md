# Weapon Library LLM Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate reviewable LLM enhancement candidates on top of deterministic weapon library baseline.

**Architecture:** Add a small candidate builder that derives guide/sensor candidates from `ProjectInventory.stack_extensions["llm_scan_proposal"]` and `CommandCatalog`, then write review markdown and machine-readable YAML during initial asset generation.

**Tech Stack:** Python, YAML, pytest.

---

## File Structure

- Create: `src/harness_builder_agent/tools/llm_enhancement_candidates.py`
  - Builds candidate report and markdown files.
- Create: `tests/unit/test_llm_enhancement_candidates.py`
  - Unit tests for candidate generation.
- Modify: `src/harness_builder_agent/tools/write_assets.py`
  - Writes review and experience candidate assets.
- Modify: `tests/integration/test_init_on_fixture_projects.py`
  - Asserts init writes candidate assets.
- Modify: `src/harness_builder_agent/tools/benchmark.py`
  - Adds candidate existence/schema/content checks.
- Modify: `tests/integration/test_benchmark_command.py`
  - Asserts benchmark checks exist.

## Task 1: Candidate Builder

**Files:**
- Create: `tests/unit/test_llm_enhancement_candidates.py`
- Create: `src/harness_builder_agent/tools/llm_enhancement_candidates.py`

- [ ] **Step 1: Write failing tests**

Test:

```python
from harness_builder_agent.schemas.command_catalog import CommandCatalog, CommandDefinition
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.tools.llm_enhancement_candidates import build_llm_enhancement_candidates


def test_build_llm_enhancement_candidates_from_scan_proposal():
    inventory = ProjectInventory(
        repo_name="demo",
        root_path="/tmp/demo",
        primary_stack="java-spring",
        stack_extensions={
            "llm_scan_proposal": {
                "architecture_signals": ["Controller layer is present"],
                "risk_areas": [{"path": "src/main/resources/application.yml", "reason": "Database config risk"}],
                "command_candidates": [
                    {"id": "unit_test", "command": "mvn test", "type": "test", "gate": "hard", "source": "pom.xml", "confidence": "high"}
                ],
            }
        },
    )
    commands = CommandCatalog(commands=[CommandDefinition(id="unit_test", command="mvn test", type="test", gate="hard", source="pom.xml")])

    report = build_llm_enhancement_candidates(inventory, commands)

    assert report["schema_version"] == "1.0"
    assert report["source"] == "llm_scan_proposal"
    assert {item["candidate_type"] for item in report["candidates"]} == {"guide", "sensor"}
    assert all(item["status"] == "candidate" for item in report["candidates"])
    assert all(item["human_confirmation_required"] is True for item in report["candidates"])
```

- [ ] **Step 2: Run test to verify failure**

Run: `.venv/bin/python -m pytest tests/unit/test_llm_enhancement_candidates.py -q`

Expected: FAIL because module does not exist.

- [ ] **Step 3: Implement builder**

Implement:

- `build_llm_enhancement_candidates(inventory, commands) -> dict`
- `candidate_guides_markdown(report) -> str`
- `candidate_sensors_markdown(report) -> str`
- `enhancement_summary_markdown(report) -> str`

- [ ] **Step 4: Run unit tests**

Run: `.venv/bin/python -m pytest tests/unit/test_llm_enhancement_candidates.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/harness_builder_agent/tools/llm_enhancement_candidates.py tests/unit/test_llm_enhancement_candidates.py
git commit -m "feat: build llm enhancement candidates"
```

## Task 2: Init Asset Integration

**Files:**
- Modify: `src/harness_builder_agent/tools/write_assets.py`
- Modify: `tests/integration/test_init_on_fixture_projects.py`

- [ ] **Step 1: Write failing integration assertions**

Assert:

```python
assert (ai / "review" / "llm-enhancement-candidates.md").exists()
assert (ai / "review" / "candidate-guides.md").exists()
assert (ai / "review" / "candidate-sensors.md").exists()
assert (ai / "experience" / "weapon-library-candidates.yaml").exists()
candidate_report = yaml.safe_load((ai / "experience" / "weapon-library-candidates.yaml").read_text())
assert candidate_report["source"] == "llm_scan_proposal"
assert candidate_report["candidates"]
assert all(item["status"] == "candidate" for item in candidate_report["candidates"])
```

- [ ] **Step 2: Run integration test to verify failure**

Run: `.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py -q`

Expected: FAIL because assets are missing.

- [ ] **Step 3: Write assets from `write_initial_assets`**

After guides/sensors are written:

- Build report.
- Write review markdown files.
- Write `.ai/experience/weapon-library-candidates.yaml`.
- Record artifacts in generation trace.

- [ ] **Step 4: Run integration tests**

Run: `.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/harness_builder_agent/tools/write_assets.py tests/integration/test_init_on_fixture_projects.py
git commit -m "feat: write llm enhancement candidate assets"
```

## Task 3: Benchmark Checks and Verification

**Files:**
- Modify: `src/harness_builder_agent/tools/benchmark.py`
- Modify: `tests/integration/test_benchmark_command.py`

- [ ] **Step 1: Write failing benchmark assertions**

Assert:

```python
assert "exists:review/llm-enhancement-candidates.md" in check_ids
assert "schema:weapon-library-candidates" in check_ids
assert "content:llm-enhancement-candidates" in check_ids
```

- [ ] **Step 2: Run benchmark test to verify failure**

Run: `.venv/bin/python -m pytest tests/integration/test_benchmark_command.py -q`

Expected: FAIL for missing check ids.

- [ ] **Step 3: Implement benchmark checks**

Add schema/content helper:

- YAML exists and has `schema_version=1.0`.
- `source=llm_scan_proposal`.
- candidates non-empty.
- every candidate is `status=candidate` and `human_confirmation_required=true`.

- [ ] **Step 4: Full verification**

Run:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m pytest tests/acceptance/test_real_llm_scan.py -q
.venv/bin/python -m pytest tests/acceptance/test_real_repositories_e2e.py -q
```

Expected: all pass.

- [ ] **Step 5: Commit and push**

```bash
git add src/harness_builder_agent/tools/benchmark.py tests/integration/test_benchmark_command.py
git commit -m "test: benchmark llm enhancement candidates"
git push origin main
```

