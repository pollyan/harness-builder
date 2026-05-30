# Workflow Recommendation Experience Index Design

## Context

Workflow recommendation review artifacts now have three pieces of coverage:

- `recommend-workflow` generates `.ai/review/workflow-routing-recommendation.yaml`.
- `benchmark` validates the optional review artifact when present.
- `summarize-experience` can feed the YAML into the LLM experience summarizer.

The remaining gap is deterministic observability. `.ai/experience/experience-index.yaml` and `.ai/maturity-evidence.yaml` do not expose whether workflow recommendation review evidence exists. That means maturity-driven improve and LLM reviewers can receive the raw source but cannot see a stable evidence count in the structured maturity pack.

## Full-Plan Capability Module

This milestone belongs to **Experience Integration** and **Maturity Evidence Pack**. It makes workflow recommendation review evidence visible to the structured Self-Improve loop without applying formal Harness changes.

## Current Gap

- `ExperienceIndex.sources` supports pending improvements, maturity reviews, asset candidates, runtime task runs, and manual experience.
- It has no source kind for workflow recommendation review artifacts.
- `ExperienceEvidence` has counts for asset candidates, maturity reviews, runtime task runs, and summary findings.
- It has no workflow recommendation count.
- `MATURITY_INPUTS` omits `.ai/review/workflow-routing-recommendation.yaml`.

## Design

Add deterministic workflow recommendation review accounting:

1. Extend `ExperienceSource.kind` with `workflow_recommendation`.
2. Add `workflow_recommendation_count` to `ExperienceIndex`.
3. `build_experience_index(ai)` counts `.ai/review/workflow-routing-recommendation.yaml` as one review source when present and schema-valid.
4. Extend `ExperienceEvidence` with `workflow_recommendation_count`.
5. `collect_maturity_evidence(ai)` copies the count from `experience-index.yaml` when present.
6. Add `.ai/review/workflow-routing-recommendation.yaml` to `MATURITY_INPUTS`.
7. Update `docs/engineering/init-workflow.md` so the output contract says experience evidence includes workflow recommendation review statistics.

## Decisions

- Count is `0` or `1` in this milestone because the current command writes one latest recommendation artifact.
- If the YAML exists but is invalid, index construction should fail through schema validation rather than silently counting it.
- This milestone does not add a history directory for multiple recommendations. That is a future Runtime/Experience Store concern.
- This milestone does not modify maturity scoring thresholds. It only improves evidence visibility for later reviewers and candidate generation.

## Assumptions

- A workflow recommendation review artifact is part of review-only experience evidence, not a formal workflow execution result.
- Structured counts make future maturity review prompts more reliable than raw source text alone.
- Backward compatibility is preserved because the new schema fields default to `0`.

## Risks

- Existing malformed recommendation artifacts may now fail index refresh. This is intentional because silent acceptance would pollute maturity evidence.
- The single-artifact count may eventually be too coarse. Future work can introduce a recommendation history store.

## Acceptance Criteria

- `ExperienceIndex` accepts `workflow_recommendation` source kind and `workflow_recommendation_count`.
- `build_experience_index` records workflow recommendation source and count when a valid YAML artifact exists.
- `collect_maturity_evidence` exposes `experience.workflow_recommendation_count`.
- `maturity_inputs` includes `.ai/review/workflow-routing-recommendation.yaml`.
- Existing flows without recommendation artifacts keep count `0`.
- No `.ai/task-runs` are generated and no formal Harness assets are modified.

## Self-Harness Gate Expectation

This milestone should improve structured observability for the Self-Improve loop and update tests/docs for the new evidence contract.
