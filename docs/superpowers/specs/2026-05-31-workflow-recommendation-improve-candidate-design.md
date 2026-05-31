# Workflow Recommendation Improve Candidate Design

## Context

Harness Builder now records workflow recommendation review artifacts through benchmark, Experience Summary, Experience Index, Maturity Evidence, and Experience maturity scoring. The remaining gap is Maturity-driven Improve: `generate_improvements` does not create a concrete follow-up candidate when maturity evidence says workflow recommendation reviews exist.

Without this follow-up, routing recommendations can be observed but not turned into a reviewable improvement path for `.ai/harness-config.yaml`.

## Full-Plan Capability Module

This milestone belongs to **Maturity-driven Improve** and **Experience Integration**. It turns structured workflow recommendation evidence into a review-only workflow policy improvement candidate.

## Current Gap

- `maturity-evidence.yaml` exposes `experience.workflow_recommendation_count`.
- `maturity_inputs` includes `.ai/review/workflow-routing-recommendation.yaml`.
- `generate_improvements` only creates candidates from generic maturity next steps, blocking caps, and task-run warnings.
- No candidate tells the Harness Maintainer to review routing recommendations against `harness-config.yaml`.

## Design

Add one deterministic candidate when `evidence_pack.experience.workflow_recommendation_count > 0`:

- id: `experience-workflow-recommendation-review`
- type: `workflow_policy_update`
- target: `.ai/harness-config.yaml`
- target_dimension: `workflow`
- priority: `medium`
- confidence: `medium`
- evidence includes the recommendation count and review-only boundary.
- evidence_sources includes `.ai/maturity-evidence.yaml` and `.ai/review/workflow-routing-recommendation.yaml` when available through `maturity_inputs`.
- acceptance checks require the candidate to stay pending review and require benchmark workflow recommendation review checks to remain valid.

The candidate does not apply routing changes. It creates a bridge for `review-maturity` and `generate-asset-candidates` to produce review-only workflow policy drafts later.

## Decisions

- Generate a deterministic candidate instead of directly changing `harness-config.yaml`.
- Keep priority `medium` because one latest recommendation is evidence, not repeated trend analysis.
- Target the workflow dimension because the actionable asset is routing policy.
- Do not require the recommendation artifact to exist in every project.

## Assumptions

- A workflow recommendation review artifact means a Harness Maintainer should inspect whether routing policy should be adjusted or whether the recommendation only validated existing policy.
- Future repeated recommendation history can raise priority; current single-artifact signal should stay conservative.

## Risks

- The deterministic candidate may be broad. That is acceptable because later LLM maturity review and asset candidate generation add semantic specificity.
- If `maturity_inputs` lacks the recommendation path, the candidate still references maturity evidence and records the count; tests cover the normal path with the recommendation source present.

## Acceptance Criteria

- `_candidates` emits `experience-workflow-recommendation-review` when `workflow_recommendation_count > 0`.
- The candidate is `workflow_policy_update`, targets `.ai/harness-config.yaml`, and requires human confirmation.
- The candidate includes `.ai/review/workflow-routing-recommendation.yaml` in evidence sources when present.
- No candidate is emitted when the count is zero.
- No formal Harness assets are modified by this candidate.

## Self-Harness Gate Expectation

This milestone should add focused unit coverage and update engineering docs so workflow recommendation review evidence remains connected to the improvement loop.
