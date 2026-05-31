# Asset Candidate Benchmark Review Check Design

## Context

Harness Builder now generates several review-only LLM artifacts:

- workflow routing recommendations;
- maturity reviews;
- asset candidate drafts.

Benchmark already validates optional workflow recommendation review artifacts when present. It does not yet validate optional `review/asset-candidates.yaml` and its Markdown companions. That leaves a regression gap: malformed asset candidate drafts, unknown source candidate references, evidence outside `.ai/`, missing Markdown review files, or missing review-only status could exist without benchmark surfacing the issue.

## Capability Module

- North Star module: Benchmark / Review Intelligence.
- Supporting modules: Intelligent Asset Candidate Generation, Experience & Self-Improve, Governance & Auditability.

## Assumptions And Decisions

- Asset candidate artifacts are optional. Baseline benchmark must pass when they are absent.
- If any asset candidate artifact is present, benchmark should treat the artifact group as present and validate it.
- Benchmark should not apply candidate drafts or require them to be accepted.
- The machine contract is `AssetCandidateReport`; schema validation should enforce `review_status: pending_harness_maintainer_review`.
- Benchmark should additionally validate cross-file references that schema alone cannot enforce:
  - source candidate ids must exist in `.ai/improvement-candidates.yaml`, unless the source review decision is `missing`;
  - evidence sources must stay under `.ai/`;
  - suggested paths must stay under `.ai/`;
  - Markdown review files must be present and contain stable review sections.

## Design

Add `_asset_candidate_review_check(ai)` to `benchmark.py` and include it in `_content_checks`.

The check returns:

- `id: content:asset-candidate-review`;
- `present: false` and `passed: true` when no asset candidate YAML or Markdown files exist;
- `present: true` and `passed: false` when the artifact set is incomplete or invalid;
- `candidate_count` and `errors` for auditability.

The expected artifact set when present is:

```text
.ai/review/asset-candidates.yaml
.ai/review/asset-candidate-guides.md
.ai/review/asset-candidate-sensors.md
.ai/review/asset-candidate-workflows.md
```

Required Markdown sections:

- `### Rationale`
- `### Draft Content`
- `### Evidence Sources`
- `### Acceptance Checks`

## Risks

- Requiring Markdown companions could fail if older generated Harnesses have only YAML. That is acceptable for benchmark review intelligence because optional review artifacts should be complete once present.
- This does not validate semantic quality of draft content. That remains an LLM/review intelligence concern for later milestones.

## Acceptance Criteria

- Benchmark report includes `content:asset-candidate-review`.
- Absent asset candidate artifacts pass as optional with `present: false`.
- Valid YAML plus Markdown companions pass with `present: true`.
- Unknown `source_candidate_id` fails.
- Evidence or suggested paths outside `.ai/` fail.
- Missing Markdown companions or stable sections fail.
- Engineering docs mention optional asset candidate review artifacts are benchmark-validated when present.
