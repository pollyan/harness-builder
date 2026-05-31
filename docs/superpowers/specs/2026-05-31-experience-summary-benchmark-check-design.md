# Experience Summary Benchmark Check Design

## Context

Benchmark already validates optional LLM review artifacts for maturity review, asset candidates, and workflow recommendation when those files exist. Experience Summary is also a review-only LLM artifact, but benchmark currently does not inspect `.ai/experience/experience-summary.yaml` or `.md`.

## Capability Module

- North Star module: Benchmark / Review Intelligence.
- Supporting modules: Experience & Self-Improve, Maturity & Evolution.

## Current State Gap

- `summarize-experience` can write `.ai/experience/experience-summary.yaml` and `.md`.
- `ExperienceSummaryReport` has a Pydantic schema and review-only status.
- Parser-level tests reject invalid LLM evidence references, but benchmark does not protect persisted artifacts from manual edits, partial files, or malformed generated output.
- `docs/engineering/sensor-and-gate-rules.md` only names maturity review and asset candidates as optional LLM review artifacts.

## Assumptions And Decisions

- Experience Summary remains optional. Benchmark must pass when neither summary file exists.
- If either summary file exists, benchmark must validate the pair as a review-only artifact.
- Validation should cover schema, `pending_harness_maintainer_review`, `.ai/` evidence sources, and stable Markdown sections.
- The check must not require `summarize-experience` during `init` or `benchmark`.

## Design

Add `content:experience-summary-artifact` to `_content_checks`.

Behavior:

1. If neither `.ai/experience/experience-summary.yaml` nor `.md` exists, pass with `present: false`.
2. If only one file exists, fail with `incomplete_experience_summary_artifact_pair`.
3. Parse YAML with `ExperienceSummaryReport`.
4. Fail if `review_status` is not `pending_harness_maintainer_review`.
5. Fail if any finding evidence source is outside `.ai/`.
6. Fail if Markdown lacks:
   - `# Experience Summary`
   - `## Summary`
   - `## Findings`
   - `## Warnings`

## Testing

Add integration tests in `tests/integration/test_benchmark_command.py`:

- Generated benchmark check list includes `content:experience-summary-artifact` and passes when absent.
- Valid summary YAML/Markdown pair passes.
- Outside-`.ai` evidence fails.
- Missing Markdown sections fail.

## Risks

- Benchmark can validate persisted artifact shape, not real semantic quality. That remains LLM prompt and schema responsibility.
- Experience Summary may have no findings. That is valid when evidence is sparse; benchmark should not force a finding count.

## Acceptance Criteria

- Benchmark includes an optional Experience Summary artifact check.
- Existing benchmark happy path still passes without requiring Experience Summary files.
- Invalid existing Experience Summary artifacts make benchmark fail with actionable error ids.
- Engineering gate docs describe the optional artifact contract.
