# Existing Harness Candidate Governance Action Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a guided existing-Harness candidate governance action for accepted/deferred/rejected decisions without applying formal assets.

**Architecture:** Keep guided orchestration in `interactive_init.py`, reuse `review_candidate()` for schema and governance artifact writing, and explicitly reject guided `applied` decisions. Tests cover real CLI flow with a prepared review-only asset candidate.

**Tech Stack:** Python, Typer, Pytest, Pydantic, YAML review artifacts.

---

### Task 1: Integration Test

**Files:**
- Modify: `tests/integration/test_init_on_fixture_projects.py`

- [x] **Step 1: Write the failing test**

Add `test_guided_init_existing_harness_can_record_candidate_governance_without_applying_assets`. The test prepares `.ai/review/asset-candidates.yaml`, snapshots formal assets, selects `review-candidate`, records an `accepted` decision and asserts governance schema, Experience index, trace artifacts and no formal overwrite.

- [x] **Step 2: Run test to verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_can_record_candidate_governance_without_applying_assets -q
```

Expected before implementation: fail because guided init treats `review-candidate` as an unknown action.

### Task 2: Guided Action Implementation

**Files:**
- Modify: `src/harness_builder_agent/tools/interactive_init.py`

- [x] **Step 1: Import governance tool and schema**

Import `CandidateGovernanceLog` and `review_candidate`.

- [x] **Step 2: Add menu and aliases**

Add `review-candidate` to the existing-Harness menu and support aliases `candidate`, `governance`, `候选`, `治理`.

- [x] **Step 3: Prompt and validate decision**

Show a short candidate summary, then prompt candidate id, decision, rationale and reviewer. Only allow `accepted`, `deferred`, `rejected`; reject `applied` with explicit error.

- [x] **Step 4: Record trace and output**

Call `review_candidate`, validate `CandidateGovernanceLog`, record governance and Experience index artifacts, then print summary.

### Task 3: Docs And Evolution Record

**Files:**
- Modify: `README.md`
- Modify: `docs/engineering/init-workflow.md`
- Modify: `docs/todos/maturity-driven-init-wizard.md`
- Modify: `docs/evolution-log.md`

- [x] **Step 1: Document guided governance boundary**

State that guided action records accepted/deferred/rejected only and does not apply formal assets.

- [x] **Step 2: Update evolution log**

Record gap analysis, decisions, assumptions, subagent use, verification, Self-Harness Gate and next candidate gaps.

### Task 4: Verification And Commit

**Files:**
- All modified files

- [x] **Step 1: Run targeted tests**

Run new candidate governance test and the existing guided maintenance action tests.

- [x] **Step 2: Run fast regression**

Run:

```bash
scripts/test-fast.sh
```

- [ ] **Step 3: Commit**

Commit:

```bash
git commit -m "feat: add existing harness candidate governance action"
```
