# Existing Harness Self-Improve Action Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a guided existing-Harness `self-improve` maintenance action that generates a review-only self-improvement package from existing Harness state.

**Architecture:** Keep guided orchestration in `interactive_init.py`, reuse `run_self_improve()` for the actual maturity/LLM/candidate pipeline, then record package artifacts and summary in the init trace. Tests mock LLM reviewer and asset candidate generator.

**Tech Stack:** Python, Typer, Pytest, Pydantic, YAML review artifacts, existing DeepSeek-backed LLM tools behind mockable functions.

---

### Task 1: Integration Test

**Files:**
- Modify: `tests/integration/test_init_on_fixture_projects.py`

- [x] **Step 1: Write the failing test**

Add `test_guided_init_existing_harness_can_self_improve_without_overwriting_formal_assets`. The test prepares a Harness, snapshots formal assets, mocks maturity review and asset candidate LLM calls, selects `self-improve`, then asserts package schema, benchmark check, trace artifacts, no scan, no formal overwrite and no `.ai/task-runs`.

- [x] **Step 2: Run test to verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_can_self_improve_without_overwriting_formal_assets -q
```

Expected before implementation: fail because guided init treats `self-improve` as an unknown action.

### Task 2: Guided Action Implementation

**Files:**
- Modify: `src/harness_builder_agent/tools/interactive_init.py`

- [x] **Step 1: Import self-improve tool and manifest schema**

Import `run_self_improve` and `SelfImprovePackageManifest`.

- [x] **Step 2: Add menu and aliases**

Add `self-improve` to the existing-Harness menu and support aliases `self`, `自改进`, `智能改进`.

- [x] **Step 3: Run self-improve and validate package**

Call `run_self_improve(repo)` and validate `.ai/review/self-improve-package.yaml`.

- [x] **Step 4: Record trace and output**

Record generated review artifacts, maturity/improvement artifacts and candidate counts in init trace, then print a review-only summary.

### Task 3: Docs And Evolution Record

**Files:**
- Modify: `README.md`
- Modify: `docs/engineering/init-workflow.md`
- Modify: `docs/todos/maturity-driven-init-wizard.md`
- Modify: `docs/evolution-log.md`

- [x] **Step 1: Document guided self-improve boundary**

State that guided `self-improve` is explicit, LLM-backed and review-only; it does not execute Runtime or apply formal assets.

- [x] **Step 2: Update evolution log**

Record gap analysis, decisions, assumptions, subagent use, verification, Self-Harness Gate and next candidate gaps.

### Task 4: Verification And Commit

**Files:**
- All modified files

- [x] **Step 1: Run targeted tests**

Run new self-improve guided test plus standalone self-improve integration test.

- [x] **Step 2: Run fast regression**

Run:

```bash
scripts/test-fast.sh
```

- [ ] **Step 3: Commit**

Commit:

```bash
git commit -m "feat: add existing harness self-improve action"
```
