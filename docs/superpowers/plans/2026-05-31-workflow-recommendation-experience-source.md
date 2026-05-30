# Workflow Recommendation Experience Source Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Feed workflow recommendation review artifacts into Experience Summary as optional review-only evidence.

**Architecture:** Extend the existing `SOURCE_PATHS` list in `summarize_experience.py` and cover it through unit and integration tests. No new schema is required because Experience Summary already validates that LLM findings only cite provided `.ai/` sources.

**Tech Stack:** Python, pytest, Typer integration tests, YAML.

---

### Task 1: Add failing source collection tests

**Files:**
- Modify: `tests/unit/test_llm_experience_summarizer.py`
- Modify: `tests/integration/test_assess_improve_commands.py`

- [x] **Step 1: Add prompt visibility assertion**

In `tests/unit/test_llm_experience_summarizer.py`, update `_sources()` to include:

```python
".ai/review/workflow-routing-recommendation.yaml": "recommended_workflow: bugfix",
```

Then update `test_build_experience_summary_messages_includes_review_only_boundary`:

```python
assert "workflow-routing-recommendation.yaml" in content
```

- [x] **Step 2: Add integration assertion**

In `test_summarize_experience_writes_review_only_summary`, write `.ai/review/workflow-routing-recommendation.yaml` before the fake summary function:

```python
(repo / ".ai" / "review" / "workflow-routing-recommendation.yaml").write_text(
    yaml.safe_dump(
        {
            "schema_version": "1.0",
            "task_id": "task-1",
            "task_brief": "Fix a regression.",
            "recommended_workflow": "bugfix",
            "matched_rule_ids": ["bugfix-intent"],
            "risk_level": "medium",
            "confidence": "high",
            "rationale": "Bugfix task.",
            "required_guides": [".ai/guides/project-context.md"],
            "required_sensors": [".ai/sensors/verification.md"],
            "human_confirmation_required": False,
            "review_status": "pending_harness_maintainer_review",
            "evidence_sources": [".ai/harness-config.yaml"],
        },
        sort_keys=False,
        allow_unicode=True,
    ),
    encoding="utf-8",
)
```

Inside `fake_summary`, add:

```python
assert ".ai/review/workflow-routing-recommendation.yaml" in sources
```

- [x] **Step 3: Run focused tests and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_llm_experience_summarizer.py tests/integration/test_assess_improve_commands.py::test_summarize_experience_writes_review_only_summary -q
```

Expected: integration test fails until `_collect_sources` includes the recommendation source.

### Task 2: Implement source collection

**Files:**
- Modify: `src/harness_builder_agent/tools/summarize_experience.py`

- [x] **Step 1: Add source path**

Append to `SOURCE_PATHS`:

```python
".ai/review/workflow-routing-recommendation.yaml",
```

- [x] **Step 2: Run focused tests and confirm pass**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_llm_experience_summarizer.py tests/integration/test_assess_improve_commands.py::test_summarize_experience_writes_review_only_summary -q
```

Expected: pass.

### Task 3: Update LLM contract docs

**Files:**
- Modify: `docs/engineering/llm-contracts.md`

- [x] **Step 1: Document optional workflow recommendation source**

Add to Prompt Management:

```markdown
- LLM experience summary may consume `.ai/review/workflow-routing-recommendation.yaml` when present as review-only evidence for workflow gaps or routing signals. It must not treat the recommendation as an applied workflow execution or formal Harness change.
```

- [x] **Step 2: Verify docs reference**

Run:

```bash
rg -n "workflow-routing-recommendation.yaml|Experience Summary" docs/engineering src tests
```

Expected: docs, source list, and tests are found.

### Task 4: Verify and commit

- [x] **Step 1: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_llm_experience_summarizer.py tests/integration/test_assess_improve_commands.py::test_summarize_experience_writes_review_only_summary -q
```

Expected: pass.

- [x] **Step 2: Run fast regression**

Run:

```bash
scripts/test-fast.sh
```

Expected: pass.

- [x] **Step 3: Commit**

Run:

```bash
git add docs/superpowers/specs/2026-05-31-workflow-recommendation-experience-source-design.md docs/superpowers/plans/2026-05-31-workflow-recommendation-experience-source.md tests/unit/test_llm_experience_summarizer.py tests/integration/test_assess_improve_commands.py src/harness_builder_agent/tools/summarize_experience.py docs/engineering/llm-contracts.md
git commit -m "feat: include workflow recommendations in experience summary"
```

Expected: commit succeeds after pre-commit fast test.

### Self-Review

- Spec coverage: source collection, integration prompt handoff, docs, no runtime execution, and no formal asset mutation are covered.
- Placeholder scan: no TBD/TODO placeholders.
- Type consistency: existing `sources: dict[str, str]` contract remains unchanged.
