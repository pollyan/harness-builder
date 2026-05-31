# Experience Source Details In Maturity Evidence Design

## Context

Harness Builder now has a stronger review artifact chain:

- Experience Index records structured sources such as pending improvements, maturity review, asset candidates, workflow recommendation review, and runtime task runs.
- Benchmark validates optional review artifacts when present.
- Maturity Evidence exposes Experience counts to maturity review and improve.

The remaining gap is detail loss. `experience-index.yaml` has `sources`, but `maturity-evidence.yaml` collapses Experience to counts only. Downstream LLM review and improvement steps can see that asset candidates or maturity reviews exist, but the evidence pack itself does not expose which review source paths exist or what source type each path represents.

## Capability Module

- North Star module: Experience & Self-Improve.
- Supporting modules: Maturity & Evolution, LLM Maturity Reviewer, Intelligent Asset Candidate Generation.

## Assumptions And Decisions

- The source list should remain machine-readable and schema-validated.
- Reusing `ExperienceSource` avoids introducing a second subtly different source contract.
- Source details are evidence only. They must not imply that review-only artifacts were applied to formal Harness assets.
- Legacy Harnesses without `experience-index.yaml` keep the existing pending-improvements-only fallback and return an empty source list.
- This milestone does not change scoring behavior; it enriches evidence for future semantic steps.

## Design

Add `sources: list[ExperienceSource]` to `ExperienceEvidence`.

When `.ai/experience/experience-index.yaml` exists:

- validate it as `ExperienceIndex`;
- copy `index.sources` into `MaturityEvidencePack.experience.sources`;
- keep existing count fields unchanged.

When the index does not exist:

- keep current legacy count behavior;
- set `sources` to `[]`.

Update engineering docs so maturity evidence explicitly promises source path details, not only counts.

## Risks

- This changes the serialized `maturity-evidence.yaml` schema. The field is additive with a default, so old files remain parseable.
- Some downstream tests may compare exact dictionaries. Current tests mostly validate fields and should tolerate the additive field.

## Acceptance Criteria

- `collect_maturity_evidence` includes Experience source details from `experience-index.yaml`.
- The source list contains path, kind, and item_count for review artifacts.
- Legacy pending-only path keeps `sources == []`.
- Unit tests validate the new schema field.
- Engineering docs describe the source details contract.
