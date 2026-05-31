# Experience Summary Prompt Injection Design

## Context

North Star modules: Experience & Self-Improve, Maturity & Evolution.

Harness Builder now has a review-only LLM Experience Summary artifact:

- `.ai/experience/experience-summary.yaml`
- `.ai/experience/experience-summary.md`

Maturity evidence records whether that summary exists and how many findings it contains. However, the next LLM stages still do not receive the semantic findings directly:

- `review-maturity` passes maturity score, maturity evidence, and deterministic improvement candidates.
- `generate-asset-candidates` passes maturity score, maturity evidence, improvement candidates, and maturity review.

This means the new Experience Summary is visible as counts but not yet used as semantic context for intelligent review and candidate generation.

## Current Gap

The self-improve loop is semantically discontinuous:

```text
Experience Summary exists
  -> maturity evidence records count
  -> LLM review / asset candidate prompt does not include findings directly
```

The next step should let downstream LLMs use the summary without making the summary mandatory for older Harness directories or regular `init` output.

## Decision

Add optional Experience Summary injection to both downstream LLM prompt builders:

- `review_maturity_with_llm(..., experience_summary=None)`
- `generate_asset_candidates_with_llm(..., experience_summary=None)`

The orchestration layers will read and validate `.ai/experience/experience-summary.yaml` if it exists, then pass the parsed `ExperienceSummaryReport` to the prompt builder. If the file is absent, the commands continue with `null` summary. This is not a silent LLM fallback; it is optional context for a review-only artifact that is produced by a separate explicit command.

## Prompt Contract

Both prompt payloads will include:

```json
"experience_summary": null | { ... ExperienceSummaryReport ... }
```

Prompt instructions must say:

- Use Experience Summary findings when judging recurring gaps, sensor feedback, workflow gaps, and risk signals.
- Do not treat findings as formal rules.
- Do not claim summary findings have been applied.
- Prefer evidence-backed follow-up recommendations.

## Boundaries

- Do not run `summarize-experience` automatically from `review-maturity` or `generate-asset-candidates`.
- Do not make Experience Summary required for benchmark, init, improve, or review commands.
- Do not modify formal Guides, Sensors, Workflow Skills, or `harness-config.yaml`.
- Do not generate `.ai/task-runs`.
- Do not change LLM output schemas for maturity review or asset candidates in this milestone.

## Data Flow

```text
.ai/experience/experience-summary.yaml
  -> parsed as ExperienceSummaryReport when present
  -> review-maturity prompt payload experience_summary
  -> generate-asset-candidates prompt payload experience_summary
```

## Acceptance Criteria

- LLM maturity reviewer prompt contains `experience_summary` when provided.
- LLM asset candidate prompt contains `experience_summary` when provided.
- `review-maturity` reads an existing summary and passes it to `review_maturity_with_llm`.
- `generate-asset-candidates` reads an existing summary and passes it to `generate_asset_candidates_with_llm`.
- Commands still work when the summary file is absent.
- Tests prove formal Harness assets are not overwritten.
- Focused and fast regression tests pass before commit.

## Assumptions

- Optional summary injection is safer than auto-running the LLM summarizer because it avoids hidden extra LLM calls and preserves explicit failure behavior.
- The existing `MaturityReviewReport` and `AssetCandidateReport` schemas are sufficient; Experience Summary should influence reasoning, not force a new output schema yet.

## Risks

- LLM may over-weight sparse summary findings. Prompt text will explicitly say they are review-only findings, not formal rules.
- If the summary is stale relative to current candidates, downstream LLMs may use outdated context. Later work can add freshness metadata; this milestone only adds optional context plumbing.
