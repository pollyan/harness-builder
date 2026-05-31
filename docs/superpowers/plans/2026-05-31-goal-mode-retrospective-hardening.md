# Goal Mode Retrospective Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden contracts and documentation after the incomplete goal-mode prompt retrospective.

**Architecture:** Keep the slice narrow: parser-level explicit-key checks, one schema field for maturity review status, read-only CLI formatting, stronger tests, and docs cleanup. No new Runtime behavior and no formal asset application changes.

**Tech Stack:** Python, Typer, Pydantic, pytest, Markdown prompt assets.

---

## Files

- Modify `src/harness_builder_agent/tools/interactive_init.py`
  - Replace single Experience total with structured read-only status lines.
- Modify `src/harness_builder_agent/tools/llm_workflow_router.py`
  - Require explicit top-level LLM keys.
- Modify `src/harness_builder_agent/prompts/llm_workflow_router_v1.md`
  - Add complete JSON output template.
- Modify `src/harness_builder_agent/schemas/maturity_review.py`
  - Add `review_status`.
- Modify `src/harness_builder_agent/tools/llm_maturity_reviewer.py`
  - Require explicit maturity-review top-level and candidate-review keys.
- Modify `src/harness_builder_agent/prompts/llm_maturity_review_v2.md`
  - Add `review_status` to field contract and template.
- Modify `src/harness_builder_agent/tools/review_maturity.py`
  - Write `## Review Boundary`.
- Modify `src/harness_builder_agent/tools/benchmark.py`
  - Require maturity-review Markdown review boundary.
- Modify tests:
  - `tests/unit/test_llm_workflow_router.py`
  - `tests/unit/test_llm_maturity_reviewer.py`
  - `tests/integration/test_assess_improve_commands.py`
  - `tests/integration/test_benchmark_command.py`
  - `tests/integration/test_init_on_fixture_projects.py`
- Modify docs:
  - `README.md`
  - `docs/todos/maturity-driven-init-wizard.md`
  - `docs/todos/README.md`
  - `docs/evolution-log.md`

## Tasks

### Task 1: RED Tests

- [x] Add unit tests proving workflow recommendation rejects missing explicit `review_status`.
- [x] Add unit tests proving maturity review rejects missing explicit `review_status`.
- [x] Extend maturity-review integration test to require YAML `review_status` and Markdown `## Review Boundary`.
- [x] Extend benchmark missing-section test to require failure when maturity review lacks `## Review Boundary`.
- [x] Extend existing-Harness exit test to assert structured status output.
- [x] Expand formal asset snapshot helper.
- [x] Run targeted tests and confirm failures are from missing implementation.

### Task 2: Green Implementation

- [x] Add explicit-key validation helpers in LLM parsers.
- [x] Add `review_status` schema field and prompt template updates.
- [x] Add maturity review Markdown boundary and benchmark required section.
- [x] Replace existing Harness status formatter with structured read-only lines.
- [x] Run targeted tests.

### Task 3: Docs And Verification

- [x] Update README and guided init todo to remove stale descriptions.
- [x] Add follow-up todo for evidence-source whitelist hardening.
- [x] Add evolution-log entry for this retrospective hardening.
- [x] Run `scripts/test-fast.sh` before commit.
