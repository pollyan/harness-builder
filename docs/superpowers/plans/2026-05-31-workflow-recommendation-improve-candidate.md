# Workflow Recommendation Improve Candidate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Generate a review-only workflow policy improvement candidate when maturity evidence contains workflow recommendation review signals.

**Architecture:** Add focused unit coverage for `generate_improvements._candidates`, then add one helper that converts `ExperienceEvidence.workflow_recommendation_count` into a deterministic `ImprovementCandidate`. No CLI or schema change is needed.

**Tech Stack:** Python, Pydantic, pytest, YAML docs.

---

### Task 1: Add failing unit tests

**Files:**
- Create: `tests/unit/test_generate_improvements.py`

- [x] **Step 1: Add candidate generation test**

Create:

```python
from harness_builder_agent.schemas.maturity_evidence import ExperienceEvidence, MaturityEvidencePack
from harness_builder_agent.schemas.maturity_report import MaturityReport
from harness_builder_agent.tools.generate_improvements import _candidates


def test_candidates_include_workflow_policy_follow_up_for_workflow_recommendation_review():
    score = MaturityReport(overall_level="L2", target_next_level="L3")
    evidence = MaturityEvidencePack(
        repo_name="demo",
        primary_stack="java-spring",
        experience=ExperienceEvidence(workflow_recommendation_count=1),
        maturity_inputs=[".ai/review/workflow-routing-recommendation.yaml"],
    )

    candidates = _candidates(score, evidence)

    candidate = next(item for item in candidates if item.id == "experience-workflow-recommendation-review")
    assert candidate.candidate_type == "workflow_policy_update"
    assert candidate.suggested_target == ".ai/harness-config.yaml"
    assert candidate.human_confirmation_required is True
    assert candidate.target_dimension == "workflow"
    assert ".ai/review/workflow-routing-recommendation.yaml" in candidate.evidence_sources
    assert any("Workflow recommendation reviews: 1" in item for item in candidate.evidence)
```

- [x] **Step 2: Add no-signal test**

Add:

```python
def test_candidates_skip_workflow_recommendation_follow_up_when_no_review_signal():
    score = MaturityReport(overall_level="L2", target_next_level="L3")
    evidence = MaturityEvidencePack(repo_name="demo", primary_stack="java-spring")

    candidates = _candidates(score, evidence)

    assert all(item.id != "experience-workflow-recommendation-review" for item in candidates)
```

- [x] **Step 3: Run focused tests and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_generate_improvements.py -q
```

Expected: first test fails because the candidate is not generated yet.

### Task 2: Implement deterministic candidate

**Files:**
- Modify: `src/harness_builder_agent/tools/generate_improvements.py`

- [x] **Step 1: Add candidate call**

In `_candidates`, after warning-derived candidates, add:

```python
if evidence_pack.experience.workflow_recommendation_count > 0:
    _append_unique(candidates, seen, _workflow_recommendation_review_candidate(evidence_pack))
```

- [x] **Step 2: Add helper**

Add:

```python
def _workflow_recommendation_review_candidate(evidence_pack: MaturityEvidencePack) -> ImprovementCandidate:
    count = evidence_pack.experience.workflow_recommendation_count
    return ImprovementCandidate(
        id="experience-workflow-recommendation-review",
        candidate_type="workflow_policy_update",
        suggested_target=".ai/harness-config.yaml",
        rationale="Workflow recommendation review evidence exists; inspect whether routing policy should be adjusted or whether current rules already cover the recommendation.",
        evidence=[
            f"Workflow recommendation reviews: {count}.",
            "Recommendation artifacts are review-only and must not be treated as applied routing changes.",
        ],
        confidence="medium",
        priority="medium",
        target_dimension="workflow",
        acceptance_checks=[
            "Candidate remains pending review before formal workflow assets are changed.",
            "Benchmark content:workflow-recommendation-review passes when recommendation artifacts are present.",
            "Benchmark content:workflow-routing-policy passes after any reviewed routing policy change.",
        ],
        evidence_sources=_evidence_sources(evidence_pack),
    )
```

- [x] **Step 3: Run focused tests and confirm pass**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_generate_improvements.py -q
```

Expected: pass.

### Task 3: Update docs and verify

**Files:**
- Modify: `docs/engineering/init-workflow.md`

- [x] **Step 1: Document improve behavior**

Add a sentence near the Experience/maturity evidence contract:

```markdown
`improve` should turn nonzero workflow recommendation review counts into pending `workflow_policy_update` candidates, never direct `harness-config.yaml` edits.
```

- [x] **Step 2: Verify references**

Run:

```bash
rg -n "workflow recommendation review|experience-workflow-recommendation-review|workflow_recommendation_count" docs/engineering src tests
```

Expected: docs, implementation, and tests are found.

### Task 4: Verify and commit

- [x] **Step 1: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_generate_improvements.py tests/unit/test_maturity_evidence.py tests/unit/test_maturity_model.py -q
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
git add docs/superpowers/specs/2026-05-31-workflow-recommendation-improve-candidate-design.md docs/superpowers/plans/2026-05-31-workflow-recommendation-improve-candidate.md tests/unit/test_generate_improvements.py src/harness_builder_agent/tools/generate_improvements.py docs/engineering/init-workflow.md
git commit -m "feat: recommend workflow policy follow-up from experience evidence"
```

Expected: commit succeeds after pre-commit fast test.

### Self-Review

- Spec coverage: positive/negative candidate behavior, review-only boundary, docs, and verification are covered.
- Placeholder scan: no TBD/TODO placeholders.
- Type consistency: candidate id and evidence field names match implementation.
