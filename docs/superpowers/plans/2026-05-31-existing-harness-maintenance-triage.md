# Existing Harness Maintenance Triage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show the top maintenance actions when guided `init` detects an existing Harness.

**Architecture:** Add a read-only triage helper that ranks structured `.ai` signals, then render its top lines in the existing-Harness guided entry before the menu.

**Tech Stack:** Python dataclasses, Pydantic schema validation, Typer CliRunner integration tests, Markdown docs.

---

## Files

- Create `src/harness_builder_agent/tools/maintenance_triage.py`
- Modify `src/harness_builder_agent/tools/interactive_init.py`
- Add `tests/unit/test_maintenance_triage.py`
- Modify `tests/integration/test_init_on_fixture_projects.py`
- Modify docs:
  - `README.md`
  - `docs/engineering/init-workflow.md`
  - `docs/todos/maturity-driven-init-wizard.md`
  - `docs/evolution-log.md`

## Tasks

### Task 1: RED Tests

- [x] Add unit tests for benchmark/schema-content priority, unresolved asset candidates, workflow recommendation signal, and no-action fallback.
- [x] Add integration assertion that existing-Harness guided `init -> exit` shows `Maintenance triage` and `top_action_1=benchmark` when benchmark has not run.
- [x] Run targeted tests and confirm they fail before implementation.

RED verification:

```text
scripts/test-unit.sh tests/unit/test_maintenance_triage.py -q && scripts/test-integration.sh tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_can_exit_without_overwriting_assets -q
ERROR ModuleNotFoundError: No module named 'harness_builder_agent.tools.maintenance_triage'
```

### Task 2: Green Implementation

- [x] Implement `MaintenanceAction` and triage ranking helper.
- [x] Render triage lines in existing-Harness guided entry.
- [x] Run targeted tests until green.

GREEN verification:

```text
scripts/test-unit.sh tests/unit/test_maintenance_triage.py -q && scripts/test-integration.sh tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_can_exit_without_overwriting_assets -q
3 passed
1 passed
```

### Task 3: Docs, Gate, Commit

- [x] Update README and init workflow docs.
- [x] Update maturity-driven init todo and evolution log.
- [x] Run targeted tests.
- [x] Run `scripts/test-fast.sh`.
- [ ] Commit with message `feat: show existing harness maintenance triage`.

Targeted verification:

```text
scripts/test-unit.sh tests/unit/test_maintenance_triage.py -q
3 passed

scripts/test-integration.sh tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_can_exit_without_overwriting_assets tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_shows_latest_workflow_recommendation_history tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_can_benchmark_without_overwriting_formal_assets -q
3 passed

scripts/test-fast.sh
262 passed in 28.04s
```
