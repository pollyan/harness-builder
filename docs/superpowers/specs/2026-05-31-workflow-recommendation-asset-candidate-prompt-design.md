# Workflow Recommendation Asset Candidate Prompt Design

## Context

Harness Builder now has a review-only workflow recommendation chain:

- `recommend-workflow` writes `.ai/review/workflow-routing-recommendation.yaml`.
- Experience Index and Maturity Evidence count that review source.
- `improve` emits `experience-workflow-recommendation-review` when workflow recommendation review evidence exists.
- The LLM asset candidate generator already supports `workflow_policy` drafts and routing-aware evidence.

The remaining gap is semantic specificity. The LLM prompt does not explicitly connect the deterministic `experience-workflow-recommendation-review` candidate to the workflow recommendation artifact that caused it. That makes it easier for the LLM to produce a generic candidate instead of a concrete review-only routing policy draft.

## Capability Module

- North Star module: Experience & Self-Improve, Maturity & Evolution, Workflow Toolkit.
- Current milestone: Intelligent Asset Candidate Generation.

## Assumptions And Decisions

- The workflow recommendation artifact is review-only evidence, not proof of an applied workflow change.
- The deterministic improvement candidate remains broad by design; the LLM should add semantic specificity.
- No schema change is required. Existing `AssetCandidateDraft.kind == "workflow_policy"` and `suggested_path == ".ai/harness-config.yaml"` are sufficient.
- The prompt should guide the LLM to use `.ai/review/workflow-routing-recommendation.yaml` when it appears in `maturity_evidence.maturity_inputs` or improvement candidate evidence sources.
- The output must remain `pending_harness_maintainer_review` and must not claim the routing policy was applied.

## Design

Update `build_asset_candidate_messages` so the schema contract contains a dedicated instruction for `experience-workflow-recommendation-review`.

When that improvement candidate exists, the LLM should:

1. inspect the recommendation evidence from `.ai/review/workflow-routing-recommendation.yaml`;
2. compare it with `maturity_evidence.harness_assets.workflow_routing_rules`;
3. prefer a `workflow_policy` draft targeting `.ai/harness-config.yaml` when routing rules, escalation conditions, required guides, required sensors, or human confirmation points need adjustment;
4. keep the draft review-only with `review_status: pending_harness_maintainer_review`;
5. never describe the candidate as an applied config change or executed workflow.

## Risks

- Prompt-only changes can be overfit. The unit test should assert stable contract phrases and evidence payload wiring, not an exact prompt blob.
- The LLM may still defer the candidate if maturity review says defer. That is acceptable; the prompt should say "prefer" when the candidate is supported or needs revision, not force invalid output.

## Acceptance Criteria

- Unit test proves the prompt includes the deterministic candidate id, workflow recommendation artifact path, `workflow_policy`, `.ai/harness-config.yaml`, and review-only status guidance.
- Existing asset candidate schema parsing tests still pass.
- Engineering docs record that this prompt contract consumes workflow recommendation reviews as review-only evidence.
