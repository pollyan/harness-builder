# Maturity Routing Evidence Detail Design

## Context

North Star modules: Maturity & Evolution, Experience & Self-Improve, and Workflow Runtime Specification.

Harness Builder now generates `workflow_routing` in `harness-config.yaml`. Maturity evidence currently records only the routing rule count and whether a standard escalation rule exists. That is enough for a hard gate, but not enough for intelligent review: LLM maturity review and LLM asset candidate generation receive `maturity-evidence.yaml`, yet they cannot see which workflow rules exist, what triggers them, which guides/sensors are required, or which rules require human confirmation.

## Current Gap

The intelligent improvement loop lacks structured workflow routing evidence. It can know that risk-based routing exists, but cannot reason about whether the current triggers are too broad, too narrow, missing security/data migration coverage, or lacking human confirmation.

This limits future `Maturity-driven Improve`, `LLM Maturity Reviewer`, and `Intelligent Asset Candidate Generation` because they must infer routing details from weak summary strings.

## Decision

Extend `maturity-evidence.yaml` with detailed workflow routing evidence copied from the validated `HarnessConfig.workflow_routing` contract.

Add a structured list under `harness_assets.workflow_routing_rules` with:

- `id`
- `selected_workflow`
- `task_type_hints`
- `triggers`
- `required_guides`
- `required_sensors`
- `human_confirmation_required`
- `rationale`

Keep the existing summary fields:

- `workflow_routing_rule_count`
- `has_standard_escalation_rule`

Benchmark will add a content check that fails if `maturity-evidence.yaml` does not expose detailed routing evidence matching `harness-config.yaml`.

## Boundaries

- Do not add task text classification.
- Do not call LLM in this milestone.
- Do not generate `.ai/task-runs`.
- Do not modify formal workflow rules based on evidence.
- Do not change `harness-config.yaml`; this milestone only projects the existing config into maturity evidence.

## Acceptance Criteria

- `MaturityEvidencePack` schema contains `harness_assets.workflow_routing_rules`.
- `collect_maturity_evidence()` populates routing rule details from `HarnessConfig`.
- Generated `.ai/maturity-evidence.yaml` includes the `standard-escalation` rule and its triggers.
- LLM maturity review prompt payload includes the detailed routing evidence automatically through `maturity_evidence`.
- Benchmark includes `content:maturity-routing-evidence` and fails when detailed routing evidence is missing or out of sync with `harness-config.yaml`.
- Existing no-runtime boundary remains covered: Builder still does not generate `.ai/task-runs`.

## Assumptions

- `harness-config.yaml` remains the authoritative source for workflow routing policy.
- `maturity-evidence.yaml` should duplicate enough routing detail for reviewers to work from a single evidence pack.
- Duplicating a small policy summary is acceptable because benchmark will verify consistency with the source config.

## Risks

- Duplicated routing detail could drift from `harness-config.yaml`; benchmark consistency checks mitigate this.
- The evidence pack will become slightly larger, but routing rules are small and machine-consumed.
