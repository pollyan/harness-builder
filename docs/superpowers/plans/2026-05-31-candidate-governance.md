# Candidate Governance MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a review-to-apply governance slice for `.ai/review/asset-candidates.yaml`.

**Architecture:** Keep LLM-generated candidates review-only, and record human/maintainer decisions in a separate governance log. Python owns schema validation, path safety, Markdown application, experience index refresh, benchmark validation, and trace artifacts.

**Tech Stack:** Python, Typer, Pydantic, YAML, pytest.

---

### Task 1: Schema And Unit Tests

**Files:**
- Create: `src/harness_builder_agent/schemas/candidate_governance.py`
- Modify: `tests/unit/test_schema_contracts.py`

- [ ] Write failing tests for valid and invalid governance decisions.
- [ ] Add Pydantic models with literal decision states.
- [ ] Run targeted schema tests.

### Task 2: Governance Tool

**Files:**
- Create: `src/harness_builder_agent/tools/candidate_governance.py`
- Modify: `tests/unit/test_candidate_governance.py`
- Modify: `src/harness_builder_agent/schemas/experience_index.py`
- Modify: `src/harness_builder_agent/tools/experience_index.py`
- Modify: `src/harness_builder_agent/schemas/maturity_evidence.py`
- Modify: `src/harness_builder_agent/tools/maturity_evidence.py`

- [ ] Write failing tests for applying a guide candidate, rejecting unsafe application, and refreshing experience index.
- [ ] Implement `review_candidate(repo, candidate_id, decision, rationale, reviewer)`.
- [ ] Restrict `applied` to guide/sensor Markdown under `.ai/`.
- [ ] Write governance YAML/Markdown and refresh experience index.
- [ ] Expose governance count in maturity evidence.

### Task 3: CLI Integration

**Files:**
- Modify: `src/harness_builder_agent/cli.py`
- Modify: `tests/integration/test_assess_improve_commands.py`

- [ ] Write failing CLI test for `review-candidate --decision applied`.
- [ ] Add Typer command and trace artifacts.
- [ ] Verify original asset candidates remain review-only.

### Task 4: Benchmark Coverage

**Files:**
- Modify: `src/harness_builder_agent/tools/benchmark.py`
- Modify: `tests/integration/test_benchmark_command.py`

- [ ] Write failing benchmark tests for valid governance artifacts and invalid references.
- [ ] Add optional governance artifact check.
- [ ] Include the check in content checks.

### Task 5: Docs And Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/engineering/architecture.md`
- Modify: `docs/engineering/init-workflow.md`
- Modify: `docs/engineering/sensor-and-gate-rules.md`
- Modify: `docs/evolution-log.md`

- [ ] Document the command and product boundary.
- [ ] Run targeted tests.
- [ ] Run `scripts/test-fast.sh` before commit.
- [ ] Commit locally.
