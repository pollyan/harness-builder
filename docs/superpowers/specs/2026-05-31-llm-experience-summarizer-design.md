# LLM Experience Summarizer Design

## Context

North Star modules: Experience & Self-Improve, Maturity & Evolution.

Harness Builder now creates Experience Markdown placeholders, an Experience Index, maturity evidence counters, LLM maturity reviews, and asset candidates. The remaining gap is semantic: downstream review and improvement flows can see counts, but they do not yet have a structured summary of repeated repair patterns, sensor feedback, workflow gaps, team preferences, or risk signals.

## Current Gap

The Experience Integration layer is count-aware but not meaning-aware. It can say that pending improvements, maturity reviews, and asset candidates exist, but cannot summarize what they imply.

This limits the self-improve loop because every later LLM call must re-read raw artifacts or operate without a stable semantic Experience artifact.

## Decision

Add an explicit `summarize-experience` command that runs an LLM semantic summarizer and writes review-only Experience summary artifacts:

- `.ai/experience/experience-summary.yaml`
- `.ai/experience/experience-summary.md`

The YAML is schema-validated and machine-consumed. The Markdown is for Harness Maintainers and later semantic context. Both outputs remain review-only and must not claim formal Guides, Sensors, Workflow Skills, or `harness-config.yaml` were changed.

## Output Contract

`experience-summary.yaml` will contain:

- `schema_version`
- `source: llm_experience_summary`
- `review_status: pending_harness_maintainer_review`
- `summary`
- `findings[]`
  - `id`
  - `kind`: `repair_pattern`, `sensor_feedback`, `team_preference`, `workflow_gap`, `risk_signal`, or `improvement_signal`
  - `title`
  - `summary`
  - `evidence_sources`
  - `confidence`
  - `suggested_follow_up`
- `warnings[]`

The parser will reject invalid JSON, schema errors, evidence paths outside `.ai/`, and evidence paths not provided to the LLM input.

## Inputs

The summarizer reads:

- `.ai/experience/experience-index.yaml`
- `.ai/experience/pending-improvements.md`
- `.ai/experience/project-experience.md`
- `.ai/experience/repair-patterns.md`
- `.ai/experience/sensor-feedback.md`
- `.ai/experience/team-preferences.md`
- `.ai/experience/deprecated-experience.md`
- `.ai/review/maturity-review.yaml`
- `.ai/review/asset-candidates.yaml`
- lightweight listings of `.ai/task-runs/<task-id>/` if host Runtime data exists

Missing optional files are omitted from the LLM input with no fabricated content. If the required `.ai` directory or Experience Index is missing, the command should build the deterministic index from current files before calling the LLM.

## Boundaries

- Do not restore or depend on `harness-builder-agent run`.
- Do not generate `.ai/task-runs`.
- Do not modify formal Guides, Sensors, Workflow Skills, or `harness-config.yaml`.
- Do not use deterministic text concatenation as a semantic fallback if DeepSeek fails.
- Do not make benchmark require `experience-summary.yaml` yet; `init` and benchmark should still pass without running this explicit command.

## Data Flow

```text
Experience Index + Experience Markdown + reviews + asset candidates
  -> LLM Experience Summarizer
  -> schema validation
  -> .ai/experience/experience-summary.yaml
  -> .ai/experience/experience-summary.md
  -> refreshed Experience Index
  -> maturity evidence can report summary availability
```

## Acceptance Criteria

- New Pydantic schema validates Experience Summary reports.
- LLM parser accepts valid strict JSON and rejects invalid JSON, invalid evidence paths, and unknown evidence sources.
- `summarize-experience` writes YAML and Markdown artifacts and records generation trace artifacts.
- The command does not create `.ai/task-runs`.
- Formal Guides remain unchanged after the command.
- Maturity evidence records whether an Experience Summary exists and how many findings it contains.
- Focused and fast regression tests pass before commit.

## Assumptions

- The first semantic Experience milestone should be explicit rather than hidden inside `improve`, because it adds a real LLM call and should fail visibly if DeepSeek is unavailable.
- Review-only Experience Summary is safe to regenerate because it is a derived artifact, not a formal rule promotion.
- Later milestones can feed this summary directly into maturity review prompts and asset candidate generation prompts.

## Risks

- LLM summaries may overgeneralize from sparse evidence. The schema requires evidence sources and confidence, and outputs remain pending review.
- Runtime task-run data is currently host-owned and may be absent. The summarizer must treat absence as a signal, not as an error.
