# Routing-Aware Asset Candidate Prompt Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for implementation steps and superpowers:verification-before-completion before commit/push.

**Goal:** Make the LLM asset candidate prompt explicitly use detailed workflow routing evidence when drafting review-only workflow policy candidates.

**Architecture:** Keep the existing `AssetCandidateReport` schema and parser. Update only the prompt contract and unit tests so routing evidence is treated as first-class review-only context. No runtime execution, task classification, or config mutation is introduced.

**Tech Stack:** Python, pytest, JSON prompt payloads, Pydantic v2.

---

## Files

- Modify: `src/harness_builder_agent/tools/llm_asset_candidate_generator.py`
- Modify: `tests/unit/test_llm_asset_candidate_generator.py`
- Modify: `docs/engineering/llm-contracts.md`
- Modify: `docs/superpowers/plans/2026-05-31-routing-aware-asset-candidate-prompt.md`

## Task 1: Routing-Aware Prompt Contract

- [ ] **Step 1: Write failing prompt assertion**

In `tests/unit/test_llm_asset_candidate_generator.py`, import `HarnessAssetEvidence` and `WorkflowRoutingRuleEvidence` from `schemas.maturity_evidence`.

Update `_evidence_pack()` to include:

```python
harness_assets=HarnessAssetEvidence(
    workflow_routing_rule_count=1,
    has_standard_escalation_rule=True,
    workflow_routing_rules=[
        WorkflowRoutingRuleEvidence(
            id="standard-escalation",
            selected_workflow="standard",
            task_type_hints=["feature"],
            triggers=["high_risk_module", "security_or_permission"],
            required_guides=[".ai/guides/architecture.md"],
            required_sensors=[".ai/sensors/verification.md"],
            human_confirmation_required=True,
            rationale="Escalate risky work.",
        )
    ],
)
```

In `test_build_asset_candidate_messages_includes_experience_summary_when_present`, assert:

```python
assert "workflow_routing_rules" in content
assert "standard-escalation" in content
assert "security_or_permission" in content
assert "When drafting workflow_policy candidates" in content
assert "pending_harness_maintainer_review" in content
```

- [ ] **Step 2: Run targeted test and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_llm_asset_candidate_generator.py::test_build_asset_candidate_messages_includes_experience_summary_when_present -q
```

Expected: fail because the payload contains routing evidence after the fixture change, but the prompt does not contain the explicit workflow policy instruction.

- [ ] **Step 3: Update prompt contract**

In `llm_asset_candidate_generator.py`, add to `schema_contract`:

```text
When drafting workflow_policy candidates, inspect maturity_evidence.harness_assets.workflow_routing_rules.
Use routing rule ids, selected workflow, triggers, required guides, required sensors, human confirmation, and rationale as evidence.
Prefer .ai/harness-config.yaml for workflow_policy suggestions that adjust routing rules or escalation conditions.
Workflow policy candidates remain review-only and must keep review_status pending_harness_maintainer_review.
Never claim workflow routing changes were applied.
```

- [ ] **Step 4: Run targeted test and confirm pass**

Run the same pytest command. Expected: pass.

## Task 2: Parser Regression for Workflow Policy Candidate

- [ ] **Step 1: Add parser test for workflow policy candidate**

In `tests/unit/test_llm_asset_candidate_generator.py`, add:

```python
def test_generate_asset_candidates_accepts_workflow_policy_candidate():
    report = parse_asset_candidate_response(
        json.dumps(
            {
                "candidates": [
                    {
                        "id": "workflow-routing-standard-escalation",
                        "kind": "workflow_policy",
                        "source_candidate_id": "candidate-1",
                        "source_review_decision": "support",
                        "suggested_path": ".ai/harness-config.yaml",
                        "title": "Refine standard escalation routing",
                        "rationale": "Uses routing evidence.",
                        "draft_content": "workflow_routing:\\n  rules:\\n    - id: standard-escalation",
                        "review_status": "pending_harness_maintainer_review",
                    }
                ]
            }
        ),
        {"candidate-1"},
    )

    assert report.candidates[0].kind == "workflow_policy"
    assert report.candidates[0].suggested_path == ".ai/harness-config.yaml"
```

- [ ] **Step 2: Run unit tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_llm_asset_candidate_generator.py -q
```

Expected: pass.

## Task 3: Docs, Verification, Commit

- [ ] **Step 1: Update LLM engineering docs**

In `docs/engineering/llm-contracts.md`, add that asset candidate generation must treat `maturity_evidence.harness_assets.workflow_routing_rules` as review-only evidence when drafting workflow policy candidates, and must not claim the policy was applied.

- [ ] **Step 2: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_llm_asset_candidate_generator.py -q
```

- [ ] **Step 3: Run fast regression**

Run:

```bash
scripts/test-fast.sh
```

- [ ] **Step 4: Self-Harness Improvement Gate**

Record the result in this plan. Expected:

- Prompt tests cover routing evidence and review-only workflow policy guidance.
- Parser accepts review-only workflow policy candidates under `.ai/`.
- No schema, runtime, or formal config mutation is introduced.
- Next candidate gap: task-brief-specific LLM routing recommendation.

- [ ] **Step 5: Commit**

Commit message:

```bash
git commit -m "feat: make asset candidates routing aware"
```
