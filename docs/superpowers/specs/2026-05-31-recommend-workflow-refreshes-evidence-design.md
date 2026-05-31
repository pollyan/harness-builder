# Recommend Workflow Refreshes Evidence Design

## Context

`recommend-workflow` writes review-only workflow recommendation artifacts. Later milestones made those artifacts visible to Experience Index, Maturity Evidence, Experience maturity scoring, and deterministic `improve` candidates. However, the command that creates the recommendation does not refresh those derived artifacts after writing the recommendation.

That means the recommendation can exist while `.ai/experience/experience-index.yaml` and `.ai/maturity-evidence.yaml` remain stale until another command runs.

## Full-Plan Capability Module

This milestone belongs to **Experience Integration**, **Maturity Evidence Pack**, and **Observability**. It closes the loop so explicit workflow recommendation output immediately becomes structured evidence.

## Current Gap

- `recommend-workflow` writes `.ai/review/workflow-routing-recommendation.yaml`.
- `experience-index.yaml` can count that artifact, but is not refreshed by `recommend-workflow`.
- `maturity-evidence.yaml` can expose the count, but is not refreshed after the recommendation is written.
- CLI trace records only the recommendation files, not the refreshed evidence artifacts.

## Design

After writing workflow recommendation YAML and Markdown:

1. Refresh `.ai/experience/experience-index.yaml` with `write_experience_index(ai)`.
2. Refresh `.ai/maturity-score.yaml`, `.ai/maturity-report.md`, and `.ai/maturity-evidence.yaml` with `assess_maturity(root)`.
3. Update the CLI trace artifact list to include refreshed `experience-index.yaml`, `maturity-score.yaml`, and `maturity-evidence.yaml`.

The command still does not execute a workflow, generate `.ai/task-runs`, or apply formal routing policy changes.

## Decisions

- Refresh maturity after writing the recommendation so `maturity-evidence.yaml` sees the updated index.
- Keep this deterministic. No additional LLM call is introduced.
- Do not run `improve` automatically. Recommendation evidence becomes available, but candidate generation remains explicit.

## Assumptions

- Derived evidence refresh is part of Builder observability, not task runtime execution.
- Re-running deterministic maturity assessment after a recommendation is acceptable because the command already depends on maturity evidence.

## Risks

- `recommend-workflow` now updates more files than before. These are derived evidence/report files, not formal Harness routing policy.
- If the recommendation artifact is invalid, `write_experience_index` will fail through schema validation. This is desired.

## Acceptance Criteria

- Running `recommend-workflow` updates `experience-index.yaml` with `workflow_recommendation_count=1`.
- Running `recommend-workflow` updates `maturity-evidence.yaml` with `experience.workflow_recommendation_count=1`.
- CLI trace records recommendation artifacts and refreshed evidence artifacts.
- `.ai/task-runs` is not created.
- No formal `harness-config.yaml` changes are applied.

## Self-Harness Gate Expectation

This milestone should add integration coverage proving recommendation evidence is immediately visible to downstream maturity/improve commands.
