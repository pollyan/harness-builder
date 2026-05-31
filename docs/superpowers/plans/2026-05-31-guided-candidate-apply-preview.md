# Guided Candidate Apply Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show a read-only apply preview before guided `review-candidate` decisions so maintainers understand the formal Harness impact before typing `applied`.

**Architecture:** Keep `review_candidate()` as the source of truth for actual apply and validation. Add a CLI-only preview helper in `interactive_init.py` that reads candidate metadata and target file state, then update guided init integration tests and product docs.

**Tech Stack:** Python, Typer CliRunner integration tests, Pydantic schemas, Markdown docs.

---

## Files

- Modify `src/harness_builder_agent/tools/interactive_init.py`
  - Call a preview helper after candidate detail and before decision prompt.
  - Add `_asset_candidate_apply_preview(repo, candidate)`.
- Modify `tests/integration/test_init_on_fixture_projects.py`
  - Extend guided Guide `applied` test for preview output.
  - Add duplicate-marker preview and failure test.
  - Extend workflow policy guided apply rejection test for expert-command preview.
- Modify docs:
  - `README.md`
  - `docs/engineering/init-workflow.md`
  - `docs/todos/maturity-driven-init-wizard.md`
  - `docs/evolution-log.md`

## Tasks

### Task 1: RED Tests

- [x] Extend Guide applied integration test to assert apply preview before decision.
- [x] Add duplicate marker integration test that sees `duplicate_marker=present` and fails on `applied` without writing governance.
- [x] Extend workflow policy rejection test to assert `apply_preview=expert_command_required`.
- [x] Run targeted tests and confirm failures.

RED verification:

```text
scripts/test-integration.sh tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_can_apply_guide_candidate_with_review_boundary tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_previews_duplicate_candidate_marker_before_apply_failure tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_rejects_workflow_policy_apply -q
FFF
```

### Task 2: Green Implementation

- [x] Add `_asset_candidate_apply_preview(repo, candidate)` for Guide / Sensor Markdown and workflow policy boundaries.
- [x] Call preview helper before prompting for decision.
- [x] Run targeted tests until green.

GREEN verification:

```text
scripts/test-integration.sh tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_can_apply_guide_candidate_with_review_boundary tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_previews_duplicate_candidate_marker_before_apply_failure tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_rejects_workflow_policy_apply -q
...
```

### Task 3: Docs, Verification, Commit

- [x] Update README and init workflow docs.
- [x] Update maturity-driven init todo and evolution log.
- [x] Run targeted tests.
- [x] Run `scripts/test-fast.sh`.
- [ ] Commit with message `feat: preview guided candidate apply impact`.

Final verification:

```text
scripts/test-integration.sh tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_can_apply_guide_candidate_with_review_boundary tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_previews_duplicate_candidate_marker_before_apply_failure tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_rejects_workflow_policy_apply -q
...

scripts/test-fast.sh
249 passed in 13.22s
```
