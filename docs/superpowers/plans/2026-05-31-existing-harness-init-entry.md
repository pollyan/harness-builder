# Existing Harness Init Entry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make default guided `init` detect an existing Harness and offer a read-only status entry with an exit path that does not overwrite formal assets.

**Architecture:** Add existing-Harness detection inside `run_guided_init` before scan starts, read current status through existing schemas, print a concise Chinese status summary, and return early on `exit`.

**Tech Stack:** Python, Typer, Pydantic, PyYAML, pytest.

---

### Task 1: Failing Integration Test

**Files:**
- Modify: `tests/integration/test_init_on_fixture_projects.py`

- [x] Add a test that creates a Harness with `init --non-interactive`.
- [x] Run default guided `init` with TTY and input `exit`.
- [x] Assert output includes existing Harness status and current maturity.
- [x] Assert `scan_repository` is not called and formal `.ai` assets are unchanged.
- [x] Assert latest trace records the exit action.

### Task 2: Guided Existing Harness Entry

**Files:**
- Modify: `src/harness_builder_agent/tools/interactive_init.py`

- [x] Detect `.ai/project-inventory.json` and `.ai/harness-config.yaml` at the start of guided init.
- [x] Read `ProjectInventory`, `MaturityReport`, optional benchmark report and optional experience index via schema.
- [x] Print status summary and actions: `exit` or `reinit`.
- [x] On `exit`, record trace event and finish with `existing_harness_action=exit`.
- [x] On `reinit`, continue the existing guided generation flow.

### Task 3: Docs And Verification

**Files:**
- Modify: `docs/engineering/init-workflow.md`
- Modify: `docs/todos/maturity-driven-init-wizard.md`
- Modify: `docs/evolution-log.md`

- [x] Document existing Harness guided entry behavior.
- [x] Mark the read-only existing Harness entry slice as completed in the todo.
- [x] Run targeted init integration tests.
- [x] Run `scripts/test-fast.sh`.
- [ ] Commit locally.
