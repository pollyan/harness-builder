# Workflow Recommendation Asset Candidate Prompt Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make LLM asset candidate generation explicitly turn `experience-workflow-recommendation-review` into a concrete review-only workflow policy draft when review evidence supports it.

**Architecture:** Keep the existing schemas and parser. Add one prompt contract clause and one unit test that verifies the candidate id, recommendation artifact, workflow policy target, and review-only boundary are present in the generated prompt.

**Tech Stack:** Python, Pydantic schemas, pytest, DeepSeek-compatible chat messages.

---

### Task 1: Add Prompt Contract Test

**Files:**
- Modify: `tests/unit/test_llm_asset_candidate_generator.py`

- [ ] **Step 1: Write the failing test**

Add a helper report containing `experience-workflow-recommendation-review`, and assert the generated prompt includes the review source and workflow policy guidance:

```python
def _workflow_recommendation_improvement_candidates() -> ImprovementCandidateReport:
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


def test_build_asset_candidate_messages_guides_workflow_recommendation_candidate():
    evidence = _evidence_pack()
    evidence.maturity_inputs.append(".ai/review/workflow-routing-recommendation.yaml")

    messages = build_asset_candidate_messages(
        _score(),
        evidence,
        _workflow_recommendation_improvement_candidates(),
        MaturityReviewReport(
            summary="Workflow recommendation review should become a routing policy draft.",
            candidate_reviews=[
                {
                    "candidate_id": "experience-workflow-recommendation-review",
                    "decision": "support",
                    "rationale": "Routing policy should be reviewed.",
                }
            ],
        ),
    )

    content = messages[-1]["content"]
    assert "experience-workflow-recommendation-review" in content
    assert ".ai/review/workflow-routing-recommendation.yaml" in content
    assert "workflow_policy" in content
    assert ".ai/harness-config.yaml" in content
    assert "pending_harness_maintainer_review" in content
    assert "review-only workflow recommendation evidence" in content
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_llm_asset_candidate_generator.py::test_build_asset_candidate_messages_guides_workflow_recommendation_candidate -q
```

Expected: FAIL because the new prompt phrase is absent.

### Task 2: Add Prompt Guidance

**Files:**
- Modify: `src/harness_builder_agent/tools/llm_asset_candidate_generator.py`
- Modify: `docs/engineering/llm-contracts.md`

- [ ] **Step 1: Implement minimal prompt text**

Add this contract text after the existing workflow policy routing guidance:

```text
When improvement candidate experience-workflow-recommendation-review is present, inspect review-only workflow recommendation evidence from .ai/review/workflow-routing-recommendation.yaml when available in maturity inputs or candidate evidence sources.
If maturity review supports or revises that candidate, prefer a workflow_policy draft targeting .ai/harness-config.yaml that explains routing rule, escalation, required guide, required sensor, or human confirmation adjustments.
The draft must remain pending_harness_maintainer_review and must not claim the recommendation was executed or applied.
```

- [ ] **Step 2: Update engineering doc**

Add one bullet to `docs/engineering/llm-contracts.md` explaining the same review-only contract.

- [ ] **Step 3: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_llm_asset_candidate_generator.py -q
```

Expected: all tests in the file pass.

### Task 3: Verify And Commit

**Files:**
- Modified files from Tasks 1 and 2.
- Created spec and plan files.

- [ ] **Step 1: Run fast regression**

Run:

```bash
scripts/test-fast.sh
```

Expected: fast suite passes.

- [ ] **Step 2: Commit**

Run:

```bash
git add docs/engineering/llm-contracts.md docs/superpowers/specs/2026-05-31-workflow-recommendation-asset-candidate-prompt-design.md docs/superpowers/plans/2026-05-31-workflow-recommendation-asset-candidate-prompt.md src/harness_builder_agent/tools/llm_asset_candidate_generator.py tests/unit/test_llm_asset_candidate_generator.py
git commit -m "feat: guide asset candidates from workflow recommendations"
```

- [ ] **Step 3: Run full regression and push**

Run:

```bash
scripts/test-full.sh
git push
scripts/check-ci.sh
```

Expected: local full suite passes before push; push succeeds; CI status is checked after push.
