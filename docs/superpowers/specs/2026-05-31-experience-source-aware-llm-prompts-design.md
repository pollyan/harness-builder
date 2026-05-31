# Experience Source Aware LLM Prompts Design

## Context

`maturity-evidence.yaml` now preserves `experience.sources` from `experience-index.yaml`. That gives downstream LLM steps a structured index of review-only evidence paths, including maturity reviews, asset candidates, workflow recommendations, pending improvements, and runtime task-run directories.

The current maturity review and asset candidate prompts include the full evidence payload, but they do not explicitly tell the LLM how to use `maturity_evidence.experience.sources`. Without prompt guidance, the model may continue to reason from aggregate counts and miss the concrete review source paths.

## Capability Module

- North Star module: Experience & Self-Improve.
- Supporting modules: LLM Maturity Reviewer, Intelligent Asset Candidate Generation, Maturity & Evolution.

## Assumptions And Decisions

- `maturity_evidence.experience.sources` is an index of available review/evidence artifacts, not proof that any review-only candidate has been applied.
- LLM maturity review should use source details to ground `evidence_sources`, risks, and defer/revise decisions.
- LLM asset candidate generation should use source details to ground draft evidence and to avoid inventing review artifacts that are not present.
- No schema change is required. Existing prompt payloads already include `maturity_evidence.experience.sources`.
- The change should be tested at the prompt-contract level, not by relying on real LLM behavior.

## Design

Update both prompt contracts:

1. `build_maturity_review_messages`
   - Tell the reviewer to inspect `maturity_evidence.experience.sources`.
   - Use `path`, `kind`, and `item_count` to identify available review-only evidence.
   - Prefer citing source paths from the source index in `candidate_reviews[].evidence_sources`.
   - Do not treat source entries as applied Harness changes.

2. `build_asset_candidate_messages`
   - Tell the asset candidate generator to inspect `maturity_evidence.experience.sources`.
   - Use source `kind` to locate maturity review, asset candidate, workflow recommendation, pending improvement, or runtime evidence.
   - Ground candidate `evidence_sources` in source paths that are present.
   - Do not invent missing source paths or treat review-only sources as applied rules.

## Risks

- Prompt-only changes are not hard guarantees. Unit tests verify the prompt contract, while schema and benchmark continue to enforce deterministic boundaries.
- Overly broad prompt text could make the LLM over-cite sources. The wording should say "prefer" and "ground", not force every output to cite every source.

## Acceptance Criteria

- Maturity review prompt test proves the contract mentions `maturity_evidence.experience.sources`, `path`, `kind`, `item_count`, and review-only semantics.
- Asset candidate prompt test proves the same contract exists for draft generation.
- LLM engineering docs document the source-aware prompt contract.
- No formal Harness asset application behavior is introduced.
