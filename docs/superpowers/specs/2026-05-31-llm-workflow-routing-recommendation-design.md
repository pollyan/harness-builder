# LLM Workflow Routing Recommendation Design

## Context

North Star modules: Workflow Runtime Specification, Workflow Toolkit, Maturity & Evolution, and Intelligent Asset Candidate Generation.

Harness Builder now generates:

- fixed Workflow Skills: `lightweight`, `bugfix`, and `standard`;
- a deterministic `workflow_routing` policy in `harness-config.yaml`;
- detailed routing evidence in `maturity-evidence.yaml`;
- routing-aware LLM asset candidate prompt guidance.

The missing next step is task-specific workflow selection. The strategy says Harness Mapping should use task intent, risk, impact scope, confidence, required guides, sensors, and escalation conditions to choose Standard, Lightweight, or Bugfix. Current code exposes the policy but does not let an LLM evaluate a specific task brief against that policy.

## Current Gap

There is no structured, review-only way to ask Harness Builder:

> Given this task brief and the current Harness routing policy, which workflow should the host Runtime use and why?

Without this, downstream Runtime integration still has to interpret routing rules itself or rely on ad hoc prompting.

## Decision

Add a new review-only CLI command:

```bash
harness-builder-agent recommend-workflow --repo <repo> --task "<task brief>" [--task-id <id>]
```

The command will:

1. Read `.ai/harness-config.yaml` and `.ai/maturity-evidence.yaml`.
2. Call DeepSeek with a strict JSON prompt containing the task brief, workflow definitions, routing rules, and maturity evidence.
3. Validate the response with a Pydantic schema.
4. Reject selected workflows that are not configured.
5. Reject referenced routing rule IDs that do not exist.
6. Write review-only artifacts:
   - `.ai/review/workflow-routing-recommendation.yaml`
   - `.ai/review/workflow-routing-recommendation.md`

This command does not execute the selected workflow. It does not create Harness Map runtime artifacts and does not generate `.ai/task-runs`.

## Schema

The recommendation schema will include:

- `task_id`
- `task_brief`
- `recommended_workflow`
- `matched_rule_ids`
- `risk_level`
- `confidence`
- `rationale`
- `required_guides`
- `required_sensors`
- `human_confirmation_required`
- `review_status: pending_harness_maintainer_review`
- `evidence_sources`

## Boundaries

- Do not restore `run`.
- Do not execute workflow stages.
- Do not write `.ai/task-runs`.
- Do not modify `harness-config.yaml`.
- Do not auto-apply the recommendation to formal Harness assets.
- Do not fallback to deterministic task classification if DeepSeek fails.

## Acceptance Criteria

- Unit tests validate schema and parser behavior.
- Prompt tests prove the task brief, routing rules, and review-only boundary are included.
- Parser rejects unknown selected workflows.
- Parser rejects unknown routing rule IDs.
- Integration test proves CLI writes YAML/Markdown review artifacts with mocked LLM.
- Integration test proves CLI does not create `.ai/task-runs`.
- Engineering docs record that workflow recommendation is review-only and LLM-first.

## Assumptions

- The first implementation can be opt-in and review-only; host Runtime integration can consume the artifact later.
- Recommending a workflow for one task is materially different from executing that workflow, so it remains within Builder boundaries.
- The routing policy remains deterministic source of truth, while the LLM performs task-specific interpretation.

## Risks

- LLM may over-escalate tasks to `standard`. The recommendation remains review-only and includes confidence/rationale.
- A task brief may be too vague. The schema allows lower confidence and human confirmation.
- The command introduces another LLM call path, so tests must cover schema failure, unknown workflows, and no silent fallback.
