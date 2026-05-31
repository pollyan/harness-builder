# Existing Harness Recommend Workflow Action Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a guided existing-Harness `recommend-workflow` maintenance action that generates review-only workflow routing recommendations from a task brief.

**Architecture:** Keep guided orchestration in `interactive_init.py`, reuse `recommend_workflow()` for LLM/schema/artifact behavior, then record the guided action in the init trace. Tests use mock LLM and real CLI flow.

**Tech Stack:** Python, Typer, Pytest, Pydantic, YAML review artifacts, DeepSeek-backed LLM prompt behind an existing mockable function.

---

### Task 1: Integration Test

**Files:**
- Modify: `tests/integration/test_init_on_fixture_projects.py`

- [x] **Step 1: Write the failing test**

Add `test_guided_init_existing_harness_can_recommend_workflow_without_overwriting_formal_assets`. The test prepares a Harness, snapshots formal assets, mocks `recommend_workflow_with_llm`, selects `recommend-workflow`, enters task brief and task id, then asserts review-only artifacts, Experience/Maturity refresh, trace summary, benchmark validation, no scan and no formal asset overwrite.

- [x] **Step 2: Run test to verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_can_recommend_workflow_without_overwriting_formal_assets -q
```

Expected before implementation: fail because guided init treats `recommend-workflow` as an unknown action.

### Task 2: Guided Action Implementation

**Files:**
- Modify: `src/harness_builder_agent/tools/interactive_init.py`

- [x] **Step 1: Import recommendation tool and schema**

Import `recommend_workflow` and `WorkflowRecommendationReport`.

- [x] **Step 2: Add menu and action aliases**

Add menu text and branch for `recommend-workflow`, `recommend`, `workflow`, `工作流`, and `路由`.

- [x] **Step 3: Prompt for task input and run recommendation**

Prompt for task brief and task id. Reject empty brief with explicit failure. Call `recommend_workflow(repo, task_brief=task_brief, task_id=task_id)`.

- [x] **Step 4: Print summary and trace artifacts**

Read `.ai/review/workflow-routing-recommendation.yaml`, print recommended workflow/risk/confidence/review-only boundary, and record artifacts plus summary fields in the init trace.

### Task 3: Docs And Evolution Record

**Files:**
- Modify: `README.md`
- Modify: `docs/engineering/init-workflow.md`
- Modify: `docs/todos/maturity-driven-init-wizard.md`
- Modify: `docs/evolution-log.md`

- [x] **Step 1: Document guided recommend-workflow boundary**

State that it writes review-only workflow recommendation and derived evidence, does not execute runtime or apply routing policy.

- [x] **Step 2: Update evolution log**

Record gap analysis, decisions, assumptions, subagent use, verification, Self-Harness Gate and next candidate gaps.

### Task 4: Verification And Commit

**Files:**
- All modified files

- [x] **Step 1: Run targeted tests**

Run the new test and related existing-Harness init tests.

- [x] **Step 2: Run fast regression**

Run:

```bash
scripts/test-fast.sh
```

- [ ] **Step 3: Commit**

Commit:

```bash
git commit -m "feat: add existing harness workflow recommendation action"
```
