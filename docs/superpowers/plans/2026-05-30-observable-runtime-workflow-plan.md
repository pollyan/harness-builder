# Observable Runtime Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add task-level runtime workflow trace files under `.ai/task-runs/<task_id>/`.

**Architecture:** Keep runtime observability local to `run_task.py` for the POC. The task runner already owns harness-map, sensor report, decision log, and handoff; it will also write JSONL workflow events, used guide index, and runtime summary.

**Tech Stack:** Python, YAML, JSONL, pytest.

---

## File Structure

- Modify: `src/harness_builder_agent/tools/run_task.py`
  - Add helper functions for workflow events, used guides, and runtime summary.
- Modify: `tests/integration/test_task_run_workflow.py`
  - Assert runtime trace files for bugfix and lightweight runs.
- Modify: `tests/e2e/test_fixture_end_to_end.py`
  - Assert fixture e2e includes runtime trace.
- Modify: `src/harness_builder_agent/tools/benchmark.py`
  - Add runtime trace checks.
- Modify: `tests/integration/test_benchmark_command.py`
  - Assert benchmark report includes runtime trace checks.
- Modify: `tests/acceptance/test_real_repositories_e2e.py`
  - Assert real repositories include runtime summary.

## Task 1: Runtime Trace for `run`

**Files:**
- Modify: `tests/integration/test_task_run_workflow.py`
- Modify: `src/harness_builder_agent/tools/run_task.py`

- [ ] **Step 1: Write failing assertions**

In `_assert_task_outputs`, add:

```python
assert (task_dir / "workflow-events.jsonl").exists()
assert (task_dir / "used-guides.yaml").exists()
assert (task_dir / "runtime-summary.yaml").exists()

events = [json.loads(line) for line in (task_dir / "workflow-events.jsonl").read_text().splitlines()]
stages = {event["stage"] for event in events}
assert {"task-classification", "guide-selection", "workflow-selection", "sensor-selection", "sensor-execution", "handoff", "experience-candidate"}.issubset(stages)

used_guides = yaml.safe_load((task_dir / "used-guides.yaml").read_text())
assert used_guides["workflow_skill"]["path"] == f".ai/skills/{expected_workflow}/SKILL.md"
assert all(item["path"].startswith(".ai/guides/") for item in used_guides["required_guides"])
assert all(item["exists"] is True for item in used_guides["required_guides"])

runtime = yaml.safe_load((task_dir / "runtime-summary.yaml").read_text())
assert runtime["selected_workflow"] == expected_workflow
assert runtime["used_guide_count"] == len(used_guides["required_guides"])
assert runtime["sensor_statuses"]
```

- [ ] **Step 2: Run test to verify failure**

Run: `.venv/bin/python -m pytest tests/integration/test_task_run_workflow.py -q`

Expected: FAIL because runtime trace files do not exist.

- [ ] **Step 3: Implement runtime trace helpers**

In `run_task.py`:

- Add `_workflow_event(...)`.
- Add `_write_workflow_events(...)`.
- Add `_used_guides(...)`.
- Add `_runtime_summary(...)`.

Write the three files after sensor execution and before handoff.

- [ ] **Step 4: Run integration test**

Run: `.venv/bin/python -m pytest tests/integration/test_task_run_workflow.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/harness_builder_agent/tools/run_task.py tests/integration/test_task_run_workflow.py
git commit -m "feat: trace runtime workflow"
```

## Task 2: E2E and Benchmark Checks

**Files:**
- Modify: `tests/e2e/test_fixture_end_to_end.py`
- Modify: `src/harness_builder_agent/tools/benchmark.py`
- Modify: `tests/integration/test_benchmark_command.py`

- [ ] **Step 1: Add failing e2e assertions**

Assert fixture e2e has:

```python
assert (task_dir / "runtime-summary.yaml").exists()
assert (task_dir / "used-guides.yaml").exists()
```

- [ ] **Step 2: Add failing benchmark assertions**

In benchmark tests:

```python
assert "schema:runtime-summary" in check_ids
assert "content:runtime-workflow-trace" in check_ids
```

- [ ] **Step 3: Run tests to verify failure**

Run: `.venv/bin/python -m pytest tests/e2e/test_fixture_end_to_end.py tests/integration/test_benchmark_command.py -q`

Expected: benchmark assertions fail before implementation.

- [ ] **Step 4: Implement benchmark runtime checks**

Add `_runtime_trace_checks(ai)` to `benchmark.py`:

- Validate `.ai/task-runs/demo-task-001/runtime-summary.yaml`.
- Validate `.ai/task-runs/demo-task-001/workflow-events.jsonl`.
- Validate `.ai/task-runs/demo-task-001/used-guides.yaml`.
- Check required stages exist and used guide count matches.

- [ ] **Step 5: Run tests**

Run: `.venv/bin/python -m pytest tests/e2e/test_fixture_end_to_end.py tests/integration/test_benchmark_command.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/harness_builder_agent/tools/benchmark.py tests/e2e/test_fixture_end_to_end.py tests/integration/test_benchmark_command.py
git commit -m "test: benchmark runtime workflow trace"
```

## Task 3: Acceptance Verification

**Files:**
- Modify: `tests/acceptance/test_real_repositories_e2e.py`

- [ ] **Step 1: Add real repository assertion**

Assert:

```python
runtime_summary = yaml.safe_load((ai / "task-runs" / "demo-task-001" / "runtime-summary.yaml").read_text())
assert runtime_summary["selected_workflow"] == expected_workflow
assert runtime_summary["used_guide_count"] > 0
```

- [ ] **Step 2: Run default tests**

Run: `.venv/bin/python -m pytest -q`

Expected: PASS.

- [ ] **Step 3: Run real DeepSeek fixture acceptance**

Run: `.venv/bin/python -m pytest tests/acceptance/test_real_llm_scan.py -q`

Expected: PASS.

- [ ] **Step 4: Run real repository e2e acceptance**

Run: `.venv/bin/python -m pytest tests/acceptance/test_real_repositories_e2e.py -q`

Expected: PASS.

- [ ] **Step 5: Push**

```bash
git push origin main
```

