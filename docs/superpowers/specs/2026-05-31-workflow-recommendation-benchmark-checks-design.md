# Workflow Recommendation Benchmark Checks Design

## Context

Harness Builder now has `recommend-workflow`, which uses LLM judgment to produce review-only workflow routing recommendations in `.ai/review/workflow-routing-recommendation.yaml` and `.md`.

The current benchmark validates static Harness assets, workflow routing policy, maturity routing evidence, and core review candidates. It does not validate optional workflow recommendation artifacts. That leaves a gap: a generated recommendation can drift from `harness-config.yaml`, lose its review-only boundary, or point to non-Harness evidence without benchmark noticing.

## Full-Plan Capability Module

This milestone belongs to **Benchmark / Review Intelligence** and supports the broader Workflow Toolkit Evolution loop. It strengthens the review layer around LLM-generated routing judgments without restoring runtime execution.

## Current Gap

- `recommend-workflow` writes structured review artifacts.
- `WorkflowRecommendationReport` has a schema and unit tests.
- `benchmark` does not check those artifacts when they exist.
- `REQUIRED_FILES` should not include recommendation artifacts because `recommend-workflow` is an optional post-init review action.

## Design

Add optional benchmark checks for workflow recommendation artifacts:

1. If neither `.ai/review/workflow-routing-recommendation.yaml` nor `.md` exists, benchmark records an advisory-style check as passed with `present: false`.
2. If either file exists, benchmark validates both files as a pair.
3. YAML must parse through `WorkflowRecommendationReport`.
4. `recommended_workflow` must exist in `.ai/harness-config.yaml`.
5. Every `matched_rule_id` must exist in `harness-config.workflow_routing.rules`.
6. `review_status` must remain `pending_harness_maintainer_review`.
7. Every evidence source must stay under `.ai/`.
8. Markdown must contain stable sections that make review intent clear:
   - `# Workflow Routing Recommendation`
   - `## Task`
   - `## Recommended Workflow`
   - `## Matched Routing Rules`
   - `## Required Harness Assets`
   - `## Review Boundary`
9. The check must not create `.ai/task-runs`, execute any workflow, or modify formal Harness assets.

## Key Decisions

- The benchmark check is optional, not a required file gate, because recommendations are produced by a separate command.
- If one recommendation file exists without the other, benchmark fails the check. Partial review artifacts are unsafe.
- Python validates schema and cross-file references. LLM remains responsible only for generating the recommendation judgment.
- This milestone does not introduce an apply-review flow. Formal Harness changes remain out of scope.

## Assumptions

- Review artifacts under `.ai/review/` are part of Harness Builder's observable output surface.
- Optional artifacts should still be audited when present.
- Benchmark can fail for malformed optional review artifacts because malformed review artifacts can mislead a Harness Maintainer.

## Risks

- Existing projects with manually edited malformed recommendation files will see benchmark fail after this change. That is acceptable because the failure is explicit and actionable.
- The Markdown section contract may need future evolution. The initial set is intentionally small and review-focused.

## Acceptance Criteria

- Benchmark passes on existing init/benchmark fixture flow when no workflow recommendation exists.
- Benchmark includes `content:workflow-recommendation-review` with `present: false` in that case.
- Benchmark passes when a valid workflow recommendation YAML and Markdown pair exists.
- Benchmark fails when the recommendation references an unknown workflow.
- Benchmark fails when the recommendation references an unknown routing rule.
- Benchmark fails when the Markdown review sections are missing.
- Tests prove the check does not require `.ai/task-runs` and does not make recommendation files required.

## Self-Harness Gate Expectation

This milestone should update benchmark coverage and the sensor/gate engineering rule so future review-only LLM artifacts are not left outside validation.
