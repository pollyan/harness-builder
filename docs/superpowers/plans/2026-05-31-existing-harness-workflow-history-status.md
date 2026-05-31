# Existing Harness Workflow History Status Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show the latest workflow recommendation history signal in the existing-Harness guided init entry and trace history artifacts from guided `recommend-workflow`.

**Architecture:** Add a small status helper in `interactive_init.py` that consumes existing Pydantic schemas. Keep output line-oriented to match the current maintenance entry, and keep guided recommend artifacts aligned with standalone `recommend-workflow`.

**Tech Stack:** Python, Typer CliRunner integration tests, Pydantic schemas, YAML.

---

## Files

- Modify `src/harness_builder_agent/tools/interactive_init.py`
  - Import `WorkflowRecommendationHistory`.
  - Add helper for latest workflow recommendation status.
  - Add history artifacts to guided recommend trace/output.
- Modify `tests/integration/test_init_on_fixture_projects.py`
  - Add history-status exit test.
  - Add legacy latest-status exit test.
  - Extend guided recommend-workflow test for history artifacts.
- Modify docs:
  - `README.md`
  - `docs/engineering/init-workflow.md`
  - `docs/evolution-log.md`

## Tasks

### Task 1: RED Tests

- [x] Add integration test for existing-Harness `exit` showing latest workflow recommendation history details.
- [x] Add integration test for legacy latest recommendation status without history index.
- [x] Extend guided `recommend-workflow` integration test to assert history paths in output and trace artifacts.
- [x] Run targeted tests and confirm failures.

RED verification:

```text
scripts/test-integration.sh tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_shows_latest_workflow_recommendation_history tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_shows_legacy_latest_workflow_recommendation tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_can_recommend_workflow_without_overwriting_formal_assets -q
FFF
```

### Task 2: Green Implementation

- [x] Implement `_workflow_recommendation_status_lines(ai)`.
- [x] Update `_experience_status_lines(ai)` to include latest workflow recommendation status.
- [x] Update guided `recommend-workflow` trace artifacts and summary output for history index / summary.
- [x] Run targeted tests until green.

GREEN verification:

```text
scripts/test-integration.sh tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_shows_latest_workflow_recommendation_history tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_shows_legacy_latest_workflow_recommendation tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_can_recommend_workflow_without_overwriting_formal_assets -q
...
```

### Task 3: Docs, Verification, Commit

- [x] Update README and init workflow docs.
- [x] Add evolution log entry.
- [x] Run targeted tests.
- [x] Run `scripts/test-fast.sh`.
- [ ] Commit with message `feat: surface workflow recommendation history status`.

Final verification:

```text
scripts/test-integration.sh tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_shows_latest_workflow_recommendation_history tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_shows_legacy_latest_workflow_recommendation tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_can_recommend_workflow_without_overwriting_formal_assets -q
...

scripts/test-fast.sh
248 passed in 13.22s
```
