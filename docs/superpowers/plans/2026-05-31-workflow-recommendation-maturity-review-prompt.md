# Workflow Recommendation Maturity Review Prompt Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make LLM maturity review explicitly evaluate `experience-workflow-recommendation-review` from workflow recommendation review evidence.

**Architecture:** Keep `MaturityReviewReport` unchanged. Add one prompt clause and one unit test that verifies workflow recommendation evidence is first-class review-only context for the reviewer.

**Tech Stack:** Python, pytest, Pydantic schemas, DeepSeek-compatible chat messages.

---

### Task 1: Add Prompt Contract Test

**Files:**
- Modify: `tests/unit/test_llm_maturity_reviewer.py`

- [ ] **Step 1: Write the failing test**

Add this helper and test:

```python
def _workflow_recommendation_candidates() -> ImprovementCandidateReport:
    return ImprovementCandidateReport(
        candidates=[
            ImprovementCandidate(
                id="experience-workflow-recommendation-review",
                candidate_type="workflow_policy_update",
                suggested_target=".ai/harness-config.yaml",
                rationale="Review workflow recommendation evidence.",
                evidence=[
                    "Workflow recommendation reviews: 1.",
                    "Recommendation artifacts are review-only and must not be treated as applied routing changes.",
                ],
                target_dimension="workflow",
                evidence_sources=[
                    ".ai/maturity-evidence.yaml",
                    ".ai/review/workflow-routing-recommendation.yaml",
                ],
            )
        ]
    )


def test_build_maturity_review_messages_guides_workflow_recommendation_candidate():
    evidence = _evidence_pack()
    evidence.maturity_inputs.append(".ai/review/workflow-routing-recommendation.yaml")

    messages = build_maturity_review_messages(
        _score(),
        evidence,
        _workflow_recommendation_candidates(),
    )

    content = messages[-1]["content"]
    assert "experience-workflow-recommendation-review" in content
    assert ".ai/review/workflow-routing-recommendation.yaml" in content
    assert "workflow_routing_rules" in content
    assert "review-only workflow recommendation evidence" in content
    assert "support or revise" in content
    assert "must not claim" in content
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_llm_maturity_reviewer.py::test_build_maturity_review_messages_guides_workflow_recommendation_candidate -q
```

Expected: FAIL because the prompt lacks the dedicated workflow recommendation reviewer clause.

### Task 2: Add Reviewer Prompt Guidance

**Files:**
- Modify: `src/harness_builder_agent/tools/llm_maturity_reviewer.py`
- Modify: `docs/engineering/llm-contracts.md`

- [ ] **Step 1: Implement minimal prompt text**

Add this prompt contract text:

```text
When improvement candidate experience-workflow-recommendation-review is present, inspect review-only workflow recommendation evidence from .ai/review/workflow-routing-recommendation.yaml when available in maturity inputs or candidate evidence sources.
Compare the recommendation with maturity_evidence.harness_assets.workflow_routing_rules before deciding whether current routing already covers it.
Prefer support or revise when evidence indicates routing policy, escalation, required guide, required sensor, or human confirmation adjustments should be drafted later.
The review must not claim the recommendation was executed, applied, or written into formal Harness assets.
```

- [ ] **Step 2: Update engineering doc**

Add one bullet in `docs/engineering/llm-contracts.md` for maturity review handling of `experience-workflow-recommendation-review`.

- [ ] **Step 3: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_llm_maturity_reviewer.py -q
```

Expected: all maturity reviewer unit tests pass.

### Task 3: Verify And Commit

**Files:**
- Created spec and plan files.
- Modified reviewer prompt, reviewer tests, and LLM contract docs.

- [ ] **Step 1: Run fast regression**

Run:

```bash
scripts/test-fast.sh
```

Expected: fast suite passes.

- [ ] **Step 2: Commit**

Run:

```bash
git add docs/engineering/llm-contracts.md docs/superpowers/specs/2026-05-31-workflow-recommendation-maturity-review-prompt-design.md docs/superpowers/plans/2026-05-31-workflow-recommendation-maturity-review-prompt.md src/harness_builder_agent/tools/llm_maturity_reviewer.py tests/unit/test_llm_maturity_reviewer.py
git commit -m "feat: guide maturity review from workflow recommendations"
```

- [ ] **Step 3: Run full regression and push**

Run:

```bash
scripts/test-full.sh
git push
scripts/check-ci.sh
```

Expected: local full suite passes before push; push succeeds; CI status is checked after push.
