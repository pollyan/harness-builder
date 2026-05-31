# Routing-Aware Asset Candidate Prompt Design

## Context

North Star modules: Intelligent Asset Candidate Generation, Maturity & Evolution, and Workflow Runtime Specification.

Harness Builder now exposes detailed `workflow_routing_rules` in `maturity-evidence.yaml`. The LLM asset candidate generator receives this evidence, but its prompt only gives generic instructions about Guide, Sensor, and Workflow candidates. It does not explicitly tell the LLM how to use routing rule evidence when drafting review-only `workflow_policy` candidates.

## Current Gap

The asset candidate generator can technically see routing evidence, but the prompt does not turn that evidence into an explicit reasoning contract. For workflow-related candidates, the LLM should inspect routing rule IDs, triggers, required guides, required sensors, human confirmation, and maturity review decisions before drafting `.ai/harness-config.yaml` policy changes.

Without this, routing-aware candidate generation depends on incidental model behavior.

## Decision

Update the LLM asset candidate prompt contract to make workflow routing evidence first-class.

The prompt will instruct the LLM to:

- inspect `maturity_evidence.harness_assets.workflow_routing_rules`;
- draft `workflow_policy` candidates when routing triggers, human confirmation, required guides, or required sensors need adjustment;
- prefer `.ai/harness-config.yaml` for workflow policy candidates;
- keep all workflow policy output review-only with `pending_harness_maintainer_review`;
- never claim routing changes were applied.

No schema changes are required. The existing `AssetCandidateDraft.kind == "workflow_policy"` and `suggested_path` validation already support this.

## Boundaries

- Do not call LLM during tests.
- Do not auto-apply candidate workflow policy changes.
- Do not alter `harness-config.yaml` generation.
- Do not add task text routing or runtime execution.
- Do not generate `.ai/task-runs`.

## Acceptance Criteria

- Asset candidate prompt includes explicit workflow routing evidence instructions.
- Asset candidate prompt payload includes `workflow_routing_rules` details when present.
- Unit tests cover routing-aware prompt behavior.
- Existing schema validation still rejects unknown source candidates and non-`.ai/` paths.
- Engineering docs mention asset candidate prompt must treat workflow routing evidence as review-only context.

## Assumptions

- Prompt-level guidance is the right next small step because the required structured evidence now exists.
- Later milestones can add task-brief-specific routing recommendation or richer workflow policy draft validation.

## Risks

- Prompt-only changes depend on model compliance. Existing strict JSON parsing and schema validation mitigate output format drift.
- Over-prescribing prompt behavior could reduce flexibility, so the instruction should focus on evidence use and review-only boundaries rather than fixed wording.
