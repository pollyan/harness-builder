# Experience Source Details In Maturity Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve Experience Index source details inside `maturity-evidence.yaml` so downstream review and improve steps can see concrete review source paths.

**Architecture:** Add an additive `sources` field to `ExperienceEvidence` and populate it from `ExperienceIndex.sources`. Keep legacy fallback behavior unchanged.

**Tech Stack:** Python, Pydantic, YAML, pytest.

---

### Task 1: Add Failing Unit Tests

**Files:**
- Modify: `tests/unit/test_maturity_evidence.py`

- [ ] **Step 1: Extend indexed evidence fixture**

Add `sources` to the existing `experience-index.yaml` fixture:

```python
"sources": [
    {"path": ".ai/experience/pending-improvements.md", "kind": "pending_improvements", "item_count": 2},
    {"path": ".ai/review/maturity-review.yaml", "kind": "maturity_review", "item_count": 1},
    {"path": ".ai/review/asset-candidates.yaml", "kind": "asset_candidates", "item_count": 3},
    {"path": ".ai/review/workflow-routing-recommendation.yaml", "kind": "workflow_recommendation", "item_count": 1},
],
```

- [ ] **Step 2: Add assertions**

In `test_collect_maturity_evidence_uses_experience_index`, assert:

```python
assert [source.path for source in pack.experience.sources] == [
    ".ai/experience/pending-improvements.md",
    ".ai/review/maturity-review.yaml",
    ".ai/review/asset-candidates.yaml",
    ".ai/review/workflow-routing-recommendation.yaml",
]
assert pack.experience.sources[1].kind == "maturity_review"
assert pack.experience.sources[2].item_count == 3
```

In `test_collect_maturity_evidence_keeps_pending_only_legacy_path`, assert:

```python
assert pack.experience.sources == []
```

- [ ] **Step 3: Run RED**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_maturity_evidence.py::test_collect_maturity_evidence_uses_experience_index -q
```

Expected: FAIL because `ExperienceEvidence` has no `sources` field.

### Task 2: Implement Schema And Collector

**Files:**
- Modify: `src/harness_builder_agent/schemas/maturity_evidence.py`
- Modify: `src/harness_builder_agent/tools/maturity_evidence.py`
- Modify: `docs/engineering/init-workflow.md`

- [ ] **Step 1: Reuse `ExperienceSource` in schema**

Add:

```python
from harness_builder_agent.schemas.experience_index import ExperienceSource
```

Then add to `ExperienceEvidence`:

```python
sources: list[ExperienceSource] = Field(default_factory=list)
```

- [ ] **Step 2: Populate from index**

In `_experience(ai)`, when index exists, pass:

```python
sources=index.sources
```

Do not populate sources in the legacy fallback.

- [ ] **Step 3: Update engineering doc**

Update the maturity evidence paragraph in `docs/engineering/init-workflow.md` so it says Experience evidence exposes both counts and source path details from `experience-index.yaml`.

- [ ] **Step 4: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_maturity_evidence.py tests/unit/test_schema_contracts.py -q
```

Expected: tests pass.

### Task 3: Verify And Commit

**Files:**
- Created spec and plan files.
- Modified schema, collector, unit tests, and engineering docs.

- [ ] **Step 1: Run fast regression**

Run:

```bash
scripts/test-fast.sh
```

Expected: fast suite passes.

- [ ] **Step 2: Commit**

Run:

```bash
git add docs/engineering/init-workflow.md docs/superpowers/specs/2026-05-31-experience-source-details-in-maturity-evidence-design.md docs/superpowers/plans/2026-05-31-experience-source-details-in-maturity-evidence.md src/harness_builder_agent/schemas/maturity_evidence.py src/harness_builder_agent/tools/maturity_evidence.py tests/unit/test_maturity_evidence.py
git commit -m "feat: include experience source details in maturity evidence"
```

- [ ] **Step 3: Run full regression and push**

Run:

```bash
scripts/test-full.sh
git push
scripts/check-ci.sh
```

Expected: local full suite passes before push; push succeeds; CI status is checked after push.
