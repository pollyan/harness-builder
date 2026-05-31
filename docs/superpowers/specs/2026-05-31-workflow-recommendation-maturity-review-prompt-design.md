# Workflow Recommendation Maturity Review Prompt Design

## Context

The workflow recommendation feedback loop now flows through several assets:

1. `recommend-workflow` writes `.ai/review/workflow-routing-recommendation.yaml`.
2. Experience and maturity evidence expose the recommendation as review-only evidence.
3. `improve` emits `experience-workflow-recommendation-review`.
4. LLM asset candidate generation now knows how to turn that candidate into a review-only `workflow_policy` draft.

The upstream LLM maturity reviewer still lacks an explicit instruction for this candidate. It receives the candidate and the evidence payload, but the prompt only gives generic review guidance. That can produce vague support/defer decisions and weaken the downstream asset candidate step.

## Capability Module

- North Star module: Experience & Self-Improve, Maturity & Evolution, Workflow Toolkit.
- Current milestone: LLM Maturity Reviewer + Intelligent Asset Candidate Generation.

## Assumptions And Decisions

- The reviewer must not treat workflow recommendation evidence as executed workflow history or an applied config change.
- The reviewer should inspect `.ai/review/workflow-routing-recommendation.yaml` when present in maturity inputs or candidate evidence sources.
- The reviewer should compare recommendation evidence with current `maturity_evidence.harness_assets.workflow_routing_rules`.
- The reviewer may return `support`, `revise`, or `defer`; the prompt should not force approval.
- No schema change is required. The existing `MaturityReviewReport` can express rationale, risks, checks, and evidence sources.

## Design

Update `build_maturity_review_messages` with a dedicated clause for `experience-workflow-recommendation-review`.

When this candidate exists, the reviewer should:

1. use `.ai/review/workflow-routing-recommendation.yaml` as review-only evidence;
2. judge whether current routing rules already cover the recommendation;
3. prefer `support` or `revise` when evidence points to a routing policy review;
4. include concrete risks and acceptance checks for any future `workflow_policy` draft;
5. keep the review output read-only and avoid claiming formal Harness changes were applied.

## Risks

- Prompt-only behavior cannot guarantee every LLM output. Unit tests should prove the contract is present, and schema validation still enforces structure.
- The reviewer may defer if evidence is insufficient. That is valid when the recommendation artifact is absent or inconsistent.

## Acceptance Criteria

- Unit test proves the maturity review prompt includes the deterministic candidate id, workflow recommendation artifact path, routing evidence, review-only semantics, and decision guidance.
- Existing maturity reviewer parser tests still pass.
- `docs/engineering/llm-contracts.md` documents the review-only workflow recommendation reviewer contract.
