# Guided Candidate Apply Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let Harness Maintainers apply one reviewed Guide / Sensor candidate from the existing-Harness guided `init` entry while preserving review-only boundaries for workflow policy candidates.

**Architecture:** Reuse the existing `review_candidate()` application path and governance schema. The guided `init` layer only adds candidate detail display, decision routing, trace metadata, and stricter workflow-policy rejection.

**Tech Stack:** Python, Typer `CliRunner`, Pydantic schemas, pytest integration tests, Markdown docs.

---

## Files

- Modify `src/harness_builder_agent/tools/interactive_init.py`
  - Show candidate detail before collecting decision.
  - Allow `applied` for `guide` / `sensor` candidates.
  - Reject guided `applied` for `workflow_policy`.
  - Record `applied_path_count` in trace summary.
- Modify `tests/integration/test_init_on_fixture_projects.py`
  - Add guided apply success test for a Guide candidate.
  - Add guided workflow policy apply rejection test.
- Modify docs:
  - `README.md`
  - `docs/engineering/init-workflow.md`
  - `docs/evolution-log.md`
  - `docs/superpowers/plans/2026-05-31-guided-candidate-apply.md`

## Tasks

### Task 1: RED Integration Tests

- [x] Add `test_guided_init_existing_harness_can_apply_guide_candidate_with_review_boundary`.
- [x] Add `test_guided_init_existing_harness_rejects_workflow_policy_apply`.
- [x] Run both tests and confirm failure is caused by guided `applied` currently being unsupported.

### Task 2: Guided Apply Implementation

- [x] Add a helper in `interactive_init.py` to load an `AssetCandidateDraft` by id from the existing asset candidate report.
- [x] Add a helper to render candidate detail before asking for decision.
- [x] Change guided `review-candidate` so `applied` is accepted only for `guide` and `sensor`.
- [x] Keep workflow policy `applied` as an explicit guided failure with no governance file write.
- [x] Run the new integration tests until green.

### Task 3: Docs, Gate, Verification

- [x] Update README existing-Harness action description.
- [x] Update `docs/engineering/init-workflow.md` guided `review-candidate` boundary.
- [x] Add evolution-log entry with Gap Analysis, decisions, tests, and Gate result.
- [x] Run targeted integration tests.
- [x] Run `scripts/test-fast.sh` before commit.
