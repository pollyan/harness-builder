# Experience Source Aware Maturity Design

## Context

Experience Index and Maturity Evidence now expose workflow recommendation review evidence through `workflow_recommendation_count`. However, the deterministic maturity model still scores the Experience dimension by checking only whether `.ai/experience/pending-improvements.md` exists.

This means the maturity report can miss a stronger signal: review-only workflow recommendations, maturity reviews, and asset candidates are structured experience sources that should lift the Experience dimension beyond a bare placeholder file.

## Full-Plan Capability Module

This milestone belongs to **Maturity Model v2** and **Experience Integration**. It connects structured experience source counts to the maturity score while preserving the rule that formal Harness assets are not auto-applied.

## Current Gap

- `experience-index.yaml` can now count workflow recommendation review artifacts.
- `maturity-evidence.yaml` can expose the count.
- `maturity-score.yaml` does not use the index.
- Experience dimension evidence remains too coarse for maturity-driven improve.

## Design

Update `_experience_dimension(ai)` in `maturity_model.py` to read `.ai/experience/experience-index.yaml` when present.

Scoring:

- `L0`: no experience baseline exists.
- `L1`: experience files or index exist, but there are no counted experience signals.
- `L2`: the index has review-derived or runtime-derived signals:
  - pending improvements;
  - asset candidates;
  - maturity reviews;
  - workflow recommendation reviews;
  - runtime task runs.

The dimension should include evidence summaries for all counts. It should keep the runtime-derived blocker because task outcome ingestion still belongs to the host Runtime and remains absent in current Builder-only flows.

## Decisions

- Do not introduce `L3` or `L4` changes in this milestone. Those require real Runtime task histories, trend analysis, and confirmed feedback loops.
- Do not make workflow recommendation review a required artifact. Missing count remains valid and simply does not lift the Experience dimension.
- Do not change overall maturity caps in this milestone.

## Assumptions

- Review-only artifacts are legitimate experience signals because they represent maintainable knowledge that can feed later summarization and candidate generation.
- `experience-index.yaml` is the stable source for deterministic Experience scoring.
- Legacy Harness directories without an index should keep the existing pending-file behavior.

## Risks

- Experience dimension may move from L1 to L2 after review artifacts are generated. That is intentional because the project has more than placeholder experience assets.
- The current level names are still coarse. Future Maturity Model work can split review-derived, runtime-derived, and confirmed-applied experience into more precise levels.

## Acceptance Criteria

- Maturity model reads `ExperienceIndex` when present.
- A valid index with `workflow_recommendation_count=1` lifts Experience dimension to `L2`.
- Experience dimension evidence mentions workflow recommendation reviews.
- Existing legacy pending-only behavior remains compatible.
- No `.ai/task-runs` are generated.

## Self-Harness Gate Expectation

This milestone should add direct unit coverage for the maturity model and update engineering docs so future scoring changes do not ignore structured experience sources.
