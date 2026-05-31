# Workflow Routing Policy Design

## Context

North Star module: Workflow Runtime Specification and Workflow Toolkit.

The strategy requires Harness Mapping to choose between Standard, Lightweight, and Bugfix workflows by task type, risk level, impact scope, restricted paths, confidence, and sensor coverage. The current implementation generates the three Workflow Skills and records them in `harness-config.yaml`, but it does not expose a machine-readable routing policy that a host AI Coding Runtime can consume.

## Current Gap

`harness-config.yaml` has workflow definitions but no routing rules. A host Runtime can see available workflows, but it cannot audit why a task should stay lightweight, use bugfix, or escalate to standard.

This is a Workflow Runtime Specification gap, not a runtime execution gap.

## Decision

Add a deterministic `workflow_routing` policy to `HarnessConfig` and generated `harness-config.yaml`.

The policy will include:

- default workflow: `lightweight`;
- ordered routing rules for bugfix intent, low-risk lightweight work, and standard escalation;
- explicit standard escalation triggers such as unclear impact, high-risk modules, cross-module design, security/permission, money/core state, data migration, low code-mapping confidence, insufficient sensor coverage, and required human business decisions;
- the selected workflow path and whether human confirmation is required.

Maturity evidence will expose routing policy coverage so later Maturity Reviewer and Improve flows can reason about risk-based routing. Benchmark will fail when the routing policy is missing, lacks a standard escalation rule, or points to an unknown workflow.

## Boundaries

- Do not classify arbitrary user task text in this milestone.
- Do not generate `.ai/task-runs`.
- Do not change `runtime.default_workflow`; it remains `lightweight`.
- Do not restore `harness-builder-agent run`.
- Do not use LLM for routing policy generation yet; this is a stable baseline contract.

## Acceptance Criteria

- `HarnessConfig.default()` includes `workflow_routing`.
- The routing policy has rules for `bugfix`, `lightweight`, and `standard`.
- The standard rule contains risk-based escalation triggers and `human_confirmation_required: true`.
- Generated `.ai/harness-config.yaml` serializes the policy.
- `maturity-evidence.yaml` records workflow routing rule count and whether standard escalation exists.
- Benchmark includes `content:workflow-routing-policy` and fails if the standard escalation rule is missing or references an unknown workflow.
- Tests keep proving Builder does not generate `.ai/task-runs`.

## Assumptions

- A deterministic baseline routing policy is useful before LLM-based task classification because it gives the host Runtime a stable contract.
- Dynamic routing recommendations can later consume this policy plus task text, runtime history, and maturity evidence.
- The policy should live in `harness-config.yaml` rather than a separate file for now because it is directly tied to configured Workflow Skills.

## Risks

- Static rules can look less intelligent than LLM classification. This milestone deliberately builds the audit contract first; later milestones can add LLM judgment against the contract.
- Overly broad standard escalation can push too many tasks into heavier flow. Keeping `default_workflow` as `lightweight` and making rules ordered avoids changing default behavior.
