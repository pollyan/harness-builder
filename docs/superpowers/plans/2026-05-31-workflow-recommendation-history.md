# Workflow Recommendation History Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve every review-only workflow recommendation while keeping the existing latest recommendation files compatible.

**Architecture:** Add a small history schema and writer inside the recommendation flow. Experience index and benchmark consume the history index when present, but latest files remain the compatibility path.

**Tech Stack:** Python, Pydantic, YAML, Typer integration tests, pytest.

---

## Files

- Create `src/harness_builder_agent/schemas/workflow_recommendation_history.py`
  - Defines history index schema.
- Modify `src/harness_builder_agent/tools/recommend_workflow.py`
  - Writes per-recommendation YAML/Markdown, index YAML, summary Markdown, and latest compatibility files.
- Modify `src/harness_builder_agent/tools/experience_index.py`
  - Counts history index entries before legacy latest file.
- Modify `src/harness_builder_agent/tools/benchmark.py`
  - Validates optional recommendation history artifacts.
- Modify tests:
  - `tests/unit/test_schema_contracts.py`
  - `tests/unit/test_experience_index.py`
  - `tests/integration/test_assess_improve_commands.py`
  - `tests/integration/test_benchmark_command.py`
- Modify docs:
  - `README.md`
  - `docs/engineering/init-workflow.md`
  - `docs/engineering/sensor-and-gate-rules.md`
  - `docs/evolution-log.md`

## Tasks

### Task 1: RED Tests

- [x] Add workflow recommendation history schema unit test.
- [x] Add Experience index unit test for two historical recommendations.
- [x] Add integration test for two `recommend-workflow` calls preserving two history entries and latest compatibility files.
- [x] Add benchmark integration test for invalid history artifact failing.
- [x] Run targeted tests and confirm failures.

### Task 2: Green Implementation

- [x] Implement `WorkflowRecommendationHistory` schema.
- [x] Update `recommend_workflow()` to write history artifacts and latest compatibility files.
- [x] Update `experience_index` to count history entries.
- [x] Update benchmark optional checks.
- [x] Run targeted tests until green.

### Task 3: Docs, Gate, Verification

- [x] Update README and engineering docs.
- [x] Add evolution log entry.
- [x] Run targeted tests.
- [x] Run `scripts/test-fast.sh` before commit.
