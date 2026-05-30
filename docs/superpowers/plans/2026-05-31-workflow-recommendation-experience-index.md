# Workflow Recommendation Experience Index Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Expose workflow recommendation review artifacts in `experience-index.yaml` and `maturity-evidence.yaml`.

**Architecture:** Add a new review source kind and count to the existing Experience Index schema, populate it from the schema-validated workflow recommendation YAML, and copy it into the maturity evidence pack. The change is additive and backward compatible because new fields default to zero.

**Tech Stack:** Python, Pydantic, YAML, pytest.

---

### Task 1: Write failing schema and evidence tests

**Files:**
- Modify: `tests/unit/test_schema_contracts.py`
- Create: `tests/unit/test_experience_index.py`
- Modify: `tests/unit/test_maturity_evidence.py`

- [x] **Step 1: Extend schema contract test**

In `test_experience_index_records_sources_and_counts`, add:

```python
{"path": ".ai/review/workflow-routing-recommendation.yaml", "kind": "workflow_recommendation", "item_count": 1}
```

and:

```python
"workflow_recommendation_count": 1,
```

Assert:

```python
assert index.sources[1].kind == "workflow_recommendation"
assert index.workflow_recommendation_count == 1
```

- [x] **Step 2: Add experience index builder test**

Create `tests/unit/test_experience_index.py`:

```python
from pathlib import Path

import yaml

from harness_builder_agent.tools.experience_index import build_experience_index


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def test_build_experience_index_counts_workflow_recommendation_review(tmp_path: Path):
    ai = tmp_path / ".ai"
    _write_yaml(
        ai / "review" / "workflow-routing-recommendation.yaml",
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
    )

    index = build_experience_index(ai)

    assert index.workflow_recommendation_count == 1
    source = next(item for item in index.sources if item.kind == "workflow_recommendation")
    assert source.path == ".ai/review/workflow-routing-recommendation.yaml"
    assert source.item_count == 1
```

- [x] **Step 3: Extend maturity evidence test**

In `test_collect_maturity_evidence_uses_experience_index`, add to the written index:

```python
"workflow_recommendation_count": 1,
```

Then assert:

```python
assert ".ai/review/workflow-routing-recommendation.yaml" in pack.maturity_inputs
assert pack.experience.workflow_recommendation_count == 1
```

- [x] **Step 4: Run focused tests and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py::test_experience_index_records_sources_and_counts tests/unit/test_experience_index.py tests/unit/test_maturity_evidence.py::test_collect_maturity_evidence_uses_experience_index -q
```

Expected: fail until schemas and collectors expose workflow recommendation evidence.

### Task 2: Implement schema and collectors

**Files:**
- Modify: `src/harness_builder_agent/schemas/experience_index.py`
- Modify: `src/harness_builder_agent/tools/experience_index.py`
- Modify: `src/harness_builder_agent/schemas/maturity_evidence.py`
- Modify: `src/harness_builder_agent/tools/maturity_evidence.py`

- [x] **Step 1: Extend Experience Index schema**

Add `workflow_recommendation` to `ExperienceSource.kind` and add:

```python
workflow_recommendation_count: int = 0
```

to `ExperienceIndex`.

- [x] **Step 2: Count valid workflow recommendation YAML**

Import `WorkflowRecommendationReport` and add:

```python
def _workflow_recommendation_count(path: Path) -> int:
    if not path.exists():
        return 0
    WorkflowRecommendationReport.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    return 1
```

Use it in `build_experience_index`, append source kind `workflow_recommendation` when count is positive, and set `workflow_recommendation_count`.

- [x] **Step 3: Extend maturity evidence schema and collector**

Add `workflow_recommendation_count: int = 0` to `ExperienceEvidence`.

Add `.ai/review/workflow-routing-recommendation.yaml` to `MATURITY_INPUTS`.

Set `workflow_recommendation_count=index.workflow_recommendation_count` in `_experience`.

- [x] **Step 4: Run focused tests and confirm pass**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py::test_experience_index_records_sources_and_counts tests/unit/test_experience_index.py tests/unit/test_maturity_evidence.py::test_collect_maturity_evidence_uses_experience_index -q
```

Expected: pass.

### Task 3: Update engineering docs

**Files:**
- Modify: `docs/engineering/init-workflow.md`

- [x] **Step 1: Update output contract**

Update the maturity evidence and experience index paragraphs so they mention workflow recommendation review count and optional `.ai/review/workflow-routing-recommendation.yaml`.

- [x] **Step 2: Verify references**

Run:

```bash
rg -n "workflow recommendation|workflow-routing-recommendation|workflow_recommendation_count" docs/engineering src tests
```

Expected: docs, schemas, collectors, and tests are all referenced.

### Task 4: Verify and commit

- [x] **Step 1: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py::test_experience_index_records_sources_and_counts tests/unit/test_experience_index.py tests/unit/test_maturity_evidence.py::test_collect_maturity_evidence_uses_experience_index -q
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
git add docs/superpowers/specs/2026-05-31-workflow-recommendation-experience-index-design.md docs/superpowers/plans/2026-05-31-workflow-recommendation-experience-index.md tests/unit/test_schema_contracts.py tests/unit/test_experience_index.py tests/unit/test_maturity_evidence.py src/harness_builder_agent/schemas/experience_index.py src/harness_builder_agent/tools/experience_index.py src/harness_builder_agent/schemas/maturity_evidence.py src/harness_builder_agent/tools/maturity_evidence.py docs/engineering/init-workflow.md
git commit -m "feat: index workflow recommendation experience evidence"
```

Expected: commit succeeds after pre-commit fast test.

### Self-Review

- Spec coverage: schema, index builder, maturity evidence, docs, no runtime execution, and no formal asset mutation are covered.
- Placeholder scan: no TBD/TODO placeholders.
- Type consistency: `workflow_recommendation_count` is used consistently across schema, collector, and tests.
