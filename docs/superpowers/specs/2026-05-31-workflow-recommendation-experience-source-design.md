# Workflow Recommendation Experience Source Design

## Context

`recommend-workflow` now produces review-only workflow routing recommendations, and benchmark validates those optional artifacts when present. The next gap is Experience Integration: `summarize-experience` does not collect workflow recommendation review artifacts, so downstream LLM summaries cannot learn recurring routing gaps, workflow escalation patterns, or task classification issues from them.

## Full-Plan Capability Module

This milestone belongs to **Experience Integration** and supports Workflow Toolkit Evolution. It connects review-only routing judgments to the experience learning loop while preserving the boundary that formal Harness assets are not automatically modified.

## Current Gap

- `.ai/review/workflow-routing-recommendation.yaml` is a structured review artifact.
- Experience summary already consumes pending improvements, maturity review, and asset candidates.
- Experience summary does not consume workflow recommendation artifacts.
- LLM prompts therefore cannot turn repeated workflow routing recommendations into `workflow_gap`, `risk_signal`, or `improvement_signal` findings.

## Design

Add `.ai/review/workflow-routing-recommendation.yaml` to the experience summarizer source list.

The implementation stays intentionally small:

1. `_collect_sources` includes the workflow recommendation YAML when it exists.
2. The integration test for `summarize-experience` writes a valid recommendation review artifact and asserts the fake LLM receives it as a source.
3. The LLM prompt contract remains review-only; the model can summarize findings but cannot claim changes were applied.
4. `docs/engineering/llm-contracts.md` documents that workflow recommendation review artifacts are optional Experience Summary inputs.

## Decisions

- Only YAML is added as a source in this milestone. The YAML carries the machine-readable judgment and evidence references; Markdown is human-facing review context and can be added later if needed.
- Missing recommendation artifacts remain valid. `summarize-experience` should not run `recommend-workflow` automatically or fabricate recommendation evidence.
- This milestone does not change `ExperienceIndex` counters. A future index enhancement can count workflow recommendation artifacts separately.

## Assumptions

- Workflow recommendation evidence can usefully inform `workflow_gap` and `improvement_signal` findings.
- Keeping the source optional avoids making task-level recommendation a required baseline step.
- The current source validation already prevents the LLM from citing unknown evidence paths.

## Risks

- If the recommendation artifact is malformed, summarize-experience currently passes source text to the LLM without parsing it first. This is acceptable for this milestone because benchmark now validates the artifact when present; a future enhancement can add pre-parse validation before summarization.

## Acceptance Criteria

- `_collect_sources` returns `.ai/review/workflow-routing-recommendation.yaml` when the file exists.
- `summarize-experience` passes the workflow recommendation source to the LLM summarizer.
- The existing review-only prompt boundary remains visible in unit tests.
- No `.ai/task-runs` are generated.
- No formal Guides, Sensors, Workflow Skills, or `harness-config.yaml` are modified.

## Self-Harness Gate Expectation

This milestone should update LLM contract documentation and tests so new review artifacts remain connected to the learning loop instead of becoming isolated files.
