# Existing Harness Benchmark Action Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a guided existing-Harness `benchmark` maintenance action that refreshes quality evidence without overwriting formal Harness assets.

**Architecture:** Keep orchestration in `interactive_init.py`, reuse `run_benchmark` with the current init trace so benchmark can validate generation trace state, then finish the trace again with guided-action summary. Tests cover pass and failed-check reporting paths through the real CLI.

**Tech Stack:** Python, Typer, Pytest, Pydantic schema validation, YAML artifacts.

---

### Task 1: Integration Tests

**Files:**
- Modify: `tests/integration/test_init_on_fixture_projects.py`

- [x] **Step 1: Write failing tests**

Add tests for `benchmark` and `bench` selections after a non-interactive baseline init. Assert no scan, formal assets unchanged, `BenchmarkReport` schema validates, output includes status summary, and trace records `existing_harness_action: benchmark`.

- [x] **Step 2: Run tests to verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_can_benchmark_without_overwriting_formal_assets tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_benchmark_reports_failed_checks -q
```

Expected before implementation: both tests fail because `benchmark` and `bench` are treated as unknown actions.

### Task 2: Guided Init Implementation

**Files:**
- Modify: `src/harness_builder_agent/tools/interactive_init.py`

- [x] **Step 1: Import benchmark runner and report schema**

Import `run_benchmark` and `BenchmarkReport`.

- [x] **Step 2: Add menu option and action branch**

Add `benchmark` to the existing-Harness menu. For aliases `benchmark`, `bench`, `质量`, `验收`, call `run_benchmark(repo, profile=inventory.primary_stack, trace=trace)`.

- [x] **Step 3: Record trace and output summary**

Record derived artifacts, write summary fields, and print status with failed check ids. Keep failed benchmark visible but do not turn it into a silent success.

### Task 3: Docs And Evolution Record

**Files:**
- Modify: `README.md`
- Modify: `docs/engineering/init-workflow.md`
- Modify: `docs/todos/maturity-driven-init-wizard.md`
- Modify: `docs/evolution-log.md`

- [x] **Step 1: Update user-facing docs**

Document the new guided action and clarify it refreshes derived validation/maturity/improvement evidence while preserving formal assets.

- [x] **Step 2: Update todo and evolution log**

Mark the benchmark action slice completed and record gap analysis, decisions, risks, verification, Self-Harness Gate, and next candidate gaps.

### Task 4: Verification And Commit

**Files:**
- All modified files

- [x] **Step 1: Run targeted tests**

Run the two benchmark action integration tests and the existing assess/improve tests around the same code path.

- [x] **Step 2: Run fast regression**

Run:

```bash
scripts/test-fast.sh
```

- [x] **Step 3: Commit**

Stage changed files and commit:

```bash
git commit -m "feat: add existing harness benchmark action"
```
