# Maturity Review Benchmark Check Design

## Context

Benchmark now validates optional workflow recommendation reviews and asset candidate reviews. The remaining explicit LLM review artifact without benchmark validation is:

```text
.ai/review/maturity-review.yaml
.ai/review/maturity-review.md
```

This artifact is central to the Self-Improve loop because it turns deterministic improvement candidates into LLM-reviewed support/revise/defer judgments. If it is malformed, references unknown candidates, points to evidence outside `.ai/`, or loses stable Markdown sections, downstream asset candidate generation can be misled without benchmark surfacing the issue.

## Capability Module

- North Star module: Benchmark / Review Intelligence.
- Supporting modules: LLM Maturity Reviewer, Maturity & Evolution, Governance & Auditability.

## Assumptions And Decisions

- Maturity review artifacts are optional. Baseline benchmark should pass when they are absent.
- If YAML or Markdown exists, both must be present and valid.
- Schema validation uses `MaturityReviewReport`.
- Cross-file validation requires every `candidate_reviews[].candidate_id` to exist in `.ai/improvement-candidates.yaml`.
- Evidence sources in candidate reviews must stay under `.ai/`.
- Markdown must retain stable sections: Summary, Candidate Reviews, Missing Candidates, Global Risks.
- Benchmark does not judge whether the LLM decision is semantically correct; it validates contract integrity and review-only auditability.

## Design

Add `_maturity_review_artifact_check(ai)` to `benchmark.py` and include it in `_content_checks`.

The check returns:

- `id: content:maturity-review-artifact`;
- `present: false`, `passed: true` when neither file exists;
- `present: true`, `passed: false` with errors for incomplete pairs, schema failures, unknown candidate ids, evidence outside `.ai/`, or missing Markdown sections;
- `candidate_review_count` for auditability.

## Risks

- Older Harnesses with only YAML or only Markdown will fail benchmark once the partial artifact exists. That is intended because partial review artifacts are misleading.
- This milestone does not change the LLM reviewer prompt or output schema.

## Acceptance Criteria

- Benchmark report includes `content:maturity-review-artifact`.
- Absent maturity review artifacts pass as optional with `present: false`.
- Valid YAML and Markdown pair passes.
- Unknown candidate id fails.
- Evidence source outside `.ai/` fails.
- Missing Markdown sections fail.
- Engineering docs mention maturity review artifacts in optional LLM review artifact validation.
