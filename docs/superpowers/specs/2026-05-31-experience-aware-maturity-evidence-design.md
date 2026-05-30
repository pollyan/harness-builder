# Experience-aware Maturity Evidence Design

## Context

North Star module: Experience & Self-Improve plus Maturity & Evolution.

The current Builder now writes `.ai/experience/experience-index.yaml`, but `.ai/maturity-evidence.yaml` still reads Experience mostly from `.ai/experience/pending-improvements.md`. That means downstream `improve`, LLM maturity review, and asset candidate generation cannot distinguish a project that has only pending bullets from one that also has reviewed maturity judgments, generated draft assets, or host Runtime task-run evidence.

## Gap

The Experience Index is a machine contract, but it is not yet part of the maturity evidence contract. This weakens the self-improve loop because maturity scoring and LLM reviewers see less context than the Builder has already produced.

## Decision

Add Experience Index awareness to `MaturityEvidencePack.experience`.

The implementation will keep the existing pending fields for compatibility and add explicit counts:

- `has_experience_index`
- `asset_candidate_count`
- `maturity_review_count`
- `runtime_task_run_count`
- `experience_file_count`

`maturity_inputs` will include `.ai/experience/experience-index.yaml`. When the index is present, maturity evidence should use it as the authoritative summary. When the index is absent, maturity evidence should retain current behavior by counting pending improvements directly. This is not a silent fallback from failed LLM behavior; it is compatibility with older generated Harness directories that predate the index contract.

## Boundaries

- Do not generate `.ai/task-runs`.
- Do not restore or depend on `harness-builder-agent run`.
- Do not auto-apply reviewed asset candidates to formal Guides, Sensors, Workflow Skills, or config.
- Do not introduce new LLM calls in this milestone.

## Data Flow

```text
.ai/experience/experience-index.yaml
  -> collect_maturity_evidence(...)
  -> MaturityEvidencePack.experience
  -> maturity-score.yaml / improvement-candidates.yaml / LLM review context
```

If the index is missing:

```text
.ai/experience/pending-improvements.md
  -> collect_maturity_evidence(...)
  -> MaturityEvidencePack.experience
```

## Acceptance Criteria

- `MaturityEvidencePack` schema accepts and exposes the new Experience fields.
- `collect_maturity_evidence` reads `.ai/experience/experience-index.yaml` when present.
- Older `.ai` directories without an index still produce valid maturity evidence from `pending-improvements.md`.
- `maturity_inputs` includes `.ai/experience/experience-index.yaml`.
- Unit tests cover schema validation, index-backed collection, and legacy pending-only collection.
- Fast regression passes before commit.

## Assumptions

- Experience Index is deterministic evidence, so Python should parse and validate it before use.
- Counts are sufficient for this milestone; semantic extraction from Experience Markdown remains future work.
- The host Runtime owns task-level `.ai/task-runs`; Builder only counts directories if they exist.

## Risks

- If maturity logic later needs qualitative signals from Experience Markdown, counts alone will be insufficient. That should be handled by a later LLM-based Experience summarizer, not by this schema plumbing milestone.
- Backward compatibility with older generated Harness directories requires keeping the pending-only path until all generated fixtures include Experience Index.
