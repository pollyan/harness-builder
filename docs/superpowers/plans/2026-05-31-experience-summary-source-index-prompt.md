# Experience Summary Source Index Prompt Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the LLM Experience Summary prompt explicitly use `experience_index.sources` as review-only source index metadata.

**Architecture:** Keep the existing schemas and orchestration. Add one prompt-contract test, update the prompt string in the LLM summarizer, and document the contract in LLM engineering rules.

**Tech Stack:** Python, pytest, Pydantic schemas, DeepSeek-compatible chat message payloads.

---

### Task 1: Add Failing Prompt Contract Test

**Files:**
- Modify: `tests/unit/test_llm_experience_summarizer.py`

- [ ] **Step 1: Add source-aware index data to the test helper**

Import `ExperienceSource`:

```python
from harness_builder_agent.schemas.experience_index import ExperienceIndex, ExperienceSource
```

Update `_index()` so it contains source metadata:

```python
def _index() -> ExperienceIndex:
    return ExperienceIndex(
        experience_files={"pending-improvements.md": True},
        sources=[
            ExperienceSource(path=".ai/experience/pending-improvements.md", kind="pending_improvements", item_count=1),
            ExperienceSource(path=".ai/review/maturity-review.yaml", kind="maturity_review", item_count=1),
            ExperienceSource(path=".ai/review/asset-candidates.yaml", kind="asset_candidates", item_count=1),
            ExperienceSource(path=".ai/review/workflow-routing-recommendation.yaml", kind="workflow_recommendation", item_count=1),
        ],
        pending_improvement_count=1,
        asset_candidate_count=1,
        maturity_review_count=1,
        workflow_recommendation_count=1,
        runtime_task_run_count=0,
    )
```

- [ ] **Step 2: Add the failing prompt assertion**

Add this test:

```python
def test_build_experience_summary_messages_guides_source_index_details():
    messages = build_experience_summary_messages(_index(), _sources())

    content = messages[-1]["content"]
    assert "experience_index.sources" in content
    assert "path, kind, and item_count" in content
    assert ".ai/review/workflow-routing-recommendation.yaml" in content
    assert "review-only source index" in content
    assert "Do not invent missing source paths" in content
```

- [ ] **Step 3: Run RED**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_llm_experience_summarizer.py::test_build_experience_summary_messages_guides_source_index_details -q
```

Expected: FAIL because the prompt does not yet mention the source-index guidance.

### Task 2: Implement Prompt Guidance

**Files:**
- Modify: `src/harness_builder_agent/tools/llm_experience_summarizer.py`
- Modify: `docs/engineering/llm-contracts.md`

- [ ] **Step 1: Update the Experience Summary prompt**

Add to the schema contract:

```text
Use experience_index.sources as a review-only source index. Inspect each source path, kind, and item_count to understand available pending improvement, maturity review, asset candidate, workflow recommendation, manual experience, or runtime evidence.
Ground findings[].evidence_sources in paths that are present in the provided sources map.
Do not invent missing source paths, and do not treat review-only source entries as applied Guides, Sensors, Workflow Skills, harness-config changes, or task executions.
```

- [ ] **Step 2: Update LLM contract docs**

Add one prompt-management bullet explaining that LLM Experience Summary must explicitly consume `experience_index.sources` as review-only source index metadata.

- [ ] **Step 3: Run GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_llm_experience_summarizer.py -q
```

Expected: Experience Summary unit tests pass.

### Task 3: Verify And Commit

**Files:**
- Create: `docs/superpowers/specs/2026-05-31-experience-summary-source-index-prompt-design.md`
- Create: `docs/superpowers/plans/2026-05-31-experience-summary-source-index-prompt.md`
- Modify: `tests/unit/test_llm_experience_summarizer.py`
- Modify: `src/harness_builder_agent/tools/llm_experience_summarizer.py`
- Modify: `docs/engineering/llm-contracts.md`

- [ ] **Step 1: Run focused prompt tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_llm_experience_summarizer.py tests/unit/test_llm_maturity_reviewer.py tests/unit/test_llm_asset_candidate_generator.py -q
```

Expected: source-aware prompt tests pass across all three LLM review steps.

- [ ] **Step 2: Run fast regression before commit**

Run:

```bash
scripts/test-fast.sh
```

Expected: fast suite passes.

- [ ] **Step 3: Commit**

Run:

```bash
git add docs/engineering/llm-contracts.md docs/superpowers/specs/2026-05-31-experience-summary-source-index-prompt-design.md docs/superpowers/plans/2026-05-31-experience-summary-source-index-prompt.md src/harness_builder_agent/tools/llm_experience_summarizer.py tests/unit/test_llm_experience_summarizer.py
git commit -m "feat: guide experience summary with source index"
```

- [ ] **Step 4: Run full regression and push**

Run:

```bash
scripts/test-full.sh
git push
scripts/check-ci.sh
```

Expected: full local suite passes before push, push succeeds, and CI status is checked after push.
