# Experience Summary Source Index Prompt Design

## Context

Experience Summary already receives `experience_index` and raw `.ai` source text. Recent source-aware work made maturity review and asset candidate generation explicitly consume structured source metadata, but the Experience Summary prompt still treats the index as ordinary payload. That leaves the model under-guided on how to use `experience_index.sources` and how to distinguish review-only evidence from applied Harness changes.

## Capability Module

- North Star module: Experience & Self-Improve.
- Supporting modules: Maturity & Evolution, Benchmark / Review Intelligence.

## Current State Gap

- `ExperienceIndex.sources` records `path`, `kind`, and `item_count`.
- `summarize_experience_with_llm` includes the index in the prompt payload.
- The prompt contract does not explicitly say that `experience_index.sources` is a review-only source index.
- The prompt contract does not tell the model to cite only provided source paths or avoid inventing missing source paths.

## Assumptions And Decisions

- No schema change is required because `ExperienceSummaryReport` already validates `evidence_sources`.
- The change should stay prompt-contract only; Python remains responsible for validating `.ai/` paths and unknown evidence sources.
- Workflow recommendation review artifacts can inform `workflow_gap` or `improvement_signal` findings, but they are not applied routing policies.
- Runtime `.ai/task-runs` remains host Runtime data. Builder may summarize it if present, but must not generate it.

## Design

Update `build_experience_summary_messages` so the schema contract explicitly instructs the LLM to:

1. Use `experience_index.sources` as a review-only source index.
2. Inspect source `path`, `kind`, and `item_count` to understand available evidence.
3. Ground `findings[].evidence_sources` in paths present in the provided source map.
4. Do not invent missing source paths.
5. Do not treat review-only source entries as applied Guides, Sensors, Workflow Skills, harness-config changes, or task executions.

## Testing

Add a prompt-contract unit test that builds an index with source details and asserts the prompt includes:

- `experience_index.sources`
- `path, kind, and item_count`
- `.ai/review/workflow-routing-recommendation.yaml`
- `review-only source index`
- `Do not invent missing source paths`

Run the focused Experience Summary unit tests before broader verification.

## Risks

- Prompt wording cannot fully prevent hallucination. The existing parser still enforces `.ai/` paths and rejects unknown evidence sources.
- Overly strict prompt language could reduce useful synthesis. The prompt should require grounded evidence without forcing every finding to cite every available source.

## Acceptance Criteria

- Experience Summary prompt contract explicitly covers `experience_index.sources`.
- Tests prove the prompt carries source path, kind, item count, review-only, and no-invention guidance.
- LLM engineering docs document the source-aware Experience Summary contract.
- No new `run` behavior or `.ai/task-runs` generation is introduced.
